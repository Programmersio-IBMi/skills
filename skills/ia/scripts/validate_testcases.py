#!/usr/bin/env python3
"""Lint a generated Test Case Document (Gate 1 of test-case-generation.md §5). Pure stdlib.

Usage:  python validate_testcases.py <path-to-{PGM}_Test_Case_Document.md>
Exit 0 = pass, 1 = findings (printed one per line).

Checks:
  - TC ids match TC-{PGM}-NNN, share one program token, unique, sequential from 001
  - every TC block is complete: field table (Category / Priority / Traces to /
    Preconditions / Test data), numbered Steps list, Expected result,
    execution-strip table
  - execution strips are blank (Actual result / Status / Tester / Date)
  - traceability matrix is two-way consistent: every "Traces to" BR-xxx has a
    matrix row, every TC id in the matrix exists as a block, every matrix BR
    is covered by at least one TC
  - no leftover template placeholders (<UPPERCASE> tokens, TBD, TODO)
"""
import re
import sys

TC_HEAD_RX = re.compile(r"^### (TC-[A-Z0-9]+-\d{3})\s+—\s+\S")
TC_ID_RX = re.compile(r"TC-([A-Z0-9]+)-(\d{3})")
BR_RX = re.compile(r"BR-\d{3}")
PLACEHOLDER_RX = re.compile(r"<[A-Z][A-Za-z0-9_ /,.+'-]*>")
FIELD_ROWS = ["Category", "Priority", "Traces to", "Preconditions", "Test data"]
EXEC_HEADER = re.compile(r"^\|\s*Actual result\s*\|\s*Status\s*\|\s*Tester\s*\|\s*Date\s*\|")


def split_tc_blocks(lines):
    """Return [(tc_id, heading_line_no, [block lines])] for every ### TC- heading."""
    blocks, current = [], None
    for n, line in enumerate(lines, 1):
        m = TC_HEAD_RX.match(line)
        if m:
            current = (m.group(1), n, [])
            blocks.append(current)
        elif line.startswith("### ") or line.startswith("## "):
            current = None
        elif current:
            current[2].append(line)
    return blocks


def main(path):
    findings = []
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"FAIL: cannot read {path}: {e}")
        return 1
    lines = text.splitlines()

    # -- TC blocks ------------------------------------------------------------
    blocks = split_tc_blocks(lines)
    if not blocks:
        findings.append("no test case blocks found (headings must be '### TC-{PGM}-NNN — title')")

    # malformed TC headings that didn't match the strict heading regex
    for n, line in enumerate(lines, 1):
        if line.startswith("### TC-") and not TC_HEAD_RX.match(line):
            findings.append(f"malformed TC heading at line {n}: '{line.strip()}'"
                            " (expected '### TC-{PGM}-NNN — title')")

    # -- id format / program token / uniqueness / sequence ---------------------
    pgm_tokens = {TC_ID_RX.search(tc_id).group(1) for tc_id, _, _ in blocks}
    if len(pgm_tokens) > 1:
        findings.append(f"TC ids use multiple program tokens: {sorted(pgm_tokens)}")
    seen, numbers = set(), []
    for tc_id, n, _ in blocks:
        if tc_id in seen:
            findings.append(f"duplicate TC id '{tc_id}' (line {n})")
        seen.add(tc_id)
        numbers.append(int(TC_ID_RX.search(tc_id).group(2)))
    if numbers:
        expected = list(range(1, len(numbers) + 1))
        if sorted(numbers) != expected:
            findings.append(f"TC numbering not sequential from 001: found {sorted(numbers)}")
        elif numbers != expected:
            findings.append("TC blocks out of order: ids must appear in ascending sequence")

    # -- per-block completeness -------------------------------------------------
    traced_brs = set()
    for tc_id, n, body in blocks:
        body_text = "\n".join(body)
        for row in FIELD_ROWS:
            if not re.search(r"^\|\s*" + re.escape(row) + r"\s*\|", body_text, re.MULTILINE):
                findings.append(f"{tc_id}: field table missing '{row}' row")
        if not re.search(r"^\*\*Steps\*\*", body_text, re.MULTILINE):
            findings.append(f"{tc_id}: missing '**Steps**' block")
        elif not re.search(r"^1\.\s+\S", body_text, re.MULTILINE):
            findings.append(f"{tc_id}: Steps has no numbered step '1. ...'")
        if not re.search(r"^\*\*Expected result\*\*", body_text, re.MULTILINE):
            findings.append(f"{tc_id}: missing '**Expected result**' block")
        # execution strip: header row then blank data row
        strip_ok = False
        for i, line in enumerate(body):
            if EXEC_HEADER.match(line.strip()):
                data = body[i + 2] if i + 2 < len(body) else ""
                cells = [c.strip() for c in data.strip().strip("|").split("|")]
                if len(cells) == 4 and not any(cells):
                    strip_ok = True
                elif len(cells) == 4:
                    findings.append(f"{tc_id}: execution strip is not blank ({data.strip()})")
                    strip_ok = True  # present but pre-filled — already reported
                break
        if not strip_ok:
            findings.append(f"{tc_id}: missing execution strip table"
                            " (| Actual result | Status | Tester | Date |)")
        m = re.search(r"^\|\s*Traces to\s*\|(.*)\|", body_text, re.MULTILINE)
        if m:
            traced_brs.update(BR_RX.findall(m.group(1)))

    # -- traceability matrix ------------------------------------------------------
    matrix_brs = {}
    in_matrix = False
    for line in lines:
        if re.match(r"^##\s+.*Traceability Matrix", line):
            in_matrix = True
            continue
        if in_matrix and re.match(r"^##\s+", line):
            in_matrix = False
        if in_matrix:
            m = re.match(r"^\|\s*(BR-\d{3})\s*\|", line)
            if m:
                matrix_brs[m.group(1)] = set(TC_ID_RX.findall(line.split("|", 2)[-1]))
    if not matrix_brs and (traced_brs or blocks):
        findings.append("no traceability matrix rows found (section '## 5. Traceability Matrix')")
    for br in sorted(traced_brs - set(matrix_brs)):
        findings.append(f"traceability: {br} is traced by a TC but has no matrix row")
    for br, tcs in sorted(matrix_brs.items()):
        if not tcs:
            findings.append(f"traceability: matrix row {br} lists no covering TC")
        for tc in sorted("TC-%s-%s" % t for t in tcs):
            if tc not in seen:
                findings.append(f"traceability: matrix references '{tc}' which has no TC block")

    # -- leftover placeholders ------------------------------------------------------
    for n, line in enumerate(lines, 1):
        m = PLACEHOLDER_RX.search(line)
        if m:
            findings.append(f"template placeholder '{m.group(0)}' left at line {n}")
        for lit in ("TBD", "TODO"):
            if re.search(r"\b" + lit + r"\b", line):
                findings.append(f"'{lit}' left at line {n}")

    if findings:
        for f_ in findings:
            print(f"FAIL: {f_}")
        print(f"\n{len(findings)} finding(s) in {path}")
        return 1
    print(f"PASS: {path} — all checks clean")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
