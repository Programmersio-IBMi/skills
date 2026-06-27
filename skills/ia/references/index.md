# iA Skill Reference Index

This index guides progressive loading of skill references. Load only what you need for each query type.

## Trigger-Based Loading

| Query Type | Core Load | Additional Load |
|------------|-----------|-----------------|
| **Simple lookup** ("what uses X?", "find object") | SKILL.md only | — |
| **Tool selection unclear** | + [quick-reference.md](quick-reference.md) | Decision tree + intent mapping |
| **Need full tool list** | + [tool-catalog.md](tool-catalog.md) | All 51 tools by category |
| **Complex analysis** (field impact, call chains) | + [query-flows.md](query-flows.md) | Optimal tool sequences |
| **Troubleshooting / edge cases** | + [playbook.md](playbook.md) | Analysis playbooks |
| **Program documentation** | + [program-documentation.md](program-documentation.md) | 8-step workflow |
| **App map** ("app map of library/area", "3D map") | + [app-map.md](app-map.md) | JSON contract + build script |

## Reference Files

| File | Purpose | Load When |
|------|---------|-----------|
| [quick-reference.md](quick-reference.md) | Tool selection by user intent | Tool choice unclear |
| [tool-catalog.md](tool-catalog.md) | Full 51-tool inventory | Need specific tool details |
| [query-flows.md](query-flows.md) | Optimal tool chains | Complex multi-step analysis |
| [playbook.md](playbook.md) | Playbooks + chaining rules | Edge cases, troubleshooting |
| [program-documentation.md](program-documentation.md) | Spec generation workflow | "Document program X" |
| [app-map.md](app-map.md) | 3D application map workflow | "App map of library/area X" |
| [templates/](templates/) | 4 audience-specific templates | Spec generation |

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
└─ Document a program? → Load program-documentation.md
```
