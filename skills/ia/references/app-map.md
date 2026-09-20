# 3D Application Map

Use this when someone asks for an **application map** — "app map of CASELIB", "3D map of the order area", "show me the whole application", "bird's-eye view".

## What it is

An app map is a 3D picture of a library (or of every library in the repository). Every object is a node. Every relationship is a link. You fly through it in a browser.

A **lens** is one way of grouping the objects — by business area, by layer, by activity, by menu, and so on. The iA engine builds the lenses on the IBM i and stores them. The map shows one lens at a time. Nothing about the lenses is hardcoded in the viewer: the map offers whatever lenses the engine built.

The deliverable is two files:

```
docs/app-maps/{REPO}/{REPO}_AppMap_Data.json   the graph data
docs/app-maps/{REPO}/{REPO}_AppMap.html        the viewer, built from that data
```

`{REPO}` = the iA repository name. The script fills it in for you.

## The pipeline

```
engine on IBM i  ->  ia_app_map_* tools  ->  build_app_map.py  ->  {REPO}_AppMap.html
```

## THE RULE

> **You never extract the rows. You never read the rows.**
> You run the script, you read the counts it prints, and you open the HTML.

The engine already did the analysis. The script moves the result from the server to the file. A map of a mid-size library is tens of thousands of rows. Pulling those through your context costs a fortune and adds nothing — the script is the ETL, not you.

You may call `ia_app_map_schemes` yourself, to show the user which lenses exist. That is a handful of rows. Everything else is script work.

## Workflow

### 1. Ask for the scope

One library, or the whole repository? Default is the whole repository (`*ALL`). If the user names a library, pass it.

Do not guess a library name. If the user is vague, run `ia_app_map_schemes(library='*ALL')` and show them the libraries and lenses that exist.

### 2. Build it

One command does everything:

```bash
python .claude/skills/ia/scripts/build_app_map.py all --url http://SERVER:3010/mcp
```

For one library:

```bash
python .claude/skills/ia/scripts/build_app_map.py all --url http://SERVER:3010/mcp --library CASELIB
```

The URL comes from the user or from the `IA_MCP_URL` environment variable. Default is `http://localhost:3010/mcp`.

If the server needs credentials:

```bash
--token YOUR_TOKEN              # or set IA_MCP_TOKEN
--user  YOURUSER --password ... # exchanged for a token by the server
--insecure                      # self-signed certificate
```

The script writes both files under `docs/app-maps/{REPO}/` and prints counts, sizes and warnings. Read those lines. Do not ask for the data.

### 3. Open it

Open `docs/app-maps/{REPO}/{REPO}_AppMap.html` in the browser and confirm it renders. Then tell the user the counts and where the files are.

### The three steps on their own

`all` is `fetch` then `build`. Run them separately when you need to:

```bash
python .claude/skills/ia/scripts/build_app_map.py fetch    --url URL [--library LIB] [--out PATH]
python .claude/skills/ia/scripts/build_app_map.py validate --data PATH [--upgrade]
python .claude/skills/ia/scripts/build_app_map.py build    --data PATH [--template PATH] [--out PATH]
```

- `fetch` pulls the data and writes the JSON. It pages the big tables for you.
- `validate` checks the JSON against the contract. Exit 0 = good. Exit 1 = read the `ERROR:` lines.
- `build` validates, then injects the JSON into the viewer template.

`build` is also how you rebuild after you edit the JSON — see notes below.

## Notes: the only AI work

The map ships with no prose. When the user asks "explain this program", "what is this cluster", you write short text into the JSON and rebuild. That is the one place your tokens belong.

1. Pick the objects to describe. **At most 75.** Ask the user which ones, or take the cluster they are looking at.
2. Get the facts with the normal tools: `ia_program_summary`, `ia_object_context_matrix`, `ia_call_hierarchy`.
3. Write the text into the `notes` map in the JSON:

```json
"notes": {
  "DEMOERP/OEENTRY":        "Order entry. Writes the order header and lines, then submits the pick list.",
  "cluster:AREA/AR":        "Accounts receivable: invoicing, cash receipts and the aged debt report."
}
```

Keys are `"LIBRARY/OBJECT"` or `"cluster:SCHEME/CLUSTER_ID"`. One or two plain sentences each. Every claim must come from a tool result, never from the name.

4. Rebuild:

```bash
python .claude/skills/ia/scripts/build_app_map.py build --data docs/app-maps/{REPO}/{REPO}_AppMap_Data.json
```

A later `fetch` to the same file keeps the notes you wrote. It says so in its output.

## Verification checklist

- [ ] `fetch` printed non-zero counts for nodes, links, clusters and schemes.
- [ ] You read every `WARN:` line and told the user about any that matter.
- [ ] `build` exited 0 and reported the HTML size.
- [ ] The HTML opens in a browser and the graph renders (it loads its 3D library from a CDN, so the machine needs internet).
- [ ] The lens list in the viewer matches the lens count the script reported.
- [ ] Counts you quote to the user come from the script output, not from memory.

## Troubleshooting

| What you see | What it means | What to do |
|---|---|---|
| `does not have the app-map tools` | The server is an older iA release | Ask the iA administrator to update the iA MCP server. Nothing on your side fixes it. |
| `Cannot reach the iA MCP server` | Wrong URL, server down, VPN off | Check the URL with the user. Confirm the server is running. |
| `Authentication failed` | No token, wrong token, wrong password | Add `--token` / `IA_MCP_TOKEN`, or `--user` and `--password`. |
| TLS / certificate error | Self-signed certificate on the server | Add `--insecure`. |
| `server is busy - waiting Ns` | The server rate-limits each client | Nothing. The script waits as long as the server asks and carries on. A big repository can take a few minutes. |
| `rate limiting this client ... did not recover` | The limit outlasted six waits | Wait a few minutes and run it again. A smaller `--page` does not help a per-request limit. |
| `WARN: rules ...` / `no rules rows` | The rules seed is not reachable | The map is still valid. Business-area cluster names may be missing or generic. Say so; do not retry. |
| `retired v1 format` | An old hand-written map file | That shape is gone. Run `fetch` to make a new one. |
| `contract is N` | The file is from a newer or older producer | Re-fetch. Do not edit the file to get past it. |
| `no 'contract' key` (warning only) | A file made before the envelope existed | It still builds. `validate --data PATH --upgrade` stamps the missing keys. |
| `link(s) start at an object that is not a node` | The engine data is inconsistent | Report it. It is an engine defect, not a script bug. |
| `link(s) marked in-scope point at an object that is nowhere in the map` | The target was not built as a node | Warning only. The viewer drops those links. Mention the count; do not try to fix the file. |
| `group(s) have no primary cluster and no fallback bucket` | An object is ungrouped in one lens | Warning only. It still shows; it just sits outside the lens grouping. |
| `node kind 'X' is not in the known list` | The engine added a new object kind | Harmless. The viewer draws it as a generic node. |
| `cross-library link target(s)` (info) | A program uses an object in a sibling library | Normal in a multi-library repository. Nothing to do. |
| Repository shows as `UNKNOWN` | The server did not report its schema | Re-run with `--repo NAME`. |
| Map is an unreadable hairball | Too many objects in one picture | Re-run with `--library LIB`. See Future scenarios. |

## Future scenarios

The design already covers these. None of them needs a new script.

**One library instead of everything.** `--library LIB`. The lens list, the links and the libraries block all narrow to that library on their own.

**More than about 2000 objects.** `validate` says so. Build one map per library. A 10 000-object library is still too much for one picture — the agreed answer is a drill-down: an overview map of clusters first, then a detail map per cluster. That is designed but not built yet. Until it ships, split by library and by lens, and say plainly that a single map of that size will not read well.

**The JSON produced on the IBM i.** A future iA release exports the same JSON straight from the box (built by the iA engine) with `"source": "ifs"`. Take that file and run `build --data PATH`. No fetch, no MCP server, same viewer. The script accepts it because the contract is the same.

**New lenses.** The viewer builds its lens list from the data. When the engine adds a lens, it appears in the next map with no change here.

**New engine columns.** Unknown columns pass through the script untouched and the viewer ignores what it does not know. New node kinds and link kinds produce a warning, never a failure — `*CMD` objects are already on the way.

**A server that does not have the tools yet.** Not every customer runs the newest iA release. The script says so in one line and names the fix: the administrator updates the server. Do not try to work around it by reading rows yourself — that is the flow this replaced.

**Offline.** The viewer loads its 3D library from a CDN, so the machine viewing the map needs internet. Fetching and building do not. For a demo on a closed network, build the map in advance and check it opens on that machine.

## Notes on the template

`templates/app-map-template.html` is the viewer. The script injects the data into the `__APPMAP_DATA__` token inside it. **Never edit the HTML the script produced, and never hand-edit the data into a template.**
