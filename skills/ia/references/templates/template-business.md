# Program Documentation — <PROGRAM>

**Author:** iA by programmers.io  
**Date:** <YYYY-MM-DD>  
**Library:** <LIBRARY> | **Source:** <SRCPF>  
**Audience:** Business Analysts / Non-Technical

---

## 1. What This Program Does

<Clear, non-technical description of program purpose and business function>

**Program Type:**
- ☐ Interactive (user screens)
- ☐ Batch (scheduled/background)
- ☐ Utility (support function)

**Key Capabilities:**
- <Capability 1>
- <Capability 2>
- <Capability 3>

---

## 2. Business Rules

This program enforces the following business rules:

### Validation Rules
- **BR-001** — <rule in plain language>
- **BR-002** — <rule in plain language>

### Calculation Rules
- **BR-003** — <rule in plain language>
- **BR-004** — <rule in plain language>

### Workflow Rules
- **BR-005** — <rule in plain language>
- **BR-006** — <rule in plain language>

### Data Rules
- **BR-007** — <rule in plain language>
- **BR-008** — <rule in plain language>

---

## 3. Data Used

### Files and Tables

| File Name | Purpose | Access Type |
|-----------|---------|-------------|
| <FILE>    | <Business purpose> | Read/Write/Update |
| <FILE>    | <Business purpose> | Read only |

### Key Data Elements

| Field | File | Purpose |
|-------|------|---------|
| <FIELD> | <FILE> | <Business meaning> |
| <FIELD> | <FILE> | <Business meaning> |

---

## 4. Process Flow

```
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

1. **<Step Name>**
   - What happens: <description>
   - Business impact: <impact>

2. **<Step Name>**
   - What happens: <description>
   - Business impact: <impact>

3. **<Step Name>**
   - What happens: <description>
   - Business impact: <impact>

---

### Business Process Flow Tree *(mandatory)*

Render one ASCII process flow tree summarising the business steps and decision points in plain language (no RPG opcodes, no subroutine names). Use a fenced ```` ```text ```` block and box-drawing characters (`├──`, `└──`, `│`). Example shape:

```text
Customer Order Flow
├── Receive new order
│   ├── Customer on credit hold? -> reject + send notice
│   └── Customer in good standing -> proceed
├── Check inventory for each line item
│   ├── Available -> reserve stock
│   └── Backorder -> flag and continue
├── Calculate total (items + tax + shipping)
└── Confirm order
    ├── Auto-confirm if total < $500
    └── Manager approval if total >= $500
```

One tree minimum per program. Branches and leaves use plain business language a non-technical reader can follow.

## 5. Related Programs

### Programs This Calls
- **<PROGRAM>** — <Business purpose>
- **<PROGRAM>** — <Business purpose>

### Programs That Call This
- **<PROGRAM>** — <Business context>
- **<PROGRAM>** — <Business context>

---

## 6. Error Conditions

| Error | What It Means | What To Do |
|-------|---------------|------------|
| <Error message> | <Plain language explanation> | <Action to take> |
| <Error message> | <Plain language explanation> | <Action to take> |

---

## 7. Program Statistics

| Metric | Value | What This Means |
|--------|-------|-----------------|
| Size | <TOTAL_LINES> lines | <Small/Medium/Large> program |
| Complexity | <Low/Medium/High> | <Easy/Moderate/Difficult> to modify |
| Files Used | <COUNT> | Touches <COUNT> data sources |
| Dependencies | <COUNT> programs | Connected to <COUNT> other programs |

---

## Documentation Quality

| Aspect | Status |
|--------|--------|
| Completeness | <X>% complete |
| Business Rules | <N> rules documented |
| Last Updated | <YYYY-MM-DD> |

---

*Analysis powered by iA from [programmers.io](https://programmers.io/ia/)*
