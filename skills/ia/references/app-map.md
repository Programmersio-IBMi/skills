# 3D Application Map Generation

Use this when a user asks for an **application map** of a library or application area ("app map of CASELIB", "3D map of the order area", "bird's-eye view of the application", "show me the whole application"). The deliverable is **two files**:

```
docs/app-maps/{SCOPE}/{SCOPE}_AppMap_Data.json   ← you write this (single source of truth)
docs/app-maps/{SCOPE}/{SCOPE}_AppMap.html        ← built BY SCRIPT from the JSON
```

`{SCOPE}` = the library name (`CASELIB`) or `{LIBRARY}_{AREA}` (`CASELIB_ORDERS`).

> **You only ever author the JSON.** The HTML is produced by `python scripts/build_app_map.py <json>` (path relative to this skill's folder), which validates the JSON and injects it into `templates/app-map-template.html`. **Never write or edit the HTML by hand, never touch the template.** The node/link vocabularies below are closed — never invent a new kind.

---

## 1. Resolve the scope

- **Whole library** → `ia_object_list(library=L)` is the inventory.
- **Application area** → `ia_application_area(area_name=A)` lists the area's objects. If the user's area name doesn't match, run `ia_application_area(area_name='*LIST')` and ask the user to pick — never substitute (Rule Two).
- Record `repository` from `ia_repo_config` (repository/library configuration) for the meta block.

## 2. Inventory and budget — target ≤ 75 in-scope nodes

Run once: `ia_code_complexity(library=L, limit=5000)` — this gives every member's total/executable lines and IF/SQL/subroutine/procedure counts. You'll use it for ranking AND for node stats.

**Fill the map in this order and STOP adding when you reach 75 in-scope nodes:**

1. Every `*MENU` (if more than 5, keep the 5 that launch the most programs).
2. Every program a kept menu launches — `ia_call_hierarchy(program_name=MENU, direction='CALLEES')`.
3. Remaining `*PGM`s ranked by **executable lines (descending)** from the complexity call, until programs total ~40.
4. Data physical files used by ≥2 kept programs, then by 1 (most-shared first) — from step 3 of the link rules below. **Data PFs only** (`object_attribute='PF-DATA'`); never map source physical files (QRPGLESRC, QCLSRC, …).
5. Display files (DSPF) and printer files (PRTF) used by kept programs.
6. Up to **5** uncompiled source members ≥ 500 lines (`ia_uncompiled_sources`, keep only rows in the scoped library) — these are the modernization-candidate "floating giants".
7. Up to **10** EXT nodes (out-of-scope programs called by kept programs — see link rules).

`meta.scope.totalObjects` = the full inventory count before trimming; `meta.scope.mappedObjects` = **exactly the number of non-EXT nodes in your file** (the builder fails on any mismatch). The viewer shows "X of Y objects mapped" automatically when they differ.

## 3. Nodes — classification is mechanical

| Object | `kind` | `attr` |
|--------|--------|--------|
| `*MENU` | `MENU` | MNUDDS |
| `*PGM` attribute RPGLE / SQLRPGLE / RPG / SQLRPG | `PGM_RPG` | the attribute |
| `*PGM` attribute CLLE / CLP / CL | `PGM_CL` | the attribute |
| `*FILE` attribute DSPF | `DSPF` | DSPF |
| `*FILE` data PF | `PF` | PF |
| `*FILE` attribute PRTF | `PRTF` | PRTF |
| Source member with no compiled object | `SOURCE` | member type |
| Called program outside the scope | `EXT` | *PGM if known |

Each node: `{ "id", "kind", "attr", "lines", "sourceFile", "desc", "stats" }`.

- **One node per name.** A `*MENU` usually has a same-named `*FILE` (DSPF) and `*MSGF` — map **only the MENU node**, skip the same-named siblings (duplicate ids fail the build). Likewise skip `*MODULE` rows when a `*PGM` of the same name exists.
- `attr` = the **member type** from the complexity call when present (catches SQLRPGLE — the compiled object often just says RPGLE), else the object attribute.
- `id` = the UPPERCASE object/member name. `lines` = total source lines (integer or `null` if unknown). `sourceFile` = source physical file name (QRPGLESRC, QDDSSRC, …).
- `stats` (programs and SOURCE only, from the complexity call): `{ "execLines": N, "subroutines": N, "procedures": N, "sql": N }` — include only non-zero values. If a node has no stats, **omit the key** (never write `"stats": {}`).
- **SOURCE means "no compiled object exists".** A member only becomes a SOURCE node if it appeared in `ia_uncompiled_sources`. If a name is in the `*PGM` inventory, it is a program — even when its source looks legacy. Never decide this from the source's size or style.
- `desc` — **one plain-language sentence, ≤ 160 chars**, business role first. Patterns: program → "*Customer maintenance — display, add and F4-lookup of customers.*"; PF → "*Customer master file.*"; DSPF → "*Customer maintenance screen.*"; PRTF → "*Order report layout (spool file).*"; SOURCE → "*Legacy source member — N lines, never compiled into any object.*"; EXT → "*External program — called from this application, outside the map's scope.*". For programs, derive the role from `ia_program_summary` and the object's text description — do not guess.

## 4. Links — one rule per kind

| `kind` | Direction | Source of truth |
|--------|-----------|-----------------|
| `MENU` | menu → program | `ia_call_hierarchy(MENU, 'CALLEES')` |
| `CALL` | caller → callee | `ia_call_hierarchy(PGM, 'CALLEES')` for each kept program |
| `SBMJOB` | CL → submitted pgm (self-loop allowed) | `ia_cl_jobs(member_name='*ALL')` once, keep rows whose CL member is in scope; carry `"job"` and `"jobQueue"` |
| `INPUT` | **file → program** | `ia_find_object_usages(object_name=PF)` once per kept PF — rows with `USING_TYPE='*PGM'` whose usage is only `I` |
| `UPDATE` | **program → file** | same call — rows whose usage contains `U` or `O` (e.g. `U`, `I/O/U`) |
| `DISPLAY` | program → DSPF | `ia_program_files(member_name=PGM)` rows whose file is a DSPF |
| `PRINT` | program → PRTF | `ia_program_files` rows whose file is a PRTF |

Each link: `{ "source", "target", "kind", "label" }` — keep labels short ("reads", "reads + writes", "menu option", "CALL in batch").

- **PF links come from `ia_find_object_usages`, not `ia_program_files`** — the file map has no read/write flag and misses tables reached only through embedded SQL (`REFERENCE_SOURCE = 'S'` rows). Per (program, PF) pair: any row with `U` or `O` in `REFERENCE_USAGE` → one UPDATE link; otherwise → one INPUT link. Ignore rows whose `USING_TYPE` is not `*PGM` (skips `*MODULE` duplicates and DSPF field references).
- **Note the INPUT direction:** data flows *from* the file *into* the program, so the file is the link `source`. UPDATE flows program → file.
- **One SBMJOB beats a self-CALL.** A CL that re-submits itself shows up both in `ia_cl_jobs` (SBMJOB) and as a self-reference in `ia_call_hierarchy` — emit only the SBMJOB self-link (the validator rejects a CALL self-link anyway).
- **Logical files are never nodes.** When a usage row's file is an LF, re-point the link to its based-on physical file: call `ia_file_dependencies(file_name=PF)` once per kept PF and collect its dependent LFs into a lookup; an LF whose parent PF isn't mapped → drop the link. After substitution, de-duplicate identical (source, target, kind) links.
- **EXT rule:** a callee that is not in the scope inventory becomes an EXT node and the link must be `CALL` into it. EXT nodes are never link sources and never get file/screen links.
- **SOURCE nodes get no links** — an uncompiled member has no compiled object, so iA records no relationships for it; the floating, disconnected node IS the message. The builder rejects any link touching a SOURCE node.
- A CL program that re-submits itself produces a SBMJOB **self-loop** — that's correct and renders as a loop; the validator allows self-links for SBMJOB only. Take the `job`/`jobQueue` values verbatim from the `ia_cl_jobs` row — the job name is usually NOT the CL's own name.

## 5. Guided tour — 5–7 steps, fixed storyline

Write `meta.tour` as an array of `{ "title", "text", "focus" }` (focus = a node id; omit it for a wrap-up step). Follow this storyline, **skipping any step whose subject doesn't exist**:

1. **The front door** — the menu (or most-called program if no menu).
2. **The workhorse** — the `PGM_RPG`/`PGM_CL` node with the highest `stats.execLines` **in your own nodes array**. A SOURCE node is never the workhorse — it doesn't run.
3. **The batch pattern** — the CL driver, if any SBMJOB link exists.
4. **Where the report lands** — the PRTF at the end of that batch chain.
5. **Shared data = shared risk** — the PF with the most program links **in your own links array**.
6. **The modernization candidate** — a SOURCE node, if any ("compiled into nothing").
7. **Wrap-up** (no focus) — restate the exact `meta.scope` numbers and that iA can drill into any node.

Titles ≤ 5 words; text 1–3 short sentences. **Every claim must be checkable against your own JSON** — names, counts and line numbers come from the nodes/links you wrote, nothing else. Never describe scheduling or frequency ("nightly", "overnight", "daily") — a SBMJOB is user-triggered unless a job-scheduler entry proves otherwise.

## 6. The meta block

```json
"meta": {
  "title": "CASELIB Application Map",
  "library": "CASELIB",
  "area": "ORDERS",                  ← only for area-scoped maps; omit otherwise
  "repository": "{REPOSITORY}",
  "generated": "2026-06-12",
  "author": "iA by programmers.io",
  "scope": { "totalObjects": 30, "mappedObjects": 26 },
  "tour": [ { "title": "…", "text": "…", "focus": "CASEMNU" } ]
}
```

## 7. Build — the only way to produce the HTML

```
python scripts/build_app_map.py docs/app-maps/{SCOPE}/{SCOPE}_AppMap_Data.json
```

Exit 0 → `{SCOPE}_AppMap.html` is written next to the JSON. Exit 1 → read each `ERROR:` line, fix the **JSON**, re-run. Never work around an error by editing HTML. Warnings (`WARN:`) don't block but read them — they catch over-budget maps and orphan nodes.

## 8. Browser gate — open the HTML and confirm

- [ ] Graph renders (not a black screen); needs internet for the CDN modules.
- [ ] Header shows the right library/scope and the stats chips match the JSON counts.
- [ ] Every node kind present appears in the filter list; toggling a filter hides those nodes.
- [ ] Search for one program by name — it flies to the node and opens the info panel with desc + connections.
- [ ] If SBMJOB links exist, the red batch loop is visible.
- [ ] EXT nodes (grey wireframe pyramids) sit at the edge with only incoming CALL links.
- [ ] Guided tour steps through and focuses the right nodes.

## Common errors

| Symptom | Fix |
|---------|-----|
| Builder: `kind 'X' is not one of …` | You invented a kind. Map the object using the §3 table — or leave it out. |
| Builder: `INPUT must be file → program …` (or similar direction error) | The link is inverted — swap `source` and `target`. INPUT is the only file→program kind; everything else flows out of the program. |
| Builder: `SOURCE … nodes are isolated by design` | You linked an uncompiled member, or misclassified a program as SOURCE / a SOURCE as a program. Re-check `ia_uncompiled_sources`. |
| Builder: `mappedObjects is N but the file has M` | Count your non-EXT nodes and set `meta.scope.mappedObjects` to that number. |
| Builder: `source/target … is not a node id` | A link references an evicted or misspelled node. Drop the link or add the node. |
| Builder warns `zero CALL links` | You almost certainly missed the program→driver→print chains — run `ia_call_hierarchy(CALLEES)` for every kept program. |
| Builder: `exceeds the hard cap` | Re-apply §2 fill order — evict lowest-ranked programs' files first, then programs. |
| Builder: `EXT node … cannot be a link source` | EXT is a CALL target only. If you know the external program's own links, it belongs in scope instead. |
| Map is a hairball in the browser | Too many nodes — trim toward 75; drop single-use PFs and PRTFs of minor programs. |
| A file shows no links | It was reached only through logical files whose parent PF you didn't map — apply the LF substitution rule in §4. |
| Tour step flies nowhere | Its `focus` id isn't a node — the builder catches this; re-run it. |
