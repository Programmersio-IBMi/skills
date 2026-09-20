# Functional Document
# **<FUNCTION> - <IMPLEMENTATION_NAME>**

**Author:** iA by programmers.io  
**Date:** <YYYY-MM-DD> (repository snapshot: <YYYY-MM-DD>)  
**Library:** <LIBRARY> | **Source:** <SRCPF>  
**Audience:** Business Analysts / Non-Technical

> Fill-in copy for the `Synon_Functional_Document` DocType. The authoritative rules are in
> [synon-documentation.md §6F](../synon-documentation.md#6f-functional-document-structure) — read them before filling this in.
> Seven sections, in this order, nothing added or renamed. Unknowns are `Not Available`, never a guess.
> Delete this block in the generated document.

---

## 1. What This Program Does

<Plain-language description of what this function does for the business. No 2E vocabulary — no "action diagram", "access path", "EXCINTFUN". No file, field or program names; those belong in sections 3 and 5.>

**Program Type:**
- ☐ Interactive (user screens)
- ☐ Batch (scheduled/background)
- ☐ Utility (support function)

**Key Capabilities:**
- <Something a user can accomplish>
- <Something a user can accomplish>
- <Something a user can accomplish>

**How users reach it:** <Menu path in user terms, or `Not Available`>

**When it runs:** <Batch or scheduled trigger, or `Not Available` for an interactive function>

---

## 2. Business Rules

This program enforces the following business rules. Numbering runs continuously from BR-001 across all four groups; omit a group the action diagram has nothing for.

### Validation Rules
- **BR-001** — <Condition that rejects input or blocks an action, and what happens when it fails. Cite the block it comes from in words — "on Option 6, Lock Load". Quote any message text exactly.>
- **BR-002** — <rule in plain language>

### Calculation Rules
- **BR-003** — <What is computed, from which inputs, under which conditions>
- **BR-004** — <rule in plain language>

### Workflow Rules
- **BR-005** — <Sequencing, status transition, approval, what may follow what>
- **BR-006** — <rule in plain language>

### Data Rules
- **BR-007** — <What is created, updated or deleted, and the condition that triggers it>
- **BR-008** — <rule in plain language>

---

## 3. Data Used

### Files and Tables

Physical files only — resolve every logical file to the physical file it is built over.

| File Name | Purpose | Access Type |
|-----------|---------|-------------|
| <Description - IMPLNAME> | <What this file holds for this function, in business terms> | Read/Write/Update |
| <Description - IMPLNAME> | <Business purpose> | Read only |

### Key Data Elements

Only the fields the section 2 rules turn on. Never a programmatic variable name.

| Field | File | Purpose |
|-------|------|---------|
| <Field label> | <File> | <Business meaning> |
| <Field label> | <File> | <Business meaning> |

---

## 4. Process Flow

```text
1. Program starts
   ↓
2. <Business step description>
   ↓
3. <Business step description>
   ↓
4. <Business step description>
   ↓
5. Program ends
```

**Detailed Steps:**

One entry per arrow-flow step, in the same order. **What happens** and **Business impact** each carry at least two sentences — a one-line answer is a defect.

1. **<Step Name>**
   - What happens: <at least two sentences: what the step does, the data it reads or writes, and the condition that governs it>
   - Business impact: <at least two sentences: why the step matters to the business, and what goes wrong for the user or the downstream process when it fails or is skipped>

2. **<Step Name>**
   - What happens: <at least two sentences: what the step does, the data it reads or writes, and the condition that governs it>
   - Business impact: <at least two sentences: why the step matters to the business, and what goes wrong for the user or the downstream process when it fails or is skipped>

3. **<Step Name>**
   - What happens: <at least two sentences: what the step does, the data it reads or writes, and the condition that governs it>
   - Business impact: <at least two sentences: why the step matters to the business, and what goes wrong for the user or the downstream process when it fails or is skipped>

### Business Process Flow Tree *(mandatory)*

One ASCII tree summarising the business steps and decision points in plain language. No 2E or RPG vocabulary, no Mermaid. Follow the action diagram's execution order at business granularity — one branch per user point or option, not one per statement. Example shape:

```text
Load Lock Flow
├── Operator selects a load
│   ├── No orders assigned -> reject with "No Orders Assigned"
│   └── Orders present -> continue
├── Check the load may be locked
│   ├── Load status not I / L / S -> reject
│   ├── Carrier code blank -> reject with "Carrier must be entered for load"
│   └── All checks pass -> proceed
├── Calculate total load miles across all stops
└── Lock the load
    ├── Set status to Locked, record deadline departure
    └── Write a change-log entry for the Traffic Dept
```

One tree minimum per function. Branches and leaves use plain business language a non-technical reader can follow.

---

## 5. Related Programs

Both sub-sections are always present, even when empty. Exclude `Y2`-prefixed 2E system objects.

### Programs This Calls
- **<NAME>** — <What this callee does *for this function*, in business terms>
- **<NAME>** — <Business purpose>

### Programs That Call This
- **<NAME>** — <Business context in which it calls this function>
- **<NAME>** — <Business context>

---

## 6. Error Conditions

Message text is quoted exactly as the action diagram carries it, with its message id where present.

| Error | What It Means | What To Do |
|-------|---------------|------------|
| <"Literal message text"> | <Plain-language explanation of the condition that triggered it> | <Corrective action a user or support analyst takes> |
| <"Literal message text"> | <Plain-language explanation> | <Action to take> |

---

## 7. Program Statistics

| Metric | Value | What This Means |
|--------|-------|-----------------|
| Size | <TOTAL_LINES> lines | <Small/Medium/Large> program |
| Complexity | <Low/Medium/High> | <Easy/Moderate/Difficult> to modify |
| Files Used | <COUNT> | Touches <COUNT> data sources |
| Dependencies | <COUNT> programs | Connected to <COUNT> other programs |

For the internal function types 2E compiles inline (`CRTOBJ`, `CHGOBJ`, `DLTOBJ`, `RTVOBJ`, `EXCINTFUN`, `PRTOBJ`) there is no standalone generated program, so Size and Complexity are `Not Available` — say so in the What This Means cell rather than dropping the row.

---

## Documentation Quality

| Aspect | Status |
|--------|--------|
| Completeness | <X>% complete |
| Business Rules | <N> rules documented |
| Last Updated | <YYYY-MM-DD> |

---

*Analysis powered by iA from [programmers.io](https://programmers.io/ia/)*
