---
name: ia
description: Guide for using iA by programmers.io MCP tools to analyze IBM i programs — dependency tracing, call hierarchies, field impact, source retrieval, and program documentation. ALWAYS use this skill for ANY IBM i analysis question.
---

# iA Impact Analysis — Agent Guide

iA by [programmers.io](https://programmers.io/ia/) pre-parses IBM i source (RPG, CL, COBOL, DDS) into a queryable repository accessed through the `ia_*` MCP tools.

**Goal:** Answer most questions in 1-2 tool calls. Consult [quick-reference.md](references/quick-reference.md) for tool selection, [tool-catalog.md](references/tool-catalog.md) for the full 50-tool list.

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

1. `ia_file_field_impact_analysis(file_name=X, field_name=Y)` → Direct PF references
2. `ia_file_dependencies(file_name=X)` → LFs/indexes/views over PF
3. `ia_find_object_usages` on every STRUCTURAL `*FILE` from step 1 (parallel)
4. `ia_find_object_usages(object_name=<each_LF>)` from step 2 (parallel)

Present as four sections: **Direct (NEEDS_CHANGE)**, **Direct (NEEDS_RECOMPILE)**, **Structural Dependents**, **Programs via LF**.

## When to Chain

**DO chain:** `*SRVPGM` in results (amplifier — check what binds to it), field impact (run all steps).

**DON'T chain:** Simple counts (count your results), every `*PGM` (only critical ones), `ia_member_lookup` just for location.

## Parameter Rules

- Object/member names: **10-char uppercase** (`'CUSTMAST'`)
- `object_type`: Star-prefixed (`*PGM`, `*SRVPGM`, `*FILE`, `*DSPF`)
- Wildcard `*ALL` = no filter (default for optional params)
- Only `ia_object_lookup` supports `%` wildcards in names

## Interpreting Results

| Value | Meaning |
|-------|---------|
| `*SRVPGM` in results | Amplifier — always check dependents |
| `*DSPF` in results | User-facing screen — flag prominently |
| Empty results | May be scheduler-invoked or external |
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
| Full 50-tool list | [tool-catalog.md](references/tool-catalog.md) |
| Complex analysis chains | [query-flows.md](references/query-flows.md) |
| Analysis playbooks | [playbook.md](references/playbook.md) |
| Program documentation | [program-documentation.md](references/program-documentation.md) |
