# Cross-Library Member Comparison

Use this when the question is about the **whole repository**, not one program:
*"which members differ between our libraries?"*, *"is this application the same in
2024, 2025 and 2026?"*, *"what diverged between dev and prod?"*

> Not the same as [version-comparison.md](version-comparison.md). That one diffs
> **one member** line by line across the libraries holding it. This one answers
> **"which members are worth diffing at all"** across the entire repository, and
> hands you the shortlist. Normal order: this first, then version-comparison on
> what it flags.

---

## 1. What it rests on

Cross-library source fingerprints the repository build must already have
produced — two SHA-256 hashes per member per library, one over the source
verbatim and one over code lines only, normalized — plus the ranking and verdict
that `ia_member_variants` and `ia_variant_summary` read.

**If `ia_variant_summary` returns nothing, stop and say so.** The tools will
return nothing and the workbook will be empty; that is a deployment gap in the
repository build, not an analysis result.

### The four verdicts

| Verdict | Meaning | What to do |
|---------|---------|------------|
| `SINGLE` | One copy only | Nothing to compare |
| `IDENTICAL` | Byte-for-byte the same in every library | Safe |
| `COSMETIC` | Differs only in comments, blank lines, trailing blanks, free-form indentation or case | Ignore |
| `LOGIC` | **The code itself differs** | The shortlist — this is what people act on |

---

## 2. Workflow

Two entry points, and they take different routes. Pick one before you call anything.

### Asked for a **report / workbook / comparison document** — exactly three steps

```
1. ia_variant_summary()                  → non-empty? proceed. Empty → §1, stop
2. python build_member_diff.py --out …   → exit 0 = no data-quality blockers
3. read Overview + Members from the .xlsx (openpyxl) and narrate from that
```

Nothing else. In particular, on this path do **not**:

- call `ia_member_variants` — the script pulls those rows itself and writes them
  to the Members sheet. Calling it first buys the same shortlist twice, once into
  the context and once into the workbook
- go looking for the underlying fingerprint objects — step 1 returning rows
  already proves they exist and are populated. That check belongs in the
  *diagnostic for when step 1 comes back empty*, not in a pre-flight
- hand-check the fingerprints for empty or duplicated hashes — the script's
  data-quality block does exactly that and **exits 1** on a blocker. Read its
  Overview findings instead of re-deriving them (and the column is `NORM_HASH`,
  not `CODE_HASH`)

The script is the report tier because it keeps tens of thousands of rows out of
the conversation. Investigating by hand first spends the context the script exists
to save.

### Asked a **question** about divergence — query directly, no workbook

```
ia_variant_summary()                      → the shape of the problem
ia_member_variants()                      → defaults to LOGIC only: the shortlist
ia_member_variants(member_name='X',
                   verdict='*ALL')        → one member, every library
```

Then, for anything on the LOGIC shortlist that matters, drop into
[version-comparison.md](version-comparison.md) to see the actual line changes.

**Never call `ia_member_variants(verdict='*ALL')` just to look around** — on a real
repository that is tens of thousands of rows into the context for no benefit. The
summary tool already tells you the totals. Use `*ALL` only for a named member.

---

## 3. The workbook

```
python .claude/skills/ia/scripts/build_member_diff.py \
       [--url http://localhost:3010/mcp] [--out FILE] [--member-type RPGLE]
```

Requires `pip install openpyxl` and a running MCP server. The script pulls every
member+library row over the MCP HTTP endpoint itself — **do not** pull those rows
into the conversation and hand them over; that is the whole reason the report tier
is a script. Three sheets:

1. **Overview** — run metadata, verdict distribution, and data-quality findings
2. **Members** — one row per member, one column per library, variant label in the
   cell. Three explanatory notes sit above the header; the header row and the
   member column are frozen. Autofilter on; filter Verdict = LOGIC for the shortlist
3. **Detail** — one row per member+library copy, with line counts and hash prefixes

Member-level columns, and what they actually mean:

| Column | Meaning |
|--------|---------|
| `Member Type Differs` | The member is a different type in different libraries (`CLP` here, `CLLE` there). Grouping is by name alone, so converted programs are flagged rather than split apart |
| `Source File Differs` | The copies sit in different source physical files. Can also mean two unrelated members share a name — check the source file in Detail before concluding |
| `Max Source Lines` | Verbatim line count of the **longest** copy, comments and blanks included. Reduce across the copies — the first row read is whichever library sorted first, not the longest |
| `Line Count Delta` | Longest copy minus shortest. Length only — **not** a measure of sameness |

`Line Count Delta` = 0 does **not** mean the copies are identical: lines changed in
place keep the count the same. Read `Verdict` for sameness. The reverse pairing is
the useful one — `IDENTICAL` with a delta above 0 is self-contradictory and is
raised as a blocker.

Default output `member-diff-YYYYMMDD.xlsx`; for a client deliverable write it to
`docs/reports/`.

---

## 4. Read the data-quality block before you believe anything

The script checks the fingerprints for self-contradiction and writes findings to
the top of the Overview sheet. It **exits 1** when it finds a blocker. Report
blockers to the user rather than narrating the verdicts as if they were sound:

| Finding | What it means |
|---------|---------------|
| Every `EXACT_HASH` is `e3b0c44298fc...` | That is the SHA-256 of the **empty string**. The hash routine is opened and closed but never fed any data, so every member looks identical to every other. Every verdict is meaningless. Report it and rebuild the fingerprints |
| All members share one hash | Same conclusion — distinct source cannot share a fingerprint |
| Reported `IDENTICAL` but line counts differ | A direct contradiction, and the cheapest proof the hashes are wrong |
| Only one library has fingerprints | Nothing to compare; every member can only be `SINGLE`. At least two libraries must be fingerprinted |

A wrong report that looks right is worse than no report, so these are surfaced
loudly and never smoothed over.

---

## 5. Interpretation notes

- **Grouping is by member name alone.** A program that is `CLP` in one library and
  `CLLE` in another is still the same program and still compares. `TYPE_DRIFT`
  and `PF_DRIFT` flag those cases instead of splitting them apart — so a `Y` in
  `PF_DRIFT` can also mean two genuinely unrelated members happen to share a name.
  Check the source file in the Detail sheet before concluding.
- **Variant labels are `Base`, `v1`, `v2`, …** — `Base` is the version most
  libraries share, and each further distinct version gets the next number, so a
  member reads as a version history rather than as arbitrary letters. The
  underlying data still ranks them `A`, `B`, `C`; the script relabels them so a
  member reads as a version history.
- **Labels are deterministic**: most-shared hash first, ties broken by earliest
  change timestamp, then library name. Two runs over an unchanged repository
  produce the same labels. If they move between runs, something is wrong
  upstream.
- **Case-folding is deliberate.** A member differing only in the case of a literal
  shows as `COSMETIC` with two exact variants — visible, but not escalated.
- There is no ceiling on the labels — a member with 40 distinct versions runs to
  `v39`, where the old lettering had to fall back to `V27` past the alphabet.
