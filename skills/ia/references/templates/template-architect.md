# Architecture Specification — <PROGRAM>

**Author:** iA by programmers.io  
**Date:** <YYYY-MM-DD>  
**Library:** <LIBRARY> | **Source:** <SRCPF> | **Type:** <MEMBER_TYPE>  
**Audience:** Architects / Technical Leadership

---

## 1. Program Overview

<High-level architectural purpose and role in the system>

**Classification:**
- **Type:** <Interactive/Batch/Service/Utility>
- **Layer:** <Presentation/Business Logic/Data Access/Integration>
- **Criticality:** <High/Medium/Low>

**Key Architectural Characteristics:**
- <Characteristic 1>
- <Characteristic 2>
- <Characteristic 3>

---

## 2. System Context

### Position in Architecture

```
[Upstream Systems/Programs]
         ↓
    [THIS PROGRAM]
         ↓
[Downstream Systems/Programs]
```

### Integration Points

| Direction | Object | Type | Purpose |
|-----------|--------|------|---------|
| Inbound   | <CALLER> | *PGM/*SRVPGM | <Purpose> |
| Outbound  | <CALLEE> | *PGM/*SRVPGM | <Purpose> |

---

## 3. Data Architecture

### Data Dependencies

| File | Type | Role | Coupling Level |
|------|------|------|----------------|
| <FILE> | PF/LF | <Master/Transaction/Reference> | <High/Medium/Low> |

### Data Flow

```
Input Sources → Processing → Output Destinations
```

**Key Data Transformations:**
- <Transformation 1>
- <Transformation 2>

---

## 4. Dependency Analysis

### Service Programs Used

| Service Program | Exported Procedures Used | Coupling Risk |
|-----------------|-------------------------|---------------|
| <SRVPGM> | <PROC1>, <PROC2> | <High/Medium/Low> |

### Binding Dependencies

| Object | Type | Purpose | Impact if Changed |
|--------|------|---------|-------------------|
| <OBJ> | *BNDDIR/*MODULE | <Purpose> | <Impact> |

---

## 5. Call Hierarchy

### Upstream Dependencies (Callers)

| Caller | Type | Call Pattern | Risk Level |
|--------|------|--------------|------------|
| <CALLER> | *PGM | Direct/Indirect | <High/Medium/Low> |

**Total Callers:** <COUNT>  
**Blast Radius:** <High/Medium/Low>

### Downstream Dependencies (Callees)

| Callee | Type | Purpose | Failure Impact |
|--------|------|---------|----------------|
| <CALLEE> | *PGM/*SRVPGM | <Purpose> | <Impact> |

**Total Callees:** <COUNT>  
**Dependency Depth:** <N> levels

### Call Hierarchy Diagram

<!-- Include if CALL_PGM_COUNT > 0; omit if no external calls -->
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

### Dependency / Integration Flow Tree *(mandatory)*

Render one ASCII process flow tree showing this program's place in the broader system: callers above, callees and integration points below, with file-sharing edges noted. Use a fenced ```` ```text ```` block and box-drawing characters (`├──`, `└──`, `│`). Example shape:

```text
ORDENTRY (PRDLIB)
├── Callers
│   ├── MENU01 (PRDLIB) -> interactive entry
│   └── BATCHQ (PRDLIB) -> scheduled batch
├── Callees
│   ├── CUSTLOOKUP (UTILIB) -> reads CUSTMAST (PRDLIB)
│   ├── PRICECALC (UTILIB) -> reads PRICELIST (PRDLIB)
│   └── ORDERWRITE (PRDLIB) -> writes ORDHIST (PRDLIB)
├── Service programs
│   └── DATELIB (UTILIB) -> date arithmetic procedures
└── External integrations
    └── *DTAARA ORDDTA (PRDLIB) -> control flags read at startup
```

One tree minimum per program. Leaves carry the actual library on every name.

## 6. Complexity & Maintainability

### Complexity Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Cyclomatic Complexity | <IF+DO+SEL+WHEN> | <50 | <✅/⚠️/❌> |
| Lines of Code | <TOTAL_LINES> | <1000 | <✅/⚠️/❌> |
| SQL Statements | <SQL_COUNT> | <20 | <✅/⚠️/❌> |
| GOTO Usage | <GOTO_COUNT> | 0 | <✅/⚠️/❌> |
| Procedure Count | <PROC_COUNT> | <10 | <✅/⚠️/❌> |

**Overall Assessment:** <Low/Medium/High/Critical> complexity

### Maintainability Concerns

- ⚠️ <Concern 1>
- ⚠️ <Concern 2>
- ✅ <Strength 1>
- ✅ <Strength 2>

---

## 7. Architectural Patterns

### Design Patterns Identified

- **<Pattern Name>** — <Usage description>
- **<Pattern Name>** — <Usage description>

### Anti-Patterns Detected

- ⚠️ **<Anti-pattern>** — <Description and impact>
- ⚠️ **<Anti-pattern>** — <Description and impact>

---

## 8. Change Impact Assessment

### Modification Risk

| Aspect | Risk Level | Reason |
|--------|------------|--------|
| Code Changes | <High/Medium/Low> | <Reason> |
| Interface Changes | <High/Medium/Low> | <Reason> |
| Data Changes | <High/Medium/Low> | <Reason> |
| Deployment | <High/Medium/Low> | <Reason> |

### Blast Radius

- **Direct Impact:** <N> programs
- **Indirect Impact:** <N> programs (via service programs)
- **Data Impact:** <N> files
- **User Impact:** <High/Medium/Low/None>

---

## 9. Modernization Readiness

### Current State

| Aspect | Status | Notes |
|--------|--------|-------|
| Code Format | <Free/Fixed/Mixed> | <% free-format> |
| SQL Usage | <Embedded/Native/None> | <SQL_COUNT> statements |
| Modularization | <High/Medium/Low> | <PROC_COUNT> procedures |
| Error Handling | <Structured/Legacy> | <Assessment> |

### Modernization Recommendations

1. **<Recommendation 1>**
   - Priority: <High/Medium/Low>
   - Effort: <High/Medium/Low>
   - Benefit: <Description>

2. **<Recommendation 2>**
   - Priority: <High/Medium/Low>
   - Effort: <High/Medium/Low>
   - Benefit: <Description>

---

## 10. Technical Debt

### Identified Issues

| Issue | Severity | Effort to Fix | Business Impact |
|-------|----------|---------------|-----------------|
| <Issue> | <High/Medium/Low> | <High/Medium/Low> | <Impact> |

### Refactoring Opportunities

- <Opportunity 1>
- <Opportunity 2>

---

## Architecture Quality Report

| Metric | Score | Status |
|--------|-------|--------|
| Modularity | <X>/10 | <✅/⚠️/❌> |
| Coupling | <Low/Medium/High> | <✅/⚠️/❌> |
| Cohesion | <High/Medium/Low> | <✅/⚠️/❌> |
| Complexity | <Low/Medium/High> | <✅/⚠️/❌> |
| Maintainability | <X>/10 | <✅/⚠️/❌> |
| Documentation | <X>% | <✅/⚠️> |

**Overall Architecture Grade:** <A/B/C/D/F>

---

*Analysis powered by iA from [programmers.io](https://programmers.io/ia/)*
