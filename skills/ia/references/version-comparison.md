# Version Comparison Reference

Use this guide when a user wants to **compare multiple versions of the same program/member** — the copies that exist in different libraries (e.g. yearly source libraries `LIB2024` / `LIB2025` / `LIB2026`, or `DEV` / `TEST` / `PROD`). The deliverable is a **cross-version comparison report** focused on **what changed** and the behavioral impact of each change, optionally followed by a **detailed Excel diff workbook**.

**Trigger phrases:** "compare the versions of X", "compare X across libraries", "diff the versions of X", "what changed between the versions of X", "version comparison report for X", "how did X evolve".

---

## ⛔ Intent Routing — Compare vs Document

There is a deliberate split between two workflows that both begin by finding a member in several libraries:

| Intent | Workflow | Behavior on multiple versions |
|--------|----------|-------------------------------|
| **Document one version** ("document X", "spec for X") | [program-documentation.md](program-documentation.md) | **HARD STOP** — present the version table and ask which **single** version to document. |
| **Compare versions** ("compare the versions of X") | **this doc** | Discover every version, show the version table, then **ask which versions to include** (any subset of two or more; all is the recommended default) **and which output format(s)** the user wants — see Step 1. |

If the request is ambiguous ("look at X in all the libraries"), ask one clarifying question: *"Do you want a comparison report across the versions, or a spec for one specific version?"*

---

## ⛔ The Report Is About What CHANGED

This report is not a program spec and not an inventory. Every section must earn its place by describing a **difference**. Three hard rules:

1. **No "What Stayed the Same" section.** Do not enumerate the identical declarations, subroutines or logic. The diff hunks bound the change by construction; a change-footprint line (Step 6) states the bound in one sentence.
2. **No complexity-metrics table.** IF/DO/SELECT counts, executable-line counts, operation counts and subroutine counts do not belong in this report. If a metric genuinely changed *because of* a change, state it inline in that change's prose.
3. **The Side-by-Side matrix carries only rows that differ.** Drop any aspect whose value is the same in every library ("Files used", "Subroutines: 17 / 17 / 17"). A row that reads the same across all columns is noise.

Observations & Risks stays — it is the analytical payload.

---

## Step 1 — Discover Every Version

One call:

```
ia_member_lookup(member_name=X)     # source_library defaults to *ALL
```

This returns one row per library where the member exists, with `SOURCE_LIBRARY`, `SOURCE_FILE`, `MEMBER_TYPE`, total / comment / blank line counts, and the change date/time.

- **Zero rows** → the member does not exist (Rule Two). Report the negative; suggest `ia_object_lookup('%X%')`.
- **One row** → only one version exists — there is nothing to compare. Tell the user, and offer program documentation instead.
- **Two or more rows** → **show the user the full version list first** (every library, its total source code lines, and change date), then **stop and ask two questions in one interaction** before retrieving any source:
  1. **Which versions should the comparison include?** Offer **all versions** as the recommended default; the user may pick any subset of **two or more**. If they pick only one, that is the *documentation* workflow — see Intent Routing. Never silently drop a version from the set the user chose.
  2. **Which format(s) do they want the final report in?** Offer **Markdown (`.md`)**, **Word (`.docx`)**, **PDF**, and the **side-by-side Excel diff workbook** (libraries laid out horizontally, one row per change block, colored git-style, changed parts only — see Step 8). More than one is fine. Recommend **Word** for the readable report — its converter colors the diff hunks, while PDF renders them as plain monospace. The `.md` is always written regardless, since it is the canonical copy the other formats are generated from.

  Do not start the comparison until both answers are in.

---

## Step 2 — Order the Versions and Pick the Baseline

- Sort the versions **oldest → newest** by change date.
- The **oldest** version is the **baseline** — usually the **bottom library** in the list (e.g. `LIB2024` under `LIB2025` under `LIB2026`). Compare everything forward from there.
- If change dates are missing or tie, fall back to library sort order (**bottom = baseline**) and say so. When the timestamps are unreliable (e.g. all members loaded into the repository in the same batch), order by **content containment** instead and state that in the report.
- **State the baseline assumption explicitly** — e.g. *"Baseline = LIB2024 (oldest version, changed 2024-…)."*

---

## Step 3 — Retrieve Each Version's Source

Route by `MEMBER_TYPE` from Step 1 (all versions share the same type):

| MEMBER_TYPE | Tool |
|-------------|------|
| `RPGLE`, `SQLRPGLE`, `RPG`, `SQLRPG` | `ia_rpg_source(member_name=X, library_name=L)` |
| `CLLE`, `CLP`, `CL` | `ia_cl_source(member_name=X, library_name=L)` |

Fetch once per version, passing that version's `library_name`. Apply the standard pagination rule (loop `offset` in 10,000-line pages if the member exceeds 10,000 lines).

Write each version to a working file, **one source line per line, in `SOURCE_RRN` order**:

```
{scratch}/{PROGRAM}_{LIBRARY}.txt
```

Plain source text is fine when RRNs run 1..N (the normal case). If RRNs are sparse, write `rrn<TAB>text` instead — the diff builder accepts both.

---

## Step 4 — Compute the Diff with the Bundled Builder

**Never hand-author the diff.** Hand-typed line numbers drift, and the report and the workbook then disagree. Run the builder once; it computes the alignment with `difflib` and emits both artifacts from that single computation.

```bash
python .claude/skills/ia/scripts/build_version_diff.py \
    --program ICS100 \
    --src LIB2024={scratch}/ICS100_LIB2024.txt \
    --src LIB2025={scratch}/ICS100_LIB2025.txt \
    --src LIB2026={scratch}/ICS100_LIB2026.txt \
    --emit-meta-template {scratch}/ICS100_meta.json \
    --emit-md {scratch}/ICS100_hunks.md
```

`--src` is repeated **oldest first**. The run prints every hunk it found with an id (`LIB2025->LIB2026#1`) and an auto-derived section name, and writes a `--emit-meta-template` JSON skeleton keyed by those ids.

**Two-pass flow:**

1. **Pass 1** — run as above. Read the hunks. Fill in the meta JSON: per-step `title` / `intro`, per-hunk `section` (override the auto-derived guess — it is only the nearest `BegSr`/comment banner), `what`, `impact`, `risks`, plus the top-level `description` / `member_type` / `source_file` / `baseline` / `date` / `versions[].headline` / `risks[]`.
2. **Pass 2** — re-run with `--meta {scratch}/ICS100_meta.json` plus `--emit-md` and (when the user chose Excel in Step 1) `--emit-xlsx`.

Options: `--context N` sets context lines each side of a change (**default 2** — keep it).

---

## Step 5 — The Diff Hunk Format

The builder emits ```` ```diff ```` fences that render green/red natively in Markdown viewers **and** in the Word export (the docx converter has a dedicated `diff` renderer). Do not reformat them.

```diff
@@ LIB2025 → LIB2026 · Main Processing Logic · +5 −0 @@
    72 │   72 │ PGMNAME = PgmDS.PgmName;
    73 │   73 │
+    · │   74 │ if %parms = 1;
+    · │   75 │    KCUSTID = %trim(custno);
     74 │   79 │ DoU EXIT = *On;
```

- **Column 1 is the git marker** — `+` added, `−`/`-` removed, space unchanged. It must stay in column 1 or Markdown highlighters lose the colors.
- **Dual gutter** — old library RRN `│` new library RRN. `·` means the line does not exist in that version.
- **Hunk header** names the enclosing RPG section, the way git shows function context.
- **Two lines of real code before and after** every change, so a reviewer sees where it landed.

For each hunk write a one-line **behavioral impact** — what the program now does differently, or "none — preparatory". Distinguish a *declared-but-unused* addition from one actually wired into the logic.

---

## Step 6 — Assemble the Report

Follow **Report Structure** below and apply every rule in **Report-Writing Conventions**. Paste the builder's hunks verbatim into the Change Timeline.

**Change footprint** — one line in the Executive Summary, replacing any "what stayed the same" prose. Derive the numbers from the builder's summary line:

> **Change footprint:** 3 hunks · +12 −0 lines · 2.7% of the 448-line member touched · 0 subroutines, 0 files and 0 screens added or removed.

---

## Step 7 — Save and Export

- **Save target (single canonical copy):**
  ```
  docs/program-specs/{PROGRAM_NAME}/{PROGRAM_NAME}_Version_Comparison.md
  ```
  Create the folder if needed. One copy per program — overwrite in place on a re-run. (This is a distinct deliverable from the five canonical spec DocTypes; it is **not** subject to the program-documentation Step 1.5 gate.)
- **Export** to whichever of Word/PDF the user chose in Step 1, via the bundled converters (`scripts/convert_md_to_docx.py` / `convert_md_to_pdf.py`), written alongside the `.md`. Do not generate formats the user didn't ask for. (The docx converter colors `diff` fences; the PDF converter renders them as plain monospace — which is why Word is the recommended choice.)

---

## Step 8 — Build the Detailed Excel (when requested)

The Excel workbook is chosen **up front**, in the Step 1 format question — do not ask about it again after the report is saved. If the user selected it, re-run the builder with `--meta` and `--emit-xlsx`; if they didn't, skip this step entirely:

```bash
python .claude/skills/ia/scripts/build_version_diff.py \
    --program ICS100 \
    --src LIB2024=… --src LIB2025=… --src LIB2026=… \
    --meta {scratch}/ICS100_meta.json \
    --emit-xlsx docs/program-specs/ICS100/ICS100_Version_Diff.xlsx
```

The workbook (requires `pip install openpyxl`) has four sheets:

| Sheet | Contents |
|-------|----------|
| **Summary** | Program header, per-library line counts and Δ, lines added/removed per step, color legend. |
| **Diff (side-by-side)** | The horizontal view: **one row per change block** — a whole diff block per row, never one row per source line. One column per library holds that version's slice of the block (context plus whatever that version has), RRN-prefixed, one source line per line inside the cell. Lines are colored individually via rich text — see the marker table below. A **blank line** means the version has no counterpart there, which keeps all library cells aligned line-for-line, so line *n* of one cell is line *n* of every other. Frozen header and metadata columns, autofilter on hunk / step / section / type. |
| **Change Log** | One row per hunk: step, section, type, old/new line ranges, ± counts, what changed, behavioral impact, risk refs. |
| **Risks** | The Observations & Risks table, split into Introduced vs Pre-existing. |

Save it next to the `.md` as `{PROGRAM_NAME}_Version_Diff.xlsx`.

### Reading a Diff-sheet cell

| Marker | Colour | Means |
|--------|--------|-------|
| `+` | green | added in this library and it survives |
| `~` | green | **rewritten** in this library — this is the new text |
| `~` | red | superseded in the next library — this is the text that was replaced |
| `-` | red | removed in the next library |
| `+` / `~` | amber | added or rewritten here, then rewritten or removed again later — this exact text existed only in this version |
| *(space)* | grey | unchanged context |
| *(blank line)* | — | this library has no counterpart at that position |

A **rewritten line and its replacement share one row**, so you read the before and after straight across the library columns — this is the one place the workbook deliberately departs from git, which would show a rewrite as a `-` line followed by an unrelated-looking `+` line. Markdown hunks keep the git form.

**A block changed by more than one step is a single row, not one row per step.** The `Step`, `Type` and `Δ` columns then carry a `;`-separated entry per step, in order, so `insert; modify` with `+6 −0; +4 −2` reads as *"inserted in the first step, then modified in the second."* Left as separate rows the same block would appear twice with near-identical content.

> **Hunk ids are positional.** `LIB2025->LIB2026#1` means "the first hunk of that step" — if the source changes and a new hunk appears earlier in the member, every later id shifts and the meta narrative silently attaches to the wrong hunk. Re-run pass 1 and re-check the ids whenever the source files change.

---

## Report-Writing Conventions (non-negotiable)

1. **"Total source code lines", not "Lines".** The line-count column header reads **Total source code lines**. Never just "Lines".
2. **Identify versions by library name, never by year.** Columns and row labels use the **library name** (`LIB2024`, `PRODLIB`, …). A year may appear as descriptive context; the identifying label is always the library.
3. **Every diff carries source line numbers.** The builder's dual-RRN gutter satisfies this. A diff without line numbers is incomplete.
4. **Say "Main Processing Logic", not "Mainline".** Match the section name used in program documentation.
5. **Prefer "usage" over "reference" for variables/parameters/fields** — *"declared but no usage"*, not *"declared but not referenced"*.
6. **State the baseline** up front, so every "added / removed / changed" is unambiguous.
7. **No "What Stayed the Same" section and no complexity table** — see the rules block above.

**Branding:** `Author: iA by programmers.io`. First mention "iA by programmers.io", thereafter "iA". Close with *"Prepared with iA by programmers.io."*

---

## Report Structure

Scale depth to the number of versions; with only two versions the "progressive" timeline collapses to a single baseline-vs-new diff.

```markdown
# {PROGRAM} — Cross-Version Comparison Report

**Program:** {PROGRAM} ({alt name / description if in source header})
**Type:** {MEMBER_TYPE}
**Source file:** {SOURCEPF}
**Libraries compared:** {LIB_A} · {LIB_B} · {LIB_C}   (oldest → newest)
**Baseline:** {LIB_A} — {why}
**Author:** iA by programmers.io
**Date:** {YYYY-MM-DD}

## 1. Executive Summary
- One or two sentences: what the program does.
- The theme of the changes across versions.
- Summary table — one row per version, ordered oldest → newest:

  | Library | Total source code lines | Δ vs prior | What changed |
  |---------|------------------------:|:----------:|--------------|
  | {LIB_A} | {n} | — (baseline) | Baseline. … |
  | {LIB_B} | {n} | +{d} | … |
  | {LIB_C} | {n} | +{d} | … |
- **Change footprint:** {h} hunks · +{a} −{r} lines · {pct}% of the {n}-line member
  touched · {what categories were not added or removed}.
- Net effect statement.

## 2. Change Timeline (progressive)
For each adjacent pair, oldest → newest:
### {LIB_A} → {LIB_B}: <short title> (+{n} lines)
<builder-emitted ```diff hunk, verbatim>
**Behavioral impact:** <what changed at runtime, or "none — preparatory">
### {LIB_B} → {LIB_C}: <short title> (+{n} lines)
- …

## 3. Side-by-Side (differences only)
One column per **library**. Include only aspects whose value differs somewhere:

| Aspect | {LIB_A} | {LIB_B} | {LIB_C} |
|--------|---------|---------|---------|
| … | … | … | … |

## 4. Observations & Risks
### Introduced by these changes
| # | Version | Finding |
### Pre-existing items (present in all versions — informational, not regressions)
| # | Finding |

## 5. Conclusion
- One-line evolution summary (baseline → … → latest).
- The follow-ups worth raising.

*Prepared with iA by programmers.io.*
```

---

## Common Traps

| Trap | Fix |
|------|-----|
| Starting the comparison without asking which versions and which formats | Step 1 requires showing the version table, then asking for the version set (default: all) **and** the output format(s) (.md / Word / PDF / Excel) before any source is retrieved. |
| Asking the user to pick a **single** version | That's the *documentation* workflow. A comparison needs at least two versions — see Intent Routing. |
| Writing a "What Stayed the Same" section | Removed by design. Use the one-line change footprint instead. |
| Including a complexity-metrics table | Removed by design. Mention a metric only when a change caused it to move. |
| Side-by-Side rows identical in every column | Delete them. The matrix shows differences only. |
| Hand-typing the diff and its line numbers | Run `build_version_diff.py`. Hand-typed RRNs drift and desync the report from the workbook. |
| Reformatting the builder's `diff` fences | Leave the marker in column 1 and the dual gutter intact, or the colors break in Markdown and Word. |
| Trusting the auto-derived hunk section name | It is the nearest `BegSr`/comment banner — often a stale header. Override it in the meta JSON. |
| Labelling columns/rows by year | Use the **library name**; iA tracks libraries, not calendar years. |
| Calling a declared-but-unused addition a "feature" | Separate *declared* from *wired in*. Note when a parameter/field has no usage yet. |
| Not naming the baseline | State the oldest/bottom library as baseline up front. |
| Treating a constant, cross-version issue as a regression | Put unchanged issues under "Pre-existing items", clearly informational. |
| Asking about the Excel after the report is saved | Formats — including the Excel — are chosen up front in the Step 1 question. Build what was chosen; don't re-ask. |
| Saying "Mainline" / "not referenced" | Use "Main Processing Logic" and "usage". |
