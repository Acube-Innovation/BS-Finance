"""Shared layout of the BrahMos client documents prepared by Acube Innovations (reportlab).

A4, DejaVu Sans (renders the rupee sign), Acube navy #1F3A5F and teal #1C7C8C, a cover page, a header and a footer
with "Page X of Y" on every other page.

    from acube_pdf import Doc, styles as S, table, callout, image, bullets, numbered, prompt_box, spacer
    doc = Doc("out.pdf", title="TDS in ERPNext", short_title="TDS in ERPNext – User Guide")
    story = doc.cover(title, subtitle, details=[("Prepared for", "..."), ...], key_message="...", contents=[...])
    story += [S.h1("1. ..."), S.p("..."), table([...], [40, 60]), ...]
    doc.build(story)

Run with a Python that has reportlab (not the bench env).
"""

import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
	BaseDocTemplate,
	CondPageBreak,
	Frame,
	Image,
	KeepTogether,
	ListFlowable,
	ListItem,
	NextPageTemplate,
	PageBreak,
	PageTemplate,
	Paragraph,
	Spacer,
	Table,
	TableStyle,
)

NAVY = colors.HexColor("#1F3A5F")
TEAL = colors.HexColor("#1C7C8C")
TEAL_LIGHT = colors.HexColor("#E3F1F3")
NAVY_LIGHT = colors.HexColor("#E8EDF4")
GREY = colors.HexColor("#5B6573")
GRID = colors.HexColor("#B8C4D2")
ZEBRA = colors.HexColor("#F5F7FA")
AMBER_LIGHT = colors.HexColor("#FFF4DD")
AMBER = colors.HexColor("#B7791F")
GREEN_LIGHT = colors.HexColor("#E6F4EA")
GREEN = colors.HexColor("#2F7D4A")
RED_LIGHT = colors.HexColor("#FDECEC")
RED = colors.HexColor("#B03A3A")

COMPANY = "Acube Innovations Private Limited"
COMPANY_LINE = "Acube Innovations Private Limited | Kochi & Thiruvananthapuram, Kerala, India"

PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))
# the oblique faces are not installed everywhere: italic falls back to the upright face
for _name, _file, _fallback in (("DejaVu-Oblique", "DejaVuSans-Oblique.ttf", "DejaVuSans.ttf"),
	("DejaVu-BoldOblique", "DejaVuSans-BoldOblique.ttf", "DejaVuSans-Bold.ttf")):
	_path = os.path.join(FONT_DIR, _file)
	pdfmetrics.registerFont(TTFont(_name, _path if os.path.exists(_path) else os.path.join(FONT_DIR, _fallback)))
pdfmetrics.registerFont(TTFont("DejaVuMono", os.path.join(FONT_DIR, "DejaVuSansMono.ttf")))
pdfmetrics.registerFontFamily(
	"DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu-Oblique", boldItalic="DejaVu-BoldOblique"
)


def _style(name, **kw):
	base = dict(fontName="DejaVu", fontSize=9.5, leading=13.5, textColor=colors.black, spaceAfter=5)
	base.update(kw)
	return ParagraphStyle(name, **base)


class styles:
	TITLE = _style("title", fontName="DejaVu-Bold", fontSize=24, leading=30, textColor=NAVY, spaceAfter=8)
	SUBTITLE = _style("subtitle", fontSize=12.5, leading=17, textColor=TEAL, spaceAfter=14)
	H1 = _style("h1", fontName="DejaVu-Bold", fontSize=15, leading=20, textColor=NAVY, spaceBefore=4, spaceAfter=8,
		keepWithNext=1)
	H2 = _style("h2", fontName="DejaVu-Bold", fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=8, spaceAfter=5,
		keepWithNext=1)
	H3 = _style("h3", fontName="DejaVu-Bold", fontSize=10, leading=13.5, textColor=NAVY, spaceBefore=5, spaceAfter=3,
		keepWithNext=1)
	BODY = _style("body")
	SMALL = _style("small", fontSize=8, leading=11, textColor=GREY)
	CELL = _style("cell", fontSize=8.5, leading=11.5, spaceAfter=0)
	CELL_BOLD = _style("cell_bold", fontName="DejaVu-Bold", fontSize=8.5, leading=11.5, spaceAfter=0)
	CELL_HEAD = _style("cell_head", fontName="DejaVu-Bold", fontSize=8.5, leading=11.5, textColor=colors.white,
		spaceAfter=0)
	CELL_RIGHT = _style("cell_right", fontSize=8.5, leading=11.5, spaceAfter=0, alignment=TA_RIGHT)
	CELL_RIGHT_BOLD = _style("cell_right_bold", fontName="DejaVu-Bold", fontSize=8.5, leading=11.5, spaceAfter=0,
		alignment=TA_RIGHT)
	CAPTION = _style("caption", fontName="DejaVu-Oblique", fontSize=8, leading=11, textColor=GREY,
		alignment=TA_CENTER, spaceBefore=2, spaceAfter=8)
	CALLOUT = _style("callout", fontSize=9, leading=13, spaceAfter=0)
	MONO = _style("mono", fontName="DejaVuMono", fontSize=7.8, leading=10.5, spaceAfter=0)

	@staticmethod
	def p(text, style=None):
		return Paragraph(text, style or styles.BODY)

	@staticmethod
	def h1(text):
		return Paragraph(text, styles.H1)

	@staticmethod
	def h2(text):
		return Paragraph(text, styles.H2)

	@staticmethod
	def h3(text):
		return Paragraph(text, styles.H3)

	@staticmethod
	def small(text):
		return Paragraph(text, styles.SMALL)


S = styles


def spacer(height_mm=3):
	return Spacer(1, height_mm * mm)


def _cell(value, style):
	if isinstance(value, (Paragraph, Table, Image, ListFlowable, KeepTogether)) or hasattr(value, "wrapOn"):
		return value
	return Paragraph("" if value is None else str(value), style)


def table(rows, widths, header=True, zebra=True, right_cols=(), bold_rows=(), total_row=False, font_size=None,
	head_color=NAVY, repeat=1, highlight_rows=()):
	"""rows: list of rows (strings or flowables); widths: relative widths (any unit, scaled to the content
	width); right_cols: column indexes aligned right; bold_rows: row indexes in bold; total_row: last row bold with
	a line above; highlight_rows: row indexes with a teal tint."""
	total = float(sum(widths))
	col_widths = [CONTENT_W * w / total for w in widths]
	data = []
	for r, row in enumerate(rows):
		cells = []
		for c, value in enumerate(row):
			if header and r == 0:
				style = S.CELL_HEAD
			elif c in right_cols:
				style = S.CELL_RIGHT_BOLD if (r in bold_rows or (total_row and r == len(rows) - 1)) else S.CELL_RIGHT
			else:
				style = S.CELL_BOLD if (r in bold_rows or (total_row and r == len(rows) - 1)) else S.CELL
			if font_size:
				style = ParagraphStyle(style.name + "_fs", parent=style, fontSize=font_size,
					leading=font_size * 1.35)
			cells.append(_cell(value, style))
		data.append(cells)
	t = Table(data, colWidths=col_widths, repeatRows=repeat if header else 0)
	cmds = [
		("GRID", (0, 0), (-1, -1), 0.5, GRID),
		("VALIGN", (0, 0), (-1, -1), "TOP"),
		("TOPPADDING", (0, 0), (-1, -1), 3.5),
		("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
		("LEFTPADDING", (0, 0), (-1, -1), 4.5),
		("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
	]
	if header:
		cmds.append(("BACKGROUND", (0, 0), (-1, 0), head_color))
	start = 1 if header else 0
	if zebra:
		for r in range(start, len(rows)):
			if (r - start) % 2 == 1:
				cmds.append(("BACKGROUND", (0, r), (-1, r), ZEBRA))
	for r in highlight_rows:
		cmds.append(("BACKGROUND", (0, r), (-1, r), TEAL_LIGHT))
	if total_row:
		cmds.append(("LINEABOVE", (0, len(rows) - 1), (-1, len(rows) - 1), 1, NAVY))
		cmds.append(("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1), NAVY_LIGHT))
	t.setStyle(TableStyle(cmds))
	return t


def key_value(rows, widths=(28, 72)):
	"""A two-column details table: label (tinted, bold) | value."""
	total = float(sum(widths))
	col_widths = [CONTENT_W * w / total for w in widths]
	data = [[_cell(k, S.CELL_BOLD), _cell(v, S.CELL)] for k, v in rows]
	t = Table(data, colWidths=col_widths)
	t.setStyle(TableStyle([
		("GRID", (0, 0), (-1, -1), 0.5, GRID),
		("BACKGROUND", (0, 0), (0, -1), NAVY_LIGHT),
		("VALIGN", (0, 0), (-1, -1), "TOP"),
		("TOPPADDING", (0, 0), (-1, -1), 4),
		("BOTTOMPADDING", (0, 0), (-1, -1), 4),
		("LEFTPADDING", (0, 0), (-1, -1), 5),
	]))
	return t


CALLOUT_KINDS = {
	"note": (TEAL_LIGHT, TEAL, "Note"),
	"key": (NAVY_LIGHT, NAVY, "Key message"),
	"warn": (AMBER_LIGHT, AMBER, "Important"),
	"ok": (GREEN_LIGHT, GREEN, "Result"),
	"error": (RED_LIGHT, RED, "Problem"),
}


def callout(text, kind="note", title=None, width=None):
	"""A tinted box with a coloured bar on the left; text may hold several paragraphs (list of strings)."""
	fill, bar, default_title = CALLOUT_KINDS[kind]
	heading = title if title is not None else default_title
	parts = text if isinstance(text, list) else [text]
	content = []
	if heading:
		content.append(Paragraph(f"<font color='{bar.hexval().replace('0x', '#')}'><b>{heading}</b></font>",
			S.CALLOUT))
	for part in parts:
		content.append(part if hasattr(part, "wrapOn") else Paragraph(part, S.CALLOUT))
	w = width or CONTENT_W
	inner = Table([[c] for c in content], colWidths=[w - 4 - 14])  # box width less the bar and the padding
	inner.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
		("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
	t = Table([["", inner]], colWidths=[4, w - 4])
	t.setStyle(TableStyle([
		("BACKGROUND", (0, 0), (0, 0), bar),
		("BACKGROUND", (1, 0), (1, 0), fill),
		("LEFTPADDING", (1, 0), (1, 0), 7),
		("RIGHTPADDING", (1, 0), (1, 0), 7),
		("TOPPADDING", (1, 0), (1, 0), 6),
		("BOTTOMPADDING", (1, 0), (1, 0), 6),
		("LEFTPADDING", (0, 0), (0, 0), 0),
		("RIGHTPADDING", (0, 0), (0, 0), 0),
	]))
	return KeepTogether([t, Spacer(1, 3 * mm)])


def prompt_box(text):
	"""Monospaced text in a light box (code, formulas, exact values)."""
	t = Table([[Paragraph(text.replace("\n", "<br/>"), S.MONO)]], colWidths=[CONTENT_W])
	t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ZEBRA), ("BOX", (0, 0), (-1, -1), 0.5, GRID),
		("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 5),
		("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
	return t


def image(path, width_mm=None, max_height_mm=None, caption=None, border=True):
	"""An image scaled to the width (default: content width) and at most max_height_mm high, with a thin border
	and an optional caption."""
	from reportlab.lib.utils import ImageReader

	iw, ih = ImageReader(path).getSize()
	width = (width_mm * mm) if width_mm else CONTENT_W
	height = width * ih / iw
	if max_height_mm and height > max_height_mm * mm:
		height = max_height_mm * mm
		width = height * iw / ih
	img = Image(path, width=width, height=height)
	parts = []
	if border:
		t = Table([[img]], colWidths=[width + 2])
		t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, GRID), ("LEFTPADDING", (0, 0), (-1, -1), 0.5),
			("RIGHTPADDING", (0, 0), (-1, -1), 0.5), ("TOPPADDING", (0, 0), (-1, -1), 0.5),
			("BOTTOMPADDING", (0, 0), (-1, -1), 0.5)]))
		parts.append(t)
	else:
		parts.append(img)
	if caption:
		parts.append(Paragraph(caption, S.CAPTION))
	else:
		parts.append(Spacer(1, 2 * mm))
	return KeepTogether(parts)


def bullets(items, style=None):
	style = style or S.BODY
	return ListFlowable([ListItem(_cell(i, style), leftIndent=12, value="•") for i in items],
		bulletType="bullet", start="•", leftIndent=12, bulletFontName="DejaVu", bulletFontSize=8,
		bulletColor=TEAL, spaceAfter=4)


def numbered(items, style=None, start=1):
	style = style or S.BODY
	return ListFlowable([ListItem(_cell(i, style), leftIndent=14) for i in items], bulletType="1", start=start, bulletFormat="%s.",
		leftIndent=14, bulletFontName="DejaVu-Bold", bulletFontSize=8.5, bulletColor=NAVY, spaceAfter=4)


def status_chip(text, kind="ok"):
	fill, bar, _ = CALLOUT_KINDS[kind]
	style = ParagraphStyle("chip", parent=S.CELL_BOLD, textColor=bar, alignment=TA_CENTER)
	t = Table([[Paragraph(text, style)]])
	t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fill), ("TOPPADDING", (0, 0), (-1, -1), 1.5),
		("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
	return t


class _NumberedCanvas(rl_canvas.Canvas):
	"""Canvas that knows the page count, for "Page X of Y"."""

	def __init__(self, *args, doc=None, **kwargs):
		super().__init__(*args, **kwargs)
		self._saved_pages = []
		self._acube_doc = doc

	def showPage(self):
		self._saved_pages.append(dict(self.__dict__))
		self._startPage()

	def save(self):
		total = len(self._saved_pages)
		for state in self._saved_pages:
			self.__dict__.update(state)
			self._acube_doc._draw_frame(self, self._pageNumber, total)
			super().showPage()
		super().save()


class Doc:
	def __init__(self, path, title, short_title=None, client="BrahMos Aerospace Thiruvananthapuram (BATL)",
		doc_date=None, audience_line=None):
		self.path = path
		self.title = title
		self.short_title = short_title or title
		self.client = client
		self.doc_date = doc_date or date.today().strftime("%d %B %Y").lstrip("0")
		self.audience_line = audience_line

	# --- cover --------------------------------------------------------------------------------------------
	def cover(self, title, subtitle, details=(), key_message=None, contents=(), note=None):
		story = [Spacer(1, 30 * mm), Paragraph(title, S.TITLE), Paragraph(subtitle, S.SUBTITLE)]
		if self.audience_line:
			story.append(Paragraph(self.audience_line, S.SMALL))
		story.append(Spacer(1, 4 * mm))
		if details:
			story += [key_value(list(details)), Spacer(1, 6 * mm)]
		if key_message:
			story.append(callout(key_message, "key"))
		if contents:
			story.append(Paragraph("Contents", S.H2))
			rows = [[f"{i}.", c] for i, c in enumerate(contents, 1)]
			t = Table([[Paragraph(a, S.CELL_BOLD), Paragraph(b, S.CELL)] for a, b in rows],
				colWidths=[10 * mm, CONTENT_W - 10 * mm])
			t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, GRID), ("TOPPADDING", (0, 0), (-1, -1), 3),
				("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 2)]))
			story.append(t)
		if note:
			story += [Spacer(1, 5 * mm), Paragraph(note, S.SMALL)]
		story += [NextPageTemplate("body"), PageBreak()]
		return story

	# --- page decoration -----------------------------------------------------------------------------------
	def _draw_frame(self, c, page_no, total):
		c.saveState()
		if page_no == 1:
			# cover: navy band with the company name, teal rule
			c.setFillColor(NAVY)
			c.rect(0, PAGE_H - 34 * mm, PAGE_W, 34 * mm, stroke=0, fill=1)
			c.setFillColor(TEAL)
			c.rect(0, PAGE_H - 36 * mm, PAGE_W, 2 * mm, stroke=0, fill=1)
			c.setFillColor(colors.white)
			c.setFont("DejaVu-Bold", 17)
			c.drawString(MARGIN_X, PAGE_H - 14 * mm, "ACUBE INNOVATIONS PRIVATE LIMITED")
			c.setFont("DejaVu", 9.5)
			c.drawString(MARGIN_X, PAGE_H - 20.5 * mm, "Official ERPNext / Frappe Implementation Partner")
			c.setFont("DejaVu", 8.5)
			c.drawString(MARGIN_X, PAGE_H - 30.5 * mm, f"Prepared for {self.client}")
			c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 30.5 * mm, self.doc_date)
			c.setFillColor(NAVY)
			c.rect(0, 0, PAGE_W, 14 * mm, stroke=0, fill=1)
			c.setFillColor(colors.white)
			c.setFont("DejaVu", 8)
			c.drawString(MARGIN_X, 5.5 * mm, COMPANY_LINE)
		else:
			c.setFillColor(NAVY)
			c.setFont("DejaVu-Bold", 8.5)
			c.drawString(MARGIN_X, PAGE_H - 11 * mm, "ACUBE INNOVATIONS")
			c.setFont("DejaVu", 8.5)
			c.setFillColor(GREY)
			c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 11 * mm, self.short_title)
			c.setStrokeColor(TEAL)
			c.setLineWidth(1.2)
			c.line(MARGIN_X, PAGE_H - 13.5 * mm, PAGE_W - MARGIN_X, PAGE_H - 13.5 * mm)
			c.setStrokeColor(GRID)
			c.setLineWidth(0.5)
			c.line(MARGIN_X, 13 * mm, PAGE_W - MARGIN_X, 13 * mm)
			c.setFont("DejaVu", 7.5)
			c.setFillColor(GREY)
			c.drawString(MARGIN_X, 8.5 * mm, f"{COMPANY} | {self.client}")
			c.drawRightString(PAGE_W - MARGIN_X, 8.5 * mm, f"Page {page_no} of {total}")
		c.restoreState()

	def build(self, story):
		doc = BaseDocTemplate(self.path, pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X,
			topMargin=20 * mm, bottomMargin=18 * mm, title=self.title, author=COMPANY, subject=self.short_title,
			creator=COMPANY)
		cover_frame = Frame(MARGIN_X, 18 * mm, CONTENT_W, PAGE_H - 18 * mm - 40 * mm, id="cover")
		body_frame = Frame(MARGIN_X, 17 * mm, CONTENT_W, PAGE_H - 17 * mm - 18 * mm, id="body")
		doc.addPageTemplates([PageTemplate(id="cover", frames=[cover_frame]),
			PageTemplate(id="body", frames=[body_frame])])
		owner = self

		class _Canvas(_NumberedCanvas):
			def __init__(self, *args, **kwargs):
				super().__init__(*args, doc=owner, **kwargs)

		doc.build(story, canvasmaker=_Canvas)
		return self.path


__all__ = [
	"Doc", "S", "styles", "table", "key_value", "callout", "prompt_box", "image", "bullets", "numbered", "spacer",
	"status_chip", "PageBreak", "CondPageBreak", "KeepTogether", "Paragraph", "Spacer", "Table", "TableStyle",
	"NAVY", "TEAL", "TEAL_LIGHT", "NAVY_LIGHT", "GREY", "GRID", "ZEBRA", "CONTENT_W", "mm", "colors",
]
