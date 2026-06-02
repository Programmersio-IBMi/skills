# iA Quick Reference — Tool Selection

> **Rule Zero:** Never search the local workspace/filesystem for IBM i members or source — always resolve through `ia_*` tools. See [SKILL.md → Routing Pitfalls](../SKILL.md) for the common wrong-tool traps (F-specs, BIF search, join LFs, lifecycle).
>
> **Rule One:** UPPERCASE every object/member/file/field name before calling a tool (`iAdepRpt` → `IADEPRPT`). Names are stored uppercase; the tools also upper-case in SQL, but normalize on your side too.
>
> **Rule Two:** Empty result = not found. Report the negative; never substitute a similarly-named file and present its results instead.

## Top 10 Tools (80% of Queries)

| Tool | Use Case |
|------|----------|
| `ia_find_object_usages` | What references X? |
| `ia_file_field_impact_analysis` | Field change blast radius |
| `ia_call_hierarchy` | Call tree (callers/callees) |
| `ia_program_detail(section=*ALL)` | Everything about program X |
| `ia_unused_objects` | Dead code candidates |
| `ia_rpg_source` / `ia_cl_source` | Read source code line-by-line |
| `ia_code_complexity(member=*ALL)` | Complexity hotspots |
| `ia_object_lookup` | Find object by name (% wildcards) |
| `ia_dashboard` | Repository health overview |
| `ia_program_spec_bundle` | One-call spec inventory |

## User Intent → Tool Mapping

| User Intent | Single Best Tool | Returns |
|-------------|------------------|---------|
| "What uses X?" | `ia_find_object_usages` | Referencing objects with library, usage type, file usage |
| "Impact of field change?" | `ia_file_field_impact_analysis` | Affected programs + impact_type (NEEDS_CHANGE / NEEDS_RECOMPILE) |
| "LFs/views over file X?" | `ia_file_dependencies` | All dependents, bifurcated by SQL kind (INDEX/VIEW/DDS_LF/...); use `dependent_kind=INDEX` to filter |
| "Constraints/select-omit on file X?" | `ia_file_constraints` | PK/UQ/FK/CHECK + LF select/omit rules; `kind` filter |
| "Which fields in file X are reused as REFFLD?" | `ia_field_reffld_consumers` | Inverse of `ia_file_fields` — only fields acting as DDS reference templates |
| "Tell me about program X" | `ia_program_detail` (section=*ALL) | Calls, files, subs, vars, overrides — ALL in one query |
| "Call tree for X?" | `ia_call_hierarchy` | Callers + callees |
| "Dead code?" | `ia_unused_objects` | Zero-reference compiled objects |
| "Orphaned sources?" | `ia_uncompiled_sources` | Sources without compiled objects |
| "Complexity hotspots?" | `ia_code_complexity` (member=*ALL) | All programs ranked by complexity |
| "Find object named X?" | `ia_object_lookup` | Type/library/attr (supports % wildcards) |
| "System name for a SQL long table/column name?" (or where-used for one) | `ia_sql_table_names` → then `ia_find_object_usages` on the `system_short_name` | Long↔short for tables + columns; the where-used cross-reference only knows the 10-char system name |
| "Does member X exist?" | `ia_member_lookup` | Source file, library, type, timestamps |
| "Repository overview?" | `ia_dashboard` | Full inventory stats |
| "Copybook impact?" | `ia_copybook_impact` | Programs including the copybook |
| "What copybooks does X use?" | `ia_member_copybooks` | Copybooks included by a member |
| "SRVPGM exports?" | `ia_srvpgm_exports` | Exported/imported procedures |
| "Procedure callers?" | `ia_procedure_xref` | Procedure-level call graph |
| "Batch jobs?" | `ia_cl_jobs` | SBMJOB calls in CL programs |
| "Procedure signature?" | `ia_procedure_params` | PR/PI parameter definitions |
| "Show source for program X?" | `ia_object_lookup` → `ia_rpg_source` / `ia_cl_source` | Source lines with type/spec filtering |

## Tool Selection

| User Intent | Tool |
|-------------|------|
| What references object X? | `ia_find_object_usages` |
| How many refs to X? | `ia_reference_count` |
| What does X call / who calls X? | `ia_call_hierarchy` |
| Params passed at each call site? | `ia_call_parameters` — one row per param per call site; same callee on different `call_line`s = multiple sites, not dupes |
| Impact of changing field F in file X? | `ia_file_field_impact_analysis` |
| Variables in program X? | `ia_program_variables` |
| Data structures in program X? | `ia_data_structures` |
| Subroutines in program X? | `ia_subroutines` (not `ia_program_detail` — this adds usage_count + line_number) |
| File fields / formats for file X? | `ia_file_fields` |
| File overrides (OVRDBF)? | `ia_file_overrides`, `ia_override_chain` |
| What type/library is object X? | `ia_object_lookup` (compiled objects; if empty, try `ia_member_lookup` for source-only members) |
| Does member X exist? Metadata? | `ia_member_lookup` — pass the bare name; exact short names now resolve, add `%` only for wildcard search |
| Inventory of objects by type? | `ia_object_list`; for physical files use `object_attribute=PF-DATA` / `PF-SRC` (plain `PF` returns both with a `pf_kind` label) |
| List all display files in the repo? | `ia_object_list(object_type='*FILE', object_attribute='DSPF')` — display files are `*FILE`/attr `DSPF`, not `*DSPF` |
| Program metadata / compile info? | `ia_program_summary` |
| Lifecycle / last-used dates? | `ia_object_lifecycle` |
| Object size / largest or unused? | `ia_obj_size` |
| Dead code (compiled)? | `ia_unused_objects` (source physical files excluded; each row shows `OBJECT_ATTRIBUTE`) |
| Dead code (sources)? | `ia_uncompiled_sources` |
| Complexity hotspots? | `ia_code_complexity` |
| Circular call chains? | `ia_circular_deps` (SELF recursion + MUTUAL A↔B) |
| Repo health / member inventory? | `ia_dashboard` |
| List tables in iA library? | `ia_library_files` |
| Raw RPG/CL token stream? | `ia_rpg_source_tokens`, `ia_cl_source_tokens` |
| Source code for member X (RPG)? | `ia_rpg_source` |
| Source code for member X (CL)? | `ia_cl_source` |
| F-specs / D-specs / source declarations in X? | `ia_rpg_source(source_spec='F'/'D')` |
| Search RPG source for keyword? | `ia_rpg_source_search` |
| Find a BIF / `%keyword` (e.g. `%CHECK`) in source? | `ia_rpg_source_search` (pass the literal `%`) |
| Modernization / format stats? | `ia_rpg_source_stats` |
| Logical files over physical file X? | `ia_file_dependencies` |
| Join logical files over file X (+ join fields)? | `ia_join_logical_files` |
| Copybook change impact? | `ia_copybook_impact` |
| Copybooks used by member X? | `ia_member_copybooks` |
| SRVPGM exports/imports? | `ia_srvpgm_exports` |
| Procedure-level callers? | `ia_procedure_xref` |
| Procedure signature? | `ia_procedure_params` |
| Batch job detection? | `ia_cl_jobs` |
| **Document program X?** | [program-documentation.md](program-documentation.md) |
| **Export generated doc to Word/PDF?** | `scripts/convert_md_to_docx.py` / `scripts/convert_md_to_pdf.py` (see [program-documentation.md → Step 9](program-documentation.md)) |
