#!/usr/bin/env python3
"""
Professional Markdown-to-PDF converter with comprehensive formatting support.
Produces polished technical documents suitable for distribution.

Usage: python convert_md_to_pdf.py input.md [output.pdf]

Requirements: pip install reportlab
"""

import argparse
import os
import re
import sys
from collections import OrderedDict
from typing import List, Optional, Tuple, Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, Flowable,
        NextPageTemplate, PageTemplate, BaseDocTemplate, Frame,
    )
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
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
C_ROW_ALT   = colors.HexColor('#ebf4ff')
C_RULE      = colors.HexColor('#e2e8f0')
C_COVER_BG  = colors.HexColor('#1a365d')
C_COVER_ACC = colors.HexColor('#2b6cb0')
C_INLINE_CODE = colors.HexColor('#c7254e')
C_CODE_TEXT   = colors.HexColor('#2d3748')
C_BLOCKQUOTE = colors.HexColor('#4a5568')

# Unicode character replacements for PDF compatibility
CHAR_REPLACEMENTS = {
    '\u26a0\ufe0f': '\u26a0', '\u2705': '\u2713', '\u274c': '\u2717',
    '\U0001f4c4': '[DOC]', '\U0001f4ca': '[CHART]', '\U0001f50d': '[FIND]',
    '\U0001f4cb': '[LIST]', '\U0001f4a1': '[TIP]', '\U0001f527': '[TOOL]',
    '\U0001f4cc': '[PIN]', '\U0001f3af': '[TARGET]', '\U0001f680': '[LAUNCH]',
    '\u2013': '--', '\u2014': '---', '\u2018': "'", '\u2019': "'",
    '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2190': '<-', '\u2192': '->',
    '\u00d7': 'x', '\u2022': '•', '\u25cf': '●', '\u25cb': '○',
    '\u2610': '☐', '\u2611': '☑', '\u2713': '✓', '\u2717': '✗',
}

def sanitize_text(text: str) -> str:
    """Replace characters that don't render well in standard PDF fonts."""
    if not text:
        return text
    for bad, good in CHAR_REPLACEMENTS.items():
        text = text.replace(bad, good)
    return ''.join(ch if ord(ch) < 128 else '?' for ch in text)

def inline_md_to_xml(text: str) -> str:
    """Convert inline markdown formatting to reportlab XML tags."""
    if not text:
        return text
    text = sanitize_text(text)
    
    # Extract inline code spans first (protect from bold/italic regex)
    code_spans = []
    def save_code(m):
        idx = len(code_spans)
        content = m.group(1).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        code_spans.append(
            f'<font name="Courier" size="9" backColor="#edf2f7">'
            f'<font color="#c7254e">&nbsp;{content}&nbsp;</font></font>'
        )
        return f'\x00C{idx}\x00'
    text = re.sub(r'`(.+?)`', save_code, text, flags=re.DOTALL)
    
    # Bold + italic, then bold, then italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    # Links: [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'<font color="#3182ce"><u>\1</u></font>', text)
    # Checkboxes
    text = re.sub(r'- \[x\] ', '\u2611 ', text, flags=re.IGNORECASE)
    text = re.sub(r'- \[ \] ', '\u2610 ', text)
    # Restore code spans
    for idx, code in enumerate(code_spans):
        text = text.replace(f'\x00C{idx}\x00', code)
    return text

# ── Table Parsing ────────────────────────────────────────────────────────
def is_table_separator(line: str) -> bool:
    line = line.strip()
    return line.startswith('|') and line.endswith('|') and \
           all(re.match(r'^[\s\-:]+$', c) for c in [c.strip() for c in line.split('|')[1:-1]])

def parse_md_table(lines: List[str], start_idx: int) -> Tuple[List[List[str]], int]:
    """Parse markdown table starting at start_idx. Returns (rows, next_idx)."""
    rows = []
    idx = start_idx
    while idx < len(lines):
        line = lines[idx].rstrip()
        if not line.startswith('|'):
            break
        if is_table_separator(line):
            idx += 1
            continue
        cells = [inline_md_to_xml(c.strip()) for c in line.split('|')[1:-1]]
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
def make_styles():
    base = getSampleStyleSheet()
    return {
        'cover_title': ParagraphStyle('CoverTitle', fontSize=28, leading=34, textColor=colors.white,
            fontName='Helvetica-Bold', alignment=TA_LEFT, spaceAfter=10),
        'cover_subtitle': ParagraphStyle('CoverSubtitle', fontSize=14, leading=18,
            textColor=colors.HexColor('#bee3f8'), fontName='Helvetica', alignment=TA_LEFT, spaceAfter=20),
        'cover_meta': ParagraphStyle('CoverMeta', fontSize=10, leading=16, textColor=colors.white,
            fontName='Helvetica', spaceAfter=4),
        'h1': ParagraphStyle('H1', parent=base['Heading1'], fontSize=24, leading=30,
            textColor=C_PRIMARY, fontName='Helvetica-Bold', spaceAfter=8, spaceBefore=30),
        'h2': ParagraphStyle('H2', parent=base['Heading2'], fontSize=16, leading=22,
            textColor=C_SECONDARY, fontName='Helvetica-Bold', spaceAfter=6, spaceBefore=22),
        'h3': ParagraphStyle('H3', parent=base['Heading3'], fontSize=13, leading=18,
            textColor=C_ACCENT, fontName='Helvetica-Bold', spaceAfter=4, spaceBefore=16),
        'h4': ParagraphStyle('H4', parent=base['Heading4'], fontSize=11, leading=15,
            textColor=colors.HexColor('#4a5568'), fontName='Helvetica-Bold', spaceAfter=3, spaceBefore=12),
        'h5': ParagraphStyle('H5', parent=base['Heading5'], fontSize=10, leading=14,
            textColor=colors.HexColor('#718096'), fontName='Helvetica-Bold', spaceAfter=2, spaceBefore=10),
        'h6': ParagraphStyle('H6', parent=base['Heading6'], fontSize=9, leading=12,
            textColor=colors.HexColor('#a0aec0'), fontName='Helvetica-Bold', spaceAfter=2, spaceBefore=8),
        'body': ParagraphStyle('Body', parent=base['BodyText'], fontSize=10.5, leading=16,
            alignment=TA_JUSTIFY, fontName='Helvetica', spaceAfter=6),
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
        'code': ParagraphStyle('CodeBlock', parent=base['Code'], fontSize=8.5, leading=12,
            fontName='Courier', backColor=C_CODE_BG, leftIndent=10, rightIndent=10,
            spaceAfter=10, spaceBefore=8, borderPadding=8, borderColor=C_BORDER, borderWidth=0.5),
        'quote': ParagraphStyle('Quote', parent=base['BodyText'], fontSize=10, leading=15,
            fontName='Helvetica-Oblique', leftIndent=24, rightIndent=24, textColor=C_BLOCKQUOTE,
            spaceAfter=8, spaceBefore=8),
        'table_cell': ParagraphStyle('TCell', parent=base['Normal'], fontSize=9, leading=12.5, fontName='Helvetica'),
        'table_header': ParagraphStyle('THead', parent=base['Normal'], fontSize=9.5, leading=13,
            fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_CENTER),
    }

# ── Custom Flowables ─────────────────────────────────────────────────────
class SectionRule(HRFlowable):
    def __init__(self, color=C_RULE, thickness=1.5, width='100%'):
        HRFlowable.__init__(self, width=width, thickness=thickness, color=color, spaceAfter=8, spaceBefore=4)

class ThinRule(HRFlowable):
    def __init__(self):
        HRFlowable.__init__(self, width='100%', thickness=0.5, color=C_RULE, spaceAfter=10, spaceBefore=10)

class CodeBlockFlowable(Flowable):
    def __init__(self, code_text: str, language: str = '', width: float = CONTENT_W):
        Flowable.__init__(self)
        self.code_text = code_text or ''
        self.language = language
        self.width = width
    def wrap(self, availWidth, availHeight):
        self.width = min(self.width, availWidth)
        lines = self.code_text.split('\n')
        self.rows = [line.replace('\t', '    ')[:120] for line in lines]
        line_h = 11
        header_h = 20 if self.language else 0
        self.height = header_h + len(self.rows) * line_h + 20
        return (self.width, self.height)
    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        line_h = 11
        header_h = 20 if self.language else 0
        pad = 12
        c.setFillColor(C_CODE_BG)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=1)
        if self.language:
            c.setFillColor(C_BORDER)
            c.roundRect(0, h - header_h, w, header_h, 4, fill=1, stroke=0)
            c.setFillColor(C_BORDER)
            c.rect(0, h - header_h, w, 4, fill=1, stroke=0)
            c.setFillColor(C_MUTED)
            c.setFont('Helvetica-Bold', 8)
            c.drawString(pad, h - header_h + 6, self.language.upper())
        c.setFillColor(C_CODE_TEXT)
        c.setFont('Courier', 8.5)
        y = h - header_h - 12
        for row in self.rows:
            c.drawString(pad, y, row)
            y -= line_h

# ── Page Templates ───────────────────────────────────────────────────────
class DocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame_cover = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2 * MARGIN, id='cover_frame')
        frame_body = Frame(MARGIN, MARGIN + 10, CONTENT_W, PAGE_H - 2 * MARGIN - 30, id='body_frame')
        cover_tpl = PageTemplate(id='Cover', frames=[frame_cover], onPage=self._draw_cover)
        body_tpl = PageTemplate(id='Body', frames=[frame_body], onPage=self._draw_body)
        self.addPageTemplates([cover_tpl, body_tpl])
        self._doc_title = ''
        self._cover_offset = 0
    def set_title(self, title):
        self._doc_title = title
    def set_cover_offset(self, n):
        self._cover_offset = n
    def _draw_cover(self, canvas, doc):
        c = canvas
        c.saveState()
        c.setFillColor(C_COVER_BG)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setFillColor(C_COVER_ACC)
        c.rect(0, 0, 10 * mm, PAGE_H, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#2a4365'))
        c.circle(PAGE_W - 3 * cm, PAGE_H - 3 * cm, 5 * cm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#23415c'))
        c.circle(PAGE_W - 2 * cm, PAGE_H - 2.5 * cm, 3.5 * cm, fill=1, stroke=0)
        c.setStrokeColor(C_COVER_ACC)
        c.setLineWidth(1.5)
        c.line(MARGIN, 2.5 * cm, PAGE_W - MARGIN, 2.5 * cm)
        c.setFont('Helvetica', 7.5)
        c.setFillColor(C_MUTED)
        c.drawString(MARGIN, 2 * cm, "Generated by iA from programmers.io")
        c.drawRightString(PAGE_W - MARGIN, 2 * cm, "Confidential")
        c.restoreState()
    def _draw_body(self, canvas, doc):
        c = canvas
        c.saveState()
        c.setStrokeColor(C_ACCENT)
        c.setLineWidth(1.5)
        c.line(MARGIN, PAGE_H - MARGIN + 14, PAGE_W - MARGIN, PAGE_H - MARGIN + 14)
        if self._doc_title:
            c.setFont('Helvetica-Bold', 8)
            c.setFillColor(C_MUTED)
            c.drawString(MARGIN, PAGE_H - MARGIN + 18, self._doc_title[:80])
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.line(MARGIN, MARGIN - 6, PAGE_W - MARGIN, MARGIN - 6)
        page_num = doc.page - self._cover_offset
        if page_num > 0:
            c.setFont('Helvetica', 8)
            c.setFillColor(C_MUTED)
            c.drawRightString(PAGE_W - MARGIN, MARGIN - 16, f"Page {page_num}")
        c.restoreState()

# ── Metadata Extraction ──────────────────────────────────────────────────
def extract_metadata(md_content: str) -> Tuple[OrderedDict, int]:
    meta = OrderedDict()
    lines = md_content.split('\n')
    in_header = False
    skip_count = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            if in_header and meta:
                skip_count = i + 1
                break
            continue
        if re.match(r'\*\*[^*]+\*\*:', line):
            in_header = True
            m = re.match(r'\*\*([^*]+)\*\*:\s*(.+)', line)
            if m:
                meta[m.group(1).strip()] = m.group(2).strip()
                skip_count = i + 1
        elif in_header and line == '---':
            skip_count = i + 1
            break
        elif in_header and not line.startswith('**') and meta:
            skip_count = i
            break
        elif in_header:
            skip_count = i + 1
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
def parse_list(lines: List[str], start_idx: int, ordered: bool) -> Tuple[List[Dict], int]:
    items = []
    idx = start_idx
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
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
        # Handle multi-line list items
        while idx + 1 < len(lines) and (lines[idx + 1].startswith(' ') or lines[idx + 1].startswith('\t')):
            idx += 1
            items[-1]['text'] += ' ' + lines[idx].strip()
        idx += 1
    return items, idx

# ── Markdown to PDF Elements ─────────────────────────────────────────────
def md_to_pdf_elements(md_content: str, doc_title: str = '') -> List[Flowable]:
    styles = make_styles()
    elements = []
    lines = md_content.split('\n')
    i = 0
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
            elements.append(Spacer(1, 2))
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
                elements.append(CodeBlockFlowable('\n'.join(code_lines), lang))
        # Table
        elif line.strip().startswith('|'):
            rows, new_idx = parse_md_table(lines, i)
            if rows:
                elements.append(Spacer(1, 4))
                table = create_table(rows)
                if table:
                    elements.append(table)
                elements.append(Spacer(1, 4))
            i = new_idx
            continue
        # Blockquote
        elif line.strip().startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(inline_md_to_xml(lines[i].strip()[1:].strip()))
                i += 1
            if quote_lines:
                elements.append(Paragraph('<br/>'.join(quote_lines), styles['quote']))
        # Unordered List
        elif re.match(r'^[\s]*[-*+] ', line):
            list_items, new_idx = parse_list(lines, i, ordered=False)
            for item in list_items:
                level = item['level']
                text = inline_md_to_xml(item['text'])
                if level == 0:
                    elements.append(Paragraph(f'• {text}', styles['bullet']))
                elif level == 1:
                    elements.append(Paragraph(f'  ◦ {text}', styles['bullet2']))
                else:
                    elements.append(Paragraph(f'    ▪ {text}', styles['bullet3']))
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
                    elements.append(Paragraph(f'    {num}. {text}', styles['number2']))
                else:
                    elements.append(Paragraph(f'        {num}. {text}', styles['number3']))
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
        i += 1
    return elements

def create_table(rows: List[List[str]]) -> Optional[Table]:
    if not rows:
        return None
    max_cols = max(len(row) for row in rows)
    for row in rows:
        while len(row) < max_cols:
            row.append('')
    col_widths = calc_col_widths(rows, CONTENT_W)
    data = []
    for row_idx, row in enumerate(rows):
        row_data = []
        for col_idx, cell in enumerate(row):
            if row_idx == 0:
                row_data.append(Paragraph(f'<b>{cell}</b>', make_styles()['table_header']))
            else:
                row_data.append(Paragraph(cell, make_styles()['table_cell']))
        data.append(row_data)
    if not data:
        return None
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0,0), (-1,0), C_TABLE_HDR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ('TOPPADDING', (0,1), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('LINEBELOW', (0,0), (-1,0), 1.5, C_TABLE_HDR),
    ]
    for row_idx in range(1, len(data)):
        if row_idx % 2 == 0:
            style.append(('BACKGROUND', (0,row_idx), (-1,row_idx), C_ROW_ALT))
    table.setStyle(TableStyle(style))
    return table

# ── Main Conversion ─────────────────────────────────────────────────────
def convert_md_to_pdf(md_file: str, pdf_file: str = None) -> str:
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
    doc = DocTemplate(pdf_file, pagesize=A4,
                      rightMargin=MARGIN, leftMargin=MARGIN,
                      topMargin=MARGIN, bottomMargin=MARGIN + 10)
    doc.set_title(title)
    doc.set_cover_offset(1)
    elements = []
    elements.append(NextPageTemplate('Cover'))
    elements.append(PageBreak())
    elements.extend(build_cover(meta, title, make_styles()))
    elements.append(NextPageTemplate('Body'))
    elements.append(PageBreak())
    elements.extend(md_to_pdf_elements(md_content, title))
    doc.build(elements)
    return pdf_file

def build_cover(meta: OrderedDict, title_text: str, styles: dict) -> List[Flowable]:
    elements = [Spacer(1, 4 * cm)]
    elements.append(Paragraph(title_text, styles['cover_title']))
    elements.append(Spacer(1, 0.4 * cm))
    parts = []
    for key in ['Member type', 'Type', 'Program']:
        if key in meta:
            parts.append(meta[key])
            break
    for key in ['Source file', 'File']:
        if key in meta:
            parts.append(f"Source: {meta[key]}")
            break
    for key in ['Library version documented', 'Library']:
        if key in meta:
            parts.append(f"Library: {meta[key]}")
            break
    subtitle = '  |  '.join(parts) if parts else 'Technical Specification'
    elements.append(Paragraph(subtitle, styles['cover_subtitle']))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(HRFlowable(width='35%', thickness=1.2, color=colors.HexColor('#4a9fd8'),
                                spaceAfter=20, spaceBefore=6, hAlign='LEFT'))
    for key in ['Author', 'Date', 'Audience', 'Version', 'Status']:
        if key in meta:
            elements.append(Paragraph(
                f'<font color="#90cdf4"><b>{key}:</b></font>  '
                f'<font color="#e2e8f0">{meta[key]}</font>', styles['cover_meta']))
            elements.append(Spacer(1, 0.15 * cm))
    return elements

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
    print(f"✓ Successfully created: {output_file}")

if __name__ == '__main__':
    main()
