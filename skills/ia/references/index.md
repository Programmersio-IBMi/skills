# iA Skill Reference Index

This index guides progressive loading of skill references. Load only what you need for each query type.

## Trigger-Based Loading

| Query Type | Core Load | Additional Load |
|------------|-----------|-----------------|
| **Simple lookup** ("what uses X?", "find object") | SKILL.md only | — |
| **Tool selection unclear** | + [quick-reference.md](quick-reference.md) | Decision tree + intent mapping |
| **Need full tool list** | + [tool-catalog.md](tool-catalog.md) | All 54 tools by category |
| **Complex analysis** (field impact, call chains) | + [query-flows.md](query-flows.md) | Optimal tool sequences |
| **Troubleshooting / edge cases** | + [playbook.md](playbook.md) | Analysis playbooks |
| **Program documentation** | + [program-documentation.md](program-documentation.md) | 8-step workflow |
| **Change impact** ("what breaks if I resize/drop X", "effort to add a parm") | + [change-impact-analysis.md](change-impact-analysis.md) | classify the change (C1–C15) → spine + class traps → silent-failure catalogue → risk verdict → `build_change_estimate.py` workbook |
| **Object context matrix** ("context matrix for X", "everything around X") | + [object-context-matrix.md](object-context-matrix.md) | one `ia_object_context_matrix` call → sectioned tables → download menu (`build_context_matrix.py`) |
| **Onboarding guide** ("onboard a new developer on menu X", "menu to program to file mapping") | + [onboarding-guide.md](onboarding-guide.md) | resolve the menu → spine (call hierarchy + complexity + one context matrix per program) → option numbers from the menu source members → sectioned guide → freshness + cross-check gate → downloads (`build_onboarding_guide.py`) |
| **Version comparison** ("compare the versions of X", "diff X across libraries") | + [version-comparison.md](version-comparison.md) | discover all versions → ask which to compare + output format(s) → `build_version_diff.py` → changed-only report + optional side-by-side Excel |
| **Member diff** ("which members differ between our libraries", repository-wide) | + [member-diff.md](member-diff.md) | `ia_variant_summary` → `ia_member_variants` (LOGIC shortlist) → `build_member_diff.py` workbook |
| **App map** ("app map of library/area", "3D map") | + [app-map.md](app-map.md) | JSON contract + build script |

## Reference Files

| File | Purpose | Load When |
|------|---------|-----------|
| [quick-reference.md](quick-reference.md) | Tool selection by user intent | Tool choice unclear |
| [tool-catalog.md](tool-catalog.md) | Full 54-tool inventory | Need specific tool details |
| [query-flows.md](query-flows.md) | Optimal tool chains | Complex multi-step analysis |
| [playbook.md](playbook.md) | Playbooks + chaining rules | Edge cases, troubleshooting |
| [program-documentation.md](program-documentation.md) | Spec generation workflow | "Document program X" |
| [change-impact-analysis.md](change-impact-analysis.md) | Planned-change impact + field lineage + costed estimate | "What breaks if I change X?", "how long will it take?" |
| [object-context-matrix.md](object-context-matrix.md) | Inbound + outbound context for any object, with downloads | "Object context matrix for X" |
| [onboarding-guide.md](onboarding-guide.md) | Menu-scoped onboarding document for a developer new to the application | "Onboard a new developer on CASEMNU" |
| [version-comparison.md](version-comparison.md) | Cross-version comparison report workflow | "Compare the versions of program X" |
| [member-diff.md](member-diff.md) | Repository-wide cross-library member comparison | "Which members differ between LIB2025 and LIB2026?" |
| [app-map.md](app-map.md) | 3D application map workflow | "App map of library/area X" |
| [templates/](templates/) | Audience templates | Spec generation |

## Quick Decision

```
User asks about iA / IBM i analysis?
│
├─ Single-tool answer obvious? → Use SKILL.md guidance, call tool
│
├─ Which tool to use? → Load quick-reference.md
│
├─ Multi-step analysis? → Load query-flows.md for optimal chain
│
├─ About to CHANGE something? → Load change-impact-analysis.md
│
└─ Document a program? → Load program-documentation.md
```
