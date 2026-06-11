# Test Case Document — <PROGRAM>

**Author:** iA by programmers.io
**Date:** <YYYY-MM-DD>
**Library version documented:** <LIBRARY> | **Source file:** <SRCPF> | **Member type:** <MEMBER_TYPE>
**Audience:** QA / UAT Testers

---

## 1. Introduction

**Program under test:** `<PROGRAM> (<LIBRARY>)`

<Two-to-three sentence purpose of the program, in plain language — what business function it performs and who uses it.>

**Scope of this document:** Manual execution test cases covering <list the categories that apply: screen navigation and function keys, field validation, business rules, file I/O, boundary values, entry parameters>. Test cases are derived from program source analysis by iA; every functional case traces to a documented business rule (BR-xxx) with its source line anchor.

**How to use this document:**
1. Complete the environment setup in Section 2 and seed the data in Section 3.
2. Execute test cases in Section 4 in order within each category.
3. Record the actual result, status (Pass / Fail / Blocked), tester, and date in each case's execution strip.
4. Total the results in Section 6 and obtain sign-off.

---

## 2. Test Environment & Prerequisites

| Requirement | Value |
|-------------|-------|
| Test library (program) | `<LIBRARY>` |
| Library list must include | <libraries, in order> |
| User authority | <required authority / user profile class> |
| Display device | 5250 session, 24x80 <or as required by DSPF> |

**Required objects:**

| Object | Library | Type | Role in test |
|--------|---------|------|--------------|
| <PROGRAM> | <LIBRARY> | *PGM | Program under test |
| <FILE> | <LIBRARY> | *FILE (<attribute>) | <Input / Output / Update / Display> |

<If the program uses data areas, add a row per *DTAARA with the state it must hold before testing.>

**General preconditions (apply to every test case):** <signed on to test environment, library list set, files seeded per Section 3, …>

---

## 3. Test Data Preparation

> **Note:** All data values below are synthetic, derived from the file field definitions. **Replace with environment-specific values where noted** — key values must not collide with records your environment already contains unless a test explicitly requires an existing record.

### Data Set A — <purpose, e.g. "Existing records (read / update paths)">

| File (Library) | Field | Value | Why this value |
|----------------|-------|-------|----------------|
| <FILE> (<LIB>) | <FIELDNAME> (<Field Description>) | <value> | <valid mid-range / boundary / matches BR-xxx condition> |

### Data Set B — <purpose, e.g. "Values that must NOT exist (create / not-found paths)">

| Field | Value | Why this value |
|-------|-------|----------------|
| <FIELDNAME> (<Field Description>) | <value> | <must be absent so the create / not-found path fires> |

<One data set per distinct precondition group. Keep sets minimal — only fields the test cases actually use.>

---

## 4. Test Cases

<Group test cases under the category headings below, in this order. Omit any category heading with no test cases — do not pad. TC numbering is sequential across the whole document (TC-<PGM>-001, -002, …), not per category.>

### 4.1 Screen Navigation & Function Keys

### TC-<PGM>-001 — <title: one line, action + expected outcome>

| Field | Value |
|---|---|
| Category | Screen Navigation & Function Keys |
| Priority | <High / Medium / Low> |
| Traces to | <BR-xxx (line NNN, SUBROUTINE) — or "Screen flow (line NNN)" for navigation cases> |
| Preconditions | <state beyond the general preconditions, or "General preconditions only"> |
| Test data | <exact values, or "None"> |

**Steps**
1. <Exact action: CALL <PROGRAM> from command line / type value in field / press key>
2. <Next action>

**Expected result**
<Exact observable outcome: screen displayed, message text, cursor position, record state. Message text must come from source — if the exact text is not in source, write "error indicated — verify exact message text in environment".>

| Actual result | Status | Tester | Date |
|---|---|---|---|
|  |  |  |  |

### 4.2 Field Validation

<TC blocks in the same format.>

### 4.3 Business Rule / Functional

<TC blocks in the same format. Every BR-xxx gets at least one positive and, for validations, one negative case.>

### 4.4 File I/O & Data

<TC blocks in the same format. Verify record create / update / not-found behavior — expected results name the file as FILE (LIBRARY) and the fields written, each as FIELDNAME (Field Description).>

### 4.5 Boundary

<TC blocks in the same format. Values at field limits: maximum length, maximum numeric value, zero, blank.>

### 4.6 Parameter

<TC blocks in the same format. Only if the program has entry parameters.>

---

## 5. Traceability Matrix

**Business rule → test case coverage:**

| Business Rule | Description | Covered by | Coverage |
|---------------|-------------|------------|----------|
| BR-001 | <rule summary (line NNN)> | TC-<PGM>-003, TC-<PGM>-004 | ✅ |
| BR-002 | <rule summary (line NNN)> | TC-<PGM>-005 | ✅ |

**Coverage:** <N> of <M> business rules covered (<X>%). <Every BR must show ✅ — an uncovered BR is a generation error, not an acceptable gap.>

**Test case → source traceability:** every test case's "Traces to" row carries the BR id or source anchor it verifies; navigation cases trace to the screen-flow source lines.

---

## 6. Execution Summary & Sign-off

### Execution Summary

| Category | Total | Passed | Failed | Blocked |
|----------|-------|--------|--------|---------|
| Screen Navigation & Function Keys | <N> |  |  |  |
| Field Validation | <N> |  |  |  |
| Business Rule / Functional | <N> |  |  |  |
| File I/O & Data | <N> |  |  |  |
| Boundary | <N> |  |  |  |
| Parameter | <N> |  |  |  |
| **Total** | **<N>** |  |  |  |

<Only rows for categories present in Section 4. Passed / Failed / Blocked stay blank for the tester.>

### Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Tested by |  |  |  |
| Reviewed by |  |  |  |
| Approved by |  |  |  |

---

## Documentation Quality Report

| Metric | Score | Status |
|--------|-------|--------|
| BR coverage | <X>% | ✅/⚠️ <N>/<M> business rules have ≥1 test case |
| F-key coverage | <X>% | ✅/⚠️ <N>/<M> handled function keys have a test case |
| Output/Update file coverage | <X>% | ✅/⚠️ <N>/<M> written files have ≥1 test case |
| Source traceability | ✅/⚠️ | Every TC traces to a BR or source anchor: YES/NO |
| Lint gate | ✅/❌ | `validate_testcases.py` exit code 0: YES/NO |
| Freshness | Current | ✅ Generated <YYYY-MM-DD> |

**Validation Warnings (if any):**
- <Warning text>

---

*Analysis powered by iA from [programmers.io](https://programmers.io/ia/)*
