#!/usr/bin/env python3
"""Lint a generated flowchart HTML (Gate 1 of flowchart.md §6). Pure stdlib.

Usage:  python validate_flowchart.py <path-to-flowchart.html>
Exit 0 = pass, 1 = findings (printed one per line).

Checks:
  - exactly one <div class="mermaid"> block
  - diagram starts with `flowchart TD` (never `graph TD`)
  - no `subgraph`
  - no reserved node id `end`
  - every declared node has a `class` assignment; every assignment uses a
    defined `classDef` and references a declared node
  - Mermaid pinned at 10.9.0
  - no bare `&` inside the Mermaid block (must be `&amp;`)
  - no leftover template placeholders anywhere in the file
"""
import re
import sys

KNOWN_PLACEHOLDER_RX = [
    re.compile(r"\[[A-Z0-9_]+(?:[ ·/+.-][A-Z0-9_/.-]+)*\]"),  # [PROGRAM_NAME], [NNN], [N PF + N DSPF], [YYYY-MM-DD]
    re.compile(r"L\[x"),                                       # line-ref stubs L[x], L[x-y]
]
KNOWN_PLACEHOLDER_LITERALS = [
    "[PLACEHOLDER]", "[one-line", "[One-line", "[node label", "[opt 1]", "[opt 2]",
    "[Main/Display/Add", "[*ENTRY/PI params", "[CALLERS or none]", "[CALLEES or none]",
    "only keys this program handles", "[Two or three sentences", "✏",  # ✏️ template instruction marker
]


def main(path):
    findings = []
    try:
        with open(path, encoding="utf-8") as f:
            html = f.read()
    except OSError as e:
        print(f"FAIL: cannot read {path}: {e}")
        return 1

    # -- one mermaid block --------------------------------------------------
    blocks = re.findall(r'<div class="mermaid">(.*?)</div>', html, re.DOTALL)
    if len(blocks) != 1:
        findings.append(f"expected exactly 1 mermaid block, found {len(blocks)}"
                        " (multi-tab layouts are not the lean standard)")
    mermaid = blocks[0] if blocks else ""

    # strip %% comment lines and quoted labels for structural scans
    code_lines = [l for l in mermaid.splitlines() if not l.strip().startswith("%%")]
    code = "\n".join(code_lines)
    code_nq = re.sub(r'"[^"]*"', '""', code)

    # -- header -------------------------------------------------------------
    first = next((l.strip() for l in code_lines if l.strip()), "")
    if mermaid and first != "flowchart TD":
        findings.append(f"diagram must start with 'flowchart TD', found: '{first}'")
    if re.search(r"\bgraph\s+(TD|LR|RL|BT)\b", code_nq):
        findings.append("uses 'graph ...' — must be 'flowchart TD'")
    if re.search(r"\bsubgraph\b", code_nq):
        findings.append("contains 'subgraph' — breaks top-to-bottom layout, use one flat graph")

    # -- reserved id --------------------------------------------------------
    if re.search(r"(?<![A-Za-z0-9_])end(?![A-Za-z0-9_])", code_nq):
        findings.append("node id 'end' is a Mermaid reserved word — rename (e.g. ENDP)")

    # -- nodes vs class assignments ------------------------------------------
    declared = set()
    for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*(\(\[|\[\[|\[\(|\[/|\{|\[)", code_nq):
        declared.add(m.group(1))
    classdefs = set(re.findall(r"^\s*classDef\s+([A-Za-z_][A-Za-z0-9_]*)", code, re.MULTILINE))
    assigned = {}
    for m in re.finditer(r"^\s*class\s+([A-Za-z0-9_,\s]+?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;?\s*$", code, re.MULTILINE):
        ids = [i.strip() for i in m.group(1).replace(",", " ").split() if i.strip()]
        for i in ids:
            assigned[i] = m.group(2)
    for node_id, cls in sorted(assigned.items()):
        if cls not in classdefs:
            findings.append(f"node '{node_id}' assigned to undefined class '{cls}'")
        if node_id not in declared:
            findings.append(f"'class' statement references undeclared node '{node_id}' (typo?)")
    for node_id in sorted(declared - set(assigned)):
        findings.append(f"node '{node_id}' has no class assignment — text will be unreadable")

    # -- mermaid version ------------------------------------------------------
    if "mermaid@10.9.0" not in html:
        findings.append("Mermaid not pinned at 10.9.0 (v11.x has SVG layout issues)")

    # -- bare & in the diagram -------------------------------------------------
    for m in re.finditer(r"&(?!amp;|lt;|gt;|quot;|#)", mermaid):
        line_no = mermaid[: m.start()].count("\n") + 1
        findings.append(f"bare '&' in mermaid block (block line {line_no}) — use &amp;")

    # -- leftover template placeholders -----------------------------------------
    for n, line in enumerate(html.splitlines(), 1):
        for rx in KNOWN_PLACEHOLDER_RX:
            m = rx.search(line)
            if m:
                findings.append(f"template placeholder '{m.group(0)}' left at line {n}")
                break
        else:
            for lit in KNOWN_PLACEHOLDER_LITERALS:
                if lit in line:
                    findings.append(f"template placeholder/instruction '{lit}' left at line {n}")
                    break

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
