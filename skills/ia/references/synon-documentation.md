# Synon / CA 2E Program Analysis Reference

Use this guide when the target is a **CA 2E (Synon/2E) function** — the user asked for an "action diagram analysis", asked to "document this Synon function", asked for **functional documentation** of a 2E function, or handed over Synon export files (`*_AD`, `*_RPG`, `*_DDS`).

Two DocTypes live here: **`Synon_Program_Analysis`** (technical — the default) and **`Synon_Functional_Document`** (business audience). Coerce the request to exactly one in [§0](#0-doctype-selection-run-first) before any other step.

**Synon/2E only.** Load this reference only when at least one of these signals is present:

| Signal | Example |
|--------|---------|
| The user names the technology | "Synon", "CA 2E", "2E function", "action diagram" |
| A Synon export file is supplied | an `*_AD` file, or `*_RPG` / `*_DDS` alongside one |
| The name resolves as a 2E function in the repository | `ia_synon_functions(function_name=X)` returns a row — the definitive test. `ia_member_lookup` showing a Synon source member is a weaker confirmation |

**"AS400 program analysis document" is not by itself a signal** — users say that about plain RPG and CL programs too. With none of the three signals, use [program-documentation.md](program-documentation.md).

Wrong reference when:

- The member is RPG / RPGLE / SQLRPGLE / CL / CLLE / CLP with no 2E design behind it → [program-documentation.md](program-documentation.md).
- The target is the **2E-generated RPG** and the action diagram cannot be reached at all → do not document the generator's output as business logic (§9, trap 1). Say the AD is unavailable and offer a generated-code spec via [program-documentation.md](program-documentation.md) instead.
- The ask is change impact, version comparison or a context matrix — those DocTypes are technology-agnostic and keep their own references even for 2E objects.

**A functional request is not a reason to leave.** "Functional doc", "business doc" or "for business analysts" against a 2E function is `Synon_Functional_Document` **in this reference** (§0, §6F) — not `Functional_Document` in [program-documentation.md](program-documentation.md), which excludes 2E functions for every DocType it carries. The technology decides the reference; the wording decides which DocType inside it.

Both DocTypes are centred on the **Action Diagram** and save under `docs/synon-specs/{FUNCTION}/`. `Synon_Program_Analysis` is **one** comprehensive document serving developers, business/Synon analysts, stakeholders and testers from the same text — `{FUNCTION}_Program_Analysis.md`. `Synon_Functional_Document` is a shorter business-audience document with its own structure — `{FUNCTION}_Functional_Document.md`.

For `Synon_Program_Analysis` the structure in [§6](#6-output-structure) is **fixed**: exact headings, exact table columns, exact order. Nothing added, nothing dropped, nothing renamed. Two sections carry the document — **§2.4 Screen Field Mapping** and **§2.5 Processing and Validations** — and §2.5 gets the largest share of the effort. For `Synon_Functional_Document` the structure in [§6F](#6f-functional-document-structure) is fixed the same way, and **§2 Business Rules** carries it.

---

## 0. DocType selection (run first)

This reference carries **two** DocTypes for a 2E function. Coerce the request to exactly one before any other step — the choice decides the structure (§6 + §7 vs §6F), the verification gate (§8) and the filename (§10).

| User wording (examples) | DocType | Structure | Output file |
|---|---|---|---|
| "program analysis", "action diagram analysis", "document this Synon function", "AS400 program analysis document", "technical spec", **default** | `Synon_Program_Analysis` | §6 + §7 | `{FUNCTION}_Program_Analysis.md` |
| "functional doc", "functional documentation", "business doc", "BA doc", "non-technical", "for business analysts", "for stakeholders" | `Synon_Functional_Document` | §6F | `{FUNCTION}_Functional_Document.md` |

Rules:

- **"Functional" is never a modifier on the technical document.** A functional request produces the §6F structure — not §6 with softer wording, not §6 with sections dropped, not §6 with a business summary bolted on top. Answering a functional request with the §6 document is the single defect this gate exists to prevent, and it is invisible in the output: the document looks complete and correct, it is simply the wrong deliverable.
- **The default is `Synon_Program_Analysis`.** Silence, or any wording that does not signal a business audience, takes the technical DocType. §6 stays the default for the same reason it always was — it is what "document this function" means to the people who ask most often.
- **State which one you chose** in one line before the first tool call, so a mis-read costs a correction rather than a whole document.
- **Genuinely ambiguous → ask.** "Documentation for function X" with a non-technical audience named anywhere in the request is functional. With nothing pointing either way it is technical, and you say so rather than asking.
- **Both requested** ("technical and functional", "both docs") → run the workflow once per DocType and produce two files. §§1–5 are shared — the same inputs, ground rules, Master Report and AD read serve both, so the second document costs assembly effort, not a second analysis.

§§1–5 and §§8–11 apply to both DocTypes. §6 + §7 are the technical structure; §6F is the functional one.

---

## 1. Inputs and file identification

| Mode | When | Where source comes from |
|------|------|-------------------------|
| **A — attached exports** | The user attaches or points at export files | The files themselves. Reading source the user explicitly hands you is the one documented exception to SKILL.md Rule Zero |
| **B — iA repository** | Only a function/member name is given | `ia_synon_functions` → `ia_synon_action_diagram` + `ia_synon_variable_ops` (the parsed action diagram), `ia_synon_source` (verbatim AD text), `ia_rpg_source` (generated RPG), `ia_dds_source` (display-file DDS) |

Mixed inputs are normal (an attached `_AD` plus repository lookups for callers, files and menu path). Use both; never let a missing input become a guess.

| Input | Identified by | Role |
|-------|---------------|------|
| **Action Diagram** | filename suffix `_AD`, or the Synon source member | **MAIN FILE.** Dictates primary execution flow and logical structure. The whole document is centred on it |
| **Generated RPG** | suffix `_RPG` | Supporting, and **only to resolve what the AD refers to**: the real file and access-path names behind an AD reference, the implementation name of a called function, a field's declared type and length. Its own mechanics never reach the document — see §2 rule 10 |
| **Display file DDS** | suffix `_DDS` | Supporting, **and the absolute source of truth for §2.4** screen fields |
| **Master Report** | a previously generated analysis document (PDF / text / `.md`) | Corrected, human-reviewed values — see §3 |

- More than one `_AD` present → **ask which is the main function**; never auto-pick.
- An `_RPG` or `_DDS` with no matching `_AD` → say so and stop; this DocType is defined by the action diagram. For a pure RPG member use [program-documentation.md](program-documentation.md) instead.
- Functions referenced by the AD but not supplied (internal or external) → document them from the AD text and mark unresolved detail `Not Available`. Do not infer their internals.

---

## 2. Ground rules

1. **No assumptions.** If a detail is not in the provided files or in iA tool output, write `Not Available`. Never guess a value, a validation, a message or a file name.
2. **The AD is the spine.** RPG and DDS explain the AD; they never replace it. Where the RPG shows something the AD does not (a generated read, a system field), attribute it to the generated code, not to business logic.
3. **Analyse everything together.** Identify the relationship between the AD and its dependents: internal functions, external function/program calls, subroutines, subprocedures, database files, screen formats.
4. **No invented logic.** Every validation, error message and calculation must trace to a line in the supplied source.
5. **Exclusions.**
   - `Y2`-prefixed objects are 2E-generated system objects — never list them in §5.
   - **`Synon_Program_Analysis` only:** function and command keys belong **only** in §2.7, never in §2.5. In a `Synon_Functional_Document` there is no §2.7 — a key name appears inside the BR-xxx rule whose business meaning depends on it, and there is no key inventory table (§6F exclusions).
   - **`Synon_Program_Analysis` only:** screen field validations belong **only** in §2.4, never repeated in §2.5. In a `Synon_Functional_Document` there is no §2.4 — the validations that matter to the business become BR-xxx bullets in §2 (§6F exclusions).
   - Header/footer screen furniture (program title, company name, date/time, key legend) is excluded from §2.4.
   - COBOL is out of scope repository-wide.
6. **Naming convention inside the document.** Name a file as *description* + implementation name — `Order Header TRG - OPBFCPP` — and a called function as *object* + its 2E text — `PDW3XFR - CLC Total Load Miles XF`. Use the object's real 2E text, not a paraphrase.
7. **Repository snapshot.** In mode B the source is a build snapshot. Take the collection date from `ia_repo_config` and state it in the document's header block — under the branding line in a `Synon_Program_Analysis`, on the `**Date:**` line in a `Synon_Functional_Document` (`**Date:** {today} (repository snapshot: {snapshot})`). If the user needs live source, say the snapshot date and offer a live re-read.
8. **Branding.** `Author: iA by programmers.io` (see SKILL.md → Response Branding).
9. **No tool names in the document.** The deliverable never names the tooling that produced it — no `ia_*` / `ia-*` tool name, no ad-hoc SQL, no MCP or server wording, no iA repository table name, no parameter name from a tool call. Write what the analysis found, not how it was found: "Programs that call this function", never "`ia_call_hierarchy` returned". Client file, field, program and function names are of course in scope — it is the *tooling* that stays out. Provenance and coverage caveats belong in your chat reply; the §2 rule 8 branding line is the document's only reference to iA.
10. **RPG detail only where it explains the AD.** The generated RPG is read to *resolve* AD references — which physical file and access path a read hits, which program a call lands on, a field's declared type and length — and those resolved facts belong in the document. Its implementation mechanics do not: no opcodes (`CHAIN`, `SETLL`, `READE`, `WRITE`, `MOVE`, `EVAL`), no indicators, no generated subroutine or variable names, no F-spec/D-spec declarations, no RPG cycle or generated control flow. Test each RPG fact before writing it: *does a reader need this to understand the action diagram?* If not, cut it. "Reads **"Load Detail - `OMFLCPP`"** by Load ID in stop sequence" is the AD's rule; "performs a `CHAIN` to `OMFLCPP` setting `*IN71`" is generator plumbing.

---

## 3. Master Report precedence

A **Master Report** is a previously generated analysis document for the same function, supplied or pointed at by the user. It has been corrected by a human, so it outranks fresh analysis.

| Rule | Meaning |
|------|---------|
| **Source of truth** | Every value present in the Master Report is authoritative |
| **Strictly reuse** | If a section or table cell exists in the Master Report, carry it across verbatim |
| **Generate only gaps** | New analysis fills only what the Master Report does not cover |
| **Never overwrite** | Do not re-derive, rephrase or "improve" a corrected value |
| **Prefer the Master Report** | On any conflict between it and your file analysis, the Master Report wins — note the conflict in your chat reply, not in the document |
| **Same structure** | Master Report values are injected into the §6 / §6F structure of the DocType you are generating; the structure never bends to the old document's layout. A Master Report written against §6 still supplies values to a §6F document — its business function, file purposes, messages and callee descriptions carry across; its §2.4 and §2.5 tables have no §6F home and are read for the rules they contain, not copied |

This is a deliberate exception to the program-documentation Rule Zero ("never read existing documentation"): the user has explicitly opted in by supplying the report. It applies **only** to a Master Report the user supplied — not to other documents you happen to find under `docs/`.

Two Master Report specifics:

- **§Revision Log** is the only place revision history may appear, and only when the Master Report carries it — its rows come across verbatim, with the blank row kept below them.
- **§2.1 Parameters → Value** column is populated only from the Master Report; otherwise every cell stays empty.

---

## 4. Workflow

| Step | Action | Tools |
|------|--------|-------|
| 0 | **Choose the DocType (§0)** and say which one. Then identify the main `_AD`, its dependents and any Master Report (§1). Confirm the function name and library with the user if ambiguous | — |
| 1 | **Existing-output gate.** List `docs/synon-specs/{FUNCTION}/`; if the **chosen DocType's** file (§10) exists, surface it with its date and ask before regenerating. The *other* DocType's file existing is not a reason to stop — the two are separate deliverables and each has exactly one canonical copy | filesystem listing only |
| 2 | **Resolve the function and gate on it** (mode B): `ia_synon_functions` must return a row — it yields the `pgm_surrogate_id` every other Synon tool needs, the 2E `function_type` (→ §1 Program Type) and the generated AD member names. No hit, and `ia_member_lookup` shows an RPG/CL member with no 2E design behind it → wrong DocType, stop and switch to [program-documentation.md](program-documentation.md). Capture the repository build date | `ia_synon_functions`, `ia_member_lookup`, `ia_object_lookup`, `ia_repo_config` |
| 3 | **Read the action diagram in full** — parsed statements and their operands first, then the verbatim AD text, the generated RPG and the DDS. Paginate every read to the end | `ia_synon_action_diagram`, `ia_synon_variable_ops`, `ia_synon_source`, `ia_rpg_source`, `ia_code_complexity`, `ia_dds_source` |
| 4 | **Structural inventory** — files, callers, callees, parameters, subroutines, field metadata | `ia_program_spec_bundle`, `ia_program_files`, `ia_object_context_matrix`, `ia_call_hierarchy` (both directions), `ia_file_fields`, `ia_file_dependencies`, `ia_cl_jobs` |
| 5 | **Assemble** the document against §6 + §7 (`Synon_Program_Analysis`, effort budget on §2.4 and §2.5) or against §6F (`Synon_Functional_Document`, effort budget on §2 Business Rules and §4 Process Flow) | — |
| 6 | **Verify** against the §8 gate before showing anything | — |
| 7 | **Save** to `docs/synon-specs/{FUNCTION}/` under the DocType's filename (§10), then export on request | `scripts/convert_md_to_docx.py`, `scripts/convert_md_to_pdf.py` |

### Step 3 — reading the sources

Order matters: resolve, then read structure, then read text.

1. **Resolve the function** — `ia_synon_functions(function_name=X)`. Returns `pgm_surrogate_id` (the key every other Synon tool needs), `function_type`, `implementation_name`, and the generated AD members `ad_member_full` / `ad_member_concise` with their `generated_library` and `generated_source_file`. `function_name` matches the design name, the implementation name, **or the AD member name** — so a user who hands you `F1101013_F` off an export resolves in one call. Expect `implementation_name` to be **blank** for the internal function types (`CRTOBJ`, `CHGOBJ`, `DLTOBJ`, `RTVOBJ`, `EXCINTFUN`, `PRTOBJ`): 2E compiles those inline into the calling function's RPG instead of generating a standalone `*PGM`, so a blank implementation name is normal and there is no compiled object or generated RPG to read — it is not a collection gap, and step 3.5 simply does not apply. More than one match → **ask which function**; never pick one. 2E design names are mixed case and contain spaces (`Create Application`) and `implementation_name` is often blank — pass the name as the user typed it and use `%` wildcards. This is the one place in the skill where SKILL.md Rule One (upper-case every name) does not apply: matching here is case-insensitive by design.
2. **Statements** — `ia_synon_action_diagram(pgm_surrogate_id=N)`. One row per AD statement: `line_sequence` is execution order, `depth` is the nesting level, `parent_statement` links a statement to the block that owns it, `raw_text` is the statement itself, and `operation` classifies it (`IF` / `CASE` / `FOR` / `ACTION` / `*OTHERWISE` …). Two traps: `operation` is **blank on roughly 40% of statements**, so never enumerate the diagram by looping over operation values — sweep with `*ALL` and classify from `raw_text`; and `owner_table` is `*NONE` on every row in the repositories checked so far, so it cannot isolate file actions. Read to the end — the cap is 10000 statements per call, so page with `offset` until a short page comes back. A partial read silently drops nested branches and internal function calls, which is exactly the content §2.5 is judged on.
3. **Operands** — `ia_synon_variable_ops(pgm_surrogate_id=N)`, joined back to the statements by `statement_id`. One row per variable per statement: `variable_usage` (`OUT` = written, `IN` = read, `BOTH` = read and written, `NONE` = neither), `variable_context` (`PAR`/`DB1`/`LCL`/`WRK`/`CON`/`JOB`/`PGM`/`CND`/`NLL`/`ELM`, plus `DB2`/`CTL`/`RCD` in models that use them), `variable_seq` (position within the statement) and the descriptive `variable_name`. This is what turns a statement into a rule — `OUT PAR."Changed User"` seq 1 plus `IN JOB."*USER"` seq 2 reads as `PAR.Changed User = JOB.*USER`. Two filters carry whole sections: `variable_context=PAR` is the §2.1 parameter list, and **`variable_usage=OUT` plus `variable_usage=BOTH`** is every field the function writes (§2.8) — `BOTH` is a write too, typically a field handed to a `CALL` as both input and output, so `OUT` alone silently under-reports §2.8.

> **Coverage caveat — If `ia_synon_variable_ops` returned no operands, fall back to parsing `raw_text` from `ia_synon_action_diagram` (assignments appear there in full, e.g. `PAR.DS_Address = CONCAT(LCL.ACK_Dept ID,LCL.AB Fld 2,CON.1)`), and say in the document that field-level direction was derived from statement text rather than captured operands.
4. **Verbatim text** — `ia_synon_source(member_name=ad_member_full)`, using the member name step 1 returned. The parsed tables give structure and order; the source member gives the exact message text, literals and labels that §8 requires be quoted rather than paraphrased.
5. **Generated RPG** — `ia_rpg_source(member_name=..., library_name=L)`. Take the member from `implementation_name` or from the generated members in step 1; the generated member name routinely differs from the design function name, so never assume it.
6. **DDS** — `ia_dds_source(member_name={DSPF})`. This is the absolute source for §2.4: walk it record format by record format so no screen field is missed. Add `member_type='DSPF'` when a name collides across DDS types, and paginate with `offset` for a display file over 10000 lines. Do **not** take screen fields from the generated RPG — it carries programmatic names (`#1SEL`), not the user-facing labels §2.4 requires.

**Expanding called functions.** An `EXCINTFUN` / `EXCEXTFUN` / `EXCUSRPGM` statement names its target in `raw_text`. Feed that name back through `ia_synon_functions` → `ia_synon_action_diagram` (+ `ia_synon_variable_ops`) and expand the callee in place under the call, as §7 mandate 6 requires. Repeat until no new callees appear. If you stop early — a depth limit, or a function that is not in the repository — name the calls you left unexpanded instead of summarising them.

### Step 4 — deriving the header sections

- **Menu Path:** run `ia_call_hierarchy(program_name=FUNCTION, direction='CALLERS')` and walk up until a `*MENU` appears. The option number and option text come from the menu's own source members, not from the hierarchy — see [onboarding-guide.md §3](onboarding-guide.md). No menu reached → `Not Available`; never number an option yourself.
- **Scheduled Jobs:** `ia_cl_jobs(member_name='*ALL')` plus `ia_call_hierarchy(direction='CALLERS')` — a CL with an `SBMJOB` naming this function is a batch caller. Nothing found → `Not Available`.
- **§3 Related Database Table Info:** `ia_program_files` plus the `FILE_*` sections of `ia_object_context_matrix`. Logical files must be resolved to the physical file they are built over (`ia_file_dependencies`) — the section lists physical files only.
- **§5.1 / §5.2:** `ia_call_hierarchy` in both directions, enriched with each object's type, attribute and text from `ia_object_context_matrix` or `ia_object_lookup`. Drop `Y2*` rows.

---

## 5. Reading an action diagram (2E orientation)

Action diagram lines are indented statements in a fixed set of shapes. Recognise them so §2.5 mirrors the real structure — but **always take names, labels and message text verbatim from the AD**; nothing in this section is a substitute for what the file says.

| Shape | Appears as | §2.5 treatment |
|-------|-----------|----------------|
| Sequential action | a single built-in or function call | One concise bullet (`SET PAR.Counter = 0`) |
| Conditional | `IF` / `ELSE` / `CASE` / `OTHERWISE` with nested indentation | One bullet per branch, nested; every comparison spelled out |
| Iteration | a repeat/read loop over an access path | Name the file and access path, the key used, and what ends the loop |
| Internal function call | an `EXCINTFUN`-style call inside the same function | Expand recursively as a nested sub-list under the call |
| External function / program call | `EXCEXTFUN`, `EXCUSRPGM`, `CALL` | Name the object and its 2E text, list the parameters passed, then the outcome |
| Message | send-error / send-completion / send-information message | Quote the exact message text; that text is what a tester will look for |
| File action | create / change / delete / retrieve object over an access path | Name the file, the access path, the key fields and the fields written |

In mode B these shapes arrive already separated: `depth` and `parent_statement` give the nesting, `operation` classifies the statement where it is populated (`owner_table` does not — it is `*NONE` throughout), `line_sequence` fixes the order, and `ia_synon_variable_ops` supplies the operands where they were captured. Use the columns for structure and `raw_text` for wording — never the other way round.

Field contexts you will meet on the left of an assignment (2E naming, and exactly the `variable_context` values `ia_synon_variable_ops` returns): `PAR` (parameter), `DB1` / `DB2` (database record buffers), `WRK` (work field), `CON` (constant / literal), `LCL` (local), `CTL` (screen control / header), `RCD` (subfile record), and `*`-prefixed system fields (`*Return code`, `*Program mode`, `*User`, `*Job date`, `*Record data changed`). Keep the context prefix when you quote an assignment — `PAR.Load ID` and `DB1.Load ID` are different things, and the distinction is often the whole point of a step.

Standard 2E function types (from the design, echoed in the AD header, and returned as `function_type` by `ia_synon_functions`) tell you what §1 **Program Type** should say and what user points to expect: `DSPFIL`, `DSPRCD`, `EDTRCD`, `EDTFIL`, `SELRCD`, `PMTRCD` (Prompt and Validate Record), `PRTFIL`, `PRTOBJ`, `RTVOBJ`, `CRTOBJ`, `CHGOBJ`, `DLTOBJ`, `EXCINTFUN`, `EXCEXTFUN`, `EXCUSRPGM`, `DSPTRN`, `EDTTRN`. Write the type exactly as the design names it, with its expansion — e.g. `Prompt & Validate Record (PVR)`.

User-programmable points (labelled `USER:` in the AD — initialise, validate, load/process record, process command keys, exit processing) are where all custom logic lives. **Use the exact label from the file** as the §2.5 block heading; the set and wording of these points varies by function type and 2E release.

---

## 6. Output structure

The **only** valid structure for `Synon_Program_Analysis`. For `Synon_Functional_Document` use [§6F](#6f-functional-document-structure) instead — a different structure, not a subset of this one. Reproduce these headings verbatim and in this order. Formatting rules: main headers `### **Title**`, sub-headers `#### **Title**`, bullets with `-` indented two spaces under their header, GitHub-style tables never wrapped in code fences, paragraphs left-aligned directly under their heading.

| # | Heading | Content rules |
|---|---------|---------------|
| — | `# AS400 Program Analysis:` then `# **{FUNCTION} - {IMPLEMENTATION_NAME}**` | Two level-1 headers, exactly as shown — **the same shape in every document**. `{FUNCTION}` is the 2E design name, `{IMPLEMENTATION_NAME}` the generated program name. Name and implementation name are the whole title: no 2E text, no short description, no library, no paraphrase. Implementation name blank (the internal function types — §4, step 3 item 1) → the design name alone, with no dash and no substitute text |
| — | `### **Menu Path**` | Navigation path from the main menu, or `Not Available` |
| — | `### **Scheduled Jobs**` | Batch jobs related to this program, or `Not Available` |
| — | `### **Revision Log**` | **Always one blank row** under the headers, so the reader can add their own entry later. Revision history in the source code is *never* extracted here. Rows come only from a Master Report — and the blank row still follows whatever it supplies |
| 1 | `### **1. Program Name and Purpose**` | Exactly four items, in this order: `**Program Name:**` (2E design name), `**Implementation Name:**` (generated program name; `Not Available` when 2E compiles the function inline and there is none), `**Program Type:**`, `**Business Function:**`. The business function is business-oriented prose covering key user interactions, what report/update/process it triggers, and its major objectives and validations |
| 2 | `### **2. AS-IS Analysis**` | Short summary: program type, primary database files accessed, main operations (subfile loading, updates), brief DB update note |
| 2.1 | `### **2.1. Parameters**` | Table `Field Name \| Type \| Length \| Mode (I-Input, O-Output, B-Both) \| Value`, in that column order. **Field Name is the user-facing descriptive label** (`Warehouse Code`, `Load ID`) — never the programmatic name (`P0RTN`, `P1AIC3`). **Type** is the data type as the 2E dictionary or the generated declaration gives it (`Alphanumeric` / `Numeric` / `Date` / `Time`, or the concrete `A`, `P`, `S`, `Z` where that is what the source shows) and **Length** is the declared size, with decimals as `9,2` for a packed/zoned field. Take both from the field's declaration — the generated RPG or the file/dictionary field metadata — and write `Not Available` for either cell that the supplied source does not carry; never infer a length from a sample value. Mode is only `I`, `O` or `B`. Value stays empty unless a Master Report supplies it. Every AD parameter is listed |
| 2.2 | `### **2.2. Access Check**` | Fixed sentence, as plain text, nothing else: `Only users with the appropriate permissions defined in their IAM profile should be allowed to access this screen.` |
| 2.3 | `### **2.3. Record Selection Criteria**` | Bulleted **Select** and **Do not select** conditions. Each gives the field name, the file/table it lives in, and the condition. Identify the source of each condition — access path `SELECT`/`OMIT` rules vs. program logic. Only conditions explicitly present; no business-logic narration; no duplication of parameter detail |
| 2.4 | `### **2.4. Screen Field Mapping**` | See below — one of the two critical sections |
| 2.5 | `### **2.5. Processing and Validations**` | See §7 — the most important section in the document |
| 2.6 | `### **2.6. Subfile/Record Options**` | Table `Option \| Description \| Action`. Every option on the subfile/record screen, verified against the DDS and the AD. The Action cell names the program or function called and any conditional logic ("If Load ID is present, call `PDT3DFR`"). Correct inaccurate prior documentation |
| 2.7 | `### **2.7. Function Keys / Command Keys**` | Table `Key \| Action`. Every relevant key (F4, F5, F21 …) with its specific outcome: conditional logic, program calls with a short description, and how data is modified/saved/retrieved. Exclude F3/Exit, Enter, Home and Help |
| 2.8 | `### **2.8. Update Database**` | Table `File Name \| File Description \| Field(s) Updated \| Action`. Only files this program updates. Action states Create / Update / Delete plus the triggering condition. Implementation names without the F-spec prefix (`OPBFCPP`, never `FOPBFCPP`) |
| 3 | `### **3. Related Database Table Info**` | Table `File Name \| Description \| Usage (I/O/U) \| Description` — the duplicated fourth header is intentional and stays. **Physical files only**: replace every logical file with the PF it is built over. All files the program reads, updates or writes. `Not Available` if none |
| 4 | `### **4. Related Documents**` | External documents, or `Not Available`. Include subprogram calls/references shown by the action diagram and program-to-program relationships |
| 5 | `### **5. Related Programs**` | Intro to the two sub-sections; both always present, even when empty |
| 5.1 | `### **5.1. Programs that reference/execute this program**` | Table `Object Name \| Object Type \| Object Attribute \| Object Text / Description`. Every caller. Empty table with the same headers when none |
| 5.2 | `### **5.2. Programs this program references/executes**` | Same columns. Every callee, and the description must be a **precise business-level statement of what the callee does for this program** (`Rtv Addtnl Route Hrs XF - Retrieves any additional route hours needed for Load Lock calculation`), not the generic object text |

### §2.4 Screen Field Mapping — rules

Table, exactly these columns in this order:

| Screen Field Name | File Field Name | I/O | Required/Optional | Load From File or Field | Comments & Validations |
| :---------------- | :-------------- | :-- | :---------------- | :---------------------- | :--------------------- |

- A **screen field** is any field, text or numeric, on the display screen. The **DDS is the absolute source** for the complete list — walk it record format by record format so nothing is missed.
- **Screen Field Name** — the user-facing label/heading text on the screen.
- **File Field Name** — the DDS field's descriptive / file field name. **Never a programmatic variable name** (`#1SEL`, `#CAJCD`) from the RPG.
- **I/O** — `Input`, `Output` or `Both`. Every data field inside a subfile record format is `Output`, unless it is the user option field or the DDS explicitly defines it as input. Report fields are all `Output`.
- **Required/Optional** — for input fields; `N/A` for output-only fields.
- **Load From File or Field** — the exact source: a file name, `PROGRAM_CALCULATION`, `USER_INPUT`, or a reference to the initialisation logic described in §2.5.
- **Comments & Validations** — the **only** column for field-level validations (`Numeric only`, `Must be valid state code`, `Range check 1-99`, `F4 prompt available`). Every validation performed on that field goes here, and nowhere else in the document.
- Exclude header/footer furniture: program title, company name, date/time display, function-key legend, command keys.

---

## 6F. Functional Document structure

The **only** valid structure for `Synon_Functional_Document`. It mirrors the seven numbered sections the RPG/CL flow's `Functional_Document` DocType uses, so a functional document reads the same to a business analyst whether the program behind it is hand-written RPG or a 2E function — same section names, same order, only the sourcing differs, because here every rule comes from the action diagram rather than from subroutines. [templates/template-synon-functional.md](templates/template-synon-functional.md) is the fill-in copy.

Formatting: `## N. Title` for the seven sections, `### Title` for sub-headers, tables GitHub-style and never wrapped in code fences.

**Read the template before writing.** It is the structure of record: the seven headings and their order, every table's columns, and the fixed text of the metadata block and the quality footer. Copy it and fill it in — do not reconstruct the structure from memory.

The rules below are the ones the template cannot show on its own; everything else about the shape is in the template.

- **Title** — the same shape as §6, so the two documents read as a family. Implementation name blank (the internal function types — §4, step 3 item 1) → the design name alone, with no dash and no substitute text.
- **Metadata** — in mode B the repository snapshot date goes on the Date line (§2 rule 7).
- **§1** — derive the marked **Program Type** box from the 2E `function_type` and whether the function drives a display file. **Key Capabilities** is 3–6 bullets, each a thing a user can accomplish.
- **§3** — name files per §2 rule 6, and state each Purpose as what the file holds *for this function*. **Key Data Elements** carries only the fields the §2 rules turn on.
- **§4** — the arrow flow is 5–12 steps. Follow the AD's execution order but at business granularity: one step per user point or option, not one per statement. **Detailed Steps** carries one entry per arrow-flow step, in the same order, and both lines of every entry run to **at least two sentences**: *What happens* states what the step does plus the data it touches and the condition that governs it; *Business impact* states why it matters to the business plus what goes wrong for the user or the downstream process when it fails or is skipped. A single-clause line ("Validates the carrier code.") is a defect — the flow diagram already says that much, and the prose is the part a business reader acts on.
- **§5** — each purpose is what the callee does *for this function*, as in §5.2 of the technical structure.
- **§6** — `Not Available` if the AD sends no messages.
- **§7** — all four metric rows always present. For the internal function types 2E compiles inline (§4, step 3 item 1) there is no standalone generated program, so Size and Complexity are `Not Available` and the What This Means cell says why; never fall back to the calling function's line count.

### §2 Business Rules — the critical section

Where the functional document earns its keep, and the one section carrying the same analytical weight §2.5 carries in the technical document. What differs is the output *form*: §2.5 is a line-by-line trace, §2 is a numbered list of rules. The AD read behind them is identical — same full pagination, same recursive expansion of internal functions — because you cannot state a rule you have not traced. Only the traversal stays off the page.

Four `###` sub-headers in this order, each holding `- **BR-nnn** — {rule in plain language}` bullets. Numbering runs continuously from BR-001 across all four groups, never restarting per group.

| Sub-header | Holds |
|------------|-------|
| `### Validation Rules` | Every condition that can reject input or block an action, and what happens when it fails |
| `### Calculation Rules` | Every derived value — what is computed, from which inputs, under which conditions |
| `### Workflow Rules` | Sequencing, status transitions, approvals, what may follow what |
| `### Data Rules` | What is created, updated or deleted, and the condition that triggers it |

Mandates:

1. **One rule per bullet, in business language.** A rule a business analyst can confirm or dispute without knowing 2E. No file-access mechanics, no 2E context codes, no statement sequence numbers, no function-type names.
2. **Every rule traces to the AD.** The same evidentiary standard as §2.5 (§2 rules 1 and 4). A plausible business rule you cannot point at in the source is a defect, not a bonus — and it is more tempting here, because plain language hides the gap a line-by-line trace would expose.
3. **Anchor in words, not line numbers.** Cite the AD block a rule comes from in terms the reader shares — the user point, the option, the named internal function ("on Option 6, Lock Load"). Statement sequences and `line_sequence` values are provenance for your chat reply, not content for a business document.
4. **Quote message text exactly** where a rule sends one, then explain it. The literal text is what the user sees on screen, which makes it the most checkable thing in the document.
5. **Expand internal functions, then flatten.** Recurse as §7 mandate 6 requires, because most 2E validation lives one or two levels down. Their rules join the numbered list at the level the *business* sees them, not nested under the call. Recursion is how you find rules, not how you present them.
6. **Groups are for reading, not accounting.** A rule that could sit in two groups goes once, in the one a reader would look in first. Omit a group the AD has nothing for — an empty `### Calculation Rules` header is noise.
7. **Forbidden phrases carry over** from §7 mandate 4: "comprehensive checks", "standard validations", "performs validations", "updates the file", or any equivalent standing in for a rule instead of stating it. Condensing the *trace* is the point of this DocType; condensing the *rule* defeats it.

### Excluded from the functional document

| Excluded | Why, and where it lives instead |
|----------|---------------------------------|
| §2.4-style screen field mapping table | A six-column DDS field inventory is technical reference, not business content. Field validations that matter to the business become BR-xxx bullets in §2; the table belongs to §6 |
| Parameter table with types, lengths and I/O/B mode | Interface detail. Where a parameter *drives* behaviour, that behaviour is a rule in §2 |
| Line-by-line §2.5 execution trace | Replaced by §2 (the rules) and §4 (the flow). Never include both forms |
| §2.2 Access Check, §2.3 Record Selection Criteria, §2.6 Subfile Options, §2.7 Function Keys as sections | Access rules, selection criteria and what an option or key *does* become BR-xxx bullets or §4 steps. A key name (F4, F21) may appear inside a rule whose business meaning depends on it; there is no key or option inventory table |
| RPG implementation mechanics | Already excluded document-wide by §2 rule 10 — doubly out of place in front of this audience |
| Tool names, parameter names, iA table names, SQL | §2 rule 9, identically for both DocTypes |

Nothing is added either: seven sections in order, plus the header block and the quality footer.

---

## 7. §2.5 Processing and Validations — the critical section

A **sequential, line-by-line reverse-engineering** of the action diagram's execution flow. The output is an exhaustive hierarchical blueprint of the business rules, not a summary.

### Mandates

1. **Simulate a debugger trace.** Start at the AD entry point and follow **every** line in the **exact order it appears**. Describe reads, sets, conditions, calls and loops in code order — never regrouped by topic. In mode B that order is `line_sequence` ascending; `statement_id` is a surrogate key and its ascending order is **not** execution order.
2. **Scale the detail to the construct.** Simple sequential steps (an initialisation, a single field set) collapse into one-line bullets. Conditional blocks, loops, function calls and file updates expand into nested multi-bullet detail.
3. **Nest as deeply as the code does.** Indent with hyphens, one level per logical level, matching the AD's structure — 15+ levels where the AD goes that deep. In mode B `depth` *is* that level; do not flatten it, and do not invent a level the column does not show. A compound calculation (a date subtraction, a rate lookup) becomes five to seven sub-bullets, not one.
4. **No logic excluded.** Document every comparison, calculation, file access and error trigger. **Forbidden phrases:** "comprehensive checks", "standard validations", "updates the file", "performs validations", or any equivalent summary. List each check and each field update explicitly.
5. **Branching over eight lines gets five or more sub-bullets per path.**
6. **Expand internal functions recursively.** For every internal function call, nest its entry parameters, its own conditionals and loops, its file accesses and its return values directly under the call. If it calls further functions, expand those too, at the same fidelity. In mode B that is a loop, not a judgement call: the callee name in `raw_text` → `ia_synon_functions` → `ia_synon_action_diagram` + `ia_synon_variable_ops`, repeated until no new callees appear.
7. **Quote message text exactly.** Every error, warning and informational message appears with its literal text, and its message id when the AD carries one.
8. **Name every file, access path and field** involved in a step, using the §2 naming convention.

### Structure

- One bold numbered block per major logical unit, in execution order — `**1. Initialization:**`, `**2. Subfile Loading:**`, `**3. User Actions & Validations:**`, `**4. Option 2 (Confirm Order Details):**`, …
- Block titles come from the AD's own user points and option handling, not from a fixed list.
- Sub-levels are hyphen bullets, indented one level per nesting level.
- Long ordered sub-processes may use `I.`, `II.`, `III.` inside a bullet where the AD itself is a numbered sequence.

### Exclusions

- **No function keys** (F3, F4, F21 …) — they belong in §2.7.
- **No repetition of §2.4 field validations** — this section documents AD execution logic.
- **No RPG implementation mechanics** — opcodes, indicators, generated subroutine and variable names, F-specs/D-specs, generated control flow. Describe the AD's rule and name the file, access path and fields it touches; how the generator expressed it is out of scope (§2 rule 10).

### Shape of the required output

```markdown
**1. Initialization:**
- Consider **"Application Code"** as **"OMS"**.
- Get the **"User Code Model"** from **"User Profile Control - `CADRREP`"** for the user profile name.
- If **"User Code Model"** is available, use it; otherwise use **"User Profile Name"** and, with the application code, get the **company number** and **warehouse code** from **"User Application Profile - `CADTREP`"**.
- **Deny access** if those values are not present in **"User Application Profile - `CADTREP`"**.

**2. Option 6 (Lock Load):**
- **Check any errors pending as given below:**
  - A record is present in **"Load Detail - `OMFLCPP`"** for the Load ID. If no record, send error: **"No Orders Assigned"**.
  - **"Load Status"** is not **"I" or "L" or "S"**. If it is, send error: **"Load cannot be locked due to load status."**
  - **"Carrier Code"** is not blank. If blank, send error: **"Carrier must be entered for load"**.
- **If there is no error as above, then:**
  - Get **"header status"** and **"order in use"** from **"Order Header TRG - `OPBFCPP`"**. Continue when header status is not **"H"** or **"X"** and order in use is not **"Y"**.
  - Call **`PDW3XFR - CLC Total Load Miles XF`** to calculate miles between all stops, then retrieve first-stop miles.
    - **Logic for `CLC Total Load Miles XF`:**
      1. Reads **"Load Detail - `OMFLCPP`"** for the Load ID in stop sequence.
      2. For each stop, retrieves **Miles to next stop**; when it is zero, looks the mileage up from **"Legal Run Mileage Hours - `PDLGCPP`"**.
      3. Accumulates total miles and returns **PAR.Total Load Miles** to the caller.
  - Update **"Load Header - `OMFJCPP`"**: set **Load Status = "L" (Locked)**, **Deadline Departure Date**, **Deadline Departure Time** and **Ship From Warehouse**.
  - Call **`PDADXFR - CRT Load/Order Chg Log XF`** with **Load Change Type = "LOCK"**, **Department Control Code = "Traffic Dept"**, the program name and `*USER`, writing a record to **"Load/Order Change Log - `PDLHCPP`"**.
```

This is the *shape* — depth, ordering, quoting, recursive expansion — not a content template. The real blocks, options, files and messages all come from the AD in front of you.

---

## 8. Verification gate (run before showing the document)

The first table is the `Synon_Program_Analysis` gate. For `Synon_Functional_Document` run the §6F gate below it instead. The shared checks are written out in both tables rather than cross-referenced, so neither list has to be read against the other.

### `Synon_Program_Analysis` gate

| Check | Fail action |
|-------|-------------|
| Every §6 heading present, verbatim, in order; none added or removed | Fix the structure before anything else |
| Level-1 title is `{FUNCTION} - {IMPLEMENTATION_NAME}` (design name alone when there is no implementation name), and §1 carries all four items including `**Implementation Name:**` | Restore the fixed title shape and the missing item |
| No `ia_*` tool name, SQL, MCP/server wording or iA repository table name anywhere in the document | Rewrite the sentence in domain terms — provenance goes in the chat reply, not the deliverable |
| Table column headers match §6 character for character, including the duplicated `Description` in §3 | Restore the exact headers |
| §2.1 and §2.4 name columns carry **no** programmatic field names | Replace with the user-facing label / DDS field name |
| Every DDS field (minus header/footer furniture) appears in §2.4 | Walk the DDS again, format by format |
| §2.5 blocks follow AD execution order, and every internal function call has a nested expansion | Re-trace the AD from the entry point |
| **Mode B only** — every statement is accounted for: the statements traced in §2.5 match the rows `ia_synon_action_diagram` returned, paged to the end | Page again from the last `offset`; a short final page is the only proof you reached the end |
| **Mode B only** — every `variable_usage=OUT` **and** `variable_usage=BOTH` field appears in §2.8 (or in §2.5 where it is a work field) | Add the missing field; an `OUT` or `BOTH` operand is a write the document is claiming does not happen. If the operand table returned nothing for this function, this check is inconclusive — derive the writes from `raw_text` and say so, rather than recording "no writes" |
| §2.5 contains no forbidden summary phrase, no function key, no repeat of §2.4 validations | Expand or relocate |
| No RPG opcode, indicator, generated subroutine/variable name or spec declaration anywhere in the document; every RPG-derived fact is one a reader needs to follow the AD | Restate it as the AD's rule, or delete it |
| Every message text in the document is quoted from source | Remove it or mark `Not Available` |
| §3 lists physical files only, no `F`-prefixed names | Resolve LFs to their PFs |
| §5.1/§5.2 present (even if empty), no `Y2*` rows, §5.2 descriptions are business-level | Rewrite the descriptions |
| §Revision Log ends with one blank row, and carries no history unless a Master Report supplied it | Blank the extracted rows and leave exactly one empty one |
| Every Master Report value preserved unchanged | Restore from the Master Report |
| No unsupported claim anywhere; unknowns are `Not Available` | Delete the claim |

---

### `Synon_Functional_Document` gate (§6F)

| Check | Fail action |
|-------|-------------|
| **The DocType generated is the one asked for (§0)** | Regenerate against the other structure. Never patch a §6 document into a §6F one — the sections do not correspond |
| All seven §6F sections present as `## N. Title`, verbatim and in order, plus the header block and the `## Documentation Quality` footer; none added, none renamed | Fix the structure before anything else |
| Level-1 title is `{FUNCTION} - {IMPLEMENTATION_NAME}` (design name alone when there is no implementation name) | Restore the fixed title shape |
| No `ia_*` tool name, SQL, MCP/server wording or iA repository table name anywhere in the document | Rewrite the sentence in domain terms — provenance goes in the chat reply, not the deliverable |
| §1 purpose carries no 2E vocabulary and no file, field or program names | Rewrite as user-facing outcomes; the names belong in §3 and §5 |
| Every `BR-nnn` cites a named AD block, and none rests on a forbidden summary phrase | Re-trace the block and state the rule, or delete it |
| BR numbering runs continuously from BR-001 across all four groups | Renumber |
| §3 lists physical files only — no logical files, no `F`-prefixed names | Resolve every LF to its PF |
| §4 carries all three parts, and the Business Process Flow Tree is present in a `text` fence with no Mermaid anywhere | Add the missing part; convert any diagram to an ASCII tree |
| Every Detailed Steps entry has both lines, each at least two sentences, and there is one entry per arrow-flow step | Expand the thin line with the data it touches, its governing condition, and the consequence of failure — re-read the AD block rather than padding |
| §5 has both sub-sections (even when empty), no `Y2*` rows, and purposes stated in business terms | Rewrite the purposes |
| Every message text in §6 is quoted from source, not paraphrased | Quote it, or mark the row `Not Available` |
| §7 carries all four metric rows. For an inline-compiled function type there is no generated program, so Size and Complexity are `Not Available` with the reason in the What This Means cell | Restore the row with `Not Available` — never drop a metric row, and never substitute the caller's line count |
| **No excluded content included** — no screen field mapping table, no parameter type/length table, no line-by-line execution trace, no key or option inventory, no RPG mechanics | Delete it; the §6F exclusion list is exhaustive |
| **Mode B only** — the AD was paged to the end, and internal functions were expanded recursively, *before* the rules were written | Page again from the last `offset`; a rule list built on a partial read is missing rules it cannot know about |
| **Mode B only** — every `variable_usage=OUT` **and** `variable_usage=BOTH` field is accounted for by a Data Rule in §2 | Add the rule; an `OUT` or `BOTH` operand is a write the document is claiming does not happen. If the operand table returned nothing for this function, this check is inconclusive — derive the writes from `raw_text` and say so |
| Every Master Report value preserved unchanged | Restore from the Master Report |
| No unsupported claim anywhere; unknowns are `Not Available` | Delete the claim |

---

## 9. Traps

| Trap | Why it bites |
|------|--------------|
| Answering a functional request with the §6 technical document | The likeliest failure mode of this reference and the hardest to spot: the document is complete, accurate and the wrong deliverable. §0 exists for this one trap |
| Producing §6 with its technical sections deleted and calling it functional | A trimmed technical document is not a functional one. It still opens on interface detail, and it still lacks the BR-xxx rule list and the process flow the audience came for. §6F |
| Documenting the generated RPG instead of the AD | Produces a spec of 2E's code generator, not of the business logic. The AD is the spine |
| Carrying RPG mechanics across — `CHAIN`/`SETLL` calls, indicators, generated subroutine names | Noise to every audience of this document, and it describes the generator's choices rather than the design's intent. §2 rule 10 |
| Summarising a deep conditional block | The reader loses the exact rule they came for. §2.5 is judged on depth |
| Stopping at the first internal function call | Nested functions carry most of the validation logic in 2E designs |
| Reading only part of a long AD | Silently drops branches; always paginate to the end |
| Taking screen fields from the RPG | The RPG carries programmatic names; the DDS carries the labels §2.4 requires |
| Listing logical files in §3 | The section is physical-file only; resolve every LF to its PF |
| Extracting the source's own revision comments into §Revision Log | Explicitly forbidden — that table carries only Master Report rows, and always one blank row for the reader |
| Leaving a tool name, a parameter name or a table name in the deliverable | Reads as a tool transcript rather than analysis, and dates the document to one server build. Ground rule 9 |
| Putting the 2E text, a paraphrase or a library in the level-1 title | The title is name + implementation name only; a title that varies per document breaks comparison across the set |
| Renaming or reordering a section to read better | Downstream tooling and reviewers key on the exact structure |
| Filling a gap with a plausible value | `Not Available` is a correct answer; a guess is a defect |

---

## 10. Save and export

1. Save the Markdown under `docs/synon-specs/{FUNCTION}/`, one canonical copy per DocType:

   | DocType | File |
   |---------|------|
   | `Synon_Program_Analysis` | `{FUNCTION}_Program_Analysis.md` |
   | `Synon_Functional_Document` | `{FUNCTION}_Functional_Document.md` |

   The two coexist. Generating one never touches the other, and neither filename carries a version suffix.

2. On request, convert with the bundled scripts (never ad-hoc conversion code) — `{DOCUMENT}` is the filename from step 1:

```bash
python .claude/skills/ia/scripts/convert_md_to_docx.py docs/synon-specs/{FUNCTION}/{DOCUMENT}.md
python .claude/skills/ia/scripts/convert_md_to_pdf.py  docs/synon-specs/{FUNCTION}/{DOCUMENT}.md
```

3. Markdown is the source of truth — regenerate the `.docx`/`.pdf` after any edit rather than editing them directly. Tables must stay out of code fences so they survive the Word conversion.

---

## 11. Tools these DocTypes use

Everything referenced above, in call order. The four Synon-specific tools are the spine; the rest are the standard iA tools these documents borrow for their header and relationship sections.

**Both DocTypes call the same tools.** `Synon_Functional_Document` is a different rendering of the same analysis, not a cheaper one — the AD still has to be read to the end and internal functions still have to be expanded recursively, because a rule list built on a partial trace is silently short. The only reads it can skip are the ones that feed sections it does not have: `ia_dds_source` is still needed for the menu path but no longer for a field-by-field §2.4 walk, and `ia_file_fields` narrows to the fields the §2 rules turn on.

| Tool | Called for | Feeds |
|------|-----------|-------|
| `ia_synon_functions` | Step 2 gate, and again for every callee during recursive expansion. Resolves a 2E design or implementation name (mixed case, `%` wildcards) to `pgm_surrogate_id` | §1 Program Type (`function_type`), the key every other Synon tool requires, and `ad_member_full` / `ad_member_concise` for the source read |
| `ia_synon_action_diagram` | Step 3.2 — every AD statement in execution order with the nesting tree (`line_sequence`, `depth`, `parent_statement`) | **§2.5** (the spine), plus §2.3, §2.6, §2.7, §2.8 |
| `ia_synon_variable_ops` | Step 3.3 — operands per statement, with 2E context, direction and sequence. Sparse in some repositories — empty ≠ no writes | §2.1 via `variable_context=PAR`, §2.8 via `variable_usage=OUT` **and** `BOTH`, every assignment in §2.5 |
| `ia_synon_source` | Step 3.4 — the verbatim AD member named by step 1 | Exact message text, literals and screen labels quoted anywhere in the document |
| `ia_rpg_source` | Step 3.5 — the generated RPG | Real file access, called program names, generated subroutine names, field lengths. Supporting only — never the spine (§9, trap 1) |
| `ia_member_lookup` | Step 2 — member type, source file and library; the wrong-DocType gate | The routing decision, and the DSPF member name for the DDS read |
| `ia_object_lookup` | Step 2 / Step 4 — type, library, attribute and text for one object | §5.1 / §5.2 enrichment |
| `ia_repo_config` | Step 2 — repository build date | The snapshot date under the branding line (§2, rule 7) |
| `ia_code_complexity` | Step 3 — member line counts, to prove a source read reached the end | Read-completeness check |
| `ia_program_spec_bundle` | Step 4 — one-call structural inventory | §2 AS-IS summary, §3, §5 |
| `ia_program_files` | Step 4 — files accessed, with usage mode | §3 Usage (I/O/U), §2.8 |
| `ia_object_context_matrix` | Step 4 — inbound and outbound context in one call | §3, §5.1, §5.2 |
| `ia_call_hierarchy` | Step 4, **both** directions | Menu Path (`CALLERS`), §5.1, §5.2 |
| `ia_file_fields` | Step 4 — field metadata for a file | §2.4 File Field Name, §3 |
| `ia_file_dependencies` | Step 4 — resolve every logical file to the physical file it is built over | §3, which is physical-file only |
| `ia_cl_jobs` | Step 4 — CL programs with an `SBMJOB` naming this function | Scheduled Jobs header |
| `ia_dds_source` | Step 3.6 — display-file DDS, and the menu source members behind the Menu Path | **§2.4** Screen Field Mapping (the absolute source), Menu Path option numbers and text |
| `scripts/convert_md_to_docx.py` / `convert_md_to_pdf.py` | §10 — export on request | `.docx` / `.pdf` deliverables |

Mode A (attached `_AD` / `_RPG` / `_DDS`) skips the source-reading tools — the files are the source — but Steps 2 and 4 still run, for callers, files, menu path and the snapshot date.
