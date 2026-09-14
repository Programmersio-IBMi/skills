# Program Documentation Reference

Use this guide whenever a user asks for a **technical program document** for an IBM i program. Follow every step in order.

**Not for Synon / CA 2E functions.** If the target is a 2E function or the 2E-generated RPG behind one — the user says "Synon" / "2E" / "action diagram", an `*_AD` export is supplied, or `ia_member_lookup` resolves the name to a Synon source member — load [synon-documentation.md](synon-documentation.md) instead. Documenting generated 2E code as if it were hand-written yields a spec of the code generator, not of the business logic.

---

## ⛔ Rule Zero — Never Read Existing Documentation

**Every new document must be generated from scratch using live iA tool output only.** Before, during, and after generation:

- **Do NOT read any existing `.md` / `.docx` / `.pdf` under `docs/program-specs/`** — not for the target program, not for any other program, not for "style reference" or "tone." Treat the contents of every prior doc as off-limits.
- The **only** permitted use of `docs/program-specs/{PROGRAM_NAME}/` is to **list directory entries** (filenames only) and read a file's **last-modified timestamp** (filesystem metadata) — to run the Step 1.5 existence check and confirm the canonical save target. Do not open or read the *contents* of any file in that folder.
- Do not read other repos' or other audiences' prior outputs as a template either. Templates live exclusively under `references/templates/`.
- **Why:** Prior drafts may contain stale facts, hallucinations from earlier model runs, or assumptions that no longer match the current source. Reading them contaminates the new document with errors carried forward. Source-of-truth is iA tool output, never a prior document.

If you find yourself about to open any file under `docs/program-specs/`, stop. Re-derive from iA tools instead.

---

## Step 1 — Smart Profile Selection

**Check the user's request for profile indicators:**

| User Says | Action |
|-----------|--------|
| "document program X" (no preferences) | Use DEFAULT profile → skip to Step 2 |
| "standard spec", "full documentation" | Use DEFAULT profile → skip to Step 2 |
| "customize", mentions audience / sections | Run Phase 0 discovery |
| "for business analysts", "for architects" | Run Phase 0 discovery |

**DEFAULT profile (80% of users):**
- Audience: Developers
- Detail: Full inventory (all subroutines)
- Sections: All
- Format: Markdown
- Template: `template-developer.md`

If using DEFAULT, show one line: `"Using standard profile (full technical spec for developers). Say 'customize' to change."`

**Phase 0 Discovery (only when customization requested):**
Present all questions in **one message** — not sequentially:

```
Please configure your documentation preferences:

**Audience** (select all that apply):
☐ A) New developers / onboarding team
☐ B) Business analysts (non-technical)
☐ C) Architects / auditors
☐ D) Support / operations team

**Detail Level**:
○ A) Full inventory — every subroutine documented (Recommended)
○ B) Key subroutines only — business rules focus
○ C) Summary counts only

**Priority Sections** (select all that apply):
☐ A) Business rules (BR-xxx list)
☐ B) Call hierarchy (what calls what)
☐ C) Processing flow (step-by-step narrative)
☐ D) File and data area usage
☐ E) Error handling

**Format**:
○ A) Markdown with tables (Recommended)
○ B) Plain text
○ C) Both (markdown primary, plain text summary)
```

Wait for one response, then proceed.

---

## Step 1.5 — Existing Document Check (early gate)

**Runs immediately after Step 1 (DocType known) and BEFORE the Todo kickoff and any `ia_*` call.** Its purpose is to keep **a single canonical copy per (program, doc type)** and to avoid regenerating a document the user already has. Doing this *first* means a decline costs zero iA calls.

**1. Coerce the request to exactly one of five canonical DocType names:**

| User wording (examples) | Canonical DocType | Audience template |
|---|---|---|
| "technical spec", "developer doc", "code doc", default | `Technical_Specification` | `template-developer.md` |
| "functional doc", "business doc", "BA doc", "summary" | `Functional_Document` | `template-business.md` |
| "ops guide", "runbook", "support doc", "operations" | `Operations_Guide` | `template-operations.md` |
| "architecture review", "audit", "modernization", "design review" | `Architecture_Review` | `template-architect.md` |
| "test cases", "test scripts", "UAT scripts", "test case document" | `Test_Case_Document` | `template-testcases.md` |

If the request matches none, tell the user which canonical type you chose and why; if it's genuinely ambiguous, ask them to pick one. A multi-type request ("all four", "tech spec and functional doc") runs this whole gate **once per DocType**.

**2. List the program folder ROOT ONLY** — `ls docs/program-specs/{PROGRAM_NAME}/` (or platform equivalent). Filenames only; do **not** open any file (Rule Zero). If the folder doesn't exist, treat it as empty and skip to Step 1.6.

**3. Look for the canonical single-copy file** `{PROGRAM_NAME}_{CanonicalDocType}.md` (no version suffix — this is the one copy). Legacy `_v{N}` files and older free-form names (`{PGM}_Specification.md`, `{PGM}_Doc.md`, …) **do not count** for this check and are left strictly in place — never matched, moved, renamed, or deleted.

**4. If the canonical file exists → HARD STOP and ask.** Read its **last-modified date** via a filesystem stat (metadata only — never open the file). Tell the user:

> A **{CanonicalDocType}** for **{PROGRAM_NAME}** already exists (last generated **{YYYY-MM-DD}**): [{filename}](docs/program-specs/{PROGRAM_NAME}/{filename}).
> Do you want me to generate a fresh one? This will **replace** the existing copy.

- **User declines** → stop here, point them at the existing file. **Make no `ia_*` call.**
- **User confirms** → proceed to Step 1.6; the new document overwrites the canonical file in place at Step 8.
- **Request already signals regeneration** ("regenerate", "update", "replace", "redo the doc") → treat it as confirmation; skip the prompt, but still tell the user you're replacing the existing copy.

**5. If the canonical file does not exist → proceed to Step 1.6** and generate normally.

**Drafts are exempt:** an explicitly-labelled *draft* request still goes to `docs/program-specs/{PROGRAM_NAME}/drafts/` and is **not** subject to the single-copy / overwrite rule.

---

## Step 1.6 — Track the remaining steps

Steps 2–9 below are order-dependent. Keep a visible checklist of them (the host's task list if it has one, otherwise a short list in your reply), and when you drop a step as not applicable say so with the reason. Steps 7 (verification) and 7.5 (filename gate) are never dropped.

---

## Step 2 — One-call Inventory

**Use the bundled tool — one call instead of seven:**

```
ia_program_spec_bundle(program_name=X)
```

**⛔ HARD STOP — Multiple Versions Detected:**
If LOOKUP returns multiple rows (member exists in several libraries or source files):
1. Present the full version table to the user: library, source file, type, line count, last changed
2. Ask: *"I found N versions of [PROGRAM]. Which version would you like me to document?"*
3. **Wait for the user's answer. Do NOT proceed to Step 3 without explicit confirmation.**
4. Once confirmed, re-run with `library=<chosen>` and proceed.

A footnote is **not** acceptable — always pause and ask. Silently selecting a version is a documentation error.

If LOOKUP returns zero rows, stop and tell the user the member was not found in iA. Suggest `ia_object_lookup(object_name='%X%')` with a wildcard.

**Uncertainty during Steps 2–7** is recorded, not escalated: state it inline where it occurs and again in the quality report. Two cases are exceptions because only the user can resolve them — several versions in LOOKUP (above) and a file whose library cannot be resolved (Step 3). If `CALLED_BY_COUNT` > 0 but the CALLERS section is empty, run `ia_find_object_usages` on the program yourself and document what it returns.

**Bundle section → document section mapping** (sections refer to the new template-developer.md structure):

| Bundle section | Document section fed | What to extract |
|----------------|----------------------|-----------------|
| `LOOKUP` | Header, Section 1 (Overview) | All libraries where member exists; if multiple, ask user which to document. **Capture the actual library name and use it everywhere.** |
| `COMPLEXITY` | Section 9 + Technical Statistics | TOTAL_LINES, EXEC_LINES, IF/DO/SEL/WHEN, SBR/PROC/SQL/GOTO, CALL_PGM/CALLED_BY/FILES/DSPF |
| `FILES` | Section 3 (Files and Data Sources) | File list, library, type, PREFIX, RENAMED, RCDFMT, INDICATOR_DS, FILE_INFO_DS |
| `CALLEES` | Section 5 (Subroutine / Procedure Analysis) + Mermaid diagram | CALLED_OBJCT + CALLED_PROC — verified callees only |
| `CALLERS` | Section 9 (Key Observations — dependencies) | Callers verified by `ia_call_hierarchy` only |
| `SUBROUTINES` | Sections 4, 5, 6 | **Complete** subroutine list — every BEGSR is documented in §5 and is a candidate for BRs in §6 |
| `PARAMS` | Section 2 (Technical Summary — entry parameters) | Entry parameters from PI/PR — name, type, length, sequence, KEYWORDS, business meaning |
| `BINDINGS` | Section 5 (External service programs) | *SRVPGM, *BNDDIR, *MODULE references |

**BINDINGS multi-SRVPGM handling:**
When BINDINGS returns multiple `*SRVPGM` entries:
1. Group by `REFERENCED_OBJ` (service program name)
2. For each SRVPGM, list its bound procedures from the CALLEES section (match by CALLED_OBJCT)
3. Present as table:

| Service Program | Library | Procedures Used | Coupling Level |
|-----------------|---------|-----------------|----------------|
| SRVPGM1 | MYLIB | PROC1, PROC2, PROC3 | High (3+) |
| SRVPGM2 | MYLIB | PROCX | Low (1) |

Coupling levels: **High** (>3 procedures), **Medium** (2-3), **Low** (1). Modules (`*MODULE`) go in a separate "Bound Modules" subsection.

**Fallback:** If the bundle errors or returns zero LOOKUP rows, use this sequence:

```
1. ia_member_lookup(member_name=X)           → existence check + metadata
2. ia_code_complexity(member_name=X)         → complexity metrics (lines, IF/DO/SQL counts)
3. ia_program_files(member_name=X)           → file usage with PREFIX/RENAME
4. ia_call_hierarchy(program_name=X, direction=BOTH) → callers and callees
5. ia_subroutines(member_name=X)             → BEGSR/ENDSR details
6. ia_procedure_params(member_name=X)        → PI/PR parameter signatures
7. ia_object_references(object_name=X)       → SRVPGM/BNDDIR/MODULE bindings
```

Run these in order; skip any that return zero rows. Combine results to populate sections.

---

## Step 2.5 — File Enrichment + Silent Field Lookup

Before writing any document section, enrich the bundle's FILES list with **file descriptions and library names**, and load **every field's description into an in-memory lookup**. This step is non-negotiable — Section 3 (Files and Data Sources), Section 4 narrative, and inline field mentions throughout the document depend on it.

**For every file in the FILES section** (no exceptions — input, output, update, and reference files all qualify):

| Tool | What to capture | Used in |
|------|-----------------|---------|
| `ia_program_files(member_name=X)` | File usage + **FILE_TEXT / TEXT description** + **library** | Section 3 file table, narrative |
| `ia_file_fields(file_name=<file>, library_name=<lib>)` | Every field's FIELD_NAME + FIELD_TEXT (description), held as a silent lookup | Inline `FIELDNAME (Description)` whenever a field appears in narrative, BR-xxx, subroutine logic, Section 7 output behavior, or Section 8 glossary |

**Do NOT render the field list as a per-file table.** The `ia_file_fields` output is consumed only as a description lookup. Field mentions appear in the document **only** where the program logic touches them, with their inline description. (See the Field Description Rule below.)

**De-duplication:** Call `ia_file_fields` once per unique `(library, file)` pair. If the same physical file appears with multiple usage types, the field set is identical — don't re-fetch.

**If a file's TEXT description is empty** in `ia_program_files`, fall back to `describe_sql_object(object_name=<file>, library_name=<lib>)` to pull the DDL `LABEL ON` / `TEXT` description. Do not invent a description.

**Library names are mandatory for every file** — never write a file name without its library (e.g., `CUSTMAST (PRDLIB)`). If the library is unresolved, that is a **HARD STOP**: ask the user which library to document against. Do not default to `*LIBL` or leave blank.

**Field description rule (applies everywhere in the document):**

Every field reference — in narrative prose, BR-xxx entries, output behavior, key-field lists, and glossary — must include the field's plain-language description in parentheses, **on every mention**:

> Read `CUSTMAST (PRDLIB)` keyed on `CUSTNO (Customer Number)`. Update `STATUS (Account Status Code)` when `BALANCE (Outstanding Balance Amount)` exceeds `CRDLIM (Credit Limit Amount)`.

- The description comes from `FIELD_TEXT` returned by `ia_file_fields`.
- If `FIELD_TEXT` is blank, look at column heading text or fall back to "(no description in DDL)" — do not invent meaning.
- This applies on **every occurrence** of the field, not just the first. Verbosity is intentional: viewers reading any single paragraph in isolation must understand what the field represents.

---

## Step 3 — Source + Business Rule Extraction

Retrieve source and extract business rules using the appropriate source tool **based on member type** (from Step 2's LOOKUP section):

| MEMBER_TYPE | Tool to use |
|-------------|-------------|
| `RPGLE`, `SQLRPGLE`, `RPG`, `SQLRPG` | `ia_rpg_source` |
| `CLLE`, `CLP`, `CL` | `ia_cl_source` |

Call the appropriate tool with:
- `member_name`: The program's source member name
- `library_name`: The library you confirmed in Step 2 (don't leave as `*ALL` when multiple versions exist)
- `limit`: See pagination rule below
- Optional (`ia_rpg_source` only): `source_spec` to filter by RPG spec type (C, D, F, H, I, O, P)

**Pagination — mandatory for sources >10,000 lines:**

Both `ia_rpg_source` and `ia_cl_source` have a hard `limit` cap of **10,000 lines per call**. Before fetching, read `TOTAL_LINES` from Step 2's COMPLEXITY section:

| TOTAL_LINES | Action |
|---|---|
| ≤ 10,000 | One call: `limit=10000, offset=0` (or set limit to TOTAL_LINES for a tighter fetch) |
| > 10,000 | Loop: `offset=0,10000,20000,…` with `limit=10000` until you have all lines. Stop when a call returns fewer than 10,000 rows. |

**Never write a spec from a partial source.** Real programs can exceed 30,000 lines — a single call returns under 30% of these. Verify completeness: the highest `SOURCE_RRN` you fetched should equal `TOTAL_LINES` from COMPLEXITY.

This returns source lines with line numbers, spec types, format classification, and source text. Complexity metrics are already available from Step 2's COMPLEXITY section.

**Auto-cluster subroutines by name patterns:**

| Pattern | Cluster Type | Examples |
|---------|--------------|----------|
| `*VALID*`, `*CHECK*` | Validation | VALIDATECUST, CHECKINPUT |
| `*CALC*`, `*COMPUTE*` | Calculation | CALCPRICE, COMPUTETAX |
| `*EMAIL*`, `*SEND*`, `*NOTIF*` | Communication | SENDEMAIL, SENDNOTIF |
| `*INIT*`, `*SETUP*` | Initialization | INITVARS, SETUPSCREEN |
| `*CLEAN*`, `*CLOSE*`, `*END*` | Cleanup | CLEANUP, CLOSEFILE |
| `*ERROR*`, `*ABORT*` | Error Handling | ERRORHANDLER, ABORTPGM |
| `*READ*`, `*WRITE*`, `*UPDATE*`, `*DELETE*` | I/O | READCUST, WRITEORDER |
| `*PROCESS*`, `*HANDLE*` | Workflow | PROCESSORDER, HANDLEREQ |

For each cluster, scan source for:
- IF/WHEN/SELECT conditions → validation rules
- Constants (named or literal) → business constants
- SQL WHERE clauses → data filters
- GOTO/EXSR patterns → workflow rules

**BR-xxx format:**
```markdown
- **BR-001** [VALIDATION] — Customer number must be numeric (line 145, subroutine: VALIDATECUST)
- **BR-002** [CALCULATION] — Order total = sum(line items) + tax (line 230, subroutine: CALCORDERTOTAL)
```

---

## Step 4 — Template Selection

| Audience | Template | Focus |
|----------|----------|-------|
| Developers / onboarding (DEFAULT) | [`templates/template-developer.md`](templates/template-developer.md) | Full technical detail |
| Business analysts | [`templates/template-business.md`](templates/template-business.md) | Plain language, business rules |
| Architects / auditors | [`templates/template-architect.md`](templates/template-architect.md) | Architecture, dependencies, modernization |
| Support / operations | [`templates/template-operations.md`](templates/template-operations.md) | Runtime, monitoring, troubleshooting |
| QA / UAT testers | [`templates/template-testcases.md`](templates/template-testcases.md) | Manual execution test scripts — assembly + verification per [`test-case-generation.md`](test-case-generation.md) |
| Multiple audiences | `template-developer.md` | Most comprehensive |

See [`templates/README.md`](templates/README.md) for comparison matrix.

---

## Step 5 — Document Assembly Rules (template-developer.md, default tech-spec structure)

> **Tone rule (applies to every section):** Use business-friendly language with technical accuracy. **Never** describe the code line-by-line. **Never** assume a pattern that is not explicitly present in the source.

> **Library resolution rule (applies everywhere):** Always use the **actual library name** (e.g., `PRDLIB`) wherever a library appears — header, file tables, output sections, mermaid labels, glossary. Resolve from the bundle's LOOKUP / FILES sections; never leave a placeholder in the deliverable. **Every file mention** must carry its library: `FILENAME (LIBRARY)`.

> **Field-format rule (applies everywhere):** Every field reference — narrative, BR-xxx entries, subroutine blocks, output behavior, glossary — must include the field's description in parentheses on **every** mention: `FIELDNAME (Field Description)`. Pull the description from `FIELD_TEXT` in `ia_file_fields`. Verbosity is intentional so any paragraph stands on its own.

### Section 1 — Program Overview
- Program name (and any alternate name in source comments).
- One-to-two sentence primary purpose.
- Bulleted business problem / functionality addressed.
- Execution type — Batch, Interactive, or Online — justified by DSPF count, F-spec usage, or scheduling context.
- Key outputs and how they are consumed downstream.

### Section 2 — Technical Summary
- Program ID, RPG type (RPG III / RPG IV fixed / RPG IV free / SQLRPGLE / CLLE) — sourced from MEMBER_TYPE in iA, not from reading the source header.
- **Mandatory:** call `ia_procedure_params` first. If it returns rows, populate the entry-parameters table exactly with **business meaning** for each parameter.
- Only write "No entry parameters declared." if `ia_procedure_params` returns zero rows AND source has no `dcl-pr`/`dcl-pi`/`*ENTRY PLIST`. Never write "Not determinable."
- Notable revisions / assumptions / commented-out logic — capture revision tags, disabled file integrations, and any explicit assumption stated in source comments.

### Section 3 — Files and Data Sources
- Populate from bundle FILES section only — do not add files from source that aren't confirmed by iA.
- For each file include: name, **actual library** (mandatory — never blank, never `*LIBL`), usage type (Input / Output / Update / Reference), **file description** (from `ia_program_files` FILE_TEXT or `describe_sql_object`), business purpose.
- **Do NOT render an exhaustive per-file fields table.** Field metadata loaded by Step 2.5 is used only as an inline-description lookup. Individual fields are mentioned in narrative, BR-xxx, subroutine logic, and Section 7 only where the program touches them, always with the inline `FIELDNAME (Field Description)` format.
- **Data areas (*DTAARA) are NOT files.** Add a separate subsection: **"Data Areas Used"** with columns Name, Library, Size, Operations (IN/OUT), Purpose.
- If `ia_object_references` shows *FILE entries not in FILES section, note them as "detected via object reference, not F-spec."

### Section 4 — Main Processing Logic
- Narrate the program's execution flow **in the same sequence in which it actually runs**, from start to end. Numbered steps or paragraph prose are both acceptable.
- For every read / write / update / chain on a file, mention which **key fields** are used, which **fields are derived**, and which **fields are written or updated**.
- When processing routes through a subroutine, mention its **name** and a one-line summary of what it does (full detail in Section 5).
- Describe how control flows between major logic blocks; identify distinct paths only if they naturally occur.
- **Do not pre-classify** logic by category (dates, control breaks, etc.) — narrate in execution order.
- Add line-number anchors *(line NNN)* where they aid traceability.

### Section 5 — Subroutine / Procedure Analysis
- Use the **complete SUBROUTINES list** from Step 2 — never document subroutines selectively. Every non-trivial routine gets its own block.
- **Mandatory subroutine block format:**

  ```markdown
  #### SUBROUTINE_NAME — lines {START_LINE}–{END_LINE}

  **Purpose:** <one sentence>

  **High-level behavior:**
  - <bullet> *(line NNN)*
  - <bullet> *(line NNN)*

  **Key decisions / calculations:**
  - <decision/calc with field names + descriptions> *(line NNN)*

  **Files accessed:** `FILE1 (LIB1)` keyed on `KEY1 (Key 1 Description)`, ...
  **Calls:** [CALLP] CALLEE1 *(line NNN)*, [EXSR] OTHER_SR *(line NNN)*
  ```

  - `{START_LINE}` = BEGSR line number from `ia_subroutines` / SUBROUTINES section.
  - `{END_LINE}` = ENDSR line number from same source.
  - **Every internal anchor** (decision, calculation, I/O opcode, EXSR call, CALLP, GOTO) must carry an inline `*(line NNN)*` tag.
  - Field references inside the block follow the field-format rule: `FIELDNAME (Description)` on every mention.
- If a subroutine name implies a capability (e.g., SENDEMAILPROCESS, POPULATEMEMBEREXCLUSIONDETAILS) not yet reflected anywhere, document it even if you cannot see the full logic — still include the line range from SUBROUTINES.
- **Call Hierarchy Diagram (text-based ASCII tree)** — include if `CALL_PGM_COUNT > 0` OR CALLEES has rows. Use the **actual library** in the parent node label (e.g., `ORDENTRY (PRDLIB)`). One-level depth unless the user asks for deeper traversal.
- Only list callees that appear in CALLEES; only list service programs from BINDINGS. If `CALL_PGM_COUNT = 0` but CALLEES has rows, prepend the "bound CALLP only" note from Step 6.
- Callers go in Section 9 (Key Observations) — only if confirmed by CALLERS section.

### Section 6 — Business Rules and Calculations
- Use the **BR-xxx** identifier format with a category tag and source anchor: `**BR-001** [VALIDATION] — <rule> (line NNN, subroutine: NAME)`.
- Categories: VALIDATION, CALCULATION, CLASSIFICATION, STATUS / FLAG, EXCEPTION, ACCUMULATION.
- Group rules by what they do in the business: accumulations / totals / rollups, classification, status / flag-driven behavior, special conditions / exception handling.
- Coverage target: BR count ≥ 50% of subroutine count. Below that, surface a warning in the quality report.
- Character-constant validators missing digits → always flag as "verify against source."

### Section 7 — Output File Behavior
- For each file the program writes or updates, document conditions for create vs. update, field population / accumulation logic, and the relationship between input and output fields.

### Section 8 — Glossary
- Define every important keyword, abbreviation, and field **that was actually referenced elsewhere in the document** in plain language, including unit / domain when relevant.
- Do not list every field returned by `ia_file_fields` — only fields that surfaced in narrative, BR-xxx, subroutine analysis, or Section 7. The glossary mirrors the document's actual scope, not the full file schemas.

### Section 9 — Key Observations (Optional)
- Complexity or risk areas (high IF/DO counts, GOTOs, deep nesting, large data structures).
- Dependency on reference data or external programs (DAYMINUS, lookup files, data areas).
- Modernization / refactoring opportunities.
- Caller summary: if callers list is empty but `CALLED_BY_COUNT > 0`, write "iA reports N caller(s) but no matching record found in the call-hierarchy data — likely a CL→RPG call; manual verification recommended."

### Technical Statistics block
Include **all** complexity metrics from COMPLEXITY section (Total / Exec lines, IF / DO / SEL / WHEN, SQL, Subroutine — *agents often omit this* — Procedure, GOTO, Files, DSPF, Calls Out, Called By) plus an overall **Complexity Assessment** (Low / Medium / High / Critical).

---

## Step 6 — Call Hierarchy Diagram

After assembling Section 5 (Subroutine / Procedure Analysis), add a call hierarchy using CALLEES data — **always with the actual library name** in the parent label.

**Skip if:** CALL_PGM_COUNT = 0 **AND** CALLEES section is empty (no bound procedure calls confirmed by iA).

**Include if:** CALL_PGM_COUNT > 0 (traditional CALL opcodes) **OR** CALLEES section has any rows (bound CALLP procedure calls confirmed by iA) — even if CALL_PGM_COUNT = 0.

If CALL_PGM_COUNT = 0 but CALLEES has rows (bound procedures only), add this note before the diagram:
> **Note:** No traditional `CALL` opcodes detected. Diagram shows confirmed bound procedure calls (CALLP via prototype). The full prototype declaration list is in Section 2.

**Include in:** `template-developer.md` and `template-architect.md` only (not business or operations templates).

**Format — text-based ASCII tree in a fenced `text` code block:**

\`\`\`markdown
## Call Hierarchy Diagram

\`\`\`text
PROGRAMNAME (LIBRARY)
│
├── [CALLP] CALLEE1
├── [CALLP] CALLEE2          ×3
├── [CALLP] CALLEE3 (proc: PROCNAME)
├── [CALL]  CALLEE4
└── [CALL]  CALLEE5
\`\`\`
\`\`\`

**Why text instead of Mermaid:** Mermaid diagrams render to PNG when exported to Word/PDF. With many callees (IBM i programs often have 10–30), the PNG either becomes unreadably wide (`graph TD`) or unreadably tall (`graph LR`), and labels degrade at any zoom level. A monospace text tree in a fenced code block renders natively in every output format (Markdown preview, Word `.docx`, PDF), stays selectable/searchable, never blurs, and survives copy-paste.

**Conventions:**
- Parent line: `PROGRAMNAME (LIBRARY)` — use the actual library name.
- Use `├──` for non-last children, `└──` for the last child.
- Tag each callee with `[CALLP]` (bound procedure call) or `[CALL]` (traditional program call) — left-pad `[CALL]` with one extra space so callee names align in monospace.
- If a callee is invoked more than once, append `×N` aligned in a trailing column.
- If `CALLED_PROC` is populated and differs from `CALLED_OBJCT`, append `(proc: PROCNAME)` after the name.
- Keep to direct callees only (one level depth) unless the user asks for deeper traversal.

**Add a brief legend below the tree** (see template files for the exact text).

---

## Step 7 — Automated Verification Pass

**Run all checks before presenting the document:**

| Check | Rule | Action if Failed |
|-------|------|------------------|
| ✓ Section 2 (Technical Summary) | No "Not determinable" parameters without `ia_procedure_params` call | **ERROR** — must fix |
| ✓ Section 3 (Files & Data Sources) | No *DTAARA in file table; library column shows actual library | **ERROR** — move data areas to subsection; substitute library |
| ✓ Section 4 (Main Processing Logic) | Narrative follows execution order; no pre-classification by category | **ERROR** — re-narrate |
| ✓ Section 5 (Subroutines) | Every subroutine from SUBROUTINES list appears; CALL_PGM_COUNT=0 → no external calls listed | **ERROR** — fill missing routines / remove unverified calls |
| ✓ Section 6 (Business Rules) | BR count ≥ 50% of subroutine count | **WARNING** — may be incomplete |
| ✓ Section 7 (Output File Behavior) | Every Output / Update file from Section 3 has a corresponding block | **WARNING** — incomplete |
| ✓ Section 8 (Glossary) | Important fields/keywords referenced elsewhere are defined | **WARNING** — gaps |
| ✓ Statistics | All 9+ complexity metrics present | **WARNING** — incomplete stats |
| ✓ Header | Library version stated; actual library name used throughout (no placeholders) | **ERROR** — substitute actual library |
| ✓ Step 2.5 (File enrichment) | `ia_file_fields` called for every unique file in FILES section; field descriptions held as silent lookup (no per-file fields table rendered) | **ERROR** — re-run enrichment |
| ✓ File library coverage | Every file mention includes its library: `FILENAME (LIBRARY)` | **ERROR** — substitute library on every mention |
| ✓ File description coverage | Every file row in Section 3 has a description sourced from `ia_program_files` / `describe_sql_object` | **ERROR** — fetch and populate |
| ✓ Field-format rule | Every field reference in narrative/BRs/sub-blocks carries `(Description)` on every mention | **ERROR** — rewrite occurrences |
| ✓ Subroutine line ranges | Every subroutine block header shows `lines START–END`; every internal anchor has `*(line NNN)*` | **ERROR** — add line numbers |
| ✓ Source isolation | No file under `docs/program-specs/` was read during generation (only directory listed for versioning) | **ERROR** — regenerate from iA tools only |
| ✓ DocType = Test_Case_Document | Run both gates in [`test-case-generation.md`](test-case-generation.md) §5: `python scripts/validate_testcases.py <file>` exits 0, then the TC content-check table | **ERROR** — fix every finding before delivery |
| ✓ Absolute access-method claims | Any "all / only / no / never" claim about data access (e.g. "SQL-only — no CHAIN/READ") is backed by in-session proof: `ia_rpg_source(source_spec='F')` shows only WORKSTN files **and** `ia_rpg_source_search` for native opcodes (`CHAIN`, `READ`, `WRITE `, `UPDATE `, `SETLL`) over the member returns no database-file hits | **ERROR** — drop the absolute; describe access as mixed, per file |
| ✓ Source fingerprint in footer | Quality Report Freshness row carries the source fingerprint: member changed date/time + total lines + repo schema (all already in hand from Step 2 LOOKUP/COMPLEXITY) | **ERROR** — add fingerprint |

Fix all **ERRORs** before delivery. Present **WARNINGs** with notes in the quality metrics footer.

**Validation report format:**
```
✅ All checks passed — document ready for delivery
⚠️ 2 warnings detected:
  - Section 4: Only 5 BRs for 12 subroutine clusters (42% coverage)
  - Section 6: Subroutine cluster "Email" not in processing flow
❌ 1 error detected:
  - Section 3: Data area MYDTAARA found in file table
```

---

## Step 7.5 — Filename Resolution Gate

**Mandatory gate between Step 7 (Verification) and Step 8 (Save). It produces the one save target. Step 8 consumes that filename verbatim — never compute it inline.**

The canonical **single-copy** filename is:

```
docs/program-specs/{PROGRAM_NAME}/{PROGRAM_NAME}_{CanonicalDocType}.md
```

where `{CanonicalDocType}` was already coerced in **Step 1.5** (one of `Technical_Specification`, `Functional_Document`, `Operations_Guide`, `Architecture_Review`, `Test_Case_Document`). There is **no version suffix** — each (program, doc type) pair has exactly one file.

### Algorithm

1. **Reuse the `{CanonicalDocType}` from Step 1.5.** Do not re-coerce — it was already resolved, and any existing copy was already surfaced to the user there.
2. **Emit the target path** and print it back before any write: `Writing {PGM}_{CanonicalDocType}.md`.
3. **If that file already exists**, the regenerate was already confirmed at Step 1.5 — Step 8 **overwrites it in place**. If you somehow reached here *without* that confirmation, stop and return to Step 1.5; never overwrite silently.

### Hard-stop conditions

- **DocType was never coerced** (Step 1.5 skipped) → go back and run Step 1.5; do not invent a filename.
- **Folder listing fails** (permission, IO error) → halt and report.

### Legacy filename note

Files like `BIO60R_Specification.md`, `IAMENUR_Doc.md`, `{PGM}_Technical_Specification_v2.md`, `ADMINP-Functional-Document.md` are **left strictly in place** — never matched, moved, renamed, or deleted. They are not the canonical single copy and play no part in naming.

---

## Step 8 — Branding and Quality Metrics

**Apply branded header:**
```markdown
# Technical Specification — <PROGRAM>

**Author:** iA by programmers.io
**Date:** <YYYY-MM-DD>
**Library version documented:** <LIBRARY> | **Source file:** <SRCPF> | **Member type:** <MEMBER_TYPE>
```

**Add quality metrics footer before the final branding line:**
```markdown
---

## Documentation Quality Report

| Metric | Score | Status |
|--------|-------|--------|
| Completeness | <X>% | ✅/⚠️ <N>/<TOTAL> sections populated |
| Verification Rules | <X>% | ✅/❌ <N>/7 rules passed |
| Business Rules Coverage | <X>% | ✅/⚠️ <N> BRs for <M> subroutine clusters |
| Source Traceability | ✅/⚠️ | Line numbers included: YES/NO |
| Freshness | Current | ✅ Generated <YYYY-MM-DD> · source changed <YYYY-MM-DD HH:MM> · <N> lines · repo <SCHEMA> |

**Validation Warnings (if any):**
- <Warning text>

**Recommendations:**
- <Recommendation text>
```

**Save location — use the filename emitted by Step 7.5 verbatim:**

```
docs/program-specs/{PROGRAM_NAME}/{PROGRAM_NAME}_{CanonicalDocType}.md
```

The five canonical DocType names are coerced in **Step 1.5**; **Step 7.5 — Filename Resolution Gate** confirms the single-copy target path. Step 8 does not recompute either; it only consumes the filename string Step 7.5 produced.

**Save rules:**

- Create `docs/program-specs/{PROGRAM_NAME}/` if it does not exist. **Do not** save anywhere else (project root, `BIO60R_Program_Analysis.md` style files at repo root are wrong — always use the program subfolder).
- **Single canonical copy per (program, doc type).** If `{PROGRAM_NAME}_{CanonicalDocType}.md` already exists, **overwrite it in place** — but *only* because the user confirmed the regenerate at Step 1.5. If you reach Step 8 and that file exists without a Step 1.5 confirmation, halt and return to Step 1.5; never overwrite silently. If it does not exist, write it fresh.
- If the file is an explicitly-labeled draft, save it to `docs/program-specs/{PROGRAM_NAME}/drafts/` instead — drafts are iterative and exempt from the single-copy rule. The final/canonical iteration goes to the subfolder root as the single `{PROGRAM_NAME}_{CanonicalDocType}.md`.
- Exported formats (`.docx`, `.pdf`) go in the same subfolder as their `.md` source, sharing its base name (`{PROGRAM_NAME}_{CanonicalDocType}.docx`) — never in the parent `docs/program-specs/` root. When the `.md` is regenerated, any previously exported `.docx`/`.pdf` of the same name are now stale; a re-export (Step 9) overwrites them. Do not delete them yourself.

**Final footer:** `*Analysis powered by iA from [programmers.io](https://programmers.io/ia/)*`

---

## Step 9 — Export to Word / PDF (on request)

If the user asks to "export to Word", "save as DOCX", "convert to PDF", "give me a PDF" — or similar — **after** the markdown spec has been generated, run the bundled converter scripts.

**Scripts shipped with this skill** (under `scripts/` in the skill root):

| Format | Script | Dependencies |
|--------|--------|--------------|
| Word (DOCX) | `convert_md_to_docx.py` | `pip install python-docx requests` |
| PDF | `convert_md_to_pdf.py` | `pip install reportlab` |

**Invocation:**

```bash
python convert_md_to_docx.py docs/program-specs/{PROGRAM}/{PROGRAM}_Technical_Specification.md
python convert_md_to_pdf.py  docs/program-specs/{PROGRAM}/{PROGRAM}_Technical_Specification.md
```

Each script writes its output next to the source `.md` with the `.docx` / `.pdf` extension — the same `docs/program-specs/{PROGRAM}/` subfolder, sharing the source base name. A re-export overwrites the prior same-name `.docx`/`.pdf`, keeping the export in step with the single canonical `.md`.

**Operational rules:**

- **Staleness gate** — if the `.md` being exported was **not generated in this session**, run `ia_member_lookup(member_name)` and compare against the doc's Freshness fingerprint line (grep that **one line only** from the file — the single sanctioned read under `docs/program-specs/`; never read other content). If the changed date/time or line count differ, stop: tell the user the source has changed since the doc was generated and offer to regenerate before exporting.
- **One format at a time** — only generate the format the user asked for. Don't produce both unless explicitly requested.
- **Missing dependency** — if a script exits with `Error: python-docx is not installed` (or `reportlab`), run the printed `pip install …` command, then re-run the conversion. Do not silently swap to a different tool.
- **No network calls expected** — both scripts are self-contained. The DOCX converter only reaches `mermaid.ink` if it encounters a ```` ```mermaid ```` fenced block; specs produced by this skill use text-based ASCII trees instead, so this path is not exercised.
- **Both scripts apply iA branding automatically** — PDF cover page, DOCX author metadata. Do not re-add the branding manually.
- **Output report** — after a successful conversion, tell the user the full output path so they can open it directly.

**What renders well:**

- All markdown the skill produces — headings, tables, fenced code blocks, lists, blockquotes, inline code, links.
- Text-based ASCII call-hierarchy trees in fenced ```` ```text ```` blocks render as native monospace code in both DOCX and PDF (which is precisely why this skill uses them instead of Mermaid).

---

## Verification Rules (Never Violate)

| Rule | Why |
|------|-----|
| Never assert a called program without call-hierarchy confirmation from `ia_call_hierarchy` | Unverified calls are worse than missing ones |
| Never use line counts from reading source | Use the iA complexity metrics — counting is error-prone and version-specific |
| Never put data areas in the file table | They are accessed via IN/OUT, not F-specs; separate section required |
| Never leave Section 2 as "Not determinable" without first calling ia_procedure_params | The tool exists; use it |
| Never document subroutines selectively | Get the full list from SUBROUTINES section first |
| Never omit a functional capability implied by subroutine names | SENDEMAILPROCESS = email; document it even if you can't see the logic |
| Always state which library version is being documented | Multiple versions often exist with different line counts |
| Always use the actual library name throughout the deliverable | Leaking placeholder text makes the document look auto-generated and broken. Resolve from LOOKUP/FILES sections. |
| Keep one canonical `{PGM}_{DocType}.md` per doc type; overwrite it only after the user confirmed a regenerate at Step 1.5 | The user wants a single current copy per type, not a version pile-up; an unconfirmed overwrite could discard work they still wanted |
| Never read any existing document under `docs/program-specs/` | Prior drafts may contain stale facts or hallucinations; re-deriving from iA tools is the only safe source of truth |
| Always call `ia_file_fields` for every file in FILES section | Inline `FIELDNAME (Description)` mentions throughout the document depend on this lookup; skipping leads to vague prose |
| Never render an exhaustive per-file fields table | Fields appear only where the program touches them, with inline descriptions — readers want what the program uses, not full record layouts |
| Every file mention must include its library: `FILENAME (LIBRARY)` | A file name without library is ambiguous on IBM i; readers cannot locate the object |
| Every field reference must include its description in parentheses on every mention | Viewers reading any paragraph in isolation must understand the field; relying on a glossary lookup breaks readability |
| Every subroutine block must show `lines START–END` and `*(line NNN)*` on every internal anchor | Without line numbers, the document cannot be cross-referenced against source for verification or maintenance |
| Every document must contain at least one ASCII process flow tree in the section required by its template | Visual flow trees are how readers navigate IBM i programs; their absence reduces the doc to prose with no decision-path overview |
| Output filename must match canonical pattern `{PGM}_{CanonicalDocType}.md` from Step 7.5 | CanonicalDocType ∈ {Technical_Specification, Functional_Document, Operations_Guide, Architecture_Review, Test_Case_Document}, no version suffix; any other shape = **ERROR**, do not write |
| Run the Step 1.5 existence check before any `ia_*` call; if the canonical doc exists, surface it (date + link) and get confirmation before regenerating | Avoids silently regenerating a doc the user already has and avoids wasting iA calls when they decline |
| Never make an absolute access-method claim ("all data access via SQL", "no native I/O") without in-session proof from F-specs + a native-opcode source search | A later mod that adds native I/O turns a confident absolute into a QA-visible falsehood; absolutes require machine proof, not impressions |

---

## Common Traps

| Trap | Symptom | Fix |
|------|---------|-----|
| Subroutine tunnel vision | Document 10 of 46 subroutines | Step 2 is mandatory — get full list, group into clusters |
| Missing capability | Email, exclusions, scheduling absent from BRs and flow | Every subroutine cluster must appear in BRs and flow |
| Unverified external calls | Asserting calls despite CALL_PGM_COUNT=0 | Check COMPLEXITY CALL_PGM_COUNT before asserting external calls |
| Data area as file | Data area listed in file table | Separate "Data Areas" subsection — data areas use IN/OUT opcodes |
| Silent version selection | Documenting one library version without saying so | **HARD STOP** — after Step 2, if multiple versions found, present the version table and wait for explicit user confirmation. A footnote is not sufficient; the user must choose. |
| Parameter gap | Section 2 all "Not determinable" | `ia_procedure_params` is mandatory before writing Section 2 |
| Caller assertion | Caller listed with no CALLERS result in iA | Only assert callers confirmed by `ia_call_hierarchy` |
| Character validator gap | Alphanumeric validator missing digits | Flag any alphanumeric validator missing digits as "verify against source" |
| Reading a prior doc for "style" | New doc inherits stale facts from `_v1` or another program's spec | **Forbidden** — never open any file under `docs/program-specs/`; re-derive everything from iA tool output |
| File name without library | `CUSTMAST` written instead of `CUSTMAST (PRDLIB)` | Substitute library from FILES section on every mention |
| Field name without description | `CUSTNO` written instead of `CUSTNO (Customer Number)` | Inline `(FIELD_TEXT)` from `ia_file_fields` on every occurrence |
| Subroutine missing line range | Block header says only "SUBROUTINE_NAME" without `lines NNN–NNN` | Pull START/END line numbers from `ia_subroutines` and add to every block |
| Rendered an exhaustive fields table | Section 3 has 200-row field tables when the program touches 8 fields | Drop the table entirely — fields are inline-only where the program logic references them |
| Picked a filename without running Step 7.5 | New file lands as `BIO60R_Specification.md` or a stray `_v{N}` name | Step 7.5 is mandatory; the only legitimate filename is `{PGM}_{CanonicalDocType}.md` |
| Regenerated a doc that already exists without asking | Replaced the user's current spec, or re-ran all the iA queries when they'd have declined | Step 1.5 is mandatory — list the folder, surface the existing canonical doc (date + link), get confirmation before any `ia_*` call |
| Missing ASCII process flow tree | Generated doc has no visual flow in the section required by its template | One ASCII tree (fenced `text` block, box-drawing chars) per template-required section |
| Stale spec vs live source | QA flags operations (e.g. native READ/WRITE) the doc says don't exist; doc line refs don't match current source | The doc describes an older source version. Compare its Freshness fingerprint to `ia_member_lookup` (changed date + line count) — if the member changed after generation, regenerate; don't patch the old doc |

---

## Canonical Tech-Spec Prompt (default for every "technical specification" request)

When the user asks for a technical specification / program analysis document for an IBM i program, this is the **mandatory internal prompt** that drives the writing. It is not shown to the user — but every document produced must conform to it.

```
You are an expert IBM i (AS/400) RPG consultant and legacy application analyst.

Analyze the RPG program source provided below and generate a clear, professional
Program Analysis Document suitable for senior developers, architects, and support teams.

Explain what the program does, how it works, and the business rules it enforces.
Use business-friendly language while retaining technical accuracy.

DO NOT describe the code line by line.
DO NOT assume the presence of any specific business pattern unless it is explicitly present in the code.

--------------------------------
DOCUMENT STRUCTURE
--------------------------------

1. Program Overview
   - Program name and primary purpose
   - Business problem or functionality it addresses
   - Execution type (Batch / Interactive / Online)
   - Key outputs and how they are used or consumed

2. Technical Summary
   - Program ID and RPG type (RPG III, RPG IV, fixed-format, free-form)
   - Entry parameters and their business meaning (if present)
   - Notable revisions, assumptions, or commented-out logic

3. Files and Data Sources
   For each file used in the program:
   - File name
   - Usage type (Input / Output / Update / Reference)
   - Business purpose of the file

4. Main Processing Logic
   Describe the program's execution flow in the same sequence in which it runs:
   - Explain the logic as it progresses from start to end including all the rules,
     conditions, logic etc.
   - If a file is being read/written/updated, mention which keys it is read on,
     what fields are derived out of it and what fields are updated/written.
   - If processing executes through a sub-routine/sub-procedure, mention its
     name and a high-level description of what is happening inside it.
   - Mention setup, validations, parameter usage, loops, calculations, or
     branching only when they are encountered during execution.
   - Describe how control flows between major logic blocks.
   - Identify distinct processing paths only if they naturally occur in the
     program flow.
   - Do not separate or pre-classify logic by category (such as dates, control
     breaks, etc.).

5. Subroutine / Procedure Analysis
   For each significant subroutine or procedure:
   - Name
   - Purpose
   - High-level behavior
   - Key decisions or calculations handled

6. Business Rules and Calculations
   Summarize important rules discovered in the code, such as:
   - Accumulations, totals, or rollups
   - Classification or categorization logic
   - Status, flag, or code-driven behavior
   - Special conditions or exception handling

7. Output File Behavior
   - Conditions under which records are created or updated
   - How values are populated or accumulated
   - Relationship between input data and output results

8. Glossary of important keywords and fields used in the program.

9. Key Observations (Optional)
   - Complexity or risk areas
   - Dependency on reference data or external programs
   - Opportunities for simplification, refactoring, or modernization

--------------------------------
FORMATTING GUIDELINES
--------------------------------
- Use clear section headings and bullet points
- Be concise, accurate, and professional
- Assume IBM i knowledge but no familiarity with this specific program
- Do not infer or invent logic not present in the source

```

The tool sequence, Rule Zero, the Verification Rules table and the Step 7.5 filename gate above apply to this prompt unchanged; they are not repeated here.

---

## Reference: Section → iA Tool Map

| Document Section | Primary iA Source | Fallback |
|---|---|---|
| 1. Program Overview | LOOKUP + COMPLEXITY (DSPF/FILE counts for execution type) | Source header comments |
| 2. Technical Summary — Entry Parameters | `ia_procedure_params` | dcl-pr/dcl-pi or *ENTRY PLIST in source |
| 2. Technical Summary — Revisions / Assumptions | Source comments scan | — |
| 3. Files and Data Sources — file list + library + description | `ia_program_files` (FILE_TEXT) + FILES section | `describe_sql_object` for DDL TEXT |
| 3. Data Areas Used | `ia_variable_ops(opcode=IN or OUT)` | Source D-spec / dcl-ds scan |
| Inline field descriptions (anywhere) | `ia_file_fields(file_name, library_name)` — silent lookup, called once per unique file in Step 2.5 | — |
| 4. Main Processing Logic | Source narrative + SUBROUTINES (for routing); field descriptions from `ia_file_fields` | — |
| 5. Subroutine / Procedure Analysis | SUBROUTINES section (START/END lines) + source bodies | — |
| 5. Call Hierarchy Diagram | CALLEES + BINDINGS | — |
| 6. Business Rules | SUBROUTINES → source IF/WHEN/SELECT/SQL clusters; field descriptions from `ia_file_fields` | — |
| 7. Output File Behavior | FILES section (Output / Update) + source write/update opcodes; field descriptions from `ia_file_fields` | — |
| 8. Glossary | `ia_file_fields` FIELD_TEXT + variable scan | — |
| 9. Key Observations — Callers | CALLERS section | — |
| 9. Key Observations — Service Programs | BINDINGS section | — |
| Statistics block | COMPLEXITY section | — |
