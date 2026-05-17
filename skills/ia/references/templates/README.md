# Documentation Templates — Audience-Specific Variants

This directory contains specialized documentation templates for different audiences. Each template emphasizes the information most relevant to its target audience while maintaining consistency with iA verification rules.

---

## Available Templates

| Template | Audience | Focus | Sections | Use When |
|----------|----------|-------|----------|----------|
| [`template-developer.md`](template-developer.md) | Developers, Technical Team | Code structure, technical details | All 8 sections + Mermaid diagram + quality metrics | Standard technical documentation (DEFAULT) |
| [`template-business.md`](template-business.md) | Business Analysts, Non-Technical | Business rules, data, process flow | 7 sections (no error handling details) | Business-focused documentation |
| [`template-architect.md`](template-architect.md) | Architects, Technical Leadership | Architecture, dependencies, complexity | 10 sections + Mermaid diagram + architecture quality | Architecture reviews, modernization planning |
| [`template-operations.md`](template-operations.md) | Operations, Support Team | Runtime, monitoring, troubleshooting | 10 sections + operational readiness | Operations runbooks, support guides |

---

## Template Selection Logic

| User Says / Phase 0 Answer | Template Used |
|----------------------------|---------------|
| "document program X" (no preferences) | `template-developer.md` (DEFAULT) |
| "New developers / onboarding team" | `template-developer.md` |
| "Business analysts (non-technical)" | `template-business.md` |
| "Architects / auditors" | `template-architect.md` |
| "Support / operations team" | `template-operations.md` |
| Multiple audiences | `template-developer.md` (most comprehensive) |

---

## Template Comparison

### Section Coverage Matrix

| Section | Developer | Business | Architect | Operations |
|---------|-----------|----------|-----------|------------|
| Program Purpose | ✅ | ✅ | ✅ | ✅ |
| Parameters | ✅ | ❌ | ❌ | ❌ |
| File Usage | ✅ | ✅ (simplified) | ✅ (data architecture) | ✅ (operational view) |
| Business Rules | ✅ | ✅ | ❌ | ❌ |
| Call Hierarchy | ✅ | ✅ (simplified) | ✅ (dependency analysis) | ✅ (dependencies) |
| Mermaid Diagram | ✅ | ❌ | ✅ | ❌ |
| Processing Flow | ✅ | ✅ | ❌ | ❌ |
| Error Handling | ✅ | ✅ (user-facing) | ❌ | ✅ (troubleshooting) |
| Statistics | ✅ | ✅ (simplified) | ✅ (complexity metrics) | ✅ (runtime info) |
| Quality Metrics | ✅ | ✅ | ✅ | ✅ |
| Architecture Patterns | ❌ | ❌ | ✅ | ❌ |
| Modernization | ❌ | ❌ | ✅ | ❌ |
| Monitoring | ❌ | ❌ | ❌ | ✅ |
| Troubleshooting | ❌ | ❌ | ❌ | ✅ |

---

## Template Features

### Developer Template
**Best for:** Day-to-day development, code reviews, onboarding

**Key Features:**
- Complete technical detail (all 8 standard sections)
- Parameter signatures with keywords
- Full subroutine inventory with clustering
- Source line references in business rules
- Mermaid call hierarchy diagram (if CALL_PGM_COUNT > 0)
- Complexity assessment with thresholds
- Quality metrics footer

**Verification Rules:** All 7 rules enforced

---

### Business Template
**Best for:** Business analysis, requirements validation, user documentation

**Key Features:**
- Plain language descriptions (no technical jargon)
- Business rules in natural language
- Simplified data view (files as "tables")
- Visual process flow
- Error messages in user terms
- Simplified statistics

**Verification Rules:** 5 of 7 rules enforced (parameter and caller rules relaxed)

---

### Architect Template
**Best for:** Architecture reviews, modernization planning, technical debt assessment

**Key Features:**
- System context and integration points
- Dependency analysis with coupling assessment
- Mermaid call hierarchy diagram (if CALL_PGM_COUNT > 0)
- Complexity metrics with thresholds
- Design patterns and anti-patterns
- Change impact assessment
- Modernization readiness scoring
- Technical debt inventory
- Architecture quality grade

**Verification Rules:** All 7 rules enforced + architecture-specific validations

---

### Operations Template
**Best for:** Operations runbooks, support documentation, troubleshooting guides

**Key Features:**
- Runtime and scheduling information
- File locks and resource usage
- Common errors with resolutions
- Monitoring metrics and thresholds
- Troubleshooting decision trees
- Support escalation contacts
- Maintenance procedures
- Operational readiness checklist

**Verification Rules:** 6 of 7 rules enforced (business rule coverage relaxed)

---

## Adding a New Template

1. Copy the closest existing template
2. Adjust sections for target audience
3. Update this README with template details
4. Add to template selection logic in [program-documentation.md](../program-documentation.md)
5. Test with a sample program

---

*Template library maintained by iA team — [programmers.io](https://programmers.io/ia/)*
