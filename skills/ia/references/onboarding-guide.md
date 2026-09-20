# New-Developer Onboarding Guide (menu → program → file)

Use this when a user asks to **onboard someone onto an application** — "onboarding guide for CASEMNU", "get a new developer up to speed on this menu", "menu to program to file mapping", "what does this menu do and what does it touch", "new developer walkthrough".

The deliverable is one readable document that answers, for a whole menu: **what the menu launches, what each program touches, what data is shared, and where to start reading.** The reader is a developer new to this application — and often new to IBM i — but not new to programming. Explain platform idioms, never `if` statements.

```
docs/onboarding/{MENU}/{MENU}_Onboarding_Guide.md      ← source of truth (you author this)
docs/onboarding/{MENU}/{MENU}_Onboarding_Guide.xlsx    ← built BY SCRIPT from the .md, on request
docs/onboarding/{MENU}/{MENU}_Onboarding_Guide.docx    ← existing converter, on request
docs/onboarding/{MENU}/{MENU}_Onboarding_Guide.pdf     ← existing converter, on request
```

> **Markdown is the source of truth.** Every other format is derived from it, so what the user reads is exactly what they download. Never hand-author the `.xlsx`.

**Scope in this version is a `*MENU`.** A single-program deep tour (annotated source excerpts + idiom glossary) is a planned later arm of this same DocType — if the user asks for one program, generate a program spec instead ([program-documentation.md](program-documentation.md)) and say why.

---

## 1. Resolve the menu

- User named a `*MENU` → `ia_object_lookup(object_name=MENU)` confirms type, library, description. Proceed.
- User named a **library** → `ia_object_list(library=L, object_type='*MENU')`.
- User named an **application area** → `ia_application_area(area_name=A)`, then keep its `*MENU` rows.
- User named a **program** → this DocType is menu-scoped. Offer a program spec or an object context matrix instead.

Then:

| Menus found | Do |
|---|---|
| Exactly 1 | Proceed, and **say so** — "CASELIB has one menu, CASEMNU; generating for that." |
| More than 1 | Show them in a table with the program count each launches, and ask which. Never auto-pick the biggest. |
| Zero | Report the negative plainly (Rule Two). Offer [app-map.md](app-map.md) or a program spec. Do **not** invent a scope. |

## 2. The data spine — run in this order

| # | Call | Gives you |
|---|------|-----------|
| 1 | `ia_object_lookup(object_name=MENU)` | type, library, description |
| 2 | `ia_repo_config()` | repository collection date → the freshness stamp |
| 3 | `ia_call_hierarchy(program_name=MENU, direction='CALLEES')` | the programs the menu launches |
| 4 | `ia_code_complexity(library=L, limit=5000)` | one call: exec lines, subroutine/procedure/SQL/file counts and `called_by_count` for **every** member — used for the cap ranking, the Start Here ranking and each program's stats line |
| 5 | `ia_member_lookup(source_library=L, limit=5000)` | `CHANGED_DATE` + member description + member type for every member in **one** call — the freshness gate at library scale. Do **not** call `ia_object_lifecycle` per program. |
| 6 | `ia_object_context_matrix(object_name=PGM)` — one per kept program | that program's files bucketed by usage mode, each with attribute, description, record formats and key fields, plus its own callees (`CALLS_PROGRAM`) and callers (`CALLED_FROM`) |
| 7 | `ia_cl_jobs(member_name='*ALL')` | SBMJOB batch pattern — job name and job queue |
| 8 | `ia_file_dependencies(file_name=PF)` — one per distinct data PF | logical files over each PF, for the LF annotation in §5. **Skip entirely if the scope has no LF objects** (check once with `ia_object_list(library=L, object_attribute='LF')`). |
| 9 | `ia_program_summary(program_name=PGM)` — **only for the Start Here 5** | compile detail where it matters. Every other program's role comes from its object text description plus its complexity stats. |

**Expanding the tree.** Step 3 gives level 1. Step 6's `CALLS_PROGRAM` rows give the next level for each program — follow them until no new program appears. A CL that appears as a callee is usually the batch driver; its own matrix reveals the RPG it submits.

**Cap:** rank every reached `*PGM` by `EXEC_LINES` descending and give a detail section to the top **25**. Programs the menu launches directly are always kept regardless of rank. Everything beyond the cap goes in the "Reached but not detailed" table with name, role and how it is reached — **state the overflow count in the document. Never truncate silently.**

## 3. Menu option numbers — not in the call hierarchy

`ia_call_hierarchy(MENU, 'CALLEES')` returns *which* programs a menu launches but **not the option number or the option text**: those rows come from the object cross-reference fallback, so `CALL_SEQUENCE` is empty. The mapping lives in the menu's two source members, read with **`ia_dds_source`**:

- **`{MENU}QQ`, member type `MNUCMD`** — one line per option, `NNNN CALL PGM(TARGET)`. This is the authoritative option → program mapping.
- **`{MENU}`, member type `MNUDDS`** — the screen. Option numbers appear as positioned literals (`5  7'1.'`) and the option text on the same screen row (`5 10'Customer Maintenance'`). **Join by screen row**, not by sequence number.

Pull both members in a single call with a wildcard — `ia_dds_source(member_name='{MENU}%')` — then split the result by its `library_name` / `member_name` / `member_type` columns. Two guards on the wildcard: it also drags in unrelated members sharing the prefix (`CASEDSP`, `CASEPRT` for `CASE%`), so narrow with `member_type='MNUCMD'` when that happens; and if the menu exists in more than one library the copies arrive back to back with `source_rrn` restarting, so pass `library_name` or split on it before reading.

If the `MNUCMD` member is absent, fall back to the call-hierarchy list, order it alphabetically, and **say in the document that option numbers could not be recovered** — never number the options yourself.

> A menu option can run a command other than `CALL PGM(...)` (e.g. `SBMJOB`, `STRSQL`, a `*CMD`). Take the option's command verbatim; only map it to a program when the command names one.

## 4. Ranking for "Start here"

Pick **5**, in this order, skipping any that don't exist:

1. The **front door** — the option-1 program, or the one with the highest `called_by_count`.
2. The **workhorse** — the highest `EXEC_LINES` among reached programs.
3. The **shared master file** — the data PF touched by the most programs (from your own file tables, not a guess).
4. The **batch driver** — the CL with an SBMJOB, if any.
5. The **oddity** — whichever of these is present: a program with an unusually high SQL count, an override/QTEMP pattern, a program reached only indirectly.

One line each on *why it matters*, not what it is.

## 5. Building the file tables

Per program, from its context matrix rows:

| Column | Source |
|---|---|
| File | `OBJECT_NAME` |
| Type | `OBJECT_ATTRIBUTE` — PF / LF / DSPF / PRTF |
| Over | base PF, for LF rows only (from step 8) — blank otherwise |
| Access | `USAGE_MODE` verbatim (Input / Output / Update / Combined) |
| Purpose | `DESCRIPTION`; if blank, write "no description recorded" — **never invent one** |

Rules:

- **Logical files stay visible.** List the LF by its own name and annotate the base PF in the "Over" column. The reader opening the source will see the LF in the F-specs; collapsing it to the PF (which the [app map](app-map.md) does deliberately, because a graph node per LF is noise) makes the document disagree with the code.
- **`C` on a display file means Combined** — read and written — not "create". Never render it as Create.
- **The same file can appear twice** with different `DETECTED_FROM` (`O` = from the compiled object, `S` = from source). Merge them into one row and union the access modes; note the union, e.g. `Input Update`.
- **Files in `QTEMP` and `#`-suffixed duplicates are runtime work files**, not repository objects — they surface as unenriched rows (blank attribute/description). Don't table them as data files; explain them in the program's role sentence instead (see the override pattern in §7).

## 6. Shared data and risk

Build one matrix of every data PF touched by **≥2** programs: rows = files, columns = programs, cells = access mode.

Then call out, in prose:

- Any file **updated by more than one program** — "change its layout and every one of these needs recompiling and retesting".
- The file with the **most** touching programs — the application's spine.
- Any program that updates a file it does not own by name (cross-area write).

Keep it factual. This is not a change-impact assessment — if the user is actually about to change something, route to [change-impact-analysis.md](change-impact-analysis.md).

## 7. "Terms you'll see" — only what this scope contains

Detect from the metadata already fetched; include an entry **only if the scope actually has one**. 2–3 plain sentences each, plus where it appears.

| Include when | Term |
|---|---|
| Any `*FILE` with attribute DSPF | Display file, record format, subfile (`SFL`/`SFLCTL` in the format list) |
| Any PRTF | Printer file and spooled output |
| Any LF | Logical file over a physical file |
| An `ia_cl_jobs` row | SBMJOB — user-triggered submission to a job queue. **Never say "nightly"/"scheduled"** unless a scheduler entry proves it |
| CL source shows `OVRDBF` / `OPNQRYF` / `CRTDUPOBJ` to QTEMP | The override pattern — the program reads a name that has been redirected to a job-scoped copy at runtime |
| Members typed `SQLRPGLE` | Embedded SQL inside RPG |
| `SOURCE_FORMAT` mixes FULLY FREE and MIXED/FIXED | Fixed-form vs free-form RPG |
| Consistent name prefixes/suffixes | The shop's naming convention — state the pattern you observed, e.g. `*R` suffix = RPG, `*C` suffix = CL driver |
| Any file access mode column | The `I` / `O` / `U` / `C` legend |

No generic RPG textbook padding. If the scope has no LFs, there is no LF entry.

## 8. Document structure

Follow [templates/template-onboarding-guide.md](templates/template-onboarding-guide.md). Sections, in order:

1. Header — menu, library, repository + collection date, `Author: iA by programmers.io`, freshness verdict
2. What this menu does
3. Start here (the 5)
4. Menu options table
5. Call map — a **text ASCII tree in a fenced ```text``` block. Never Mermaid.**
6. Program details — one subsection each
7. Shared data
8. Terms you'll see
9. Reached but not detailed (omit if the cap wasn't hit)
10. Where to go next

## 9. Verification gate — before showing the document

**Freshness.** Compare each in-scope member's `CHANGED_DATE` (step 5) with the repository collection date (step 2). Any member changed *after* collection → flag it in the header: the document describes the metadata, which is older than the source. Convert the `CYYMMDD` form (`1260708` → 2026-07-08) before comparing.

**Cross-check every claim against your own tool output:**

- [ ] Every program in the document appears in the call-hierarchy or a `CALLS_PROGRAM` row
- [ ] Every file row traces to a context-matrix row — no file appears that no tool returned
- [ ] Every option number came from the `MNUCMD` member, or the document says they couldn't be recovered
- [ ] Counts in the prose match the table row counts
- [ ] Overflow count stated if the cap was hit
- [ ] No access mode rendered as "Create"
- [ ] Nothing described as scheduled/nightly without evidence

## 10. Downloads

After showing the document, offer: **Word**, **PDF**, **Excel**, or all three.

```
python scripts/build_onboarding_guide.py docs/onboarding/{MENU}/{MENU}_Onboarding_Guide.md
python scripts/convert_md_to_docx.py     docs/onboarding/{MENU}/{MENU}_Onboarding_Guide.md
python scripts/convert_md_to_pdf.py      docs/onboarding/{MENU}/{MENU}_Onboarding_Guide.md
```

`build_onboarding_guide.py` parses the markdown tables and writes a four-sheet workbook (Menu Options, Program → File Relations, Shared Data, Program Stats). If it errors, fix the **markdown** — never patch the workbook by hand.

## Common mistakes

| Symptom | Cause / fix |
|---|---|
| Option numbers invented or alphabetical | You used `ia_call_hierarchy` for ordering. Read the `MNUCMD` member (§3). |
| A display file listed as "Created by" the program | `C` is Combined. §5. |
| Same file listed twice per program | Object-detected and source-detected rows not merged. §5. |
| A `#`/QTEMP file tabled as a data file | Runtime work file from an override. §5, §7. |
| "Runs nightly" | Nothing in iA says that. An SBMJOB is user-triggered. §7. |
| Document is 40 pages | The cap wasn't applied. §2. |
| Every program says "no description recorded" | The repo's object text is blank — that's a real finding, say it once in the header rather than 25 times. |
