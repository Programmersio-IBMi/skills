# Test Case Generation Reference

Use this guide when the Step 1.5 DocType is **`Test_Case_Document`** — the user asked for "test cases", "test scripts", "UAT scripts", or a "test case document" for an IBM i program. The deliverable is a manual QA/UAT execution document built on [`templates/template-testcases.md`](templates/template-testcases.md).

The workflow **reuses program-documentation.md Steps 1.5–3 and 7.5–9 unchanged** (existence check, TodoWrite kickoff, `ia_program_spec_bundle`, silent `ia_file_fields` lookup, source + BR-xxx extraction, filename gate, save, export). This reference replaces Steps 4–7 (assembly + verification) for this DocType only. No new `ia_*` tools are involved.

**Audience calibration:** the executor is a QA/UAT tester at a 5250 session — not a developer. Steps say exactly what to type and press; expected results say exactly what to observe. No RPG jargon in steps or expected results (subroutine names belong in "Traces to", not in the instructions).

---

## 1. Inputs (already gathered by Steps 2–3)

| Input | Source | Feeds |
|-------|--------|-------|
| Program metadata, files, params, subroutines | `ia_program_spec_bundle` | §1 Introduction, §2 Environment, category selection |
| File + field descriptions | `ia_program_files` + silent `ia_file_fields` lookup | §2 required objects, §3 data values, every field mention |
| BR-xxx list with line anchors | Step 3 source extraction | §4 functional cases, §5 traceability matrix |
| Handled function keys + EXFMT flow | Step 3 source read (CFnn/CA keywords, F-key handling logic) | §4.1 navigation cases |
| Validation logic, message text, file opcodes (CHAIN/WRITE/UPDATE/DELETE) | Step 3 source read | §4.2–4.5 cases, expected results |

If BR extraction produced zero rules for a program with executable logic, stop and re-run Step 3 — a test case document without BR-driven cases is not deliverable.

---

## 2. Derivation rules — source evidence → test cases

Generate cases **only from source evidence**. A category with no evidence is omitted from the document entirely (no empty headings, no padding).

| Source evidence | Test cases generated | Category |
|-----------------|----------------------|----------|
| BR-xxx [VALIDATION] | 1 positive (value accepted) + 1 negative (value rejected, error observed) | Field Validation or Business Rule / Functional |
| BR-xxx [CALCULATION] | 1 case with concrete synthetic inputs → expected computed value (compute it yourself from the rule; show the arithmetic in the expected result) | Business Rule / Functional |
| BR-xxx [STATUS / FLAG, CLASSIFICATION, EXCEPTION, ACCUMULATION] | 1 case per distinct behavior branch the rule drives | Business Rule / Functional |
| Each handled F-key (CFnn/CA + handling logic) | 1 case: press the key, observe the documented behavior | Screen Navigation & Function Keys |
| EXFMT screen flow | 1 entry case (call program, initial screen correct) + 1 exit case (leave program cleanly) | Screen Navigation & Function Keys |
| Output/Update file | create path + update path + not-found path (from CHAIN/%FOUND handling); duplicate-key case **only** if source shows duplicate handling | File I/O & Data |
| Validated field's type/length/decimals (`ia_file_fields`) | boundary cases: maximum value/length, zero, blank — only for fields the program actually validates | Boundary |
| Entry parameters (PARAMS / `ia_procedure_params`) | 1 valid-call case + 1 invalid/missing-parameter case | Parameter |

**Anti-explosion rule:** one test case per validation *rule*, not per field instance. If the same rule applies to several fields (e.g. "required field" on five fields), write **one** case listing the affected fields in the test data row. Target a focused document — quality of evidence over case count.

**Coverage floors (hard — generation errors if missed):**
- every BR-xxx has ≥ 1 test case
- every handled F-key has 1 test case
- every Output/Update file has ≥ 1 test case

---

## 3. Synthetic test data construction

All data values are synthetic, built from `ia_file_fields` metadata. Never copy live repository data into the deliverable.

| Field metadata | Valid value | Invalid / boundary values |
|----------------|-------------|---------------------------|
| Packed/zoned `7,2` | mid-range, e.g. `1250.00` | max `99999.99`, zero, negative (if source rejects) |
| Char `10` code field | a plausible 10-char (or shorter) code | blank, lowercase (if source uppercases/rejects), value absent from the file (not-found path) |
| Date field | a valid date in the program's format | invalid date (e.g. month 13) **only if source validates dates** |
| Key field | value seeded in Data Set A (exists) | value reserved in Data Set B (must not exist) |

Rules:
- Use the field's **FIELD_TEXT description** to make values plausible (a `CUSTNO (Customer Number)` gets a numeric-looking key, not `XXXXX`).
- Every value used in a test case step must appear in a §3 data set (existing-record sets vs must-not-exist sets), so the tester can seed before executing.
- Flag each data set with *"replace with environment-specific values where noted"* — key values are suggestions, the structure is the contract.
- Invalid values must violate **exactly one** rule at a time — a value that is both too long and non-numeric proves nothing.

---

## 4. Assembly rules (template-testcases.md)

- **TC ID:** `TC-{PGM}-{NNN}`, three digits, sequential across the **whole document** starting at 001 — not per category.
- **Category order:** Screen Navigation & Function Keys → Field Validation → Business Rule / Functional → File I/O & Data → Boundary → Parameter. Omit empty categories.
- **Priority is derived, never invented:** High = BR validations + file-update integrity; Medium = navigation / boundary; Low = display-only behavior.
- **Expected results are source-evidence-only.** Use the actual message text found in source constants or message-file references. If the exact text is not in source, write *"error indicated — verify exact message text in environment"*. Never invent message text, screen layouts, or behaviors.
- **Steps are executable as written:** start from the general preconditions, name the exact field labels and keys (`press F3`, not "exit"). A tester who has never seen the program must be able to run them.
- **Traces to** carries the BR id with its line anchor — `BR-002 (line 145, VALIDCUST)` — or a screen-flow/source anchor for navigation cases.
- **Field-format + library rules apply:** every field mention is `FIELDNAME (Field Description)`, every file mention is `FILE (LIBRARY)` — same as all other DocTypes.
- **Execution strips, summary totals (Passed/Failed/Blocked), and sign-off rows ship blank** — they belong to the tester.
- **Traceability matrix (§5)** lists every BR-xxx with the TC ids covering it; coverage must read 100% (an uncovered BR is a generation error, fix before delivery).

---

## 5. Verification (Step 7 for this DocType)

Two gates, in order — same pattern as the flowchart deliverable.

**Gate 1 — lint script (run first):**

```bash
python scripts/validate_testcases.py docs/program-specs/{PGM}/{PGM}_Test_Case_Document.md
```

Exit 0 = pass. Exit 1 = findings printed one per line; fix every finding and re-run until clean. Never deliver on a failing lint.

**Gate 2 — content checks (manual, all must pass):**

| Check | Rule | Action if failed |
|-------|------|------------------|
| BR coverage floor | Every BR-xxx from Step 3 has ≥1 TC; matrix shows 100% | **ERROR** — add missing cases |
| F-key coverage floor | Every handled F-key has a TC | **ERROR** — add missing cases |
| File coverage floor | Every Output/Update file has ≥1 TC | **ERROR** — add missing cases |
| Expected-result evidence | Message text matches source, or carries the "verify exact message text" flag | **ERROR** — fix or flag |
| Data set completeness | Every value in a TC's test data row appears in a §3 data set | **ERROR** — add to data set |
| Category honesty | No empty category headings; no padded/invented cases | **ERROR** — remove |
| Tester readability | Steps contain no RPG jargon; each step is one concrete action | **WARNING** — rewrite |

Then continue with program-documentation.md Step 7.5 (filename gate → `{PGM}_Test_Case_Document.md`), Step 8 (save + branding + quality report), and Step 9 (DOCX/PDF export on request).

---

## 6. Common traps

| Trap | Symptom | Fix |
|------|---------|-----|
| Invented message text | Expected result quotes an error message that is not in source | Quote source text only, or use the "verify exact message text in environment" flag |
| Case explosion | 5 identical required-field cases for 5 fields | One case per rule, affected fields listed in test data |
| Padded categories | "Parameter" section for a program with no entry parameters | Omit the category entirely |
| Orphan test data | A step types a value that no §3 data set defines | Every step value traces to a data set |
| Uncovered BR | Matrix shows a BR with no TC | Coverage floor is hard — add the case before delivery |
| Per-category numbering | TC-PGM-001 appears in two categories | Numbering is document-global and sequential |
| Developer-speak in steps | "Trigger the VALIDCUST subroutine" | Steps describe screen actions; subroutine names live in "Traces to" |
| Pre-filled execution strip | Status column contains "Pass" on delivery | Execution strips ship blank |
