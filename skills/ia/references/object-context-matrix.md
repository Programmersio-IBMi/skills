# Object Context Matrix

Use this when the user asks for the **context matrix** of an object — *"object
context matrix for CUSTMNTR"*, *"what's the full context of CUSTMST"*, *"show me
everything around ICS100"*. The deliverable is a sectioned report of everything
the object **uses** and everything that **uses it**, followed by a download menu.

It is the AI counterpart to the portal's Object Context Matrix screen, but a
**superset** of it: the same sections, plus whatever else the object's shape
makes relevant (§4), plus a short opening summary the screen has no room for.

> Not the same as [program-documentation.md](program-documentation.md). That
> produces a written spec of how a program *works*. This one is purely the
> object's **surroundings** — its inbound and outbound edges — and it works for
> any object type, not just programs.

---

## 1. One call gets everything

```
ia_object_context_matrix(object_name='CUSTMNTR', object_type='*PGM',
                         object_library='CASELIB')
```

`object_type` and `object_library` are both optional (`*ALL`). Pass them when the
user gave them, or when the bare name is ambiguous. Row 1 is always
`section = OBJECT` — the requested object itself.

**Do not** build this from `ia_object_references` + `ia_find_object_usages` +
per-object `ia_object_lookup`. Neither of those returns the referenced object's
**attribute** (which is what splits display and printer files out from data
files) or its **description**, so that route costs one extra call per referenced
object and still has to bucket by hand.

**If the call returns zero rows the object does not exist under that name** —
report the negative (Rule Two). Do not fall back to a similarly-named object.

### Usage mode — read `usage_mode`, never `FILE_USAGES`

The tool derives `usage_mode` from `REFERENCED_OBJUSG`. On `*FILE` rows the raw
codes are `I`/`O`/`U`/`C` — **Input / Output / Update / Combined** — and they
combine (`I/U`, `I/O/U`, `C/O`); the tool has already merged duplicate rows and
rendered them as `Input Update`. On `*SRVPGM`, `*MODULE` and `*BNDDIR` rows the
same `I` means *Implicit* instead. The separate `FILE_USAGES` column is empty in
current repositories — never read usage from it.

**`C` is Combined, not Create.** It marks a workstation file opened for both
read and write — in practice always a `DSPF`. Reading it as "create" turns every
program that merely displays a screen into the program that *created* the
display file. The tool guards the inbound side so combined references to a
`DSPF`/`PRTF` land in `READ_BY`, never `CREATED_BY`; `FILE_CREATE` and
`CREATED_BY` are reserved for a genuine create and are empty in every repository
seen so far. If you ever see a display file under "Created By", the guard has
regressed.

---

## 2. Sections → headings

Render one `##` heading per section **that has rows**, with the row count, in
this order. Omit empty sections silently — do not print "none".

| `section` | Heading |
|-----------|---------|
| `FILE_UPDATE` | Files Used In Update Mode(s) |
| `FILE_INPUT` | Files Used In Input Mode(s) |
| `FILE_OUTPUT` | Files Used In Output Mode(s) |
| `FILE_CREATE` | Files Created |
| `DISPLAY_FILE` | Display File(s) |
| `PRINTER_FILE` | Printer File(s) |
| `CALLS_PROGRAM` | Programs Called |
| `USES_SRVPGM` | Service Programs Used |
| `BOUND_MODULE` | Modules Bound |
| `USES_DTAARA` | Data Areas Used |
| `USES_BNDDIR` | Binding Directories |
| `USES_OTHER` | Other Objects Used |
| `CALLED_FROM` | Called From Program(s) |
| `UPDATED_BY` | Updated By Program(s) |
| `WRITTEN_BY` | Written By Program(s) |
| `CREATED_BY` | Created By Program(s) |
| `READ_BY` | Read By Program(s) |
| `REFERENCED_BY` | Referenced By |

`section_seq` already sorts them — render in the order returned.

### Columns per section family

| Family | Columns |
|--------|---------|
| Data files (`FILE_*`) | File Library · File Name · File Description · File Attribute · Record Format · Key Field · Select/Omit |
| `DISPLAY_FILE`, `PRINTER_FILE` | File Library · File Name · File Description · File Attribute · Record Format |
| Everything else | Object Library · Object Name · Object Type · Object Description · Object Attribute |

Add **Usage Mode** as a column only when a section mixes modes (e.g. `UPDATED_BY`
holding both `Update` and `Input Update`). Drop columns that are empty for every
row in that section — a Select/Omit column of seven blanks is noise.

### Escape pipes in every cell value

Object text on IBM i may contain `|` — e.g. the real description
`CLPGM1  CALLED BY COMMAND || AICAL ||`. Written into a markdown table unescaped
it ends the cell early: the description is **silently truncated** and every
column to its right shifts left and loses its last value. Nothing errors, the
row count is unchanged, and the damage is carried into the `.xlsx`, `.html`,
`.docx` and `.pdf` alike. Replace `|` with `\|` in every cell you emit —
descriptions are the only field where it realistically occurs, but the rule is
cheapest applied to all of them.

---

## 3. Shape of the answer

1. **Title** — `# Object Context Matrix — {NAME} ({TYPE}, {LIBRARY})`
2. **Summary** — 2–4 sentences from the `OBJECT` row plus the section counts:
   what the object is, what it touches, what reaches it, and one risk sentence.
   This is the AI's contribution; keep it factual and derived only from rows you
   actually have.
3. **The section tables** (§2).
4. **Enrichment sections** (§4), if any earned their place.
5. **The download menu** (§5).

Do not invent a "what stayed the same" or filler section. If the object has one
inbound edge and no outbound ones, the report is short — that is the finding.

---

## 4. What to add beyond the portal (the superset)

The tool covers every reference-derived section. Add these **only when the
object's own data makes them relevant** — each costs a call, so none are
automatic:

| Add | When | Tool |
|-----|------|------|
| Copybooks | Object is a program/module and the user asked about change impact | `ia_member_copybooks` |
| Override routing | The program has any `OVRDBF` — a declared file may not be the file actually read | `ia_file_overrides`, then `ia_override_chain` if it chains |
| LFs / views over each PF | A `FILE_UPDATE` row exists — changing that PF also hits everything built over it | `ia_file_dependencies` |
| Complexity / risk framing | The user asked "is this risky to change" | `ia_code_complexity` |
| Indirect reach | `CALLED_FROM` is non-empty and the user wants the full blast radius, not just direct callers | `ia_call_hierarchy` |

Rule of thumb: if the extra call would not change a sentence of the summary or
add a row someone would act on, skip it. A matrix that answers the question in
one call is better than a thorough one that took eight.

---

## 5. Offer the downloads

After the tables, always offer the menu — the user picks, then you build:

```
Download this matrix as:
  1. Markdown (.md)   2. Excel (.xlsx)   3. Word (.docx)
  4. PDF (.pdf)       5. HTML (interactive)   6. All of the above
```

Markdown is the source of truth. Write the `.md` first, then derive:

```
python .claude/skills/ia/scripts/build_context_matrix.py REPORT.md --xlsx --html
python .claude/skills/ia/scripts/convert_md_to_docx.py  REPORT.md
python .claude/skills/ia/scripts/convert_md_to_pdf.py   REPORT.md
```

`build_context_matrix.py` needs `openpyxl` for `--xlsx` (`--html` has no
dependencies). It parses the `##` headings and pipe tables out of the `.md`, so
whatever you rendered — including sections you added in §4 — is exactly what
lands in every format. Never hand-author the workbook or re-query for it.

### Where the files go

| Object type | Path |
|-------------|------|
| `*PGM` | `docs/program-specs/{NAME}/{NAME}_Context_Matrix.{ext}` — alongside that program's spec and flowchart |
| everything else | `docs/context-matrix/{NAME}/{NAME}_Context_Matrix.{ext}` |

---

## 6. Interpretation notes

- **The same name can appear twice under different types.** `MNTO0101` shows up
  as a `*MODULE` in `READ_BY` and as a `*PGM` in `UPDATED_BY`. Both are real —
  the module and the program it is bound into are separate objects. Do not
  dedupe them.
- **The same name across yearly libraries is not a duplicate.** `ICS100` in
  `LIB2024`, `LIB2025` and `LIB2026` are three copies of one program. Say so in
  the summary, and offer [version-comparison.md](version-comparison.md) as the
  next step rather than listing them as three unrelated callers.
- **A row still showing `*LIBL`** means the program did not qualify the library
  *and* the name is not unique across libraries, so it could not be resolved.
  Those rows come back with no attribute, description or record formats — the
  blanks are unresolvable, not missing data. Say which library you think it
  resolves to at runtime only if `ia_object_lookup` confirms it.
- **`detected_from`** — `S` = found in source, `O` = found in the compiled
  object, `S+O` = both. An `O`-only row on a program whose source you can read
  usually means the source was changed and not recompiled, or vice versa; worth a
  sentence when it shows up.
- **Empty `CALLED_FROM` does not mean dead.** The object may be launched by a
  scheduler, a menu outside the repository, or a command line. Say "no callers
  recorded in iA", not "unused" — `ia_unused_objects` is the tool that makes that
  claim.
- **`DAYS_USED = 0` with a recent `last_changed`** is a common false alarm:
  usage statistics are only collected when the repository is configured to gather
  them. Check `ia_repo_config` before drawing a conclusion from it.
