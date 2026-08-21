#!/usr/bin/env python3
"""Cross-version diff builder for the /ia version-comparison workflow.

Aligns the same source member across N libraries (oldest -> newest) and emits:

  * ``--emit-md``   dual-RRN unified diff hunks, ready to paste into the
                    comparison report (```diff fences, git markers in column 1).
  * ``--emit-xlsx`` a workbook whose Diff sheet lays the libraries out
                    horizontally: one row per whole change block, each library
                    cell holding that version's slice of the block, padded so
                    the cells stay line-for-line aligned. Read across to see how
                    a block evolved; blocks touched by more than one step are
                    merged into a single row that carries per-step counts.

The alignment is computed by difflib, never by hand -- the RRNs in the report
and the RRNs in the workbook come from the same computation and cannot drift.

Usage
-----
    python build_version_diff.py --program ICS100 \
        --src LIB2024=ICS100_LIB2024.txt \
        --src LIB2025=ICS100_LIB2025.txt \
        --src LIB2026=ICS100_LIB2026.txt \
        --meta ICS100_meta.json \
        --emit-md hunks.md --emit-xlsx ICS100_Version_Diff.xlsx

Source files are either ``rrn<TAB>text`` per line, or plain source (RRN = line
number).  ``--emit-meta-template`` writes a JSON skeleton listing every hunk id
so the narrative can be filled in and fed back via ``--meta``.

Requires openpyxl for --emit-xlsx (``pip install openpyxl``).
"""

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

# Diff palette.  git tints the whole row and can therefore use very dark text;
# Excel gives a rich-text run no background of its own -- one fill per cell is
# the hard limit -- so here the *text* colour carries the entire signal and has
# to survive at 9pt.  These are GitHub's foreground tones (the saturated ones it
# uses for icons and labels), not its on-tint text tones, which muddy together
# into brown at this size.  Context is deliberately muted so changes pop.
FILL_CTX = "F6F8FA"
TEXT_ADD = "1A7F37"         # added
TEXT_DEL = "CF222E"         # removed
TEXT_TRANSIENT = "BF8700"   # added/rewritten here, gone or rewritten again next
TEXT_CTX = "57606A"         # unchanged context
BRAND = "1F4E79"

ABSENT = "·"           # gutter marker for "line not present in this version"


# ── Source loading ─────────────────────────────────────────────────────


def read_source(path):
    """Return [(rrn, text), ...]. Accepts rrn<TAB>text, else RRN = line number."""
    raw = Path(path).read_text(encoding="utf-8", errors="replace").split("\n")
    if raw and raw[-1] == "":
        raw.pop()
    if raw and all(re.match(r"^\d+\t", ln) for ln in raw if ln):
        out = []
        for ln in raw:
            rrn, _, text = ln.partition("\t")
            out.append((int(rrn), text))
        return out
    return [(i + 1, ln) for i, ln in enumerate(raw)]


def key(text):
    """Comparison key: trailing blanks are not a change."""
    return text.rstrip()


# ── RPG section context (git's "@@ ... @@ funcname") ────────────────────

BEGSR_RE = re.compile(r"^\s*(?:begsr|dcl-proc)\s+([*\w]+)", re.I)
BANNER_RE = re.compile(r"^\s*//\s*-*\s*(.*?)\s*-*\**\s*$")


def section_at(lines, idx):
    """Nearest enclosing subroutine/procedure, else the nearest comment banner."""
    for i in range(idx, -1, -1):
        text = lines[i][1]
        m = BEGSR_RE.match(text)
        if m:
            return m.group(1)
        m = BANNER_RE.match(text)
        if m and m.group(1) and not set(m.group(1)) <= {"-", "*"}:
            return m.group(1).rstrip(".")
    return ""


# ── Pairwise hunks ─────────────────────────────────────────────────────


def build_hunks(old, new, context):
    """Group the non-equal opcodes into hunks padded by `context` lines."""
    ops = SequenceMatcher(
        None, [key(t) for _, t in old], [key(t) for _, t in new], autojunk=False
    ).get_opcodes()

    groups, cur = [], []
    for op in ops:
        tag, i1, i2, j1, j2 = op
        if tag == "equal":
            n = i2 - i1
            if cur:
                cur.append(("equal", i1, min(i1 + context, i2), j1, min(j1 + context, j2)))
            if n > 2 * context:
                if cur:
                    groups.append(cur)
                cur = [("equal", max(i1, i2 - context), i2, max(j1, j2 - context), j2)]
            elif not cur:
                cur = [op]
        else:
            cur.append(op)
    if cur and any(t != "equal" for t, *_ in cur):
        groups.append(cur)
    return [g for g in groups if any(t != "equal" for t, *_ in g)]


def hunk_rows(group, old, new):
    """Flatten one hunk into [(marker, old_rrn|None, new_rrn|None, text), ...]."""
    rows = []
    for tag, i1, i2, j1, j2 in group:
        if tag == "equal":
            for oi, nj in zip(range(i1, i2), range(j1, j2)):
                rows.append((" ", old[oi][0], new[nj][0], new[nj][1]))
        else:
            for oi in range(i1, i2):
                rows.append(("-", old[oi][0], None, old[oi][1]))
            for nj in range(j1, j2):
                rows.append(("+", None, new[nj][0], new[nj][1]))
    return rows


# ── Markdown emission ──────────────────────────────────────────────────


def render_md(steps, meta):
    """steps: [(prev_lib, cur_lib, [(hunk_id, group, rows), ...]), ...]"""
    hmeta = meta.get("hunks", {})
    out = []
    for prev, cur, hunks in steps:
        added = sum(1 for _, _, rows in hunks for m, *_ in rows if m == "+")
        removed = sum(1 for _, _, rows in hunks for m, *_ in rows if m == "-")
        info = hmeta.get(f"{prev}->{cur}", {})
        title = info.get("title", "changes")
        delta = f"+{added}" + (f" −{removed}" if removed else "")
        out.append(f"### {prev} → {cur}: {title} ({delta} lines)\n")
        if info.get("intro"):
            out.append(info["intro"] + "\n")
        for hid, section, rows in hunks:
            a = sum(1 for m, *_ in rows if m == "+")
            d = sum(1 for m, *_ in rows if m == "-")
            hinfo = hmeta.get(hid, {})
            sect = hinfo.get("section") or section
            parts = [f"{prev} → {cur}"] + ([sect] if sect else []) + [f"+{a} −{d}"]
            out.append("```diff")
            out.append("@@ " + " · ".join(parts) + " @@")
            for marker, orrn, nrrn, text in rows:
                o = str(orrn) if orrn else ABSENT
                n = str(nrrn) if nrrn else ABSENT
                out.append(f"{marker}{o:>5} │{n:>5} │ {text}".rstrip())
            out.append("```")
            if hinfo.get("impact"):
                out.append(f"\n**Behavioral impact:** {hinfo['impact']}\n")
            else:
                out.append("")
        out.append("")
    return "\n".join(out)


# ── N-way alignment for the workbook ───────────────────────────────────


def align_all(libs, sources):
    """Rows of {lib: line_index}; a missing lib key = line absent there.

    A ``replace`` pairs each rewritten line with its replacement on the *same*
    master row, so a modified line reads straight across the library columns
    instead of appearing as a delete two rows above its own insert.  Surplus
    lines on either side of the replace fall back to their own rows.
    """
    rows = [{libs[0]: i} for i in range(len(sources[libs[0]]))]
    for prev, cur in zip(libs, libs[1:]):
        old, new = sources[prev], sources[cur]
        ops = SequenceMatcher(
            None, [key(t) for _, t in old], [key(t) for _, t in new], autojunk=False
        ).get_opcodes()
        out, p = [], 0

        def carry_to(oi):
            nonlocal p
            while p < len(rows) and rows[p].get(prev) != oi:
                out.append(rows[p])
                p += 1

        for tag, i1, i2, j1, j2 in ops:
            if tag == "equal":
                for oi, nj in zip(range(i1, i2), range(j1, j2)):
                    carry_to(oi)
                    if p < len(rows):
                        rows[p][cur] = nj
                        out.append(rows[p])
                        p += 1
            else:
                paired = min(i2 - i1, j2 - j1) if tag == "replace" else 0
                for k, oi in enumerate(range(i1, i2)):
                    carry_to(oi)
                    if p < len(rows):
                        if k < paired:
                            rows[p][cur] = j1 + k
                        out.append(rows[p])
                        p += 1
                for nj in range(j1 + paired, j2):
                    out.append({cur: nj})
        out.extend(rows[p:])
        rows = out
    return rows


def line_state(rows, ri, libs, i, sources):
    """(marker, colour) for library libs[i] on master row ri.

    Compares this line against its counterpart in the neighbouring libraries by
    *text*, not just presence, so a rewritten line is reported as modified
    (``~``) rather than as an unrelated delete + insert.
    """
    row = rows[ri]
    text = key(sources[libs[i]][row[libs[i]]][1])

    def against(j):
        """'gap' (no counterpart), 'diff' (rewritten) or 'same'."""
        if not 0 <= j < len(libs):
            return "same"                     # no neighbour = nothing changed
        other = libs[j]
        if other not in row:
            return "gap"
        return "same" if key(sources[other][row[other]][1]) == text else "diff"

    back, fwd = against(i - 1), against(i + 1)
    new_here = back in ("gap", "diff")
    superseded = fwd in ("gap", "diff")

    if back == "gap":
        marker = "+"
    elif back == "diff" or fwd == "diff":
        marker = "~"
    elif fwd == "gap":
        marker = "-"
    else:
        marker = " "

    if new_here and superseded:
        colour = TEXT_TRANSIENT
    elif new_here:
        colour = TEXT_ADD
    elif superseded:
        colour = TEXT_DEL
    else:
        colour = TEXT_CTX
    return marker, colour


# ── Workbook ───────────────────────────────────────────────────────────


def write_xlsx(path, program, libs, sources, rows, steps, meta, context):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    mono = Font(name="Consolas", size=9)
    body = Font(name="Calibri", size=10)
    head = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    title = Font(name="Calibri", size=14, bold=True, color=BRAND)
    head_fill = PatternFill("solid", fgColor=BRAND)
    thin = Side(style="thin", color="D0D7DE")
    box = Border(left=thin, right=thin, top=thin, bottom=thin)
    top = Alignment(vertical="top", wrap_text=True)

    wb = Workbook()

    def header(ws, cols, row=1):
        for c, name in enumerate(cols, start=1):
            cell = ws.cell(row=row, column=c, value=name)
            cell.font, cell.fill, cell.border = head, head_fill, box
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.freeze_panes = ws.cell(row=row + 1, column=1)

    # ── Summary ────────────────────────────────────────────────────────
    ws = wb.active
    ws.title = "Summary"
    ws["A1"] = f"{program} — Cross-Version Diff"
    ws["A1"].font = title
    info = [
        ("Program", program),
        ("Description", meta.get("description", "")),
        ("Type", meta.get("member_type", "")),
        ("Source file", meta.get("source_file", "")),
        ("Libraries (oldest → newest)", " → ".join(libs)),
        ("Baseline", meta.get("baseline", libs[0])),
        ("Author", meta.get("author", "iA by programmers.io")),
        ("Date", meta.get("date", "")),
    ]
    r = 3
    for k, v in info:
        ws.cell(row=r, column=1, value=k).font = Font(name="Calibri", size=10, bold=True)
        ws.cell(row=r, column=2, value=v).font = body
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Version summary").font = Font(
        name="Calibri", size=11, bold=True, color=BRAND
    )
    r += 1
    header(ws, ["Library", "Total source code lines", "Δ vs prior", "Lines added",
                "Lines removed", "What changed"], row=r)
    ws.freeze_panes = None
    vmeta = {v["library"]: v for v in meta.get("versions", [])}
    prev_n = None
    step_by_cur = {cur: (prev, hunks) for prev, cur, hunks in steps}
    r += 1
    for lib in libs:
        n = len(sources[lib])
        added = removed = ""
        if lib in step_by_cur:
            _, hunks = step_by_cur[lib]
            added = sum(1 for _, _, rw in hunks for m, *_ in rw if m == "+")
            removed = sum(1 for _, _, rw in hunks for m, *_ in rw if m == "-")
        vals = [lib, n, "— (baseline)" if prev_n is None else f"{n - prev_n:+d}",
                added, removed, vmeta.get(lib, {}).get("headline", "")]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font, cell.border, cell.alignment = body, box, top
        prev_n = n
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Legend").font = Font(
        name="Calibri", size=11, bold=True, color=BRAND
    )
    r += 1
    ws.cell(row=r, column=1, value="On the Diff sheet each row is one whole change block; "
                                   "line colours inside a cell read like git. Every library "
                                   "cell in a row is padded so line 1 of one cell is line 1 "
                                   "of the next — read straight across.").font = body
    r += 1
    for sample, label, colour in (
            ("+   15      custno char(10) …", "Added in this library", TEXT_ADD),
            ("-   15      custno char(10) …", "Removed in the next library", TEXT_DEL),
            ("~   15      custno char(10) …", "Rewritten — green = the new text, "
                                              "red = the text it replaced (same row)", TEXT_ADD),
            ("+   15      custno char(10) …", "Added here, then rewritten or removed later",
             TEXT_TRANSIENT),
            ("    15      custno char(10) …", "Unchanged context", TEXT_CTX),
            ("", "Blank line = that library has no counterpart here", TEXT_CTX)):
        cell = ws.cell(row=r, column=1, value=sample)
        cell.font = Font(name="Consolas", size=9, color="FF" + colour)
        cell.fill, cell.border = PatternFill("solid", fgColor=FILL_CTX), box
        ws.cell(row=r, column=2, value=label).font = body
        r += 1

    for col, w in (("A", 30), ("B", 24), ("C", 16), ("D", 13), ("E", 15), ("F", 70)):
        ws.column_dimensions[col].width = w

    # ── Diff (side-by-side) — one whole hunk per row ───────────────────
    from openpyxl.cell.rich_text import CellRichText, TextBlock
    from openpyxl.cell.text import InlineFont

    ws = wb.create_sheet("Diff (side-by-side)")
    cols = ["Hunk", "Step", "Section", "Type", "Δ"] + list(libs) + ["Behavioral impact"]
    header(ws, cols)

    hmeta = meta.get("hunks", {})
    code_fill = PatternFill("solid", fgColor=FILL_CTX)
    block_align = Alignment(vertical="top", wrap_text=True)

    # master-row position of every (library, line index)
    pos = {(lib, idx): i for i, row in enumerate(rows) for lib, idx in row.items()}
    rrn_index = {lib: {rrn: i for i, (rrn, _) in enumerate(src)}
                 for lib, src in sources.items()}

    # One row per change block. Hunks from different steps that touch the same
    # region are merged, so a block never appears twice.
    records = []
    for prev, cur, hunks in steps:
        for hid, section, hrows in hunks:
            spans = []
            for _, orrn, nrrn, _ in hrows:
                lib, rrn = (cur, nrrn) if nrrn is not None else (prev, orrn)
                idx = rrn_index[lib].get(rrn)
                if idx is not None and (lib, idx) in pos:
                    spans.append(pos[(lib, idx)])
            if not spans:
                continue
            hinfo = hmeta.get(hid, {})
            records.append({
                "lo": min(spans), "hi": max(spans),
                "ids": [hid],
                "by_step": {f"{prev} → {cur}": [
                    sum(1 for m, *_ in hrows if m == "+"),
                    sum(1 for m, *_ in hrows if m == "-")]},
                "sections": [hinfo.get("section") or section],
                "impacts": [hinfo.get("impact", "")],
            })

    records.sort(key=lambda x: (x["lo"], x["hi"]))
    merged = []
    for rec in records:
        if merged and rec["lo"] <= merged[-1]["hi"]:
            m = merged[-1]
            m["hi"] = max(m["hi"], rec["hi"])
            for k in ("ids", "sections", "impacts"):
                m[k] += rec[k]
            # A block touched by several steps keeps its counts per step, so the
            # reader sees "inserted in 2025, then modified in 2026".
            for step, (a, d) in rec["by_step"].items():
                tot = m["by_step"].setdefault(step, [0, 0])
                tot[0] += a
                tot[1] += d
        else:
            merged.append(rec)

    def joined(values):
        seen = [v for v in dict.fromkeys(values) if v]
        return "; ".join(seen)

    def kind_of(a, d):
        return "insert" if a and not d else "delete" if d and not a else "modify"

    def run(colour, text):
        # Full-opacity ARGB ("FF…"): openpyxl pads a bare 6-digit colour with a
        # 00 alpha channel, which strict renderers treat as transparent and
        # replace with their own palette.
        return TextBlock(InlineFont(rFont="Consolas", sz=9, color="FF" + colour), text)

    out_r = 2
    for rec in merged:
        lo, hi = rec["lo"], rec["hi"]
        counts = list(rec["by_step"].values())
        for c, v in enumerate([joined(rec["ids"]),
                               "; ".join(rec["by_step"]),
                               joined(rec["sections"]),
                               "; ".join(kind_of(a, d) for a, d in counts),
                               "; ".join(f"+{a} −{d}" for a, d in counts)], start=1):
            cell = ws.cell(row=out_r, column=c, value=v)
            cell.font, cell.border, cell.alignment = body, box, top

        # One cell per library: that version's slice of the block, with a blank
        # line wherever the version has no counterpart, so the library cells
        # stay line-for-line aligned.
        for i, lib in enumerate(libs):
            blocks = []
            for ri in range(lo, hi + 1):
                if lib not in rows[ri]:
                    # Alignment padding. It gets an explicit font like every
                    # other run — a bare string run has no rPr, and renderers
                    # that don't inherit the cell font mis-colour the cell.
                    blocks.append(run(TEXT_CTX, "\n"))
                    continue
                rrn, text = sources[lib][rows[ri][lib]]
                marker, colour = line_state(rows, ri, libs, i, sources)
                blocks.append(run(colour, f"{marker}{rrn:>5}  {text}\n"))
            while blocks and str(blocks[-1]) == "\n":
                blocks.pop()
            if blocks:
                blocks[-1] = TextBlock(blocks[-1].font, str(blocks[-1]).rstrip("\n"))
            cell = ws.cell(row=out_r, column=6 + i)
            cell.value = CellRichText(blocks) if blocks else None
            cell.fill, cell.border, cell.alignment = code_fill, box, block_align
            cell.font = mono

        ic = ws.cell(row=out_r, column=len(cols), value=joined(rec["impacts"]))
        ic.font, ic.border, ic.alignment = body, box, top
        ws.row_dimensions[out_r].height = 12.6 * (hi - lo + 1)
        out_r += 1

    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{out_r - 1}"
    ws.freeze_panes = "F2"
    for col, w in (("A", 20), ("B", 20), ("C", 24), ("D", 10), ("E", 10)):
        ws.column_dimensions[col].width = w
    for i in range(len(libs)):
        ws.column_dimensions[get_column_letter(6 + i)].width = 58
    ws.column_dimensions[get_column_letter(len(cols))].width = 60

    # ── Change Log ─────────────────────────────────────────────────────
    ws = wb.create_sheet("Change Log")
    header(ws, ["Hunk", "Step", "Section", "Type", "Old lines", "New lines",
                "+", "−", "What changed", "Behavioral impact", "Risks"])
    r = 2
    for prev, cur, hunks in steps:
        for hid, section, hrows in hunks:
            a = sum(1 for m, *_ in hrows if m == "+")
            d = sum(1 for m, *_ in hrows if m == "-")
            orrns = [o for m, o, _, _ in hrows if m == "-" and o]
            nrrns = [n for m, _, n, _ in hrows if m == "+" and n]
            hinfo = hmeta.get(hid, {})
            kind = "insert" if a and not d else "delete" if d and not a else "modify"
            vals = [hid, f"{prev} → {cur}", hinfo.get("section") or section, kind,
                    f"{min(orrns)}–{max(orrns)}" if orrns else "—",
                    f"{min(nrrns)}–{max(nrrns)}" if nrrns else "—",
                    a, d, hinfo.get("what", ""), hinfo.get("impact", ""),
                    ", ".join(hinfo.get("risks", []))]
            for c, v in enumerate(vals, start=1):
                cell = ws.cell(row=r, column=c, value=v)
                cell.font, cell.border, cell.alignment = body, box, top
            r += 1
    for col, w in (("A", 20), ("B", 20), ("C", 22), ("D", 10), ("E", 12), ("F", 12),
                   ("G", 6), ("H", 6), ("I", 52), ("J", 62), ("K", 12)):
        ws.column_dimensions[col].width = w

    # ── Risks ──────────────────────────────────────────────────────────
    risks = meta.get("risks", [])
    if risks:
        ws = wb.create_sheet("Risks")
        header(ws, ["#", "Category", "Scope", "Finding"])
        for r, item in enumerate(risks, start=2):
            vals = [item.get("id", ""), item.get("category", ""),
                    item.get("scope", ""), item.get("finding", "")]
            for c, v in enumerate(vals, start=1):
                cell = ws.cell(row=r, column=c, value=v)
                cell.font, cell.border, cell.alignment = body, box, top
        for col, w in (("A", 8), ("B", 18), ("C", 20), ("D", 110)):
            ws.column_dimensions[col].width = w

    wb.save(path)


# ── Driver ─────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--program", required=True)
    ap.add_argument("--src", action="append", required=True, metavar="LIB=PATH",
                    help="repeat, oldest first")
    ap.add_argument("--meta", help="JSON narrative (sections, impact, risks)")
    ap.add_argument("--context", type=int, default=2, help="context lines (default 2)")
    ap.add_argument("--emit-md")
    ap.add_argument("--emit-xlsx")
    ap.add_argument("--emit-meta-template")
    args = ap.parse_args()

    # The report uses a real minus sign; a cp1252 console must not kill the run.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    libs, sources = [], {}
    for spec in args.src:
        lib, _, path = spec.partition("=")
        if not path:
            ap.error(f"--src expects LIB=PATH, got {spec!r}")
        libs.append(lib)
        sources[lib] = read_source(path)
    if len(libs) < 2:
        ap.error("need at least two --src versions to compare")

    meta = json.loads(Path(args.meta).read_text(encoding="utf-8")) if args.meta else {}

    steps = []
    for prev, cur in zip(libs, libs[1:]):
        old, new = sources[prev], sources[cur]
        hunks = []
        for n, group in enumerate(build_hunks(old, new, args.context), start=1):
            rws = hunk_rows(group, old, new)
            anchor = next((nrrn for _, _, nrrn, _ in rws if nrrn), None)
            idx = next((i for i, (rrn, _) in enumerate(new) if rrn == anchor), 0)
            hunks.append((f"{prev}->{cur}#{n}", section_at(new, idx), rws))
        steps.append((prev, cur, hunks))

    total_add = sum(1 for _, _, h in steps for _, _, rw in h for m, *_ in rw if m == "+")
    total_del = sum(1 for _, _, h in steps for _, _, rw in h for m, *_ in rw if m == "-")
    n_hunks = sum(len(h) for _, _, h in steps)
    print(f"{args.program}: {len(libs)} versions, {n_hunks} hunks, "
          f"+{total_add} −{total_del} lines")
    for prev, cur, hunks in steps:
        for hid, section, rws in hunks:
            a = sum(1 for m, *_ in rws if m == "+")
            d = sum(1 for m, *_ in rws if m == "-")
            print(f"  {hid:<24} {section:<24} +{a} −{d}")

    if args.emit_meta_template:
        tpl = {
            "program": args.program,
            "description": "", "member_type": "", "source_file": "",
            "baseline": libs[0], "author": "iA by programmers.io", "date": "",
            "versions": [{"library": l, "headline": ""} for l in libs],
            "hunks": {},
            "risks": [{"id": "R1", "category": "Introduced", "scope": libs[-1],
                       "finding": ""}],
        }
        for prev, cur, hunks in steps:
            tpl["hunks"][f"{prev}->{cur}"] = {"title": "", "intro": ""}
            for hid, section, _ in hunks:
                tpl["hunks"][hid] = {"section": section, "what": "", "impact": "",
                                     "risks": []}
        Path(args.emit_meta_template).write_text(
            json.dumps(tpl, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {args.emit_meta_template}")

    if args.emit_md:
        Path(args.emit_md).write_text(render_md(steps, meta), encoding="utf-8")
        print(f"wrote {args.emit_md}")

    if args.emit_xlsx:
        rows = align_all(libs, sources)
        write_xlsx(args.emit_xlsx, args.program, libs, sources, rows, steps,
                   meta, args.context)
        print(f"wrote {args.emit_xlsx}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
