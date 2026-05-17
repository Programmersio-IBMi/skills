# iA Tool Catalog (50 Tools)

**Rule:** Prefer the dedicated `ia_*` tools.

## Discovery — Start Here

| Tool | Purpose |
|------|---------|
| `ia_library_files` | List every file/table in any IBM i library |
| `ia_object_lookup` | Resolve object name → type, library, attribute (supports `%` wildcards) |
| `ia_member_lookup` | Source member metadata: existence, file/library/type, timestamps, line counts |
| `ia_object_list` | Inventory objects by type (`*PGM`, `*SRVPGM`, `*FILE`, ...); optional library filter |
| `ia_program_summary` | Program overview: metadata, compile info, complexity metrics |
| `ia_program_spec_bundle` | **One-call spec inventory** — LOOKUP/COMPLEXITY/FILES/CALLS/PARAMS/BINDINGS (replaces 7 calls) |
| `ia_program_detail` | Deep structural analysis with section filtering: CALLS, FILES, SUBROUTINES, VARIABLES, OVERRIDES, CALL_PARAMS |
| `ia_dashboard` | Repo health summary: categories, line counts, library map |
| `ia_repo_config` | iA configuration; usage stats freshness |

## Where-Used & References — Highest Impact

| Tool | Purpose |
|------|---------|
| `ia_find_object_usages` | Broad where-used: all objects referencing `object_name` (optional type + library filter) |
| `ia_object_references` | Inverse: what an object references/contains (modules in SRVPGM, files used) |
| `ia_reference_count` | Lightweight: counts of references grouped by type |
| `ia_file_field_impact_analysis` | Field-level blast radius: programs affected if field X in file Y changes |

## Call Graph

| Tool | Purpose |
|------|---------|
| `ia_call_hierarchy` | Returns callers and/or callees for a program or module |
| `ia_call_parameters` | Parameters passed at each external call site |
| `ia_circular_deps` | Detect two-way circular call chains |

## Program Internals

| Tool | Purpose |
|------|---------|
| `ia_program_variables` | All variables declared in a member (type, length, DS flag) |
| `ia_data_structures` | Data structure definitions and subfields |
| `ia_subroutines` | BEGSR/EXSR with usage counts (dead-subroutine detection); filter by member/library |

## Files & Overrides

| Tool | Purpose |
|------|---------|
| `ia_file_fields` | Field-level metadata: names, aliases, types, lengths, key sequence, reference chain |
| `ia_field_reffld_consumers` | Inverse of `ia_file_fields`: only the fields **referenced as REFFLD by other files**, with consumer file/field/type info (use this for "which fields in CUSTMST are reused as templates?") |
| `ia_file_dependencies` | LFs, indexes, views dependent on a physical file. Bifurcated by SQL kind (`SQL_OBJECT_TYPE` = INDEX/VIEW/TABLE/MQT/DDS_LF). Use `dependent_kind` to filter. |
| `ia_file_constraints` | DB constraints (PK/UQ/FK/CHK) + LF select/omit rules in one call. Use `kind` to narrow (SELECT_OMIT, FOREIGN_KEY, etc.) |
| `ia_file_overrides` | OVRDBF statements — real file routing vs. declared F-spec |
| `ia_override_chain` | Chained OVRDBF dependencies (A→B→C) |

## Source-Level Analysis

| Tool | Purpose |
|------|---------|
| `ia_rpg_source` | Read RPG source line-by-line. Returns only SOURCE_RRN + SOURCE_DATA — pass a specific `member_name` and `library_name`. Use `ia_rpg_source_search` for cross-member keyword search. Cap 10000 lines/call — paginate with `offset` for larger sources |
| `ia_cl_source` | Read CL/CLLE/CLP source line-by-line. Returns only SOURCE_RRN + SOURCE_DATA — pass a specific `member_name` and `library_name`. Cap 10000 lines/call — paginate with `offset` for larger sources |
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
| `ia_unused_objects` | Dead code candidates (compiled but never referenced) |
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
| `ia_procedure_params` | Procedure PR/PI signatures; `%` wildcards; filter by member/library |
| `ia_cl_jobs` | CL SBMJOB/CALL detection with job queue info |
| `ia_variable_ops` | Variable declarations, assignments, BIF usage; `*ALL` for cross-member |
| `ia_klist_usage` | KLIST/KFLD key list definitions; `%` wildcards in kfld_name |
| `ia_application_area` | Forward: area → objects; Reverse: object → areas (`%` supported) |
| `ia_sql_names` | SQL long/short name mapping |
| `ia_program_files` | Program file usage with PREFIX/RENAME; filter by member/library |
