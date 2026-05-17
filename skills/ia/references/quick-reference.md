# iA Quick Reference — Tool Selection

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
| Params passed at each call site? | `ia_call_parameters` |
| Impact of changing field F in file X? | `ia_file_field_impact_analysis` |
| Variables in program X? | `ia_program_variables` |
| Data structures in program X? | `ia_data_structures` |
| Subroutines in program X? | `ia_subroutines` |
| File fields / formats for file X? | `ia_file_fields` |
| File overrides (OVRDBF)? | `ia_file_overrides`, `ia_override_chain` |
| What type/library is object X? | `ia_object_lookup` |
| Does member X exist? Metadata? | `ia_member_lookup` |
| Inventory of objects by type? | `ia_object_list` |
| Program metadata / compile info? | `ia_program_summary` |
| Lifecycle / last-used dates? | `ia_object_lifecycle` |
| Object size / largest or unused? | `ia_obj_size` |
| Dead code (compiled)? | `ia_unused_objects` |
| Dead code (sources)? | `ia_uncompiled_sources` |
| Complexity hotspots? | `ia_code_complexity` |
| Circular call chains? | `ia_circular_deps` |
| Repo health / member inventory? | `ia_dashboard` |
| List tables in iA library? | `ia_library_files` |
| Raw RPG/CL token stream? | `ia_rpg_source_tokens`, `ia_cl_source_tokens` |
| Source code for member X (RPG)? | `ia_rpg_source` |
| Source code for member X (CL)? | `ia_cl_source` |
| Search RPG source for keyword? | `ia_rpg_source_search` |
| Modernization / format stats? | `ia_rpg_source_stats` |
| Logical files over physical file X? | `ia_file_dependencies` |
| Copybook change impact? | `ia_copybook_impact` |
| Copybooks used by member X? | `ia_member_copybooks` |
| SRVPGM exports/imports? | `ia_srvpgm_exports` |
| Procedure-level callers? | `ia_procedure_xref` |
| Procedure signature? | `ia_procedure_params` |
| Batch job detection? | `ia_cl_jobs` |
| **Document program X?** | [program-documentation.md](program-documentation.md) |
| **Export generated doc to Word/PDF?** | `scripts/convert_md_to_docx.py` / `scripts/convert_md_to_pdf.py` (see [program-documentation.md → Step 9](program-documentation.md)) |
