#!/usr/bin/env python3
"""Build the cross-library member comparison workbook.

Pulls every member+library row from the iA MCP server over HTTP (never a direct
Db2 connection — that reuses the existing credential path and keeps one access
route to the repository) and writes a three-sheet Excel workbook:

  1. Overview  — run metadata, verdict distribution, data-quality checks
  2. Members   — one row per member, one column per library (the deliverable)
  3. Detail    — one row per member+library copy

The point of doing this in a script rather than through the model is context:
a 10,000-member / 6-library repository is ~60,000 rows. The script moves them;
the model only ever sees the small summary.

Rows come from ia_member_variants and ia_variant_summary.

Requires:  pip install openpyxl
Usage:     python build_member_diff.py [--url URL] [--out FILE] [--limit N]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import urllib.error
import urllib.request
from collections import OrderedDict, defaultdict

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("openpyxl is required:  pip install openpyxl")

DEFAULT_URL = "http://localhost:3010/mcp"

# SHA-256 of the empty string. If every fingerprint equals this, the hash
# routine never received any data and the whole report is meaningless.
EMPTY_SHA256_12 = "e3b0c44298fc"

VERDICT_ORDER = {"LOGIC": 0, "COSMETIC": 1, "IDENTICAL": 2, "SINGLE": 3}

# ── palette ────────────────────────────────────────────────────────────────
C_HEAD = "1F3B57"
C_BAND = "F2F5F8"
FILL_LOGIC = PatternFill("solid", fgColor="F8CBCB")
FILL_COSMETIC = PatternFill("solid", fgColor="FDE9C4")
FILL_IDENTICAL = PatternFill("solid", fgColor="D7EFD9")
FILL_SINGLE = PatternFill("solid", fgColor="E8EAED")
FILL_WARN = PatternFill("solid", fgColor="FFF3CD")
FILL_BAD = PatternFill("solid", fgColor="F8CBCB")
FILL_OK = PatternFill("solid", fgColor="D7EFD9")
VERDICT_FILL = {
    "LOGIC": FILL_LOGIC,
    "COSMETIC": FILL_COSMETIC,
    "IDENTICAL": FILL_IDENTICAL,
    "SINGLE": FILL_SINGLE,
}
THIN = Side(style="thin", color="D6DBE0")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


# ── MCP transport ──────────────────────────────────────────────────────────
def mcp_texts(url: str, tool: str, args: dict) -> list[str]:
    """Call one MCP tool and return its text content blocks.

    Transport and error handling only — the two callers disagree about the
    payload format, so parsing is left to them.
    """
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    })
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            raw = r.read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        sys.exit(f"cannot reach the MCP server at {url}: {e}\n"
                 "Start the iA MCP server first, then retry.")

    payload = None
    for line in raw.splitlines():          # SSE framing
        if line.startswith("data:"):
            payload = json.loads(line[5:].strip())
            break
    if payload is None:
        payload = json.loads(raw)

    if "error" in payload:
        sys.exit(f"{tool} failed: {payload['error']}")

    result = payload.get("result", {})
    texts = [c.get("text", "") for c in result.get("content", [])
             if c.get("type") == "text"]

    # The server reports tool-level problems (validation errors, SQL errors) as
    # an isError result carrying a plain-text message. Never treat that as
    # "no rows" — an empty report that should have been an error is far worse
    # than a crash.
    if result.get("isError"):
        sys.exit(f"{tool} returned an error:\n  " + "\n  ".join(texts)[:1500])
    if not texts:
        sys.exit(f"{tool} returned no usable content")
    return texts


def mcp_call(url: str, tool: str, args: dict) -> list[dict]:
    """Call an ia_* tool, which answers with a strict JSON envelope."""
    for text in mcp_texts(url, tool, args):
        try:
            doc = json.loads(text)
        except json.JSONDecodeError:
            sys.exit(f"{tool} returned a non-JSON response (treating as failure):\n"
                     f"  {text[:1500]}")
        if isinstance(doc, dict):
            if not doc.get("success", True):
                sys.exit(f"{tool} returned failure: {json.dumps(doc)[:800]}")
            return doc.get("data", []) or []
    sys.exit(f"{tool} returned no usable content")


# ── variant labelling ──────────────────────────────────────────────────────
BASE_LABEL = "Base"


def variant_label(rank: int) -> str:
    """Base for the prevailing version, then v1, v2, v3 for each divergence.

    Reads as a version history rather than as an arbitrary letter, and needs no
    special case past 26 the way A..Z did.
    """
    return BASE_LABEL if rank <= 1 else f"v{rank - 1}"


def _rank_from_letter(value) -> int | None:
    """Recover a rank from the A, B, C ... V27 labels the views produce."""
    if value is None:
        return None
    text = str(value).strip()
    if len(text) > 1 and text[0] in "Vv" and text[1:].isdigit():
        return int(text[1:])
    if len(text) == 1 and text.isalpha():
        return ord(text.upper()) - 64
    return None


def normalize_variants(detail: list[dict]) -> list[dict]:
    """Put both data paths on the same labels.

    The direct read supplies a numeric rank; the views supply letters. Reducing
    them here means the workbook is identical whichever route produced it.
    """
    for r in detail:
        for rank_key, label_key in (("VARIANT_RANK", "VARIANT"),
                                    ("NORM_VARIANT_RANK", "NORM_VARIANT")):
            rank = r.get(rank_key)
            if rank is None:
                rank = _rank_from_letter(r.get(label_key))
            if rank is not None:
                r[label_key] = variant_label(rank)
    return detail


def summarize(detail: list[dict]) -> list[dict]:
    """Roll the detail rows up per verdict.

    Derived from the same rows the sheets are built from rather than from a
    second query, so the Overview can never disagree with the Members sheet.
    """
    members: dict[str, dict] = {}
    for r in detail:
        members.setdefault(r["MEMBER_NAME"], r)

    groups: dict[str, list[str]] = defaultdict(list)
    for name, meta in members.items():
        groups[meta.get("VERDICT")].append(name)

    out = []
    for verdict, names in groups.items():
        rows = [r for r in detail if r["MEMBER_NAME"] in set(names)]
        changed = [str(r.get("MEMBER_CHANGED")) for r in rows if r.get("MEMBER_CHANGED")]
        stamped = [str(r.get("FINGERPRINTED")) for r in rows if r.get("FINGERPRINTED")]
        out.append({
            "VERDICT": verdict,
            "MEMBER_COUNT": len(names),
            "COPY_COUNT": len(rows),
            "TYPE_DRIFT_COUNT": len({r["MEMBER_NAME"] for r in rows
                                     if r.get("TYPE_DRIFT") == "Y"}),
            "PF_DRIFT_COUNT": len({r["MEMBER_NAME"] for r in rows
                                   if r.get("PF_DRIFT") == "Y"}),
            "LARGEST_MEMBER": max(rows, key=lambda r: r.get("TOTAL_LINES") or 0
                                  )["MEMBER_NAME"] if rows else None,
            "NEWEST_CHANGE": max(changed) if changed else None,
            "OLDEST_FINGERPRINT": min(stamped) if stamped else None,
        })
    return out


# ── sheet writers ──────────────────────────────────────────────────────────
def _header(ws, row: int, labels: list[str]) -> None:
    for col, text in enumerate(labels, start=1):
        c = ws.cell(row=row, column=col, value=text)
        c.font = Font(bold=True, color="FFFFFF", size=10)
        c.fill = PatternFill("solid", fgColor=C_HEAD)
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        c.border = BORDER
    ws.row_dimensions[row].height = 26


def _autosize(ws, widths: dict[int, int]) -> None:
    for idx, width in widths.items():
        ws.column_dimensions[get_column_letter(idx)].width = width


def sheet_overview(wb, summary, detail, libraries, warnings):
    ws = wb.create_sheet("Overview")
    ws.sheet_view.showGridLines = False
    _autosize(ws, {1: 34, 2: 22, 3: 16, 4: 24, 5: 25, 6: 18, 7: 24, 8: 26})

    t = ws.cell(row=1, column=1, value="Cross-Library Member Comparison")
    t.font = Font(bold=True, size=16, color=C_HEAD)
    ws.cell(row=2, column=1,
            value="Every source member in the repository, and whether its copies "
                  "in different libraries are the same.").font = Font(size=10, italic=True,
                                                                      color="5B6B78")

    total_members = len({r["MEMBER_NAME"] for r in detail})
    row = 4
    for label, value in [
        ("Generated", _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Libraries compared", ", ".join(libraries) if libraries else "(none)"),
        ("Library count", len(libraries)),
        ("Members reported", total_members),
        ("Member+library copies", len(detail)),
    ]:
        ws.cell(row=row, column=1, value=label).font = Font(bold=True, size=10)
        ws.cell(row=row, column=2, value=value).font = Font(size=10)
        row += 1

    # ── data-quality block: loud, and first, because a wrong report that looks
    #    right is worse than no report at all.
    row += 1
    ws.cell(row=row, column=1, value="Data quality").font = Font(bold=True, size=12,
                                                                 color=C_HEAD)
    row += 1
    if warnings:
        for level, text in warnings:
            c = ws.cell(row=row, column=1, value=f"{level}: {text}")
            c.fill = FILL_BAD if level == "BLOCKER" else FILL_WARN
            c.font = Font(bold=(level == "BLOCKER"), size=10)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
            ws.row_dimensions[row].height = 42
            row += 1
    else:
        c = ws.cell(row=row, column=1, value="OK: no data-quality problems detected.")
        c.fill = FILL_OK
        c.font = Font(size=10)
        row += 1

    # ── verdict distribution
    row += 1
    ws.cell(row=row, column=1, value="Verdict distribution").font = Font(bold=True, size=12,
                                                                        color=C_HEAD)
    row += 1
    _header(ws, row, ["Verdict", "Members", "Copies",
                      "Member Type Differs\ne.g. RPGLE → SQLRPGLE",
                      "Source File Differs\ne.g. QRPGSRC → QRPGLESRC",
                      "Largest Member", "Newest Change", "Oldest Snapshot"])
    ws.row_dimensions[row].height = 34   # two of these headers wrap to a second line
    row += 1
    meaning = {
        "LOGIC": "the code itself differs — this is the shortlist",
        "COSMETIC": "differs only in comments, blanks, indentation or case",
        "IDENTICAL": "byte-for-byte the same everywhere",
        "SINGLE": "only one copy exists — nothing to compare",
    }
    for r in sorted(summary, key=lambda x: VERDICT_ORDER.get(x.get("VERDICT"), 9)):
        verdict = r.get("VERDICT")
        vals = [verdict, r.get("MEMBER_COUNT"), r.get("COPY_COUNT"),
                r.get("TYPE_DRIFT_COUNT"), r.get("PF_DRIFT_COUNT"),
                r.get("LARGEST_MEMBER"), str(r.get("NEWEST_CHANGE") or ""),
                str(r.get("OLDEST_FINGERPRINT") or "")]
        for col, v in enumerate(vals, start=1):
            c = ws.cell(row=row, column=col, value=v)
            c.border = BORDER
            c.font = Font(size=10, bold=(col == 1))
            if col == 1:
                c.fill = VERDICT_FILL.get(verdict, FILL_SINGLE)
        row += 1
        note = ws.cell(row=row, column=1, value=f"    {meaning.get(verdict, '')}")
        note.font = Font(size=9, italic=True, color="5B6B78")
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
        row += 1

    row += 1
    ws.cell(row=row, column=1,
            value="How to use this: open the Members sheet, filter Verdict = LOGIC. "
                  "Those are the members whose code actually differs between "
                  "libraries. Within each verdict the largest members come "
                  "first.").font = Font(size=10, italic=True, color="5B6B78")


# Three things a first-time reader gets wrong: what the variant labels mean,
# what the two hashes are for, and that Line Count Delta is about length rather
# than sameness. Kept to three lines so the grid stays the focus.
MEMBER_NOTES = [
    "VARIANT LABELS — distinct versions are ranked by how many libraries share each; "
    "ties by earliest change date. Rank 1 = Base, then v1, v2, v3. Same label = "
    "identical source.",
    "VERDICT — LOGIC: the code differs. COSMETIC: comments, blank lines, indentation or "
    "case only. IDENTICAL: byte-for-byte match. SINGLE: one copy only.",
    "MAX SOURCE LINES — the longest single copy, all lines included. LINE COUNT DELTA — "
    "longest minus shortest. Length only: a delta of 0 does not imply a match.",
]


def member_max_lines(detail: list[dict]) -> dict[str, int]:
    """Longest copy per member.

    Line counts are per copy, so the member-level figure has to be reduced
    across the copies. Reading it off the first row gives whichever library
    sorted first, which is not the longest copy.
    """
    out: dict[str, int] = {}
    for r in detail:
        value = r.get("TOTAL_LINES")
        if value is not None and value > out.get(r["MEMBER_NAME"], -1):
            out[r["MEMBER_NAME"]] = value
    return out


def sheet_members(wb, detail, libraries):
    """One row per member, one column per library. The deliverable."""
    ws = wb.create_sheet("Members")
    ws.sheet_view.showGridLines = False

    members: "OrderedDict[str, dict]" = OrderedDict()
    cells: dict[tuple[str, str], list[str]] = defaultdict(list)
    maxlines = member_max_lines(detail)
    for r in detail:
        name = r["MEMBER_NAME"]
        if name not in members:
            members[name] = r
        cells[(name, r["LIBRARY"])].append(r.get("VARIANT") or "?")

    fixed = ["Member", "Member Type", "Source File", "Library Count",
             "Exact Variants", "Verdict", "Member Type Differs",
             "Source File Differs", "Max Source Lines", "Line Count Delta"]
    ncols = len(fixed) + len(libraries)

    for i, note in enumerate(MEMBER_NOTES, start=1):
        c = ws.cell(row=i, column=1, value=note)
        c.font = Font(size=9, italic=True, color="43525F")
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.fill = PatternFill("solid", fgColor=C_BAND)
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=ncols)
        ws.row_dimensions[i].height = 18

    hdr = len(MEMBER_NOTES) + 1
    _header(ws, hdr, fixed + list(libraries))

    row = hdr + 1
    # Within a verdict, largest member first — the biggest programs are where a
    # code difference matters most, so they lead each group.
    for name, meta in sorted(
            members.items(),
            key=lambda kv: (VERDICT_ORDER.get(kv[1].get("VERDICT"), 9),
                            -(maxlines.get(kv[0]) or 0), kv[0])):
        verdict = meta.get("VERDICT")
        vals = [name, meta.get("MEMBER_TYPE"), meta.get("SOURCE_FILE"),
                meta.get("LIB_COUNT"), meta.get("VARIANT_COUNT"), verdict,
                meta.get("TYPE_DRIFT"), meta.get("PF_DRIFT"),
                maxlines.get(name), meta.get("LINE_SPREAD")]
        for col, v in enumerate(vals, start=1):
            c = ws.cell(row=row, column=col, value=v)
            c.border = BORDER
            c.font = Font(size=10, bold=(col == 1))
            if col == 6:
                c.fill = VERDICT_FILL.get(verdict, FILL_SINGLE)
                c.font = Font(size=10, bold=True)
        for i, lib in enumerate(libraries):
            got = cells.get((name, lib))
            c = ws.cell(row=row, column=len(fixed) + 1 + i,
                        value=", ".join(sorted(set(got))) if got else "")
            c.border = BORDER
            c.alignment = Alignment(horizontal="center")
            c.font = Font(size=10, bold=True)
            if got:
                # Base is the prevailing version; anything else is a fork.
                c.fill = FILL_IDENTICAL if set(got) == {BASE_LABEL} else FILL_LOGIC
        row += 1

    # Freeze the notes, the header and the member name column.
    ws.freeze_panes = ws.cell(row=hdr + 1, column=2)
    ws.auto_filter.ref = f"A{hdr}:{get_column_letter(ncols)}{row - 1}"
    _autosize(ws, {1: 16, 2: 13, 3: 13, 4: 13, 5: 14, 6: 12, 7: 19, 8: 19,
                   9: 17, 10: 17})
    for i in range(len(libraries)):
        ws.column_dimensions[get_column_letter(len(fixed) + 1 + i)].width = 13


def sheet_detail(wb, detail):
    ws = wb.create_sheet("Detail")
    ws.sheet_view.showGridLines = False
    cols = [("MEMBER_NAME", "Member", 16), ("LIBRARY", "Library", 12),
            ("SOURCE_FILE", "Source File", 13),
            ("MEMBER_TYPE", "Member Type", 13),
            ("VARIANT", "Exact Variant", 14),
            ("NORM_VARIANT", "Normalized Variant", 19),
            ("VERDICT", "Verdict", 12), ("LIB_COUNT", "Library Count", 13),
            ("VARIANT_COUNT", "Exact Variants", 14),
            ("NORM_VARIANT_COUNT", "Normalized Variants", 20),
            ("TOTAL_LINES", "Source Lines", 13),
            ("CODE_LINES", "Code Lines", 12),
            ("EXACT_HASH_12", "Exact Hash (12)", 16),
            ("NORM_HASH_12", "Normalized Hash (12)", 21),
            ("MEMBER_CHANGED", "Member Changed", 21)]
    _header(ws, 1, [c[1] for c in cols])
    row = 2
    maxlines = member_max_lines(detail)   # same member order as the Members sheet
    for r in sorted(detail, key=lambda x: (VERDICT_ORDER.get(x.get("VERDICT"), 9),
                                           -(maxlines.get(x["MEMBER_NAME"]) or 0),
                                           x["MEMBER_NAME"], x["LIBRARY"],
                                           x.get("SOURCE_FILE") or "")):
        for col, (key, _, _w) in enumerate(cols, start=1):
            v = r.get(key)
            c = ws.cell(row=row, column=col,
                        value=str(v) if key == "MEMBER_CHANGED" and v else v)
            c.border = BORDER
            c.font = Font(size=10)
            if key == "VERDICT":
                c.fill = VERDICT_FILL.get(r.get("VERDICT"), FILL_SINGLE)
            if key in ("EXACT_HASH_12", "NORM_HASH_12"):
                c.font = Font(size=9, name="Consolas")
        if row % 2 == 0:
            for col in range(1, len(cols) + 1):
                if not ws.cell(row=row, column=col).fill.fgColor.rgb.endswith(
                        (FILL_LOGIC.fgColor.rgb[-6:], FILL_COSMETIC.fgColor.rgb[-6:],
                         FILL_IDENTICAL.fgColor.rgb[-6:], FILL_SINGLE.fgColor.rgb[-6:])):
                    ws.cell(row=row, column=col).fill = PatternFill("solid",
                                                                    fgColor=C_BAND)
        row += 1
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{row - 1}"
    _autosize(ws, {i: w for i, (_k, _l, w) in enumerate(cols, start=1)})


# ── data-quality checks ────────────────────────────────────────────────────
def check_data(detail: list[dict]) -> list[tuple[str, str]]:
    """Findings that make the report untrustworthy. Reported, never hidden."""
    out: list[tuple[str, str]] = []
    if not detail:
        out.append(("BLOCKER", "No comparison rows at all. The source table is "
                               "empty — the population program has not been run."))
        return out

    exact = {r.get("EXACT_HASH_12") for r in detail}
    norm = {r.get("NORM_HASH_12") for r in detail}

    if exact == {EMPTY_SHA256_12}:
        out.append(("BLOCKER",
                    "Every EXACT_HASH is the SHA-256 of the empty string "
                    f"({EMPTY_SHA256_12}...). The hash routine is being opened and "
                    "closed but never fed any data, so every member looks identical "
                    "to every other. Every verdict on the Members sheet is therefore "
                    "meaningless. Fix ia_hashAdd (SDS acceptance tests 1-4) and "
                    "rebuild before using this workbook."))
    elif len(exact) == 1 and len(detail) > 1:
        out.append(("BLOCKER",
                    "Every member has the same EXACT_HASH. That cannot be correct for "
                    "distinct source, so the hash routine is not working."))

    if norm == {EMPTY_SHA256_12} and exact != {EMPTY_SHA256_12}:
        out.append(("BLOCKER", "Every NORM_HASH is the empty-string digest — the "
                               "normalized stream is never fed."))

    # A member whose copies differ in length but are reported IDENTICAL is a
    # direct contradiction, and the cheapest proof the hashes are wrong.
    contradictions = sorted({
        r["MEMBER_NAME"] for r in detail
        if r.get("VERDICT") == "IDENTICAL" and (r.get("LINE_SPREAD") or 0) > 0
    })
    if contradictions:
        out.append(("BLOCKER",
                    f"{len(contradictions)} member(s) are reported IDENTICAL but their "
                    f"copies have different line counts: {', '.join(contradictions[:8])}"
                    f"{'...' if len(contradictions) > 8 else ''}. Identical source "
                    "cannot have different line counts."))

    libs = {r.get("LIBRARY") for r in detail}
    if len(libs) < 2:
        out.append(("WARNING",
                    f"Only one library ({', '.join(sorted(libs))}) has been analysed, "
                    "so there is nothing to compare across libraries — every member can "
                    "only be SINGLE. Analyse at least two libraries for this report "
                    "to answer its question."))

    stale = {r.get("MEMBER_NAME") for r in detail if r.get("VARIANT") in (None, "", "?")}
    if stale:
        out.append(("WARNING", f"{len(stale)} row(s) have no variant letter."))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=DEFAULT_URL, help=f"MCP endpoint (default {DEFAULT_URL})")
    ap.add_argument("--out", default=None, help="output .xlsx (default member-diff-YYYYMMDD.xlsx)")
    ap.add_argument("--limit", type=int, default=100000, help="max rows to pull (default 100000)")
    ap.add_argument("--member-type", default="*ALL", help="filter to one member type")
    args = ap.parse_args()

    out = args.out or f"member-diff-{_dt.date.today():%Y%m%d}.xlsx"

    print(f"Pulling rows from {args.url} ...")
    detail = mcp_call(args.url, "ia_member_variants",
                      {"verdict": "*ALL", "member_type": args.member_type,
                       "limit": args.limit})
    summary = mcp_call(args.url, "ia_variant_summary",
                       {"member_type": args.member_type, "limit": 100})
    normalize_variants(detail)
    print(f"  {len(detail)} member+library rows, {len(summary)} verdict groups")

    libraries = sorted({r["LIBRARY"] for r in detail if r.get("LIBRARY")})
    warnings = check_data(detail)
    for level, text in warnings:
        print(f"  {level}: {text}")

    wb = Workbook()
    wb.remove(wb.active)
    sheet_overview(wb, summary, detail, libraries, warnings)
    sheet_members(wb, detail, libraries)
    sheet_detail(wb, detail)
    wb.save(out)

    print(f"\n[OK] {out}")
    print(f"     Overview · Members ({len({r['MEMBER_NAME'] for r in detail})} rows) "
          f"· Detail ({len(detail)} rows)")
    if any(l == "BLOCKER" for l, _ in warnings):
        print("     NOTE: blocking data-quality problems found — see the Overview sheet.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
