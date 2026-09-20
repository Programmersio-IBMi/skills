#!/usr/bin/env python3
"""Build an iA 3D application map: fetch -> validate -> inject into the viewer.

The rows never pass through an AI context. This script talks to the iA MCP
server over HTTP, writes the graph JSON, checks it against the app-map JSON
contract (version 2), and injects it into the viewer template.

    python build_app_map.py fetch    --url http://host:3010/mcp [--library *ALL]
    python build_app_map.py validate --data PATH [--upgrade]
    python build_app_map.py build    --data PATH [--template PATH] [--out PATH]
    python build_app_map.py all      --url http://host:3010/mcp [--library *ALL]

Python 3.9+, standard library only.
"""

import argparse
import base64
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

CONTRACT = 2

NODE_TOOL = "ia_app_map_nodes"
LINK_TOOL = "ia_app_map_links"
CLUSTER_TOOL = "ia_app_map_clusters"
SCHEME_TOOL = "ia_app_map_schemes"
RULE_TOOL = "ia_app_map_rules"
LIB_TOOL = "ia_app_map_libraries"

RATE_LIMIT_CODE = -32003

# Known vocabularies. Unknown values are reported, never rejected: the engine
# adds kinds over time (*CMD nodes are already specified).
NODE_KINDS = {"MENU", "PGM_RPG", "PGM_CL", "SRVPGM", "DSPF", "PF", "PRTF", "SOURCE", "CMD"}
LINK_KINDS = {"MENU", "CALL", "SBMJOB", "INPUT", "UPDATE", "DISPLAY", "PRINT", "BIND"}

# Contract keys whose value is a number.
NUM_KEYS = {"lines", "fin", "fout", "seq", "hits", "clusters", "cov", "rule", "id", "prio", "nodes"}

TOKEN = "__APPMAP_DATA__"


class AppMapError(Exception):
    """A failure the user can act on. Printed without a traceback."""


class ToolMissing(AppMapError):
    pass


# ---------------------------------------------------------------- MCP client


class McpClient:
    """Minimal MCP streamable-HTTP client: initialize, tools/list, tools/call."""

    def __init__(self, url, token=None, insecure=False, timeout=300):
        self.url = url
        self.token = token
        self.timeout = timeout
        self.session_id = None
        self.tools = {}
        self._rpc_id = 0
        self._ctx = None
        if insecure:
            self._ctx = ssl.create_default_context()
            self._ctx.check_hostname = False
            self._ctx.verify_mode = ssl.CERT_NONE

    # -- transport

    def _post(self, payload, attempt=0):
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        if self.session_id:
            req.add_header("Mcp-Session-Id", self.session_id)
        if self.token:
            req.add_header("Authorization", "Bearer " + self.token)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
                if sid:
                    self.session_id = sid
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            if exc.code in (429, 503) and attempt < 6:
                wait = _retry_after(exc.headers, detail) or min(2 ** attempt, 30)
                print("       server is busy - waiting %ds (try %d of 6)" % (wait, attempt + 1))
                time.sleep(wait)
                return self._post(payload, attempt + 1)
            if exc.code in (429, 503):
                raise AppMapError(
                    "The server is rate limiting this client (HTTP %d) and did not recover.\n"
                    "Wait a few minutes, then run it again. A smaller --page makes each call\n"
                    "cheaper but uses more of them, so it does not help a per-request limit."
                    % exc.code)
            if exc.code in (401, 403):
                raise AppMapError(
                    "Authentication failed (HTTP %d) at %s.\n"
                    "Supply --token / IA_MCP_TOKEN, or --user and --password."
                    % (exc.code, self.url)
                )
            raise AppMapError("Server returned HTTP %d at %s.\n%s" % (exc.code, self.url, detail))
        except urllib.error.URLError as exc:
            raise AppMapError(
                "Cannot reach the iA MCP server at %s (%s).\n"
                "Check the URL, that the server is running, and any VPN or firewall.\n"
                "For a self-signed certificate add --insecure." % (self.url, exc.reason)
            )
        return _parse_body(raw)

    def _rpc(self, method, params=None, notify=False, attempt=0):
        self._rpc_id += 1
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if not notify:
            payload["id"] = self._rpc_id
        body = self._post(payload)
        if notify or body is None:
            return None
        if "error" in body:
            error = body["error"] or {}
            message = str(error.get("message", error))
            # A rate limit can arrive as a JSON-RPC error on a 200 response.
            if (error.get("code") == RATE_LIMIT_CODE or "rate limit" in message.lower()):
                if attempt < 6:
                    wait = _retry_after(None, message) or min(2 ** attempt, 30)
                    print("       server is busy - waiting %ds (try %d of 6)" % (wait, attempt + 1))
                    time.sleep(wait)
                    return self._rpc(method, params, notify, attempt + 1)
                raise AppMapError(
                    "The server is rate limiting this client and did not recover.\n%s\n"
                    "Wait a few minutes, then run it again." % message)
            raise AppMapError("Server refused %s: %s" % (method, message))
        return body.get("result", {})

    # -- protocol

    def connect(self):
        self._rpc(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "ia-build-app-map", "version": "2"},
            },
        )
        self._rpc("notifications/initialized", notify=True)
        cursor = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            result = self._rpc("tools/list", params) or {}
            for tool in result.get("tools", []):
                schema = tool.get("inputSchema") or {}
                self.tools[tool["name"]] = schema.get("properties") or {}
            cursor = result.get("nextCursor")
            if not cursor:
                break
        return self.tools

    def has(self, name):
        return name in self.tools

    def max_limit(self, name, want):
        """Honour the `limit` cap the tool declares - servers cap it and reject anything larger."""
        spec = (self.tools.get(name) or {}).get("limit") or {}
        cap = spec.get("maximum")
        return min(want, int(cap)) if isinstance(cap, (int, float)) else want

    def call(self, name, args):
        """Return (rows, metadata). Arguments the tool does not declare are dropped."""
        if not self.has(name):
            raise ToolMissing(
                "This server does not have the app-map tools (%s is missing).\n"
                "Ask your iA administrator to update the iA MCP server to a release that\n"
                "includes the app-map tools, then run this again." % name
            )
        allowed = self.tools[name]
        sent = {k: v for k, v in args.items() if not allowed or k in allowed}
        if "limit" in sent:
            sent["limit"] = self.max_limit(name, sent["limit"])
        for attempt in range(3):
            result = self._rpc("tools/call", {"name": name, "arguments": sent}) or {}
            try:
                return _rows_from_result(name, result)
            except ToolMissing:
                raise
            except AppMapError as exc:
                # The server's database pool drops when idle; the next call reconnects.
                if attempt == 2 or not any(s in str(exc).lower()
                                           for s in ("not connected", "connection", "timed out")):
                    raise
                print("       database connection dropped - retrying %s" % name)
                time.sleep(3)


def _retry_after(headers, body):
    """How long the server wants us to wait: the header, else the seconds it names in the body."""
    try:
        value = float((headers or {}).get("Retry-After") or 0)
        if value > 0:
            return min(int(value) + 1, 300)
    except (TypeError, ValueError):
        pass
    match = re.search(r"(\d+)\s*second", body or "")
    if match:
        return min(int(match.group(1)) + 2, 300)
    return 0


def _parse_body(raw):
    """Accept a plain JSON body or an SSE stream of `data:` lines."""
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith("{") or raw.startswith("["):
        return json.loads(raw)
    chunks = [line[5:].strip() for line in raw.splitlines() if line.startswith("data:")]
    for chunk in reversed(chunks):  # the last data line carries the response
        if chunk and chunk != "[DONE]":
            return json.loads(chunk)
    raise AppMapError("Could not read the server response (no JSON and no SSE data line).")


def _rows_from_result(name, result):
    """Pull the row list out of whatever shape the SQL tool wrapper returned."""
    payload = result.get("structuredContent")
    if payload is None:
        text = ""
        for item in result.get("content") or []:
            if item.get("type") == "text":
                text = item.get("text") or ""
                break
        if result.get("isError"):
            raise _tool_error(name, text)
        try:
            payload = json.loads(text)
        except (ValueError, TypeError):
            raise AppMapError("Tool %s returned text this script cannot read:\n%s" % (name, text[:300]))

    if isinstance(payload, list):
        return payload, result.get("_meta") or {}
    if not isinstance(payload, dict):
        raise AppMapError("Tool %s returned an unexpected result type (%s)." % (name, type(payload).__name__))

    if payload.get("success") is False or "error" in payload:
        err = payload.get("error") or {}
        raise _tool_error(name, err.get("message") if isinstance(err, dict) else str(err))
    if result.get("isError"):
        raise _tool_error(name, json.dumps(payload)[:300])

    for key in ("data", "rows", "results"):
        if isinstance(payload.get(key), list):
            return payload[key], payload.get("metadata") or {}
    return [], payload.get("metadata") or {}


def _tool_error(name, message):
    message = (message or "").strip()
    if "not found" in message.lower() and name.lower() in message.lower():
        return ToolMissing(
            "This server does not have the app-map tools (%s is missing).\n"
            "Ask your iA administrator to update the iA MCP server to a release that\n"
            "includes the app-map tools, then run this again." % name
        )
    return AppMapError("Tool %s failed: %s" % (name, message or "no message returned"))


def get_bearer_token(mcp_url, user, password, insecure=False, timeout=60):
    """Exchange IBM i credentials for a bearer token at <base>/api/v1/auth."""
    base = re.sub(r"/mcp/?$", "", mcp_url.rstrip("/"))
    auth_url = base + "/api/v1/auth"
    basic = base64.b64encode(("%s:%s" % (user, password)).encode("utf-8")).decode("ascii")
    req = urllib.request.Request(auth_url, data=b"", method="POST")
    req.add_header("Authorization", "Basic " + basic)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    ctx = None
    if insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = json.loads(resp.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as exc:
        raise AppMapError(
            "Authentication failed (HTTP %d) at %s.\n"
            "Check the IBM i user and password, or use --token instead." % (exc.code, auth_url)
        )
    except urllib.error.URLError as exc:
        raise AppMapError("Cannot reach the authentication endpoint %s (%s)." % (auth_url, exc.reason))
    for key in ("access_token", "token", "jwt", "bearer", "accessToken"):
        value = body.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, dict) and isinstance(value.get("token"), str):
            return value["token"]
    raise AppMapError("The authentication endpoint %s returned no token field." % auth_url)


# ---------------------------------------------------------------- row shaping


def _shape(row):
    """Column alias (uppercase) -> contract key (lowercase). Unknown columns pass through."""
    out = {}
    for key, value in row.items():
        key = key.lower()
        if value is None:
            value = "" if key not in NUM_KEYS else 0
        elif isinstance(value, str):
            value = value.strip()
            if key in NUM_KEYS:
                try:
                    value = int(value) if value else 0
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
        elif isinstance(value, float) and key in NUM_KEYS and value.is_integer():
            value = int(value)
        out[key] = value
    return out


def _page(client, tool, base_args, page, label, warnings):
    page = client.max_limit(tool, page)
    pageable = "offset" in (client.tools.get(tool) or {})
    rows, offset, meta = [], 0, {}
    while True:
        args = dict(base_args)
        args["offset"] = offset
        args["limit"] = page
        batch, batch_meta = client.call(tool, args)
        meta = meta or batch_meta
        rows.extend(_shape(r) for r in batch)
        if len(batch) < page or not pageable:
            break
        offset += page
        if offset > 2_000_000:
            warnings.append("%s stopped at %d rows - the server kept returning full pages." % (label, offset))
            break
    return rows, meta


def _repo_from_metadata(meta):
    """The tool echoes its SQL; the schema qualifier is the repository library."""
    sql = (meta or {}).get("sqlStatement") or ""
    match = re.search(r"\bFROM\s+(\"?[A-Za-z0-9_$#@]+\"?)\s*\.", sql)
    if match:
        return match.group(1).strip('"').upper()
    return None


def _libraries(nodes, rows=None):
    """Prefer the library rows the server returned; otherwise derive them from the nodes."""
    if rows:
        used = {n.get("lib") for n in nodes}
        out = [r for r in rows if not used or r.get("lib") in used]
        if out:
            for index, row in enumerate(sorted(out, key=lambda r: (r.get("seq") or 10_000, r.get("lib") or ""))):
                row["seq"] = row.get("seq") or (index + 1) * 10
                row.setdefault("descr", "")
            return sorted(out, key=lambda r: (r["seq"], r.get("lib") or ""))
    seen = {}
    for node in nodes:
        lib = node.get("lib") or ""
        if not lib:
            continue
        seq = node.get("seq")
        if lib not in seen or (not seen[lib] and seq):
            seen[lib] = seq if isinstance(seq, int) and seq else 0
    ordered = sorted(seen.items(), key=lambda kv: (kv[1] or 10_000, kv[0]))
    out = []
    for index, (lib, seq) in enumerate(ordered):
        out.append({"lib": lib, "seq": seq or (index + 1) * 10, "descr": ""})
    return out


def _built(schemes, nodes):
    stamps = []
    for row in list(schemes) + list(nodes):
        for key in ("built", "refreshed_at", "refreshed"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                stamps.append(value.strip())
    return max(stamps)[:19] if stamps else ""


# -------------------------------------------------------------------- fetch


def cmd_fetch(args):
    started = time.time()
    warnings = []

    token = args.token or os.environ.get("IA_MCP_TOKEN")
    if args.user:
        if not args.password:
            raise AppMapError("--user needs --password.")
        token = get_bearer_token(args.url, args.user, args.password, args.insecure)
        print("auth   : bearer token obtained for %s" % args.user)

    client = McpClient(args.url, token=token, insecure=args.insecure)
    client.connect()
    print("server : %s  (%d tools)" % (args.url, len(client.tools)))
    for tool in (SCHEME_TOOL, NODE_TOOL, LINK_TOOL, CLUSTER_TOOL):
        if not client.has(tool):
            raise ToolMissing(
                "This server does not have the app-map tools (%s is missing).\n"
                "Ask your iA administrator to update the iA MCP server to a release that\n"
                "includes the app-map tools, then run this again." % tool
            )

    lib = args.library
    schemes, meta = client.call(SCHEME_TOOL, {"library": lib, "limit": args.page})
    schemes = [_shape(r) for r in schemes]
    nodes, node_meta = _page(client, NODE_TOOL, {"library": lib}, args.page, "nodes", warnings)
    links, _ = _page(client, LINK_TOOL, {"library": lib, "kind": "*ALL"}, args.page, "links", warnings)
    clusters, _ = _page(client, CLUSTER_TOOL, {"library": lib, "scheme": "*ALL"}, args.page, "clusters", warnings)

    rules = []
    if client.has(RULE_TOOL):
        try:
            rules, _ = _page(client, RULE_TOOL, {}, args.page, "rules", warnings)
        except AppMapError as exc:
            warnings.append("rules not read (%s) - the map is still valid, business-area names may be missing."
                            % str(exc).splitlines()[0])
    else:
        warnings.append("rules tool not on this server - the map is still valid, "
                        "business-area names may be missing.")

    lib_rows = []
    if client.has(LIB_TOOL):
        try:
            lib_rows, _ = _page(client, LIB_TOOL, {}, args.page, "libraries", warnings)
        except AppMapError as exc:
            warnings.append("library names not read (%s) - derived from the objects instead."
                            % str(exc).splitlines()[0])

    repo = args.repo or _repo_from_metadata(node_meta) or _repo_from_metadata(meta)
    if not repo:
        repo = "UNKNOWN"
        warnings.append("repository name not reported by the server - using UNKNOWN. Pass --repo to set it.")

    out_path = args.out or os.path.join("docs", "app-maps", repo, "%s_AppMap_Data.json" % repo)
    notes = _carry_notes(out_path, warnings)

    data = {
        "contract": CONTRACT,
        "repo": repo,
        "built": _built(schemes, nodes),
        "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "mcp",
        "libraries": _libraries(nodes, lib_rows),
        "nodes": nodes,
        "links": links,
        "clusters": clusters,
        "schemes": schemes,
        "rules": rules,
        "notes": notes,
    }

    _write_json(out_path, data)
    print("repo   : %s   built %s" % (repo, data["built"] or "(not reported)"))
    print("counts : nodes=%d links=%d clusters=%d schemes=%d rules=%d libraries=%d"
          % (len(nodes), len(links), len(clusters), len(schemes), len(rules), len(data["libraries"])))
    print("wrote  : %s  (%.0f KB, %.1fs)"
          % (out_path, os.path.getsize(out_path) / 1024.0, time.time() - started))
    for warning in warnings:
        print("WARN   : %s" % warning)
    return out_path


def _carry_notes(out_path, warnings):
    if not os.path.exists(out_path):
        return {}
    try:
        with open(out_path, encoding="utf-8") as handle:
            old = json.load(handle)
    except (ValueError, OSError):
        return {}
    notes = old.get("notes") or {}
    if notes:
        warnings.append("carried %d existing note(s) over from the previous file." % len(notes))
    return notes if isinstance(notes, dict) else {}


def _write_json(path, data):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))


# ----------------------------------------------------------------- validate


def load_data(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise AppMapError("No such data file: %s\nRun `build_app_map.py fetch` first." % path)
    except ValueError as exc:
        raise AppMapError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(data, dict):
        raise AppMapError("%s must hold a JSON object." % path)
    return data


def validate(data, path="(data)"):
    """Return (errors, warnings, info). Never raises on content problems."""
    errors, warnings, info = [], [], []

    if "meta" in data or (isinstance(data.get("nodes"), list) and data["nodes"]
                          and "id" in data["nodes"][0]):
        errors.append(
            "retired v1 format (meta / desc / tour). That hand-authored shape is no longer built. "
            "Re-fetch with `build_app_map.py fetch`.")
        return errors, warnings, info

    contract = data.get("contract")
    if contract is None:
        warnings.append("no `contract` key - assuming contract %d. Run `validate --upgrade` to stamp it."
                        % CONTRACT)
    elif contract != CONTRACT:
        errors.append("contract is %r, this script builds contract %d only." % (contract, CONTRACT))
        return errors, warnings, info

    for key in ("generated", "source", "repo"):
        if not data.get(key):
            warnings.append("no `%s` key - older export. Run `validate --upgrade` to fill it." % key)

    for key in ("nodes", "links", "clusters", "schemes"):
        if not isinstance(data.get(key), list):
            errors.append("`%s` is missing or is not an array." % key)
    if errors:
        return errors, warnings, info

    nodes, links = data["nodes"], data["links"]
    clusters, schemes = data["clusters"], data["schemes"]

    if not schemes:
        errors.append("`schemes` is empty - the viewer builds its lens list from it and would show nothing.")

    # nodes
    index, by_name = set(), set()
    unknown_kinds = {}
    for pos, node in enumerate(nodes):
        lib, name = node.get("lib"), node.get("name")
        if not lib or not name:
            errors.append("nodes[%d] has no lib/name." % pos)
            continue
        index.add((lib, name))
        by_name.add(name)
        kind = node.get("kind") or ""
        if kind not in NODE_KINDS:
            unknown_kinds[kind] = unknown_kinds.get(kind, 0) + 1
    if len(index) != len(nodes):
        warnings.append("%d duplicate (library, name) node rows." % (len(nodes) - len(index)))
    for kind, count in sorted(unknown_kinds.items()):
        warnings.append("node kind %r on %d row(s) is not in the known list - the viewer draws it as generic."
                        % (kind, count))

    # links. A target may sit in a sibling library: `tlib` names it when the engine
    # resolved it, otherwise the viewer resolves the bare name across the libraries.
    unknown_link_kinds = {}
    missing_src = dangling = crosslib = unresolved = 0
    for link in links:
        lib, src, tgt = link.get("lib"), link.get("src"), link.get("tgt")
        kind = link.get("kind") or ""
        if kind not in LINK_KINDS:
            unknown_link_kinds[kind] = unknown_link_kinds.get(kind, 0) + 1
        if not src or (lib, src) not in index:
            missing_src += 1
            continue
        if tgt and (lib, tgt) in index:
            continue
        if tgt and tgt in by_name:
            crosslib += 1
        elif str(link.get("inscope", "")).upper() == "N":
            unresolved += 1
        else:
            dangling += 1
    if missing_src:
        errors.append("%d link(s) start at an object that is not a node in the same library." % missing_src)
    if dangling:
        warnings.append("%d link(s) marked in-scope point at an object that is nowhere in the map - "
                        "the viewer will drop them." % dangling)
    if crosslib:
        info.append("%d cross-library link target(s) - resolved in a sibling library." % crosslib)
    if unresolved:
        info.append("%d link target(s) outside the repository - shown as unresolved." % unresolved)
    for kind, count in sorted(unknown_link_kinds.items()):
        warnings.append("link kind %r on %d row(s) is not in the known list." % (kind, count))

    # clusters: never more than one primary per (library, lens, object). Zero is legal
    # when every row in the group is a fallback bucket (`_DUPLICATE`, `_NONE`, `_NOMENU`)
    # - a duplicate name is primary in the other library, by design.
    primaries, fallback_only = {}, {}
    for row in clusters:
        key = (row.get("lib"), row.get("scheme"), row.get("name"))
        primaries[key] = primaries.get(key, 0) + (1 if str(row.get("prim", "")).upper() == "Y" else 0)
        is_fallback = str(row.get("cid") or "").startswith("_")
        fallback_only[key] = fallback_only.get(key, True) and is_fallback
    multi = sum(1 for key, count in primaries.items() if count > 1)
    zero = [key for key, count in primaries.items() if count == 0 and not fallback_only[key]]
    if multi:
        errors.append("%d (library, lens, object) group(s) have more than one primary cluster." % multi)
    if zero:
        warnings.append("%d (library, lens, object) group(s) have no primary cluster and no fallback "
                        "bucket - the viewer leaves them ungrouped in that lens." % len(zero))

    if not data.get("rules"):
        warnings.append("no rules rows - business-area names may be missing. The map is still valid.")

    if len(nodes) > 2000:
        info.append("%d nodes. Above ~2000 a single map gets hard to read: build one map per library "
                    "(--library LIB), or split by lens." % len(nodes))

    info.append("%d nodes, %d links, %d cluster rows, %d lenses, %d rules, %d note(s)"
                % (len(nodes), len(links), len(clusters), len(schemes),
                   len(data.get("rules") or []), len(data.get("notes") or {})))
    return errors, warnings, info


def upgrade(data, path):
    """Fill the envelope keys an older export is missing. Returns True when changed."""
    changed = False
    if data.get("contract") != CONTRACT:
        data["contract"] = CONTRACT
        changed = True
    if not data.get("source"):
        data["source"] = "mcp"
        changed = True
    if not data.get("generated"):
        stamp = datetime.fromtimestamp(os.path.getmtime(path)) if os.path.exists(path) else datetime.now()
        data["generated"] = stamp.strftime("%Y-%m-%dT%H:%M:%S")
        changed = True
    if not data.get("repo"):
        data["repo"] = os.path.basename(path).split("_")[0].upper() or "UNKNOWN"
        changed = True
    if not data.get("libraries"):
        data["libraries"] = _libraries(data.get("nodes") or [])
        changed = True
    if not data.get("built"):
        data["built"] = _built(data.get("schemes") or [], data.get("nodes") or [])
        changed = True
    if "notes" not in data:
        data["notes"] = {}
        changed = True
    return changed


def cmd_validate(args):
    data = load_data(args.data)
    if args.upgrade:
        if upgrade(data, args.data):
            _write_json(args.data, data)
            print("upgraded envelope: contract=%d repo=%s source=%s"
                  % (data["contract"], data["repo"], data["source"]))
        else:
            print("envelope already complete - nothing to upgrade.")
    errors, warnings, info = validate(data, args.data)
    for line in info:
        print("INFO   : %s" % line)
    for line in warnings:
        print("WARN   : %s" % line)
    for line in errors:
        print("ERROR  : %s" % line)
    if errors:
        raise SystemExit(1)
    print("OK     : %s matches the app-map contract." % args.data)
    return data


# -------------------------------------------------------------------- build


def default_template():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "templates", "app-map-template.html")


def cmd_build(args):
    started = time.time()
    data = load_data(args.data)
    errors, warnings, info = validate(data, args.data)
    for line in info:
        print("INFO   : %s" % line)
    for line in warnings:
        print("WARN   : %s" % line)
    for line in errors:
        print("ERROR  : %s" % line)
    if errors:
        raise SystemExit(1)

    template_path = args.template or default_template()
    try:
        with open(template_path, encoding="utf-8") as handle:
            html = handle.read()
    except FileNotFoundError:
        raise AppMapError("No viewer template at %s." % template_path)
    if html.count(TOKEN) != 1:
        raise AppMapError("The template %s must contain %s exactly once (found %d)."
                          % (template_path, TOKEN, html.count(TOKEN)))

    repo = data.get("repo") or "UNKNOWN"
    out_path = args.out or os.path.join("docs", "app-maps", repo, "%s_AppMap.html" % repo)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace(TOKEN, payload)

    parent = os.path.dirname(os.path.abspath(out_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(html)

    print("template: %s" % template_path)
    print("wrote   : %s  (%.0f KB, data %.0f KB, %.1fs)"
          % (out_path, os.path.getsize(out_path) / 1024.0, len(payload) / 1024.0, time.time() - started))
    print("open it in a browser to check the map.")
    return out_path


def cmd_all(args):
    data_path = cmd_fetch(args)
    print("-" * 60)
    # --out on `all` names the JSON. Never let build write the HTML over it.
    args.data = data_path
    args.out = _html_beside(data_path) if args.out else None
    return cmd_build(args)


def _html_beside(data_path):
    base = os.path.basename(data_path)
    for suffix in ("_Data.json", "_data.json", ".json"):
        if base.endswith(suffix):
            base = base[:-len(suffix)]
            break
    if not base.endswith("_AppMap"):
        base += "_AppMap"
    return os.path.join(os.path.dirname(data_path), base + ".html")


# --------------------------------------------------------------------- main


def build_parser():
    parser = argparse.ArgumentParser(
        prog="build_app_map.py",
        description="Fetch iA app-map data over MCP and build the 3D viewer HTML.")
    subs = parser.add_subparsers(dest="command", required=True)

    def add_fetch_args(sub):
        sub.add_argument("--url", default=os.environ.get("IA_MCP_URL", "http://localhost:3010/mcp"),
                         help="iA MCP server URL (env IA_MCP_URL, default http://localhost:3010/mcp)")
        sub.add_argument("--library", default="*ALL", help="library to map, or *ALL (default)")
        sub.add_argument("--repo", help="repository name, when the server does not report it")
        sub.add_argument("--token", help="bearer token (env IA_MCP_TOKEN)")
        sub.add_argument("--user", help="IBM i user, exchanged for a token")
        sub.add_argument("--password", help="IBM i password, used with --user")
        sub.add_argument("--insecure", action="store_true", help="skip TLS certificate checks")
        sub.add_argument("--page", type=int, default=5000, help="rows per page (default 5000)")
        sub.add_argument("--out", help="output JSON path")

    add_fetch_args(subs.add_parser("fetch", help="pull the engine tables into a graph JSON"))

    validate_parser = subs.add_parser("validate", help="check a graph JSON against the contract")
    validate_parser.add_argument("--data", required=True, help="path to the graph JSON")
    validate_parser.add_argument("--upgrade", action="store_true",
                                 help="fill missing envelope keys in place")

    build_parser_ = subs.add_parser("build", help="inject a graph JSON into the viewer template")
    build_parser_.add_argument("--data", required=True, help="path to the graph JSON")
    build_parser_.add_argument("--template", help="viewer template (default: the one in this skill)")
    build_parser_.add_argument("--out", help="output HTML path")

    all_parser = subs.add_parser("all", help="fetch then build")
    add_fetch_args(all_parser)
    all_parser.add_argument("--template", help="viewer template (default: the one in this skill)")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        {"fetch": cmd_fetch, "validate": cmd_validate, "build": cmd_build, "all": cmd_all}[args.command](args)
    except AppMapError as exc:
        print("ERROR  : %s" % exc, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nstopped.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
