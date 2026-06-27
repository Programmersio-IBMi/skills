#!/usr/bin/env python3
"""Validate an iA app-map data JSON and build the 3D viewer HTML from the bundled template.

Usage:
    python build_app_map.py <path/to/{SCOPE}_AppMap_Data.json> [--template <template.html>]

The JSON is the single source of truth. This script:
  1. Validates it (schema, closed kind enums, link integrity, node budget, tour refs).
  2. Injects it into templates/app-map-template.html (single __APP_MAP_DATA__ token).
  3. Writes {SCOPE}_AppMap.html next to the JSON.

Exit 0 = built. Exit 1 = validation errors (HTML not written). Warnings never block.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Windows pipes default to cp1252-strict; arrows/dashes in messages must not crash the run.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

NODE_KINDS = {"MENU", "PGM_RPG", "PGM_CL", "DSPF", "PF", "PRTF", "SOURCE", "EXT"}
LINK_KINDS = {"MENU", "CALL", "SBMJOB", "INPUT", "UPDATE", "DISPLAY", "PRINT"}

# Allowed (source-kind, target-kind) per link kind. Catches inverted directions
# (e.g. program -> PF INPUT), fabricated menu targets, and links on SOURCE nodes.
PGM = {"PGM_RPG", "PGM_CL"}
LINK_RULES = {
    "MENU":    (({"MENU"}),       PGM | {"EXT"},  "menu → program"),
    "CALL":    ((PGM),            PGM | {"EXT"},  "program → program (EXT allowed as target)"),
    "SBMJOB":  ((PGM),            PGM,            "CL/RPG → submitted program (self-loop allowed)"),
    "INPUT":   (({"PF"}),         PGM,            "file → program (data flows INTO the program)"),
    "UPDATE":  ((PGM),            {"PF"},         "program → file"),
    "DISPLAY": ((PGM),            {"DSPF"},       "program → display file"),
    "PRINT":   ((PGM),            {"PRTF"},       "program → printer file"),
}
META_REQUIRED = ["title", "library", "repository", "generated", "author"]
ID_RE = re.compile(r"^[A-Z0-9_#$@.]+$")
BUDGET_WARN = 75    # recipe target
BUDGET_FAIL = 90    # hard cap
EXT_WARN = 15
DESC_WARN = 160
DESC_FAIL = 200

errors, warnings = [], []
err = errors.append
warn = warnings.append


def validate(data: dict) -> None:
    if not isinstance(data, dict):
        err("Top level must be a JSON object with 'meta', 'nodes', 'links'.")
        return

    # ---- meta ----
    meta = data.get("meta")
    if not isinstance(meta, dict):
        err("Missing 'meta' object.")
        meta = {}
    for f in META_REQUIRED:
        if not meta.get(f):
            err(f"meta.{f} is required and must be non-empty.")
    scope = meta.get("scope")
    if not isinstance(scope, dict):
        err("meta.scope is required: {\"totalObjects\": N, \"mappedObjects\": N}.")
    else:
        tot, mapped = scope.get("totalObjects"), scope.get("mappedObjects")
        if not isinstance(tot, int) or not isinstance(mapped, int):
            err("meta.scope.totalObjects and meta.scope.mappedObjects must be integers.")
        elif mapped > tot:
            err(f"meta.scope.mappedObjects ({mapped}) cannot exceed totalObjects ({tot}).")

    # ---- nodes ----
    nodes = data.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        err("'nodes' must be a non-empty array.")
        nodes = []
    ids = set()
    empty_stats = []
    for i, n in enumerate(nodes):
        where = f"nodes[{i}]" + (f" ({n.get('id')})" if isinstance(n, dict) and n.get("id") else "")
        if not isinstance(n, dict):
            err(f"{where}: each node must be an object.")
            continue
        nid = n.get("id")
        if not nid:
            err(f"{where}: 'id' is required.")
            continue
        if nid in ids:
            err(f"{where}: duplicate node id '{nid}'.")
        ids.add(nid)
        if not ID_RE.match(nid):
            err(f"{where}: id '{nid}' must be UPPERCASE alphanumeric (A-Z 0-9 _ # $ @ .).")
        kind = n.get("kind")
        if kind not in NODE_KINDS:
            err(f"{where}: kind '{kind}' is not one of {sorted(NODE_KINDS)}.")
        desc = n.get("desc", "")
        if not desc or not str(desc).strip():
            err(f"{where}: 'desc' is required — one plain-language sentence.")
        elif len(desc) > DESC_FAIL:
            err(f"{where}: desc is {len(desc)} chars (max {DESC_FAIL}). Shorten it.")
        elif len(desc) > DESC_WARN:
            warn(f"{where}: desc is {len(desc)} chars (target ≤{DESC_WARN}).")
        lines = n.get("lines")
        if lines is not None and not isinstance(lines, int):
            err(f"{where}: 'lines' must be an integer or null.")
        if kind == "MENU" and n.get("attr") == "DSPF":
            warn(f"{where}: kind MENU with attr DSPF — did you pick the menu's same-named display file? "
                 f"A *MENU's attr is usually MNUDDS.")
        if n.get("stats") == {}:
            empty_stats.append(nid)

    if empty_stats:
        warn(f"{len(empty_stats)} node(s) have empty stats {{}} ({', '.join(empty_stats[:5])}"
             f"{', …' if len(empty_stats) > 5 else ''}) — omit the 'stats' key instead.")

    # ---- budget ----
    in_scope = sum(1 for n in nodes if isinstance(n, dict) and n.get("kind") != "EXT")
    ext_count = sum(1 for n in nodes if isinstance(n, dict) and n.get("kind") == "EXT")
    if isinstance(scope, dict) and isinstance(scope.get("mappedObjects"), int) \
            and scope["mappedObjects"] != in_scope:
        err(f"meta.scope.mappedObjects is {scope['mappedObjects']} but the file has {in_scope} "
            f"in-scope (non-EXT) nodes — set mappedObjects to the actual node count.")
    if in_scope > BUDGET_FAIL:
        err(f"{in_scope} in-scope nodes exceeds the hard cap of {BUDGET_FAIL}. "
            f"Apply the eviction rules in app-map.md (rank by reference count) or map a smaller area.")
    elif in_scope > BUDGET_WARN:
        warn(f"{in_scope} in-scope nodes exceeds the target of {BUDGET_WARN} — consider trimming.")
    if ext_count > EXT_WARN:
        warn(f"{ext_count} EXT nodes — boundary noise; consider keeping only the most-called externals.")

    # ---- links ----
    links = data.get("links")
    if not isinstance(links, list):
        err("'links' must be an array.")
        links = []
    ext_ids = {n.get("id") for n in nodes if isinstance(n, dict) and n.get("kind") == "EXT"}
    kind_of = {n.get("id"): n.get("kind") for n in nodes if isinstance(n, dict)}
    linked = set()          # ids with at least one non-self link
    seen_links = set()
    call_count = 0
    for i, l in enumerate(links):
        where = f"links[{i}]"
        if not isinstance(l, dict):
            err(f"{where}: each link must be an object.")
            continue
        s, t, kind = l.get("source"), l.get("target"), l.get("kind")
        where = f"links[{i}] ({s} → {t})"
        if s not in ids:
            err(f"{where}: source '{s}' is not a node id.")
        if t not in ids:
            err(f"{where}: target '{t}' is not a node id.")
        if kind not in LINK_KINDS:
            err(f"{where}: kind '{kind}' is not one of {sorted(LINK_KINDS)}.")
        elif s in ids and t in ids:
            src_ok, tgt_ok, shape = LINK_RULES[kind]
            sk, tk = kind_of.get(s), kind_of.get(t)
            if sk == "SOURCE" or tk == "SOURCE":
                err(f"{where}: SOURCE (uncompiled) nodes are isolated by design — they have no compiled "
                    f"object, so iA records no links for them. Remove the link or reclassify the node.")
            elif sk not in src_ok or tk not in tgt_ok:
                err(f"{where}: {kind} must be {shape}, but source is {sk} and target is {tk}. "
                    f"If the direction is inverted, swap source and target.")
        if s == t and kind != "SBMJOB":
            err(f"{where}: self-link only allowed for SBMJOB (CL re-submitting itself).")
        if s in ext_ids:
            err(f"{where}: EXT node '{s}' cannot be a link source — externals are CALL targets only.")
        if t in ext_ids and kind != "CALL":
            err(f"{where}: link into EXT node '{t}' must be kind CALL.")
        if kind == "SBMJOB" and not l.get("job"):
            warn(f"{where}: SBMJOB link without 'job' name.")
        if kind == "CALL":
            call_count += 1
        key = (s, t, kind)
        if key in seen_links:
            warn(f"{where}: duplicate link (same source, target, kind).")
        seen_links.add(key)
        if s != t:
            linked.update([s, t])

    for n in nodes:
        if isinstance(n, dict) and n.get("id") in ids - linked and n.get("kind") != "SOURCE":
            warn(f"node '{n['id']}' has no links to other nodes (self-loops don't count) — "
                 f"only SOURCE (uncompiled) nodes are expected to be isolated.")
    n_programs = sum(1 for n in nodes if isinstance(n, dict) and n.get("kind") in PGM)
    if call_count == 0 and n_programs >= 2:
        warn(f"{n_programs} programs but zero CALL links — verify ia_call_hierarchy(direction='CALLEES') "
             f"was run for every kept program (interactive→driver and driver→print chains are easy to miss).")

    # ---- tour ----
    tour = (meta or {}).get("tour")
    if tour is not None:
        if not isinstance(tour, list):
            err("meta.tour must be an array of steps.")
        else:
            if not 3 <= len(tour) <= 9:
                warn(f"meta.tour has {len(tour)} steps (recommended 5–7).")
            for i, step in enumerate(tour):
                if not isinstance(step, dict) or not step.get("title") or not step.get("text"):
                    err(f"meta.tour[{i}]: each step needs non-empty 'title' and 'text'.")
                    continue
                focus = step.get("focus")
                if focus and focus not in ids:
                    err(f"meta.tour[{i}]: focus '{focus}' is not a node id.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("json_path", help="Path to {SCOPE}_AppMap_Data.json")
    ap.add_argument("--template", default=None, help="Override template HTML path")
    args = ap.parse_args()

    json_path = Path(args.json_path)
    if not json_path.is_file():
        print(f"ERROR: {json_path} not found.")
        return 1
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON — {e}")
        return 1

    validate(data)

    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"\nFAILED — {len(errors)} error(s). Fix the JSON and re-run; the HTML was NOT built.")
        return 1

    template_path = Path(args.template) if args.template else \
        Path(__file__).resolve().parent.parent / "templates" / "app-map-template.html"
    if not template_path.is_file():
        print(f"ERROR: template not found at {template_path}")
        return 1
    template = template_path.read_text(encoding="utf-8")
    if template.count("__APP_MAP_DATA__") != 1:
        print("ERROR: template must contain the __APP_MAP_DATA__ token exactly once.")
        return 1

    # "</" inside a string (e.g. a desc containing "</script>") would terminate the inline
    # <script> block and break the page; "<\/" is the same string to the JS parser.
    payload = json.dumps(data, indent=2, ensure_ascii=False).replace("</", "<\\/")
    html = template.replace("__APP_MAP_DATA__", payload)
    if "__APP_MAP_" in html:
        print("ERROR: unresolved __APP_MAP_ token left in output — template is corrupt.")
        return 1

    stem = json_path.name
    out_name = (stem[: -len("_Data.json")] if stem.endswith("_Data.json") else json_path.stem) + ".html"
    out_path = json_path.with_name(out_name)
    out_path.write_text(html, encoding="utf-8")

    n_nodes = len(data["nodes"])
    n_ext = sum(1 for n in data["nodes"] if n.get("kind") == "EXT")
    print(f"OK: {out_path} built — {n_nodes} nodes ({n_ext} external), {len(data['links'])} links"
          + (f", {len(warnings)} warning(s)" if warnings else "") + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
