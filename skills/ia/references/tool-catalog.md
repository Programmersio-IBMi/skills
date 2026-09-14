# iA Tool Catalog (63 Tools)

**Rule:** Prefer the dedicated `ia_*` tools.

## Discovery — Start Here

| Tool | Purpose |
|------|---------|
| `ia_library_files` | List every file/table in any IBM i library |
| `ia_object_lookup` | Resolve object name → type, library, attribute (supports `%` wildcards). Covers **compiled objects** only; if empty, try `ia_member_lookup` for source-only members |
| `ia_member_lookup` | Source member metadata: existence, file/library/type, timestamps, line counts. Pass the bare name for an exact match (names shorter than 10 chars now resolve); add `%` only for prefix/substring search |
| `ia_object_list` | Inventory objects by type (`*PGM`, `*SRVPGM`, `*FILE`, ...); optional library filter. List **all display files** with `object_type=*FILE, object_attribute=DSPF` (no `*DSPF` type exists). For physical files, `pf_kind` labels each row Data PF / Source PF; filter `object_attribute=PF-DATA` or `PF-SRC` for one kind |
| `ia_program_summary` | Program overview: metadata, compile info, module type, complexity metrics |
| `ia_program_spec_bundle` | **One-call spec inventory** — LOOKUP/COMPLEXITY/FILES/CALLS/PARAMS/BINDINGS (replaces 7 calls) |
| `ia_program_detail` | Deep structural analysis with section filtering: CALLS, FILES, SUBROUTINES, VARIABLES, OVERRIDES, CALL_PARAMS |
| `ia_dashboard` | Repo health summary: categories, line counts, library map |
| `ia_repo_config` | iA configuration; usage stats freshness |

## Where-Used & References — Highest Impact

| Tool | Purpose |
|------|---------|
| `ia_object_context_matrix` | **One-call full context for any object** — everything it uses and everything that uses it, bucketed into sections (update/input/output files, display + printer files, calls, callers) and enriched with each referenced object's attribute, description, record formats, key fields and select/omit. Replaces `ia_object_references` + `ia_find_object_usages` + one `ia_object_lookup` per referenced object |
| `ia_find_object_usages` | Broad where-used: all objects referencing `object_name` (optional type + library filter) |
| `ia_object_references` | Inverse: what an object references/contains (modules in SRVPGM, files used) |
| `ia_reference_count` | Lightweight: counts of references grouped by type |
| `ia_file_field_impact_analysis` | Field-level blast radius: programs affected if field X in file Y changes |

## Call Graph

| Tool | Purpose |
|------|---------|
| `ia_call_hierarchy` | Returns callers and/or callees for a program or module; follows `*MENU`→`*PGM` so menu-launched programs appear |
| `ia_call_parameters` | Parameters passed at each external call site; includes `call_line` + `call_type`. Same callee on different `call_line`s = multiple call sites, not duplicate rows |
| `ia_circular_deps` | Detect circular dependencies: SELF recursion (A→A) + MUTUAL (A↔B); returns cycle_type + source_table columns |

## Program Internals

| Tool | Purpose |
|------|---------|
| `ia_program_variables` | All variables declared in a member; `variable_type` is readable scope/kind (Global/Local/Program variable, Constant, Compile-time/Pre-runtime/Run-time array) |
| `ia_data_structures` | Data structure definitions and subfields; `ds_type` is readable (Externally described / Internally described / Based) |
| `ia_subroutines` | BEGSR/EXSR with usage counts (dead-subroutine detection); filter by member/library |

## Files & Overrides

| Tool | Purpose |
|------|---------|
| `ia_file_fields` | Field-level metadata: names, aliases, types, lengths, key sequence, reference chain |
| `ia_field_reffld_consumers` | Inverse of `ia_file_fields`: only the fields **referenced as REFFLD by other files**, with consumer file/field/type info (use this for "which fields in CUSTMST are reused as templates?") |
| `ia_file_dependencies` | LFs, indexes, views dependent on a physical file. Bifurcated by SQL kind (`SQL_OBJECT_TYPE` = INDEX/VIEW/TABLE/MQT/DDS_LF). Use `dependent_kind` to filter. |
| `ia_join_logical_files` | Join logical files and their join structure: which physical files each join LF combines and the join field pairs. Pass `file_name` to find join LFs over a specific file (returns the full join), or `*ALL` to list all. |
| `ia_file_constraints` | DB constraints (PK/UQ/FK/CHK) + LF select/omit rules in one call. Use `kind` to narrow (SELECT_OMIT, FOREIGN_KEY, etc.) |
| `ia_file_overrides` | OVRDBF statements — real file routing vs. declared F-spec |
| `ia_override_chain` | Chained OVRDBF dependencies (A→B→C) |

## Source-Level Analysis

| Tool | Purpose |
|------|---------|
| `ia_rpg_source` | Read RPG source line-by-line. Returns only SOURCE_RRN + SOURCE_DATA — pass a specific `member_name` and `library_name`. Use `ia_rpg_source_search` for cross-member keyword search. Cap 10000 lines/call — paginate with `offset` for larger sources |
| `ia_cl_source` | Read CL/CLLE/CLP source line-by-line. Returns only SOURCE_RRN + SOURCE_DATA — pass a specific `member_name` and `library_name`. Cap 10000 lines/call — paginate with `offset` for larger sources |
| `ia_synon_source` | Read Synon/2E source line-by-line. Returns only SOURCE_RRN + SOURCE_DATA — pass a specific `member_name` and `library_name`. Cap 10000 lines/call — paginate with `offset` for larger sources |
| `ia_synon_functions` | **Entry point for any 2E work from a name.** Resolves a 2E design name, implementation name, **or a generated AD member name** (`F1101013_F` / `F1101013_C`) — all mixed case, spaces and `%` wildcards — to the `pgm_surrogate_id` the other two Synon tools require. The AD-member match is not a convenience: internal function types (`CRTOBJ`, `CHGOBJ`, `DLTOBJ`, `RTVOBJ`, `EXCINTFUN`, `PRTOBJ`) carry a **blank** implementation name, so the AD member name is the only name they resolve by — and it is what a user reads off a Synon export. The match spans every generation on record, not just the latest. Also returns function type (→ Program Type) and the generated full/concise AD member names to pass to `ia_synon_source`, with generation date |
| `ia_dds_source` | Read DDS source line by line — display files (DSPF), PF/LF definitions, printer files (PRTF) and menu source (MNUDDS/MNUCMD). Returns MEMBER_NAME + MEMBER_TYPE + SOURCE_RRN + SOURCE_DATA. **The only tool that exposes DDS**, and the required source for two things nothing else answers: display-file **screen field labels** (the RPG carries only programmatic names) and **menu option numbers/text** (`{MENU}QQ`/`MNUCMD` holds `NNNN CALL PGM(x)`, `{MENU}`/`MNUDDS` holds the positioned text). `member_name` takes `%` wildcards — `'CASEMNU%'` pulls both menu members in one call. Both name params are case-insensitive. Cap 10000 lines/call — paginate with `offset` |
| `ia_synon_action_diagram` | Parsed action diagram of a 2E function: one row per statement in execution order (`line_sequence`) with the nesting tree resolved (`statement_id`/`parent_statement`/`depth`). Keyed by `pgm_surrogate_id` — **not** a member name; the table has no member/library column. Filters: `operation` (case-insensitive, but blank on ~40% of statements — `*ALL` + `search_text` is the reliable sweep), `search_text`. `owner_table` is `*NONE` on every row in the repositories checked so far — it cannot currently isolate file actions. Cap 10000 statements/call — paginate with `offset` |
| `ia_synon_variable_ops` | Variable operands per AD statement: 2E context (`PAR`/`DB1`/`LCL`/`WRK`/`CON`/`JOB`/`PGM`/`CND`/`NLL`/`ELM`…), direction (`IN` read / `OUT` written / `BOTH` read+written / `NONE`) and `variable_seq`, in execution order with the statement text. Every field written = `OUT` **plus** `BOTH` — `OUT` alone under-reports; `variable_context=PAR` → the parameter list. Names are mixed-case descriptive 2E names ("Changed User") — do **not** upper-case them. **Sparsely populated** (most functions in a model may have no operand rows): empty = not captured, not "writes nothing" — fall back to `raw_text` |
| `ia_rpg_source_search` | Cross-member keyword search in RPG source |
| `ia_rpg_source_stats` | Modernization metrics: free-format %, comment ratio |
| `ia_rpg_source_tokens` | Token-level RPG parse |
| `ia_cl_source_tokens` | Token-level CL parse |

## Lifecycle, Complexity, Cleanup

| Tool | Purpose |
|------|---------|
| `ia_object_lifecycle` | Creation/change/last-used dates, days-used count |
| `ia_obj_size` | Object size + usage category (Never/Rare) — lookup or rank |
| `ia_code_complexity` | IF/DO/SQL/GOTO/PROC counts, executable lines; includes LIBRARY_NAME |
| `ia_unused_objects` | Dead code candidates (compiled but never referenced); source physical files are excluded and each row shows `OBJECT_ATTRIBUTE` |
| `ia_uncompiled_sources` | Orphaned sources (never compiled into objects) |
| `ia_dds_to_ddl_status` | DDS→DDL modernization tracking |
| `ia_exception_log` | iA parser errors per member |

## Advanced Analysis

| Tool | Purpose |
|------|---------|
| `ia_copybook_impact` | Programs including a copybook via /COPY |
| `ia_member_copybooks` | Copybooks used by a source member |
| `ia_srvpgm_exports` | Service program exported/imported procedures |
| `ia_procedure_xref` | Procedure-level cross-reference |
| `ia_procedure_params` | Procedure PR/PI signatures; `%` wildcards in `procedure_name` only; filter by member/library (both exact) |
| `ia_cl_jobs` | CL SBMJOB/CALL detection with job queue info |
| `ia_variable_ops` | Variable declarations, assignments, BIF usage; `*ALL` for cross-member |
| `ia_klist_usage` | KLIST/KFLD key list definitions; `%` wildcards in kfld_name |
| `ia_application_area` | Forward: area → objects; Reverse: object → areas (`%` supported) |
| `ia_sql_names` | SQL long/short name mapping for **routines** (procedures/functions) |
| `ia_variant_summary` | Cross-library comparison roll-up — counts of IDENTICAL / COSMETIC / LOGIC / SINGLE members. Fixed-size result; call before `ia_member_variants` |
| `ia_member_variants` | Per-member/per-library variant letters + verdict. Same letter = identical source. Defaults to `verdict=LOGIC` |
| `ia_sql_table_names` | SQL long↔short name mapping for **tables + columns** (`CREATE TABLE ... FOR SYSTEM NAME`); resolve a long name to its 10-char system name before where-used. Complements `ia_sql_names` |
| `ia_program_files` | Program file usage with PREFIX/RENAME; filter by member/library |
| `ia_build_job_history` | Run log of every metadata build/refresh iA submitted, **across every repository**, not just the one being analyzed. Repo, INIT/REFRESH, real IBM i job, submitter, triggering program, submit + end timestamp, `run_minutes`. Filter by repo/mode/status/user/`called_from`/`days_back`. `job_status=P` or `S` finds builds that never finished. `status_text` is an **inferred** decode of `C`/`P`/`S` — trust the raw code when it matters |
| `ia_build_job_summary` | Per-repository roll-up of the same log — total builds, INIT vs REFRESH, completed/in-progress/submitted, last build, last completion, last attempt's mode + status, avg and max duration. **Run this before trusting any analysis**: iA tables are a build snapshot. Read `last_status_text` first; the timestamps are on different clocks (`last_build_ts` = submitted, `last_completed_ts` = ended), so only `last_completed_ts` *earlier* than `last_build_ts` means the newest build never finished |
| `ia_scheduled_refresh` | iA's standing schedule — which repositories rebuild/refresh automatically, under which IBM i scheduler entry, frequency, owner, plus last run + outcome. The **only** source that maps a scheduler job name back to the repository and purpose it serves. `process_date`/`process_time` are CHAR — they hold `*MONTHEND`/`*CURRENT` as well as real values |
| `ia_job_schedule_entries` | The application's batch schedule captured from the IBM i job scheduler at build time. OS status SCHEDULED/HELD/SAVED, frequency, days, next submission date, job queue, command, job description. **Excludes IBM `Q*` system entries.** Appended per build — `snapshot_scope` defaults to `*LATEST` (one row per job); `*ALL` shows drift. Only exists in repos built by a newer collector — SQL0204 means the repo predates the table, not that nothing is scheduled |
