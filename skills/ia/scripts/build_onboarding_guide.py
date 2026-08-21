#!/usr/bin/env python3
"""Render a New-Developer Onboarding Guide markdown report into Excel.

The markdown written by the /ia skill is the source of truth; this script only
reformats it, so the workbook always agrees with what the user read on screen.
It never queries the repository.

Unlike build_context_matrix.py — which mirrors whatever sections it finds — this
one knows the guide's shape and flattens it into four sheets a reader can filter:

    Menu Options            the option -> program table
    Program -> File         every per-program file table, with a Program column
    Shared Data             the shared-file matrix
    Program Stats           the stats line under each program heading

Sections are found by keyword, not by number, so renumbering the guide's
headings does not break the build.

Requires:  pip install openpyxl
Usage:     python build_onboarding_guide.py GUIDE.md [--outdir DIR]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_context_matrix import is_divider, split_row, strip_md  # noqa: E402

# "### CUSTMNTR — Customer maintenance" → name, role. An en/em dash or a hyphen
# all appear in practice depending on who edited the guide.
_PGM_HEADING = re.compile(r"^([A-Z0-9#@$]{1,10})\s*[-–—]\s*(.*)$")
# "`RPGLE` · 288 exec lines · 17 subroutines · … · source `QRPGLESRC/CUSTMNTR`"
_STAT = re.compile(r"(\d+)\s+(exec lines|subroutines|procedures|SQL statements)")
_ATTR = re.compile(r"^`([^`]+)`")
_SOURCE = re.compile(r"source\s+`([^`]+)`")
STAT_COLUMNS = ["exec lines", "subroutines", "procedures", "SQL statements"]


def read_tables(md_path: Path) -> tuple[str, list[dict]]:
    """Return (title, blocks) where each block is one heading and its tables.

    A block is {level, heading, tables, lines}: `lines` keeps the prose under the
    heading so the stats line can be recovered without a second pass.
    """
    lines = md_path.read_text(encoding="utf-8").splitlines()
    title = md_path.stem.replace("_", " ")
    blocks: list[dict] = []
    current: dict | None = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("# ") and not line.startswith("##"):
            title = strip_md(line[2:])
            i += 1
            continue

        # "### X" does not start with "## " — the third character is a hash, not
        # a space — so the deeper heading must be tested first and separately.
        if line.startswith("### ") or line.startswith("## "):
            level = 3 if line.startswith("### ") else 2
            text = line[4:] if level == 3 else line[3:]
            current = {"level": level, "heading": strip_md(text),
                       "tables": [], "lines": []}
            blocks.append(current)
            i += 1
            continue

        if line.startswith("|") and i + 1 < len(lines) and is_divider(lines[i + 1]):
            header = [strip_md(c) for c in split_row(line)]
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not is_divider(lines[i]):
                    rows.append([strip_md(c) for c in split_row(lines[i])])
                i += 1
            width = len(header)
            rows = [(r + [""] * width)[:width] for r in rows]
            if current is not None and rows:
                current["tables"].append({"header": header, "rows": rows})
            continue

        if line and current is not None:
            current["lines"].append(line)
        i += 1

    return title, blocks


def find(blocks: list[dict], *keywords: str) -> dict | None:
    """First level-2 block whose heading mentions every keyword."""
    for b in blocks:
        low = b["heading"].lower()
        if b["level"] == 2 and all(k in low for k in keywords):
            return b
    return None


def program_blocks(blocks: list[dict]) -> list[dict]:
    """Level-3 blocks under the Program details heading."""
    out: list[dict] = []
    inside = False
    for b in blocks:
        if b["level"] == 2:
            inside = "program detail" in b["heading"].lower()
            continue
        if inside:
            out.append(b)
    return out


def relations(pgms: list[dict]) -> tuple[list[str], list[list[str]]]:
    """Flatten every per-program file table into one sheet."""
    header = ["Program", "File", "Type", "Over", "Access", "Purpose"]
    rows: list[list[str]] = []
    for b in pgms:
        m = _PGM_HEADING.match(b["heading"])
        name = m.group(1) if m else b["heading"]
        for table in b["tables"]:
            # Index the source columns by name so a guide that adds or reorders
            # a column still lands in the right place.
            idx = {h.lower(): n for n, h in enumerate(table["header"])}
            for r in table["rows"]:
                def cell(key: str) -> str:
                    at = idx.get(key)
                    return r[at] if at is not None and at < len(r) else ""
                rows.append([name, cell("file"), cell("type"), cell("over"),
                             cell("access"), cell("purpose")])
    return header, rows


def stats(pgms: list[dict]) -> tuple[list[str], list[list[str]]]:
    header = ["Program", "Role", "Attribute", *STAT_COLUMNS, "Source"]
    rows: list[list[str]] = []
    for b in pgms:
        m = _PGM_HEADING.match(b["heading"])
        name, role = (m.group(1), m.group(2)) if m else (b["heading"], "")
        # The stats line opens with the attribute in backticks and names the
        # source member. Keying on "exec lines" instead would drop every CL
        # program — CL members carry no complexity row, so they have no such
        # count, but they still have an attribute and a source member.
        line = next((l for l in b["lines"]
                     if _ATTR.match(l) and _SOURCE.search(l)), "")
        found = {label: value for value, label in _STAT.findall(line)}
        attr = _ATTR.match(line)
        source = _SOURCE.search(line)
        rows.append([name, role,
                     attr.group(1) if attr else "",
                     *(found.get(c, "") for c in STAT_COLUMNS),
                     source.group(1) if source else ""])
    return header, rows


def write_xlsx(out: Path, title: str, sheets: list[tuple[str, list[str], list[list[str]]]]) -> None:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        sys.exit("openpyxl is required:  pip install openpyxl")

    wb = Workbook()
    head_fill = PatternFill("solid", fgColor="1F3864")
    head_font = Font(bold=True, color="FFFFFF")

    ws = wb.active
    ws.title = "Overview"
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14)
    ws["A3"] = "Generated"
    ws["B3"] = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    ws["A4"] = "Author"
    ws["B4"] = "iA by programmers.io"
    ws["A6"] = "Sheet"
    ws["B6"] = "Rows"
    for c in ("A6", "B6"):
        ws[c].font = head_font
        ws[c].fill = head_fill
    for n, (name, _, rows) in enumerate(sheets, start=7):
        ws.cell(row=n, column=1, value=name)
        ws.cell(row=n, column=2, value=len(rows))
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 10

    for name, header, rows in sheets:
        s = wb.create_sheet(name)
        s.append(header)
        for c in range(1, len(header) + 1):
            s.cell(row=1, column=c).font = head_font
            s.cell(row=1, column=c).fill = head_fill
        for r in rows:
            s.append(r)
        s.freeze_panes = "A2"
        if rows:
            s.auto_filter.ref = f"A1:{get_column_letter(len(header))}{len(rows) + 1}"
        for c, col in enumerate(header, start=1):
            longest = max([len(col)] + [len(str(r[c - 1])) for r in rows] or [len(col)])
            s.column_dimensions[get_column_letter(c)].width = min(max(longest + 2, 10), 60)
            if col.lower() in ("purpose", "role", "why it matters", "what it does"):
                for r in range(2, len(rows) + 2):
                    s.cell(row=r, column=c).alignment = Alignment(wrap_text=True)

    wb.save(out)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("markdown", help="the Onboarding Guide .md report")
    ap.add_argument("--outdir", help="output directory (default: beside the .md)")
    args = ap.parse_args()

    src = Path(args.markdown)
    if not src.is_file():
        return err(f"not found: {src}")

    title, blocks = read_tables(src)
    pgms = program_blocks(blocks)
    if not pgms:
        return err(f"no '### ' program sections under a 'Program details' heading "
                   f"in {src.name} — is this an Onboarding Guide?")

    sheets: list[tuple[str, list[str], list[list[str]]]] = []

    options = find(blocks, "menu option")
    if options and options["tables"]:
        t = options["tables"][0]
        sheets.append(("Menu Options", t["header"], t["rows"]))

    header, rows = relations(pgms)
    sheets.append(("Program to File", header, rows))

    shared = find(blocks, "shared data")
    if shared and shared["tables"]:
        t = shared["tables"][0]
        sheets.append(("Shared Data", t["header"], t["rows"]))

    sheets.append(("Program Stats", *stats(pgms)))

    outdir = Path(args.outdir) if args.outdir else src.parent
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{src.stem}.xlsx"
    write_xlsx(out, title, sheets)

    print(f"{src.name}: {len(pgms)} programs, {len(rows)} file relations")
    for name, _, r in sheets:
        print(f"  {name}: {len(r)} rows")
    print(f"  xlsx -> {out}")
    return 0


def err(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
