# Program Analysis Document — <PROGRAM>

**Author:** iA by programmers.io
**Date:** <YYYY-MM-DD>
**Library version documented:** <LIBRARY> | **Source file:** <SRCPF> | **Member type:** <MEMBER_TYPE>
**Audience:** Senior developers, architects, and support teams

> **Tone:** Business-friendly language with technical accuracy. **DO NOT** describe the code line-by-line. **DO NOT** assume any pattern that is not explicitly present in the source.

---

## 1. Program Overview

- **Program name:** <PROGRAM> (and any alternate name found in the source header)
- **Primary purpose:** <one to two sentences describing what the program does>
- **Business problem / functionality addressed:** <bulleted list of business outcomes the program enables>
- **Execution type:** <Batch / Interactive / Online> — justify briefly using DSPF count, F-spec usage, or scheduling context
- **Key outputs and how they are consumed:**
  - <output file / report / data area> — <how it is used downstream>

---

## 2. Technical Summary

- **Program ID:** <PROGRAM>
- **RPG type:** <RPG III / RPG IV (fixed-format) / RPG IV (free-form) / SQLRPGLE / CLLE>
- **Entry parameters and business meaning** *(only if present)*:

| Seq | Name | Type | Length | PR/PI | Keywords | Business Meaning |
|-----|------|------|--------|-------|----------|------------------|
| ... | ...  | ...  | ...    | ...   | ...      | ...              |

> If `ia_procedure_params` returns zero rows AND no `dcl-pr`/`dcl-pi`/`*ENTRY PLIST` exists in source, write: *"No entry parameters declared."*

- **Notable revisions / assumptions / commented-out logic:**
  - <revision date / tag — what changed>
  - <commented-out file or routine — what was disabled and likely why>
  - <any explicit assumption stated in source comments>

---

## 3. Files and Data Sources

For every file the program uses, include:

| File | Library | Usage Type | Business Purpose |
|------|---------|------------|------------------|
| ...  | <actual library, e.g. PRDLIB> | Input / Output / Update / Reference | <what the file represents and how it serves this program> |

> **Library column:** Always use the actual library name resolved from iA (e.g., `PRDLIB`). Never leave a placeholder in the document.

### Data Areas Used *(only if any)*

| Name | Library | Size | Operations (IN / OUT) | Purpose |
|------|---------|------|------------------------|---------|
| ...  | ...     | ...  | ...                    | ...     |

---

## 4. Main Processing Logic

Describe the program's execution flow **in the same sequence in which it actually runs**, from start to end.

- Walk through the logic as it progresses, including **all rules, conditions, branches, loops, and calculations** as they are encountered.
- For every read / write / update / chain on a file, mention:
  - Which **key fields** are used to position or look up
  - Which **fields are derived** from the read
  - Which **fields are written or updated** on output
- When processing routes through a subroutine or procedure, mention its **name** and a one-line description of what happens inside it (full detail goes in Section 5).
- Describe how **control flows** between major logic blocks.
- Identify distinct processing paths only if they **naturally occur** in program flow.
- **Do not pre-classify** logic by category (dates, control breaks, etc.) — narrate in execution order.

> Use clear paragraph or numbered-step prose. Add line-number anchors where helpful, e.g. *(line 245)*.

---

### Processing Flow Tree *(mandatory)*

Render one ASCII process flow tree summarising the major decision branches, EXSR/CALLP edges, and error paths through the program. Use a fenced ```` ```text ```` block and box-drawing characters (`├──`, `└──`, `│`) — never Mermaid. Example shape:

```text
Main Flow
├── Validate input parameters
│   ├── Invalid -> EXSR ERRORHANDLER -> return
│   └── Valid -> proceed
├── Read CUSTMAST (PRDLIB) keyed on CUSTNO (Customer Number)
│   ├── Not found -> log + EXSR NOTFOUND -> return
│   └── Found -> proceed
├── CALCBALANCE (line 245) -> compute new BALANCE
└── Write to TRANHIST (PRDLIB) -> commit
```

One tree minimum per program. More are fine for branchy logic. Each leaf shows `<condition or step> -> <result>` or `<step name>` with optional `*(line NNN)*` anchor.

## 5. Subroutine / Procedure Analysis

For each significant subroutine or procedure (use the **complete** SUBROUTINES list — do not omit any non-trivial routine):

### <SUBROUTINE_NAME>
- **Purpose:** <one sentence>
- **High-level behavior:** <2-4 sentences describing what it does, files it touches, branches it takes>
- **Key decisions / calculations:** <if/select conditions, formulas, accumulations, exits>

*(Repeat for each subroutine / procedure.)*

### Call Hierarchy Diagram

<!-- Include if CALL_PGM_COUNT > 0 OR CALLEES section has rows. Use actual library in the parent label. -->
<!-- Use a text-based ASCII tree in a fenced `text` code block — never Mermaid (PNG renders unreadably in Word/PDF when there are many callees). -->

```text
<PROGRAM> (<LIBRARY>)
│
├── [CALLP] CALLEE1
├── [CALLP] CALLEE2          ×3
├── [CALL]  CALLEE3
└── [CALL]  CALLEE4
```

**Legend:**
- **CALLP** — Bound procedure call (service-program / prototype)
- **CALL** — Traditional program call (dynamic)
- **×N** — Number of times called (omit if 1)

---

## 6. Business Rules and Calculations

Summarize the important rules discovered in the source. Use the **BR-xxx** identifier format with a category tag and source anchor.

- **BR-001** [VALIDATION] — <rule statement> *(line <NNN>, subroutine: <NAME>)*
- **BR-002** [CALCULATION] — <rule statement> *(line <NNN>, subroutine: <NAME>)*
- **BR-003** [CLASSIFICATION] — <rule statement> *(line <NNN>, subroutine: <NAME>)*
- **BR-004** [STATUS / FLAG] — <rule statement> *(line <NNN>, subroutine: <NAME>)*
- **BR-005** [EXCEPTION] — <rule statement> *(line <NNN>, subroutine: <NAME>)*

Group rules by what they are doing in the business, e.g.:
- **Accumulations / totals / rollups**
- **Classification or categorization**
- **Status, flag, or code-driven behavior**
- **Special conditions or exception handling**

---

## 7. Output File Behavior

For each file the program writes or updates:

- **<OUTPUT_FILE>** *(library: <LIBRARY>)*
  - **Conditions for create vs. update:** <what triggers each>
  - **Field population / accumulation logic:** <how each output field is built>
  - **Relationship to input data:** <which input fields drive which output fields>

---

## 8. Glossary

Define every important keyword, abbreviation, and field used in the program in plain language.

| Term | Meaning |
|------|---------|
| <FIELD/CONST/ABBREVIATION> | <plain-language meaning, including unit / domain when relevant> |

---

## 9. Key Observations *(Optional)*

- **Complexity or risk areas:** <high IF/DO counts, GOTOs, deep nesting, large data structures>
- **Dependency on reference data or external programs:** <DAYMINUS, lookup files, data areas>
- **Modernization / refactoring opportunities:** <free-format conversion, SQL refactor, embedded business logic to extract>

---

## Technical Statistics

| Metric | Value |
|--------|-------|
| Total Lines | <TOTAL_LINES> |
| Executable Lines | <EXEC_LINES> |
| IF Count | <IF_COUNT> |
| DO Count | <DO_COUNT> |
| SELECT Count | <SEL_COUNT> |
| WHEN Count | <WHEN_COUNT> |
| SQL Statements | <SQL_COUNT> |
| Subroutines | <SBR_COUNT> |
| Procedures | <PROC_COUNT> |
| GOTO Count | <GOTO_COUNT> |
| Files Referenced | <FILE_COUNT> |
| Display Files | <DSPF_COUNT> |
| Calls Out | <CALL_PGM_COUNT> |
| Called By | <CALLED_BY_COUNT> |

**Complexity Assessment:** <Low / Medium / High / Critical>

---

## Documentation Quality Report

| Metric | Score | Status |
|--------|-------|--------|
| Completeness | <X>% | <✅/⚠️> <N>/9 sections populated |
| Verification Rules | <X>% | <✅/❌> <N>/7 rules passed |
| Business Rules Coverage | <X>% | <✅/⚠️> <N> BRs for <M> subroutines/clusters |
| Source Traceability | <✅/⚠️> | Line numbers included: <YES/NO> |
| Library Resolution | <✅/❌> | All file/object libraries shown as actual values (no placeholders) |
| Freshness | Current | ✅ Generated <YYYY-MM-DD> |

**Validation Warnings (if any):**
- <Warning 1>

**Recommendations:**
- <Recommendation 1>

---

*Analysis powered by iA from [programmers.io](https://programmers.io/ia/)*
