#!/usr/bin/env python3
"""
Professional Markdown-to-PDF converter with comprehensive formatting support.
Produces polished technical documents suitable for distribution:
cover page, clickable table of contents, PDF outline bookmarks,
"Page N of M" footers, split-safe code blocks, accent-bar blockquotes.

Usage: python convert_md_to_pdf.py input.md [output.pdf]

Requirements: pip install reportlab
"""

import argparse
import datetime
import os
import re
import sys
from collections import OrderedDict
from typing import List, Optional, Tuple, Dict

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, Flowable,
        NextPageTemplate, PageTemplate, BaseDocTemplate, Frame,
    )
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
except ImportError:
    print("Error: reportlab is not installed.")
    print("Install with: pip install reportlab")
    sys.exit(1)

# ── Constants ────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

# Professional color palette
C_PRIMARY   = colors.HexColor('#1a365d')
C_SECONDARY = colors.HexColor('#2c5282')
C_ACCENT    = colors.HexColor('#3182ce')
C_TABLE_HDR = colors.HexColor('#2b6cb0')
C_MUTED     = colors.HexColor('#718096')
C_BORDER    = colors.HexColor('#cbd5e0')
C_CODE_BG   = colors.HexColor('#f7fafc')
C_ROW_ALT   = colors.HexColor('#eef5fc')
C_RULE      = colors.HexColor('#e2e8f0')
C_COVER_BG  = colors.HexColor('#1a365d')
C_COVER_ACC = colors.HexColor('#2b6cb0')
C_CODE_TEXT = colors.HexColor('#2d3748')
C_BLOCKQUOTE = colors.HexColor('#44546a')
C_QUOTE_BG  = colors.HexColor('#f0f5fa')
C_LINK      = colors.HexColor('#2b6cb0')

BRAND = 'iA by programmers.io'

# Unicode character replacements for PDF (WinAnsi font) compatibility
CHAR_REPLACEMENTS = {
    '⚠️': '(!)', '⚠': '(!)',
    '✅': '[x]', '❌': 'x',
    '\U0001f4c4': '[DOC]', '\U0001f4ca': '[CHART]', '\U0001f50d': '[FIND]',
    '\U0001f4cb': '[LIST]', '\U0001f4a1': '[TIP]', '\U0001f527': '[TOOL]',
    '\U0001f4cc': '[PIN]', '\U0001f3af': '[TARGET]', '\U0001f680': '[LAUNCH]',
    '–': '-', '—': '--', '‘': "'", '’': "'",
    '“': '"', '”': '"', '…': '...', '←': '<-', '→': '->',
    '×': 'x',
    '●': '•', '○': 'o', '◦': '·',
    '▪': '·', '▫': '·',
    '☐': '[ ]', '☑': '[x]', '✓': '+', '✗': 'x',
    # Box-drawing characters -> ASCII so diagrams degrade gracefully
    '─': '-', '│': '|', '┌': '+', '┐': '+',
    '└': '+', '┘': '+', '├': '+', '┤': '+',
    '┬': '+', '┴': '+', '┼': '+',
    '═': '=', '║': '|', '╔': '+', '╗': '+',
    '╚': '+', '╝': '+',
}

# Characters >= 256 that the standard fonts CAN render (WinAnsi)
_SAFE_HIGH = {'•'}


def sanitize_text(text: str) -> str:
    """Replace characters that don't render in the standard PDF fonts."""
    if not text:
        return text
    for bad, good in CHAR_REPLACEMENTS.items():
        text = text.replace(bad, good)
    return ''.join(ch if (ord(ch) < 256 or ch in _SAFE_HIGH) else '?' for ch in text)


def xml_escape(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# Markdown backslash-escapable punctuation
_MD_ESCAPE_RE = re.compile(r'\\([\\`*_{}\[\]()#+\-.!|<>])')


def inline_md_to_xml(text: str) -> str:
    """Convert inline markdown to reportlab XML markup (escaped & safe)."""
    if not text:
        return text
    text = sanitize_text(text)

    protected: List[str] = []

    def keep(rendered: str) -> str:
        protected.append(rendered)
        return f'\x00P{len(protected) - 1}\x00'

    # 1. Inline code spans first (content is literal; escape it for XML)
    def save_code(m):
        content = xml_escape(m.group(1))
        return keep(
            f'<font name="Courier" size="8.8" backColor="#edf2f7" '
            f'color="#b83254">&nbsp;{content}&nbsp;</font>'
        )
    text = re.sub(r'`(.+?)`', save_code, text, flags=re.DOTALL)

    # 2. Markdown backslash escapes -> literal character (protected)
    text = _MD_ESCAPE_RE.sub(lambda m: keep(xml_escape(m.group(1))), text)

    # 3. XML-escape everything that remains
    text = xml_escape(text)

    # Literal <br> written in markdown -> line break
    text = re.sub(r'&lt;br\s*/?&gt;', '<br/>', text, flags=re.IGNORECASE)

    # 4. Links (before bold/italic so URLs are untouched by those regexes)
    def save_link(m):
        label, url = m.group(1), m.group(2)
        return keep(f'<a href="{url}" color="#2b6cb0"><u>{label}</u></a>')
    text = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', save_link, text)

    # 5. Bold + italic, then bold, then italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)

    # Checkboxes (mid-text task lists)
    text = re.sub(r'\[x\]', '<b>[x]</b>', text, flags=re.IGNORECASE)

    # 6. Restore protected spans
    for idx, rendered in enumerate(protected):
        text = text.replace(f'\x00P{idx}\x00', rendered)
    return text


# ── Table Parsing ────────────────────────────────────────────────────────
def split_row(line: str) -> List[str]:
    """Split a markdown table row, honoring escaped pipes and optional
    leading/trailing pipes."""
    line = line.strip().replace('\\|', '\x00PIPE\x00')
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return [c.replace('\x00PIPE\x00', '\\|').strip() for c in line.split('|')]


def is_table_separator(line: str) -> bool:
    line = line.strip()
    if not line.startswith('|') and '|' not in line:
        return False
    cells = split_row(line)
    return bool(cells) and all(re.match(r'^:?-{2,}:?$|^:-+:?$|^-+$|^[\s\-:]+$', c) for c in cells if c != '') \
        and any('-' in c for c in cells)


def parse_md_table(lines: List[str], start_idx: int) -> Tuple[List[List[str]], int]:
    """Parse markdown table starting at start_idx. Returns (rows, next_idx)."""
    rows = []
    idx = start_idx
    while idx < len(lines):
        line = lines[idx].rstrip()
        if not line.strip().startswith('|'):
            break
        if is_table_separator(line):
            idx += 1
            continue
        cells = [inline_md_to_xml(c) for c in split_row(line)]
        if cells:
            rows.append(cells)
        idx += 1
    return rows, idx


def calc_col_widths(rows: List[List[str]], avail_w: float) -> List[float]:
    if not rows:
        return []
    ncols = len(rows[0])
    if ncols == 0:
        return []
    col_max = [0] * ncols
    for row in rows:
        for ci, cell in enumerate(row[:ncols]):
            col_max[ci] = max(col_max[ci], len(re.sub(r'<[^>]+>', '', cell)))
    total = sum(col_max) or 1
    min_w = 40
    raw = [max(c, total * 0.08) for c in col_max]
    raw_total = sum(raw)
    widths = [avail_w * r / raw_total for r in raw]
    for i in range(ncols):
        if widths[i] < min_w:
            deficit = min_w - widths[i]
            widths[i] = min_w
            others = [j for j in range(ncols) if j != i and widths[j] > min_w + 20]
            if others:
                for j in others:
                    widths[j] = max(min_w, widths[j] - deficit / len(others))
    return widths


# ── Style Definitions ────────────────────────────────────────────────────
_STYLES = None


def make_styles():
    global _STYLES
    if _STYLES is not None:
        return _STYLES
    base = getSampleStyleSheet()
    _STYLES = {
        'cover_eyebrow': ParagraphStyle('CoverEyebrow', fontSize=11, leading=15,
            textColor=colors.HexColor('#90cdf4'), fontName='Helvetica-Bold', spaceAfter=8),
        'cover_title': ParagraphStyle('CoverTitle', fontSize=38, leading=44, textColor=colors.white,
            fontName='Helvetica-Bold', alignment=TA_LEFT, spaceAfter=12),
        'cover_subtitle': ParagraphStyle('CoverSubtitle', fontSize=13, leading=18,
            textColor=colors.HexColor('#bee3f8'), fontName='Helvetica', alignment=TA_LEFT, spaceAfter=18),
        'cover_meta': ParagraphStyle('CoverMeta', fontSize=10, leading=16, textColor=colors.white,
            fontName='Helvetica', spaceAfter=4),
        'toc_title': ParagraphStyle('TOCTitle', fontSize=20, leading=26,
            textColor=C_PRIMARY, fontName='Helvetica-Bold', spaceAfter=4, spaceBefore=8),
        'toc1': ParagraphStyle('TOCLevel1', fontSize=10.5, leading=15, textColor=C_PRIMARY,
            fontName='Helvetica-Bold', leftIndent=0, firstLineIndent=0, spaceBefore=8),
        'toc2': ParagraphStyle('TOCLevel2', fontSize=9.5, leading=13, textColor=C_SECONDARY,
            fontName='Helvetica', leftIndent=16, firstLineIndent=0, spaceBefore=3),
        'h1': ParagraphStyle('H1', parent=base['Heading1'], fontSize=24, leading=30,
            textColor=C_PRIMARY, fontName='Helvetica-Bold', spaceAfter=8, spaceBefore=30,
            keepWithNext=1),
        'h2': ParagraphStyle('H2', parent=base['Heading2'], fontSize=16, leading=22,
            textColor=C_SECONDARY, fontName='Helvetica-Bold', spaceAfter=6, spaceBefore=22,
            keepWithNext=1),
        'h3': ParagraphStyle('H3', parent=base['Heading3'], fontSize=13, leading=18,
            textColor=C_ACCENT, fontName='Helvetica-Bold', spaceAfter=5, spaceBefore=16,
            keepWithNext=1),
        'h4': ParagraphStyle('H4', parent=base['Heading4'], fontSize=11, leading=15,
            textColor=colors.HexColor('#4a5568'), fontName='Helvetica-Bold', spaceAfter=3,
            spaceBefore=12, keepWithNext=1),
        'h5': ParagraphStyle('H5', parent=base['Heading5'], fontSize=10, leading=14,
            textColor=colors.HexColor('#718096'), fontName='Helvetica-Bold', spaceAfter=2,
            spaceBefore=10, keepWithNext=1),
        'h6': ParagraphStyle('H6', parent=base['Heading6'], fontSize=9, leading=12,
            textColor=colors.HexColor('#a0aec0'), fontName='Helvetica-Bold', spaceAfter=2,
            spaceBefore=8, keepWithNext=1),
        'body': ParagraphStyle('Body', parent=base['BodyText'], fontSize=10.5, leading=16,
            alignment=TA_JUSTIFY, fontName='Helvetica', spaceAfter=7),
        'bullet': ParagraphStyle('Bullet', parent=base['BodyText'], fontSize=10.5, leading=16,
            fontName='Helvetica', leftIndent=22, firstLineIndent=-10, spaceAfter=3, spaceBefore=1),
        'bullet2': ParagraphStyle('Bullet2', parent=base['BodyText'], fontSize=10.5, leading=16,
            fontName='Helvetica', leftIndent=44, firstLineIndent=-10, spaceAfter=3, spaceBefore=1),
        'bullet3': ParagraphStyle('Bullet3', parent=base['BodyText'], fontSize=10.5, leading=16,
            fontName='Helvetica', leftIndent=66, firstLineIndent=-10, spaceAfter=3, spaceBefore=1),
        'number': ParagraphStyle('Number', parent=base['BodyText'], fontSize=10.5, leading=16,
            fontName='Helvetica', leftIndent=26, firstLineIndent=-14, spaceAfter=3, spaceBefore=1),
        'number2': ParagraphStyle('Number2', parent=base['BodyText'], fontSize=10.5, leading=16,
            fontName='Helvetica', leftIndent=48, firstLineIndent=-14, spaceAfter=3, spaceBefore=1),
        'number3': ParagraphStyle('Number3', parent=base['BodyText'], fontSize=10.5, leading=16,
            fontName='Helvetica', leftIndent=70, firstLineIndent=-14, spaceAfter=3, spaceBefore=1),
        'quote': ParagraphStyle('Quote', parent=base['BodyText'], fontSize=9.8, leading=14.5,
            fontName='Helvetica', textColor=C_BLOCKQUOTE, spaceAfter=0, spaceBefore=0),
        'table_cell': ParagraphStyle('TCell', parent=base['Normal'], fontSize=9, leading=12.5,
            fontName='Helvetica', wordWrap='CJK'),
        'table_header': ParagraphStyle('THead', parent=base['Normal'], fontSize=9.5, leading=13,
            fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_LEFT),
    }
    return _STYLES


# ── Custom Flowables ─────────────────────────────────────────────────────
class SectionRule(HRFlowable):
    def __init__(self, color=C_RULE, thickness=1.5, width='100%'):
        HRFlowable.__init__(self, width=width, thickness=thickness, color=color,
                            spaceAfter=8, spaceBefore=4)


class ThinRule(HRFlowable):
    def __init__(self):
        HRFlowable.__init__(self, width='100%', thickness=0.5, color=C_RULE,
                            spaceAfter=10, spaceBefore=10)


class CodeBlockFlowable(Flowable):
    """Code block with language chip, auto font-fit, soft wrap of long
    lines, and page-split support."""
    PAD_X = 12
    PAD_TOP = 10
    PAD_BOT = 10

    def __init__(self, code_text: str, language: str = '', _font_size: Optional[float] = None):
        Flowable.__init__(self)
        self.raw_lines = [sanitize_text(l.replace('\t', '    ')).rstrip()
                          for l in (code_text or '').split('\n')]
        self.language = language
        self._forced_size = _font_size
        self.font_size = _font_size or 9.0
        self.rows: List[str] = []

    def _header_h(self) -> float:
        return 16 if self.language else 0

    def _layout(self, avail_w: float):
        usable = avail_w - 2 * self.PAD_X
        size = self._forced_size or 9.0
        if not self._forced_size:
            longest = max((stringWidth(l, 'Courier', 10) for l in self.raw_lines), default=0) / 10.0
            if longest > 0:
                size = min(9.0, usable / longest)
            size = max(size, 6.5)
        self.font_size = size
        self.line_h = size + 3.0
        char_w = stringWidth('M', 'Courier', size)
        max_chars = max(int(usable / char_w), 8)
        rows: List[str] = []
        for line in self.raw_lines:
            if stringWidth(line, 'Courier', size) <= usable:
                rows.append(line)
                continue
            # Hard-wrap an over-long line; continuation indented two spaces
            rest = line
            first = True
            while stringWidth(rest, 'Courier', size) > usable and len(rest) > max_chars:
                cut = max_chars if first else max_chars - 2
                rows.append((rest[:cut]) if first else ('  ' + rest[:cut]))
                rest = rest[cut:]
                first = False
            rows.append(rest if first else '  ' + rest)
        self.rows = rows

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self._layout(availWidth)
        self.height = self._header_h() + self.PAD_TOP + self.PAD_BOT + len(self.rows) * self.line_h
        return (self.width, self.height)

    def split(self, availWidth, availHeight):
        self.wrap(availWidth, availHeight)
        if self.height <= availHeight:
            return [self]
        budget = availHeight - self._header_h() - self.PAD_TOP - self.PAD_BOT
        fit_rows = int(budget // self.line_h)
        if fit_rows < 4 or fit_rows >= len(self.rows):
            return []  # move whole block to the next page
        head = CodeBlockFlowable('\n'.join(self.rows[:fit_rows]), self.language,
                                 _font_size=self.font_size)
        cont_lang = (self.language + ' (cont.)') if self.language else ''
        tail = CodeBlockFlowable('\n'.join(self.rows[fit_rows:]), cont_lang,
                                 _font_size=self.font_size)
        return [head, tail]

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        header_h = self._header_h()
        c.setFillColor(C_CODE_BG)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=1)
        # Left accent bar
        c.setFillColor(C_ACCENT)
        c.rect(0, 0, 2.2, h, fill=1, stroke=0)
        if self.language:
            c.setFillColor(colors.HexColor('#e6edf5'))
            c.rect(2.2, h - header_h, w - 2.2, header_h, fill=1, stroke=0)
            c.setFillColor(C_SECONDARY)
            c.setFont('Helvetica-Bold', 7.5)
            c.drawString(self.PAD_X, h - header_h + 5, self.language.upper())
        c.setFillColor(C_CODE_TEXT)
        c.setFont('Courier', self.font_size)
        y = h - header_h - self.PAD_TOP - self.font_size + 2
        for row in self.rows:
            c.drawString(self.PAD_X, y, row)
            y -= self.line_h


def make_quote(xml_text: str, styles) -> Table:
    """Blockquote rendered as accent-bar callout."""
    p = Paragraph(xml_text, styles['quote'])
    t = Table([[p]], colWidths=[CONTENT_W - 4])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_QUOTE_BG),
        ('LINEBEFORE', (0, 0), (0, -1), 3, C_ACCENT),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


# ── Page Templates ───────────────────────────────────────────────────────
# NOTE: a deferred-emission "NumberedCanvas" must NOT be used here — it breaks
# bookmarkPage/addOutlineEntry (every named destination binds to page 1, so
# TOC links and outline bookmarks all jump to the cover). The page total is
# taken from the previous multiBuild pass instead, which is stable once the
# table of contents has converged.
class DocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame_cover = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2 * MARGIN, id='cover_frame')
        frame_body = Frame(MARGIN, MARGIN + 10, CONTENT_W, PAGE_H - 2 * MARGIN - 30, id='body_frame')
        cover_tpl = PageTemplate(id='Cover', frames=[frame_cover], onPage=self._draw_cover)
        body_tpl = PageTemplate(id='Body', frames=[frame_body], onPage=self._draw_body)
        self.addPageTemplates([cover_tpl, body_tpl])
        self._doc_title = ''
        self._footer_left = BRAND
        self._toc_seq = 0
        self._this_pass_total = 0
        self._prev_pass_total = 0

    def set_title(self, title):
        self._doc_title = title

    def set_footer_left(self, text):
        self._footer_left = text

    # Reset per build pass (multiBuild runs several passes)
    def beforeDocument(self):
        self._toc_seq = 0
        self._prev_pass_total = self._this_pass_total
        self._this_pass_total = 0

    def afterPage(self):
        self._this_pass_total = self.page

    def afterFlowable(self, flowable):
        """Register H2/H3 headings: TOC entries + PDF outline bookmarks."""
        if not isinstance(flowable, Paragraph):
            return
        sname = flowable.style.name
        if sname not in ('H2', 'H3'):
            return
        text = flowable.getPlainText()
        key = f'toc-{self._toc_seq}'
        self._toc_seq += 1
        level = 0 if sname == 'H2' else 1
        self.canv.bookmarkPage(key)
        try:
            self.canv.addOutlineEntry(text, key, level=level, closed=False)
        except Exception:
            pass  # outline nesting can fail if an H3 precedes any H2
        self.notify('TOCEntry', (level, text, self.page - 1, key))

    def _draw_cover(self, canvas, doc):
        c = canvas
        c.saveState()
        c.setFillColor(C_COVER_BG)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setFillColor(C_COVER_ACC)
        c.rect(0, 0, 8 * mm, PAGE_H, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#3d6a9e'))
        c.rect(8 * mm, 0, 1.2, PAGE_H, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#2a4365'))
        c.circle(PAGE_W - 3 * cm, PAGE_H - 3 * cm, 5 * cm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#23415c'))
        c.circle(PAGE_W - 2 * cm, PAGE_H - 2.5 * cm, 3.5 * cm, fill=1, stroke=0)
        c.setStrokeColor(C_COVER_ACC)
        c.setLineWidth(1.5)
        c.line(MARGIN, 2.5 * cm, PAGE_W - MARGIN, 2.5 * cm)
        c.setFont('Helvetica', 7.5)
        c.setFillColor(colors.HexColor('#8aa6c4'))
        c.drawString(MARGIN, 2 * cm, f"Generated by {BRAND}")
        c.drawRightString(PAGE_W - MARGIN, 2 * cm, "Confidential")
        c.restoreState()

    def _draw_body(self, canvas, doc):
        c = canvas
        c.saveState()
        # Header: accent rule + running title
        c.setStrokeColor(C_ACCENT)
        c.setLineWidth(1.5)
        c.line(MARGIN, PAGE_H - MARGIN + 14, PAGE_W - MARGIN, PAGE_H - MARGIN + 14)
        if self._doc_title:
            c.setFont('Helvetica-Bold', 8)
            c.setFillColor(C_MUTED)
            c.drawString(MARGIN, PAGE_H - MARGIN + 18, sanitize_text(self._doc_title)[:90])
        # Footer: thin rule + brand/date (page number drawn by NumberedCanvas)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.line(MARGIN, MARGIN - 6, PAGE_W - MARGIN, MARGIN - 6)
        c.setFont('Helvetica', 8)
        c.setFillColor(C_MUTED)
        c.drawString(MARGIN, MARGIN - 16, sanitize_text(self._footer_left)[:90])
        page_num = doc.page - 1
        if page_num > 0:
            total = self._prev_pass_total - 1
            label = f"Page {page_num} of {total}" if total >= page_num else f"Page {page_num}"
            c.drawRightString(PAGE_W - MARGIN, MARGIN - 16, label)
        c.restoreState()


# ── Metadata Extraction ──────────────────────────────────────────────────
def extract_metadata(md_content: str) -> Tuple[OrderedDict, int]:
    """Parse the leading '**Key:** value' header block (after the H1 title).

    Handles several pairs on one line separated by '|', e.g.
    '**Library:** KUNALP | **Source file:** QCLSRC | **Member type:** CLLE'.
    Returns (meta, index_of_first_body_line).
    """
    meta = OrderedDict()
    lines = md_content.split('\n')
    in_header = False
    skip_count = 0
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            if in_header and meta:
                skip_count = i + 1
                break
            continue
        if line.startswith('#'):
            if in_header:
                skip_count = i
                break
            continue  # the H1 title precedes the metadata block
        if re.match(r'\*\*[^*]+?:?\*\*:?\s*\S', line):
            in_header = True
            for seg in re.split(r'\s*\|\s*(?=\*\*)', line):
                m = re.match(r'\*\*([^*]+?):?\*\*:?\s*(.+)$', seg.strip())
                if m:
                    meta[m.group(1).strip()] = m.group(2).strip()
            skip_count = i + 1
        elif in_header and line == '---':
            skip_count = i + 1
            break
        elif in_header:
            skip_count = i
            break
        else:
            break
    return meta, skip_count


def extract_title(md_content: str) -> str:
    for line in md_content.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return 'Technical Specification'


# ── List Parsing ─────────────────────────────────────────────────────────
_LIST_ITEM_RE = re.compile(r'^\s*([-*+]|\d+\.)\s')


def parse_list(lines: List[str], start_idx: int, ordered: bool) -> Tuple[List[Dict], int]:
    items = []
    idx = start_idx
    while idx < len(lines):
        line = lines[idx]
        indent = len(line) - len(line.lstrip())
        indent_level = min(indent // 2, 2)
        if ordered:
            m = re.match(r'^(\s*)(\d+)\.\s(.*)$', line)
            if not m:
                break
            items.append({'level': indent_level, 'text': m.group(3), 'number': m.group(2)})
        else:
            m = re.match(r'^(\s*)([-*+])\s(.*)$', line)
            if not m:
                break
            items.append({'level': indent_level, 'text': m.group(3)})
        # Multi-line list items: absorb indented continuation lines, but
        # never absorb lines that are themselves list items (nested items).
        while idx + 1 < len(lines) and lines[idx + 1].strip() \
                and (lines[idx + 1].startswith(' ') or lines[idx + 1].startswith('\t')) \
                and not _LIST_ITEM_RE.match(lines[idx + 1]):
            idx += 1
            items[-1]['text'] += ' ' + lines[idx].strip()
        idx += 1
    return items, idx


# ── Markdown to PDF Elements ─────────────────────────────────────────────
def md_to_pdf_elements(md_content: str, doc_title: str = '') -> List[Flowable]:
    styles = make_styles()
    elements = []
    lines = md_content.split('\n')
    section_count = 0
    _, meta_skip = extract_metadata(md_content)
    i = meta_skip
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        # Headings
        if line.startswith('###### '):
            elements.append(Paragraph(inline_md_to_xml(line[7:].strip()), styles['h6']))
            i += 1
        elif line.startswith('##### '):
            elements.append(Paragraph(inline_md_to_xml(line[6:].strip()), styles['h5']))
            i += 1
        elif line.startswith('#### '):
            elements.append(Paragraph(inline_md_to_xml(line[5:].strip()), styles['h4']))
            i += 1
        elif line.startswith('### '):
            elements.append(Paragraph(inline_md_to_xml(line[4:].strip()), styles['h3']))
            i += 1
        elif line.startswith('## '):
            section_count += 1
            if section_count >= 2:
                elements.append(PageBreak())
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(inline_md_to_xml(line[3:].strip()), styles['h2']))
            elements.append(SectionRule())
            i += 1
        elif line.startswith('# '):
            i += 1
            continue
        # Horizontal Rule
        elif line.strip() in ['---', '***', '___']:
            elements.append(Spacer(1, 0.2 * cm))
            elements.append(ThinRule())
            i += 1
        # Code Block
        elif line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i].rstrip())
                i += 1
            i += 1
            if code_lines:
                elements.append(Spacer(1, 4))
                elements.append(CodeBlockFlowable('\n'.join(code_lines), lang))
                elements.append(Spacer(1, 6))
        # Table
        elif line.strip().startswith('|'):
            rows, new_idx = parse_md_table(lines, i)
            if rows:
                elements.append(Spacer(1, 4))
                table = create_table(rows)
                if table:
                    elements.append(table)
                elements.append(Spacer(1, 6))
            i = new_idx
            continue
        # Blockquote
        elif line.strip().startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(inline_md_to_xml(lines[i].strip()[1:].strip()))
                i += 1
            if quote_lines:
                elements.append(Spacer(1, 4))
                elements.append(make_quote('<br/>'.join(q for q in quote_lines if q), styles))
                elements.append(Spacer(1, 6))
        # Unordered List
        elif re.match(r'^[\s]*[-*+] ', line):
            list_items, new_idx = parse_list(lines, i, ordered=False)
            for item in list_items:
                level = item['level']
                text = inline_md_to_xml(item['text'])
                if level == 0:
                    elements.append(Paragraph(f'• {text}', styles['bullet']))
                elif level == 1:
                    elements.append(Paragraph(f'- {text}', styles['bullet2']))
                else:
                    elements.append(Paragraph(f'· {text}', styles['bullet3']))
            i = new_idx
            continue
        # Ordered List
        elif re.match(r'^[\s]*\d+\.\s', line):
            list_items, new_idx = parse_list(lines, i, ordered=True)
            for item in list_items:
                level = item['level']
                text = inline_md_to_xml(item['text'])
                num = item.get('number', '1')
                if level == 0:
                    elements.append(Paragraph(f'{num}. {text}', styles['number']))
                elif level == 1:
                    elements.append(Paragraph(f'{num}. {text}', styles['number2']))
                else:
                    elements.append(Paragraph(f'{num}. {text}', styles['number3']))
            i = new_idx
            continue
        # Regular Paragraph
        else:
            para_lines = []
            while i < len(lines) and lines[i].strip() and \
                  not lines[i].strip().startswith('#') and \
                  not lines[i].strip().startswith('|') and \
                  not lines[i].strip().startswith('```') and \
                  not lines[i].strip().startswith('>') and \
                  not re.match(r'^[\s]*[-*+] ', lines[i]) and \
                  not re.match(r'^[\s]*\d+\.\s', lines[i]) and \
                  lines[i].strip() not in ['---', '***', '___']:
                para_lines.append(lines[i].rstrip())
                i += 1
            if para_lines:
                para_text = ' '.join(para_lines)
                elements.append(Paragraph(inline_md_to_xml(para_text), styles['body']))
            continue
    return elements


_NUMERIC_RE = re.compile(r'^-?\d+(\.\d+)?%?$')


def create_table(rows: List[List[str]]) -> Optional[Table]:
    if not rows:
        return None
    styles = make_styles()
    max_cols = max(len(row) for row in rows)
    for row in rows:
        while len(row) < max_cols:
            row.append('')
    col_widths = calc_col_widths(rows, CONTENT_W)
    data = []
    numeric_cells = []
    for row_idx, row in enumerate(rows):
        row_data = []
        for col_idx, cell in enumerate(row):
            if row_idx == 0:
                row_data.append(Paragraph(f'<b>{cell}</b>', styles['table_header']))
            else:
                plain = re.sub(r'<[^>]+>', '', cell).replace('&nbsp;', '').strip()
                if plain and _NUMERIC_RE.match(plain):
                    numeric_cells.append((col_idx, row_idx))
                row_data.append(Paragraph(cell, styles['table_cell']))
        data.append(row_data)
    if not data:
        return None
    table = Table(data, colWidths=col_widths, repeatRows=1, splitByRow=1)
    # Clean "report" style: header band, horizontal rules only, banded rows
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), C_TABLE_HDR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('LINEABOVE', (0, 0), (-1, 0), 1.0, C_PRIMARY),
        ('LINEBELOW', (0, 0), (-1, 0), 1.2, C_PRIMARY),
        ('LINEBELOW', (0, -1), (-1, -1), 0.9, C_BORDER),
    ]
    for row_idx in range(1, len(data)):
        if row_idx < len(data) - 1:
            style.append(('LINEBELOW', (0, row_idx), (-1, row_idx), 0.4, C_RULE))
        if row_idx % 2 == 0:
            style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), C_ROW_ALT))
    for col_idx, row_idx in numeric_cells:
        style.append(('ALIGN', (col_idx, row_idx), (col_idx, row_idx), 'CENTER'))
    table.setStyle(TableStyle(style))
    return table


# ── Cover & TOC ─────────────────────────────────────────────────────────
_SUBTITLE_KEYS = ('Member type', 'Type', 'Program', 'Source file', 'File',
                  'Library version documented', 'Library')


def build_cover(meta: OrderedDict, title_text: str, styles) -> List[Flowable]:
    # Split "Technical Specification — IADEPRPT" into eyebrow + main title
    eyebrow, main = 'TECHNICAL DOCUMENT', title_text
    for dash in ('—', ' -- ', ' - '):
        if dash in title_text:
            left, right = title_text.split(dash, 1)
            if left.strip() and right.strip():
                eyebrow, main = left.strip().upper(), right.strip()
            break
    main = sanitize_text(main)
    eyebrow = sanitize_text(eyebrow)
    title_style = styles['cover_title']
    if len(main) > 18:
        title_style = ParagraphStyle('CoverTitleSmall', parent=title_style,
                                     fontSize=28 if len(main) <= 30 else 22,
                                     leading=34 if len(main) <= 30 else 28)
    elements = [Spacer(1, 3.4 * cm)]
    elements.append(Paragraph(eyebrow, styles['cover_eyebrow']))
    elements.append(Paragraph(main, title_style))
    parts = []
    for key in ('Member type', 'Type', 'Program'):
        if key in meta:
            parts.append(meta[key])
            break
    for key in ('Source file', 'File'):
        if key in meta:
            parts.append(f"Source: {meta[key]}")
            break
    for key in ('Library version documented', 'Library'):
        if key in meta:
            parts.append(f"Library: {meta[key]}")
            break
    subtitle = '  |  '.join(sanitize_text(p) for p in parts) if parts else ''
    if subtitle:
        elements.append(Paragraph(subtitle, styles['cover_subtitle']))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(HRFlowable(width='35%', thickness=1.2, color=colors.HexColor('#4a9fd8'),
                               spaceAfter=20, spaceBefore=6, hAlign='LEFT'))
    shown = False
    for key, value in meta.items():
        if key in _SUBTITLE_KEYS:
            continue
        elements.append(Paragraph(
            f'<font color="#90cdf4"><b>{xml_escape(key)}:</b></font>  '
            f'<font color="#e2e8f0">{xml_escape(sanitize_text(value))}</font>',
            styles['cover_meta']))
        elements.append(Spacer(1, 0.15 * cm))
        shown = True
    if 'Date' not in meta:
        today = datetime.date.today().isoformat()
        elements.append(Paragraph(
            f'<font color="#90cdf4"><b>Date:</b></font>  '
            f'<font color="#e2e8f0">{today}</font>', styles['cover_meta']))
    return elements


def build_toc(styles) -> List[Flowable]:
    toc = TableOfContents()
    toc.levelStyles = [styles['toc1'], styles['toc2']]
    toc.dotsMinLevel = 0
    return [
        Paragraph('Contents', styles['toc_title']),
        HRFlowable(width='100%', thickness=1.2, color=C_RULE, spaceAfter=14, spaceBefore=4),
        toc,
    ]


# ── Main Conversion ─────────────────────────────────────────────────────
def convert_md_to_pdf(md_file: str, pdf_file: Optional[str] = None) -> str:
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{md_file}' not found.")
        sys.exit(1)
    except UnicodeDecodeError:
        with open(md_file, 'r', encoding='latin-1') as f:
            md_content = f.read()
    if pdf_file is None:
        pdf_file = os.path.splitext(md_file)[0] + '.pdf'
    title = extract_title(md_content)
    meta, _ = extract_metadata(md_content)
    styles = make_styles()
    doc = DocTemplate(pdf_file, pagesize=A4,
                      rightMargin=MARGIN, leftMargin=MARGIN,
                      topMargin=MARGIN, bottomMargin=MARGIN + 10,
                      title=sanitize_text(title),
                      author=meta.get('Author', BRAND),
                      subject=meta.get('Audience', 'Technical documentation'),
                      creator=f'{BRAND} markdown converter')
    doc.set_title(title)
    date_str = meta.get('Date', datetime.date.today().isoformat())
    doc.set_footer_left(f'{BRAND}  |  {date_str}')
    elements = []
    elements.extend(build_cover(meta, title, styles))
    elements.append(NextPageTemplate('Body'))
    elements.append(PageBreak())
    elements.extend(build_toc(styles))
    elements.append(PageBreak())
    elements.extend(md_to_pdf_elements(md_content, title))
    doc.multiBuild(elements)
    return pdf_file


# ── CLI ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to PDF with professional formatting')
    parser.add_argument('input', help='Input Markdown file')
    parser.add_argument('output', nargs='?', help='Output PDF file (default: same name with .pdf)')
    args = parser.parse_args()
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)
    output_file = convert_md_to_pdf(args.input, args.output)
    print(f"Successfully created: {output_file}")


if __name__ == '__main__':
    main()
