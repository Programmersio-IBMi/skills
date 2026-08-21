# Change Impact Analysis

Use this when the user is about to **change something** and wants to know what it
breaks, who has to be told, and what it costs — *"what happens if I make CUSTNO
10 long"*, *"can I drop this field"*, *"impact of adding a parameter to
ORDVAL"*, *"we're retiring ITMMAST, what depends on it"*.

The deliverable is a **Change Impact Assessment**: a classified change, a
verified list of affected artifacts, the failures that will not announce
themselves, a risk verdict, and a costed estimate workbook.

> Not the same as [object-context-matrix.md](object-context-matrix.md). That
> answers *what surrounds this object today*. This one answers *what happens if I
> alter it* — the same edges, read forward, plus the change-type-specific traps
> and an estimate.

---

## 1. Step 0 — classify the change before querying anything

Everything downstream depends on this. Ask if it is not stated; guessing wastes
calls and produces the wrong trap list.

| # | Change class | Typical phrasing |
|---|--------------|------------------|
| C1 | **Field resize** | "make it bigger", "CHAR(6) → CHAR(10)", "add two digits" |
| C2 | **Field type change** | "make it numeric", "convert to a real date" |
| C3 | **Field add** | "add a column", "new field on the file" |
| C4 | **Field remove** | "drop it", "we don't use it any more" |
| C5 | **Field rename** | "rename CUSTNO to CUSTNBR" |
| C6 | **Key change** | "add to the key", "reorder the key", "make it unique" |
| C7 | **File add / new LF** | "new table", "new index over it" |
| C8 | **File retire / delete** | "can we drop this file" |
| C9 | **Program logic change** | "change how the discount is worked out" |
| C10 | **Program interface change** | "add a parameter", "change the parm length" |
| C11 | **Service program export change** | "add a procedure", "change a PR" |
| C12 | **Copybook change** | "change the shared DS" |
| C13 | **Screen / report layout change** | "add a field to the screen" |
| C14 | **Constraint / trigger change** | "add an FK", "change the check" |
| C15 | **Object move / library change** | "promote to production", "move to a new library" |

Also capture **direction** where it applies — widening vs narrowing (C1),
optional vs mandatory (C3, C10). It changes the trap list, not just the wording.

---

## 2. The spine — run this for every change class

Six calls, most of them parallel. Everything in §3 is *added* to this.

```
1. ia_object_lookup / ia_member_lookup      → confirm the thing exists, get type + library
2. ia_object_context_matrix(object_name=X)  → all inbound + outbound edges, pre-bucketed
3. ia_find_object_usages(object_name=X)     → where-used, with reference source S/O
4. ia_object_lifecycle(object_name=X)       → is any of this actually alive
5. ia_code_complexity(member_name=*ALL, …)  → line counts for every affected program (drives the estimate band)
6. ia_repo_config                           → freshness: when was the metadata last built
```

Step 6 is not optional. An assessment built on a stale repository is worse than
none, because it reads as authoritative. If the usage data is old or blank, say so
in the report header and treat "unused" claims as unverified.

**If step 1 returns nothing, stop.** The object does not exist under that name
(Rule Two). Do not assess a similarly-named object.

---

## 3. Per-class additions

Each row lists only what the spine does **not** already cover.

### C1 / C2 — field resize or retype

The highest-risk class, because the compiler catches almost none of it.

| Check | Why this class | Tool |
|-------|----------------|------|
| Is the field REFFLD-inherited? | Changing it on this file is the *wrong edit* — the definition lives in the field-reference file | `ia_file_fields` (reference chain) |
| Who else inherits it? | One FRF edit resizes the field in every consuming file | `ia_field_reffld_consumers` |
| LFs, indexes, views | Key-length change forces rebuild; select/omit literals may no longer match | `ia_file_dependencies` |
| Join LFs | Join field pairs must match length **and** type — resize one side and the join is invalid | `ia_join_logical_files` |
| Constraints | FK means the parent key must move in lockstep; CHECK literals may stop holding | `ia_file_constraints` |
| DS overlays | A DS over the record format shifts every subfield *after* the field. Numeric widening changes packed byte length, so offsets move even when digits look harmless | `ia_data_structures` |
| KLIST / KFLD | Key resize invalidates every key list containing it, and every CHAIN/SETLL using them | `ia_klist_usage(kfld_name=…)` |
| Truncating operations | `MOVE`/`MOVEL` into an unchanged work field, `%SUBST` at hardcoded offsets, fixed-position arrays | `ia_variable_ops`, `ia_rpg_source_search` |
| Screen / print fit | A wider field may not fit its position or may overlap its neighbour | `ia_object_context_matrix` (DSPF/PRTF buckets) |

Split the affected-program table by **direction**. Widening and narrowing are
different remediation lists — widening risks truncation on the receiving side and
layout overflow; narrowing risks data loss and every widening risk in reverse.
Merging them forces the developer to re-derive the split by hand.

### C3 — field add

Cheaper than it looks, and saying so is useful. Level check still forces a
recompile of every program with an F-spec on the file, but almost nothing needs a
code change.

- `ia_object_context_matrix` → the recompile list (this is most of the work)
- `ia_data_structures` → externally-described DS pick the field up automatically; program-defined overlays do not
- `ia_file_constraints` → a NOT NULL addition without a default fails on existing rows
- Flag any `*OUTPUT`-mode program writing the record without the new field

### C4 / C5 — field remove or rename

The one class where the compiler *is* on your side — every reference fails to
compile. The work is finding them all so nothing is missed at cutover.

- `ia_file_field_impact_analysis(file_name=X, field_name=Y)` → direct references
- `ia_field_reffld_consumers` → if it is an FRF field, removal cascades
- `ia_klist_usage(kfld_name=Y)` → key lists naming it
- `ia_rpg_source_search(search_text=Y)` → catches literal/comment/SQL mentions the cross-reference misses
- `ia_file_constraints`, `ia_file_dependencies` → LF key or select/omit referencing it
- **Rename is not one change** — treat as remove + add, and check whether an SQL long name exists via `ia_sql_table_names`

### C6 — key change

- `ia_file_dependencies` → every LF/index over the file
- `ia_klist_usage` → partial-key reads break silently when key order changes
- `ia_file_constraints` → PK/UQ and any FK pointing at this key
- Adding a **unique** key can fail outright on existing duplicate data — flag as a data check, not a code change
- Reordering a key changes `READE`/`SETLL` semantics with **no compile error**

### C7 — new file or new LF

Lowest risk class. Keep the report short.

- `ia_library_files` → name collision check
- `ia_file_dependencies` on the base PF → a new index adds maintenance cost to every write path
- Note the write-path cost in the summary; do not pad the report

### C8 — file retire

- `ia_object_context_matrix` → everything reaching it
- `ia_file_dependencies` → LFs must go first, and in order
- `ia_file_overrides` + `ia_override_chain` → a program may reach it only through an override, so it will not appear as a direct reference
- `ia_object_lifecycle` + `ia_obj_size` → last-used date and row count are the evidence for "safe to drop"
- `ia_unused_objects` → corroboration, not proof

**Never call a file dead from a zero row count alone.** Find the caller and the
state it runs under first — a year-end-only program looks dead for eleven months.

### C9 — program logic change

- `ia_call_hierarchy(direction='CALLERS')` → who depends on this behaviour
- `ia_subroutines` → usage counts locate the blast radius inside the program
- `ia_program_files` → which files the change can touch, with PREFIX detail
- `ia_code_complexity` → effort band and review depth
- Field-level lineage (§4) if the change alters what a field *contains* rather than only control flow

### C10 / C11 — interface or export change

The most under-estimated class. A signature change to a `*SRVPGM` invalidates
every program bound to it, whether or not they use the changed procedure.

- `ia_call_parameters(member_name=X)` → every call site and what it passes today
- `ia_procedure_params` → the PR/PI signature being altered
- `ia_srvpgm_exports` → the export list; **export order changes break the signature**
- `ia_procedure_xref` → procedure-level callers
- `ia_find_object_usages(object_name=SRVPGM)` → everything bound, the true recompile set
- Adding a parameter at the **end** with a default is far cheaper than inserting one — say which was chosen

### C12 — copybook change

- `ia_copybook_impact(copybook_name=X)` → every member with `/COPY`
- `ia_member_copybooks` → the reverse view, to catch nested copybooks
- Fan-out here is members, not objects — a single copybook edit can touch hundreds

### C13 — screen or report change

- `ia_object_context_matrix` → programs using the DSPF/PRTF (usage mode `C` = Combined)
- `ia_file_fields` on the DSPF → position collisions
- Indicator usage via `ia_program_variables` — display files break on indicator conflicts more often than field ones

### C14 — constraint or trigger change

- `ia_file_constraints` → existing PK/UQ/FK/CHK and delete/update rules
- A new FK fails to add if existing data has orphans — always a data check
- Trigger changes affect **every** write path, including ones with no source-level reference to the trigger

### C15 — object move / library change

- `ia_file_overrides`, `ia_override_chain` → library-qualified overrides break on move
- `ia_object_lookup` → does the name already exist in the target library
- Anything still resolving through `*LIBL` becomes ambiguous — call these out individually

---

## 4. Field-level data lineage

**Available, but best-effort — never present it as complete.** It is derived from
parsed source, so it sees what the source says, not what runs.

### How it works

`ia_variable_ops` returns an assignment graph: one row per operation, with
`FACTOR1_VAL` / `FACTOR2_VAL` as sources and `RESULT_VAL` as the target, plus
`BIF` for the transform and `SOURCE_RRN` for the line.

```
ia_variable_ops(member_name='ORDENT', variable_name='CUSTNO', opcode='*ALL')
```

Follow `RESULT_VAL` of one row into `FACTOR1_VAL` of the next to build a chain:

```
CUSTNO ──(read from CUSTMST)──► WKCUST ──%CHAR──► PRTCUST ──(written to ORDPRT)
```

**Bridging file fields to variables:** the repository carries no populated
variable→file binding in the repositories checked so far, so there is nothing
direct to join on. Use the naming identity instead — for an
externally-described file, the RPG field name *is* the variable name, so match
`ia_file_fields` field names against `FACTOR`/`RESULT` values directly. Resolve
`PREFIX` first with `ia_program_files`, or every prefixed field silently misses.

**Crossing program boundaries:** `ia_call_parameters` gives the parameter at each
call site, which is the edge from caller variable to callee parameter. Chain
lineage inside program A → parameter → lineage inside program B.

### Confidence levels — label every edge

| Confidence | When |
|------------|------|
| **High** | Direct `=` assignment, both sides plain variable names, single row |
| **Medium** | A `BIF` transforms the value (`%CHAR`, `%EDITC`, `%SUBST`), or the expression spans continuation rows (`COMPARE_OPER='+'`) |
| **Low** | Target reached via DS overlay, array index, pointer, or embedded SQL |
| **None** | Dynamic — the field name is computed at runtime |

### Limits to state in the report

1. `RESULT_VAL` is `CHAR(50)` while `FACTOR1_VAL` is `CHAR(80)` — long qualified
   `DS.SUB.SUB` targets can be **truncated**, so a chain may break mid-path.
2. Multi-line expressions split across rows joined by `COMPARE_OPER='+'`. Reading
   a single row loses operands — gather all continuation rows for one `SOURCE_RRN`.
3. `RESULT_VAL` is not always a bare name (`EVAL-CORR UDPSDS` appears literally).
   Strip the opcode prefix before matching.
4. `FACTOR1_VAL` of the form `Const("…")` is a literal, not a variable. Exclude
   these from lineage edges or every constant becomes a false source.
5. Available opcodes vary by source vintage — free-form repositories carry `=` and
   `SQLEXC`; fixed-form carry `MOVE`/`MOVEL`/`Z-ADD`. Do not assume a fixed set.
6. `SQLEXC` rows carry the statement in `FACTOR2_VAL` with no `FACTOR1_VAL`.
   Lineage through embedded SQL needs the statement parsed — mark it **Low**.

### When to run it

Only for C1, C2, C4, C5, C9 — where the field's *value* moves. Skip it for
recompile-only classes; it costs calls and adds nothing to a level-check list.

---

## 5. The silent-failure catalogue

Give this its own section in every report for C1, C2, C6, C9. These compile
clean and produce wrong output — they are the reason the assessment exists.

| Failure | Class | How it is found |
|---------|-------|-----------------|
| Truncation into an unchanged work field | C1 | `ia_variable_ops` — target shorter than new source |
| DS subfield offset shift | C1, C2, C3 | `ia_data_structures` — any DS over the record format |
| Partial-key mismatch | C1, C6 | `ia_klist_usage` |
| Select/omit literal no longer matching | C1, C2 | `ia_file_constraints` |
| Join field length mismatch | C1, C2 | `ia_join_logical_files` |
| Screen/report column overflow | C1, C3, C13 | DSPF/PRTF rows + `ia_file_fields` |
| Override pointing at a different physical | all | `ia_file_overrides`, `ia_override_chain` |
| `*SRVPGM` signature invalidation | C11 | `ia_srvpgm_exports` |
| Numeric edit/format assumptions | C1, C2 | `ia_rpg_source_search` for `%EDITC`, `%EDITW` |

---

## 6. Risk verdict

Use the counts you actually have. Reuse the rubric in
[playbook.md](playbook.md) and add the class weighting:

| Verdict | When |
|---------|------|
| **Low** | ≤5 affected objects, no silent-failure rows, no `*SRVPGM`, no FRF cascade |
| **Medium** | 6–20 affected objects, or any DS overlay / KLIST hit |
| **High** | >20 affected objects, **or** any of: FRF cascade, `*SRVPGM` signature change, trigger change, narrowing with existing data |

A single `*SRVPGM` or FRF hit outranks the count. Say which factor drove the
verdict — a bare "High" that the developer cannot trace is not actionable.

---

## 7. The estimate workbook

Always offered, generated from the report — never hand-authored.

The report must contain a table under a `## Affected Artifacts` heading with
exactly these columns, because the script keys on them:

```
| Library | Object | Type | Attribute | Impact | Lines | Notes |
```

- **Impact** — one of `CHANGE`, `RECOMPILE`, `REBUILD`, `REVIEW`, `NONE`
- **Lines** — from `ia_code_complexity`; blank for non-source objects
- **Type** / **Attribute** — as returned by `ia_object_lookup` (`*PGM`, `*FILE` + `PF`/`LF`/`DSPF`/`PRTF`)

```
python .claude/skills/ia/scripts/build_change_estimate.py REPORT.md --xlsx
```

Add `--narrowing` when the change can lose data (C1 narrowing, C2, C4), which
adds the data-conversion line.

Three sheets, in this order: **Assumptions → Summary → Estimate Detail.** The rates
come first because they are what a client argues about; the workbook opens on the
negotiable page rather than on the total.

The workbook is **formula-driven**: every rate lives on the `Assumptions` sheet and
the Summary and Detail sheets reference it. Change a rate in Excel and the totals
recalculate — no re-run needed. Summary heads with a single count, **Total impacted
objects** (every row of the Affected Artifacts table, whatever its Impact verb); the
per-basis breakdown lives once, in the Basis table at the foot of the same sheet.
Defaults are deliberately lean:

| Line | Default |
|------|---------|
| Impact review & change design | 2.0 h fixed |
| Cutover / implementation | 2.0 h fixed |
| Program change — S (≤ 500 lines) | 1.5 h |
| Program change — M (501–2,000) | 3.0 h |
| Program change — L (> 2,000) | 5.0 h |
| Program — recompile only | 0.15 h |
| PF / DDS-DDL change | 0.15 h |
| Logical file / index rebuild | 0.15 h each |
| Display or printer file change | 1.0 h |
| Copybook change | 0.15 h |
| Other object change | 0.15 h |
| Review-only item | 0.5 h |
| Unit test | 0.5 h per changed program |
| System / regression test | 15% of development |
| UAT support | 10% of development |
| Data conversion (`--narrowing`) | 2.0 h |
| Contingency | 12% of subtotal |

Every non-program artifact is 0.15 h except display and printer files, which stay
at 1.0 h because a layout change is real design work rather than a rebuild. The
effort therefore sits almost entirely in the changed programs, which is where it
belongs — and it makes the S/M/L banding, not the object count, the thing worth
arguing about.

**Quote the number, then the assumption.** A total without the rate table behind
it invites a haggle; with it, the conversation is about the rates, which is a
conversation worth having.

---

## 8. Shape of the deliverable

1. **Title** — `# Change Impact Assessment — {OBJECT} · {CHANGE CLASS}`
2. **The change** — one paragraph: what, from what, to what, direction. If the
   user gave a before/after, restate it precisely; ambiguity here invalidates
   everything below.
3. **Verdict** — Low/Medium/High plus the one factor that drove it, and the
   headline effort from the workbook.
4. **Affected Artifacts** — the canonical table from §7. This is the spine of the
   document and the input to the estimate.
5. **Silent failures** (§5) — omit the section only if genuinely empty.
6. **Field lineage** (§4) — only for the classes that warrant it.
7. **Sequence** — dependency-ordered: data → files → LFs → copybooks →
   programs (callees before callers) → screens → cutover.
8. **Data checks** — what must be verified against real data before proceeding.
9. **Out of scope** (§9).
10. **Download menu.**

Escape `|` in every cell — object descriptions contain them, and an unescaped
pipe silently truncates the cell and shifts every column right of it.

### Where the files go

```
docs/change-impact/{OBJECT}/{OBJECT}_Change_Impact.md
docs/change-impact/{OBJECT}/{OBJECT}_Change_Estimate.xlsx
```

For a `*PGM` whose spec already exists, use
`docs/program-specs/{PGM}/` instead so the assessment sits with its spec.

### Downloads

```
Download this assessment as:
  1. Markdown (.md)   2. Estimate workbook (.xlsx)   3. Word (.docx)
  4. PDF (.pdf)       5. All of the above
```

```
python .claude/skills/ia/scripts/build_change_estimate.py ASSESSMENT.md --xlsx
python .claude/skills/ia/scripts/convert_md_to_docx.py    ASSESSMENT.md
python .claude/skills/ia/scripts/convert_md_to_pdf.py     ASSESSMENT.md
```

---

## 9. What this cannot tell you — state it explicitly

A section the report must always carry. It is what makes the rest credible.

- **Actual data.** Whether values exceed a narrowed size, whether duplicates
  block a unique key, whether orphans block an FK. All need a query against live
  data, not metadata. Name the specific check.
- **Physical layout feasibility.** Whether a wider field fits the screen.
- **External interfaces.** EDI layouts, flat-file exports, APIs, downstream ETL,
  reports consumed outside the box — none are in the repository.
- **Runtime-dynamic behaviour.** Dynamic CALLs with computed names, dynamic SQL,
  `*LIBL` resolution that depends on the job.
- **Business meaning.** Whether the field's semantics survive the change.
- **Anything newer than the last metadata build** (`ia_repo_config`).
