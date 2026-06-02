---
name: ia
description: Guide for using iA by programmers.io MCP tools to analyze IBM i programs — dependency tracing, call hierarchies, field impact, source retrieval, and program documentation. ALWAYS use this skill for ANY IBM i analysis question.
---

# iA Impact Analysis — Agent Guide

iA by [programmers.io](https://programmers.io/ia/) pre-parses IBM i source (RPG, CL, COBOL, DDS) into a queryable repository accessed through the `ia_*` MCP tools.

**Goal:** Answer most questions in 1-2 tool calls. Consult [quick-reference.md](references/quick-reference.md) for tool selection, [tool-catalog.md](references/tool-catalog.md) for the full 51-tool list.

## Rule Zero — Always Query iA, Never the Workspace

Never search the local workspace or filesystem for IBM i members, objects, or source. The programs you are asked about do **not** live in the editor's files — they live in the iA repository. For any "show me / find / specs for `<member>`" request, resolve through the `ia_*` tools (`ia_member_lookup` / `ia_object_lookup`, then `ia_rpg_source` / `ia_cl_source`). Do not grep the workspace and do not report "not found" until iA itself returns nothing.

## Rule One — Always UPPERCASE Object/Member/File Names

IBM i stores every object, member, file, field, program, and procedure name in **UPPERCASE**. Always upper-case names before calling any `ia_*` tool, no matter how the user typed them (`iAdepRpt` → `IADEPRPT`, `custmast` → `CUSTMAST`). The tools now also upper-case name parameters in SQL as a safety net, but normalize on your side too — a lower/mixed-case name that slips through matches nothing.

## Rule Two — Empty Means Not Found; Never Substitute

If a tool returns zero rows for a name you passed, the object/file/field **does not exist** in the repository (under that name). Report the negative plainly ("`ITMMAST` / `ITEMNO` was not found"). Do **not** silently swap in a similarly-named file and present its results as if they answered the question — that produces the wrong analysis. If you suspect a typo, use `ia_object_lookup`/`ia_member_lookup` with `%` wildcards to suggest close matches, and let the user confirm.

## Routing Pitfalls (pick the right tool the first time)

| Ask | Use | Not |
|-----|-----|-----|
| Calculation / F / D specs for member X | `ia_rpg_source(member_name=X, source_spec=C/F/D)` | workspace search; `ia_program_files` |
| File declarations (F-specs) in X | `ia_rpg_source(member_name=X, source_spec='F')` | `ia_program_files` — that's the resolved file-access map, not source lines |
| Find a BIF like `%CHECK` / `%SCAN` | `ia_rpg_source_search(search_text='%CHECK')` — pass the literal `%`; it now matches the BIF exactly | `ia_find_object_usages` (object cross-ref, not source text) |
| Join logical files over file X | `ia_join_logical_files(file_name=X)` | `ia_file_dependencies` — lists dependents but not the join structure |
| Lifecycle / when modified for X (library unknown) | `ia_object_lifecycle(object_name=X)` — library & type are optional | passing the iA repo library as the object library |
| List **all** display files in the repo | `ia_object_list(object_type='*FILE', object_attribute='DSPF')` | `ia_find_object_usages` — it's where-used for ONE object, not an inventory; there is no `*DSPF` type |
| Every program a menu launches (e.g. CASEMNU) | `ia_call_hierarchy(program_name=MENU, direction='CALLEES')` — now follows `*MENU`→`*PGM` | assuming menus aren't tracked |
| List the subroutines in program X | `ia_subroutines(member_name=X)` — adds usage_count + line_number (dead-sub detection) | `ia_program_detail` SUBROUTINES section — omits usage count and line number |
| Parameters passed by program X | `ia_call_parameters(member_name=X)` — one row per parameter per call site; same callee on different `call_line`s = multiple call sites, not duplicates | reading repeated rows as dupes |
| Where-used / field impact for a SQL **long** name (e.g. `CUSTOMER_MASTER`, column `ERROR_MESSAGE`) | `ia_sql_table_names(name_pattern=X)` → take `system_short_name`, then `ia_find_object_usages` / `ia_file_field_impact_analysis` on that 10-char name | passing the long name straight to where-used — it matches only the 10-char system name and caps input at 10 chars, so it silently returns nothing |
| Long↔short name of a SQL table/column vs a procedure/function | `ia_sql_table_names` (tables + columns) | `ia_sql_names` — that one covers routines (procedures/functions) only |
| Which library / type is **object** X | `ia_object_lookup(object_name=X)` — compiled objects (`*PGM`/`*FILE`/`*SRVPGM`…). If empty, X may be a source-only member → fall back to `ia_member_lookup(member_name=X)` | `ia_member_lookup` first for a compiled object |
| Member X "not found" by `ia_member_lookup` | pass the **bare** name (`IORDV11`) — exact names now resolve; only add `%` for prefix/substring search | concluding it's missing — a name shorter than 10 chars used to fail silently |
| `ia_rpg_source` returns nothing | confirm `MEMBER_TYPE` first (`ia_member_lookup`): CL/CLLE/CLP → `ia_cl_source`; COBOL isn't in the RPG tables. Empty ≠ missing | assuming the source doesn't exist |
| "Obsolete / unreferenced objects" | `ia_unused_objects` — source physical files (QRPGLESRC, QCLSRC…) are already excluded; remaining `*FILE` rows show `OBJECT_ATTRIBUTE` | treating every unreferenced `*FILE` as dead — DSPF/PRTF and SQL-only tables can be false positives |
| Data files vs source files in a library | `ia_object_list(object_attribute='PF-DATA')` for data files, `'PF-SRC'` for source files; plain `PF` returns both with a `pf_kind` label | assuming a source library (QRPGLESRC etc.) has data files — it usually has none |

## Top 10 Tools (80% of Queries)

| Tool | Use Case |
|------|----------|
| `ia_find_object_usages` | What references X? |
| `ia_file_field_impact_analysis` | Field change blast radius |
| `ia_call_hierarchy` | Call tree (callers/callees) |
| `ia_program_detail(section=*ALL)` | Everything about program X |
| `ia_unused_objects` | Dead code candidates |
| `ia_rpg_source` / `ia_cl_source` | Read source code line-by-line (RPG vs CL) |
| `ia_code_complexity(member=*ALL)` | Complexity hotspots |
| `ia_object_lookup` | Find object by name (% wildcards) |
| `ia_dashboard` | Repository overview |
| `ia_program_spec_bundle` | One-call spec inventory |

## Core Workflows

### Source Code Retrieval (2 calls)

1. `ia_member_lookup` or `ia_object_lookup` → Confirm MEMBER_TYPE and SOURCE_LIBRARY
2. Route by member type:
   - `RPGLE`, `SQLRPGLE`, `RPG`, `SQLRPG` → `ia_rpg_source(member_name=X, library_name=L)`
   - `CLLE`, `CLP`, `CL` → `ia_cl_source(member_name=X, library_name=L)`
3. **Pagination:** Both tools cap `limit` at 10000. If `TOTAL_LINES` (from `ia_code_complexity`) > 10000, loop with `offset=0,10000,…` until you have the full source.

**Multiple members:** Show first with source. List others briefly. Ask which to show.

### Field Impact Analysis (3-4 calls, synthesize into one response)

> If `X`/`Y` is a SQL **long** name (a `CREATE TABLE`/column long name, often >10 chars), resolve it first: `ia_sql_table_names(name_pattern=X)` → use the returned `system_short_name`/`column_short_name`. The PF and field cross-references are keyed by the 10-char system name.

1. `ia_file_field_impact_analysis(file_name=X, field_name=Y)` → Direct PF references. **If this returns empty, the file/field doesn't exist — say so (Rule Two), don't analyze a different file.**
2. `ia_file_dependencies(file_name=X)` → LFs/indexes/views over PF
3. `ia_find_object_usages` on every STRUCTURAL `*FILE` from step 1 (parallel)
4. `ia_find_object_usages(object_name=<each_LF>)` from step 2 (parallel)

Present as four sections: **Direct (NEEDS_CHANGE)**, **Direct (NEEDS_RECOMPILE)**, **Structural Dependents**, **Programs via LF**.

## When to Chain

**DO chain:** `*SRVPGM` in results (amplifier — check what binds to it), field impact (run all steps), a **SQL long name** before any system-name tool (resolve via `ia_sql_table_names` → use the `system_short_name`).

**DON'T chain:** Simple counts (count your results), every `*PGM` (only critical ones), `ia_member_lookup` just for location.

## Parameter Rules

- Object/member/file/field names: **uppercase** (`'CUSTMAST'`) — see Rule One
- `object_type`: Star-prefixed (`*PGM`, `*SRVPGM`, `*FILE`, `*CMD`, `*MENU`). **Display files are `*FILE` + attribute `DSPF`** — there is no `*DSPF` object type
- Wildcard `*ALL` = no filter (default for optional params)
- Only `ia_object_lookup` supports `%` wildcards in names

## Interpreting Results

| Value | Meaning |
|-------|---------|
| `*SRVPGM` in results | Amplifier — always check dependents |
| `DSPF` attribute on a `*FILE` row | User-facing display file — flag prominently (it is a `*FILE`, not a `*DSPF` type) |
| Empty results | Object/file not found under that name (Rule Two), or scheduler-invoked / external |
| `REFERENCE_SOURCE = O` | Detected from compiled object |
| `REFERENCE_SOURCE = S` | Detected from source code |
| `REFERENCE_USAGE = I` | Implicit (via binding directory) |
| `REFERENCE_USAGE = E` | Explicit (direct bind/call) |

**Empty results with library filter:** Report the negative explicitly. Don't silently retry without filter.

## Response Rules

- **Always use tables** for lists of objects, programs, dependencies
- **Group by impact_type:** NEEDS_CHANGE, NEEDS_RECOMPILE, STRUCTURAL
- **Summarize by object type**, count references, state risk level
- **Suggest concrete next step**

For detailed formatting examples, see [playbook.md](references/playbook.md).

## Response Branding

For reports/deliverables: `Author: iA by programmers.io`. First mention: "iA by programmers.io". Subsequent: just "iA". Skip branding for quick lookups.

## Document Export (Word / PDF)

If the user asks to export a generated program-documentation `.md` to **Word** or **PDF**, use the converter scripts bundled with this skill at `scripts/convert_md_to_docx.py` and `scripts/convert_md_to_pdf.py`. They are self-contained, apply iA branding automatically, and write output next to the source `.md`. See [program-documentation.md → Step 9](references/program-documentation.md) for invocation, dependencies, and operational rules.

## Connection / Tool Failures

If the iA repository cannot be reached or `ia_*` tools fail with connection or configuration errors (no library configured, MCP server unreachable, repeated tool errors), tell the user:

> The iA MCP server appears to be unavailable or misconfigured. Please contact **programmers.io support** at [programmers.io/ia/](https://programmers.io/ia/) for assistance.

Do not attempt to diagnose server-side issues or retry indefinitely.

## References

| Need | Load |
|------|------|
| Tool selection unclear | [quick-reference.md](references/quick-reference.md) |
| Full 51-tool list | [tool-catalog.md](references/tool-catalog.md) |
| Complex analysis chains | [query-flows.md](references/query-flows.md) |
| Analysis playbooks | [playbook.md](references/playbook.md) |
| Program documentation | [program-documentation.md](references/program-documentation.md) |
