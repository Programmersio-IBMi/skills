# Flowchart Generation

Use this when a user asks for a **visual flowchart** of an IBM i program ("flowchart for X", "diagram the logic of X", "visualize the flow"). The deliverable is **one self-contained HTML file** holding a **single top-to-bottom Mermaid diagram** of the whole program, plus a subroutine index and file list.

> **One diagram, HTML only.** Mermaid renders live in the browser, so it stays out of the text-based Word/PDF spec pipeline (which uses ASCII trees — see [program-documentation.md](program-documentation.md), Step 6). For a full written spec, use program documentation; for a visual flow, use this.

---

## 1. Gather the data (reuse the spec tools)

One call gets almost everything:

```
ia_program_spec_bundle(program_name=X)                  → LOOKUP, COMPLEXITY, FILES, SUBROUTINES, CALLEES, PARAMS
ia_subroutines(member_name=X)                           → BEGSR with exact line numbers (for the "L<n>" refs)
ia_call_hierarchy(program_name=X, direction='CALLERS')  → who calls X (the "Called by" meta line)
```

If LOOKUP returns multiple versions, **stop and ask which library** (same rule as program docs). Read the **source** (`ia_rpg_source` / `ia_cl_source`) to follow the actual control flow — the diagram must reflect what the code does, not a guess. Collect: program name/library/type, total + executable lines, last-changed date, the subroutine list with line numbers, DB files, external calls, callers, and the entry interface (`*ENTRY`/PI parameters from PARAMS — or "no parameters — interactive"). While reading the source, also note the **F-keys** the program handles (F3 exit, F4 prompt, F12 cancel, …) for the F-key row.

> **Procedure-based programs** (COMPLEXITY shows `PROC>0` with `SBR=0` — common in SQLRPGLE): `ia_subroutines` and the bundle's `SUBROUTINES` section come back empty. Build the blocks from the program's **procedures** instead — list them via `ia_procedure_params` (`PROCEDURE_NAME`) / `ia_procedure_xref`, and read source (`dcl-proc`) for line ranges.

---

## 2. Design ONE top-to-bottom diagram

A single `flowchart TD`, the **whole program in one graph**, reading top → bottom in execution order: `START` at the top, the mainline/menu, then each branch flowing **downward**, and `END` reached from the program's exit.

- **Stay at a high altitude — ~15–25 nodes for the whole program.** Show the mainline and each option/branch's key steps (the screens, the decisions, the DB I/O). **Collapse helper subroutines** (clear/reset/refresh, window load+display) into one representative node — the *full* subroutine list lives in the table below the diagram, not in boxes. This is what lets one diagram cover even a large program.
- **No `subgraph`s.** They make Mermaid cluster areas side-by-side and destroy the top-to-bottom flow. Keep it one flat graph; the `class` colors already group nodes visually.
- **External program calls are never collapsed.** Every `CALL`/`CALLP` to another *program* gets its own node in subroutine shape `[["CALL PGMX<br/>L.."]]` with class `extcall` — the hand-off to another program is exactly what a new developer must see.
- **Loops read downward:** draw loop-backs (e.g. "return to menu after each action") as **dotted** edges `-.->|loop|` to the loop entry, and the program exit as a **thick** edge `==>|Yes|` to `END`. The solid forward arrows then carry the eye straight down.
- **One `START`, one `END`.** Every block carries a line reference (`<br/>L131` or `<br/>L272-320`).
- Decisions are diamonds; label both outgoing edges.

---

## 3. Mermaid rules (v10.9.0)

The template pins `mermaid@10.9.0` — **do not change it** (v11.x has SVG layout issues).

```
flowchart TD
    NODE(["Terminal"])        ← START / END (rounded)
    NODE["Process"]           ← subroutine / process / message (rectangle)
    NODE[/"Input/Output"/]    ← EXFMT / DISPLAY screen (parallelogram)
    NODE[("Database")]        ← CHAIN / READ / WRITE / SETLL (cylinder)
    NODE[["CALL PGMX"]]       ← external program call (subroutine shape)
    NODE{"Decision?"}         ← IF / loop test / validation (diamond)
    A --> B                   ← forward step
    A -->|Label| B            ← labelled step
    A -.->|loop| B            ← loop-back (dotted)
    A ==>|Yes| B              ← program exit (thick)
```

- Always `flowchart TD`, never `graph TD`. Double quotes in labels; line breaks with `<br/>`.
- Node names: alphanumeric + underscore only. Avoid the reserved word `end` as a node id (use `ENDP`).
- Escape `&` as `&amp;`. Keep labels short — push detail into the table.

---

## 4. Colours — define once with `classDef`

Put these **seven `classDef` lines once** at the end of the diagram, then assign nodes with `class`. (Don't repeat per-node `style` lines.) Dark fills + white text are WCAG-AA.

```
classDef terminal fill:#2E7D32,stroke:#1B5E20,color:#fff,stroke-width:2px;
classDef process  fill:#1565C0,stroke:#0D47A1,color:#fff,stroke-width:2px;
classDef display  fill:#0277BD,stroke:#01579B,color:#fff,stroke-width:2px;
classDef db       fill:#6A1B9A,stroke:#4A148C,color:#fff,stroke-width:2px;
classDef extcall  fill:#00695C,stroke:#004D40,color:#fff,stroke-width:2px;
classDef decision fill:#F57F17,stroke:#E65100,color:#fff,stroke-width:2px;
classDef error    fill:#C2185B,stroke:#880E4F,color:#fff,stroke-width:2px;
class START,ENDP terminal;
class A,B process;
...
```

| Class | Use for |
|-------|---------|
| `terminal` | START / END / ENTRY / RETURN |
| `process` | subroutine / process / status message |
| `display` | EXFMT / screen / subfile |
| `db` | CHAIN / READ / WRITE / SETLL / SQL |
| `extcall` | CALL / CALLP to another program |
| `decision` | IF / loop test / validation |
| `error` | error path / failure message |

---

## 5. Build the page (copy the template)

**Copy the template — never write the HTML from scratch:**

```
templates/flowchart-template.html  →  docs/program-specs/{PROGRAM_NAME}/{PROGRAM_NAME}_Flowchart.html
```

Replace only the content; leave the CSS and the one-line `mermaid.initialize` script alone. The page has exactly these parts:

1. **Title / `<h1>` / one-line subtitle.**
2. **Meta strip** — line 1: library · source member · type · lines (total + exec) · subroutine count · files · last updated. **Line 2:** Called by `<callers or none>` · Calls `<callees or none>` · Entry: `<*ENTRY/PI params, or "no parameters — interactive">`.
3. **The diagram** (§2–4).
4. **Legend** — the seven colours + a note that dotted = loop-back, **plus an F-key row** listing only the keys the program actually handles (`F3 Exit · F4 Lookup window · F12 Back to menu`).
5. **What it does** — 2–3 sentences in plain language.
6. **Subroutines (source index)** — one row per BEGSR (or procedure): name · line · area · **in diagram** (the node that represents it — its own node, or the node it's collapsed under) · purpose. *This is where the full detail lives.*
7. **Files** — file · type/access · record format(s) · role.
8. **Footer** — print note + "flowchart by iA from programmers.io".

There are **no tabs, no zoom controls, and no print hook** — a single diagram renders on load, so `Ctrl+P` prints/saves the whole page (the print CSS just scales the SVG to the page width).

---

## 6. Verify before delivery — two gates

**Gate 1 — lint (mandatory, run first):**

```
python scripts/validate_flowchart.py docs/program-specs/{PGM}/{PGM}_Flowchart.html
```

Must exit 0. It catches: not `flowchart TD`, `subgraph`s, the reserved `end` node id, leftover template placeholders, nodes with no `class` assigned, an unknown/undefined class, an unpinned Mermaid version, and bare `&` in labels.

**Gate 2 — browser:** open the file and confirm:

- [ ] The diagram **flows top → bottom**: `START` at top, branches descending, `END` reached via the exit edge; dotted arrows are the loop-backs.
- [ ] It renders (not raw code); colours show.
- [ ] Altitude is right — roughly 15–25 nodes; helper routines are collapsed, not drawn individually.
- [ ] Every external `CALL` appears as a teal `[["CALL …"]]` node — program calls are never collapsed.
- [ ] **Every** subroutine/procedure appears in the index table with its line number, and its **In diagram** column names a real node from the diagram.
- [ ] Meta strip (both lines), F-key row, and file list match the iA data and the source.
- [ ] **Ctrl+P** preview shows the whole diagram on the page.

Save to `docs/program-specs/{PROGRAM_NAME}/{PROGRAM_NAME}_Flowchart.html`.

## Common errors

| Symptom | Fix |
|---------|-----|
| Areas sit side-by-side, flow isn't vertical | Remove `subgraph`s — use one flat `flowchart TD`. |
| Diagram is a wall of boxes | Too low-altitude: collapse helper subroutines into representative nodes; move detail to the table. |
| Mermaid syntax error | `flowchart TD` (not `graph TD`), double quotes, `<br/>` for breaks, no node id named `end`, `classDef` lines last. |
| Text invisible on a node | You used a bare node with no `class` — assign one of the seven classes. |
| An external CALL is invisible in the flow | Give it its own `[["CALL PGMX"]]` node with class `extcall` — never fold a program call into another node. |
| Lint (Gate 1) fails | Read its findings — each maps to a row above or a leftover template placeholder. Fix and re-run before the browser check. |
| Diagram broke after edits | You changed the `<script>` or mermaid version — revert to the template's. |
