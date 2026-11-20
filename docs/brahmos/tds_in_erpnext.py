"""Build "TDS in ERPNext - User Guide.pdf" for the Accounts team of BrahMos Aerospace Thiruvananthapuram Limited.

Run with a Python that has reportlab (not the bench env):
    <venv>/bin/python tds_in_erpnext.py

Every amount in the worked examples is computed here with Decimal, using the same threshold rule as ERPNext 15.90.1
(erpnext/accounts/doctype/tax_withholding_category/tax_withholding_category.py: get_tax_amount / get_tds_amount),
and every ledger table is asserted to balance, so the PDF cannot carry an arithmetic error.

Field, report and message names were checked against the installed code (ERPNext 15.90.1, India Compliance
15.25.6). The "BATL setup status" figures come from read-only SELECTs on the site database on 18 November 2026.
"""

import os
import shutil
import sys
from decimal import ROUND_HALF_UP
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.pdfbase.pdfmetrics import stringWidth  # noqa: E402
from reportlab.platypus import Flowable  # noqa: E402

from acube_pdf import (  # noqa: E402
	CALLOUT_KINDS,
	CONTENT_W,
	GREY,
	GRID,
	NAVY,
	NAVY_LIGHT,
	TEAL,
	ZEBRA,
	CondPageBreak,
	Doc,
	KeepTogether,
	Paragraph,
	S,
	Spacer,
	Table,
	TableStyle,
	bullets,
	colors,
	mm,
	numbered,
	spacer,
	table,
)

OUT_PDF = os.path.join(HERE, "TDS in ERPNext - User Guide.pdf")
COPY_TO = "/home/acubeadmin/Downloads/BATL ERP - TDS in ERPNext - User Guide.pdf"
COMPANY_NAME = "BrahMos Aerospace Thiruvananthapuram Limited"
RUPEE = "₹"

# ---------------------------------------------------------------------------------------------------------------
# money helpers
# ---------------------------------------------------------------------------------------------------------------
PAISE = D("0.01")


def inr(value, decimals=True):
	"""Indian digit grouping: 1,25,000.00 / 48,00,000.00."""
	v = D(value).quantize(PAISE, ROUND_HALF_UP)
	sign = "-" if v < 0 else ""
	whole, frac = f"{abs(v):.2f}".split(".")
	if len(whole) > 3:
		head, tail = whole[:-3], whole[-3:]
		groups = []
		while len(head) > 2:
			groups.insert(0, head[-2:])
			head = head[:-2]
		if head:
			groups.insert(0, head)
		whole = ",".join(groups) + "," + tail
	return sign + whole + ("." + frac if decimals else "")


def rs(value):
	"""Rupee amount for running text: whole rupees without paise, otherwise with paise."""
	v = D(value).quantize(PAISE, ROUND_HALF_UP)
	return RUPEE + (inr(v, decimals=False) if v == v.to_integral_value() else inr(v))


assert inr(125000) == "1,25,000.00" and inr(4800000) == "48,00,000.00" and inr(800) == "800.00"
assert inr(12345678) == "1,23,45,678.00" and rs(5300000) == f"{RUPEE}53,00,000"


def pct(rate, amount):
	return (D(amount) * D(rate) / 100).quantize(PAISE, ROUND_HALF_UP)


def erpnext_tds(bills, rate, single, cumulative, excess_only=False):
	"""TDS on each bill of one supplier (PAN) under one category within one rate period, following ERPNext 15:
	- once TDS has been deducted in the period, every later bill is taxed in full (no threshold check);
	- otherwise TDS starts when this bill >= Single Transaction Threshold, or this bill + earlier untaxed bills
	  >= Cumulative Transaction Threshold; the base is then this bill + all earlier untaxed bills;
	- with Only Deduct Tax On Excess Amount, when the cumulative threshold is breached the base is
	  (earlier untaxed bills + this bill - cumulative threshold);
	- a threshold of 0 is not used."""
	rate, single, cumulative = D(rate), D(single), D(cumulative)
	out, untaxed, deducted = [], D(0), False
	for amount in bills:
		amount = D(amount)
		if deducted:
			tds = pct(rate, amount)
		else:
			cumulative_hit = bool(cumulative) and (untaxed + amount) >= cumulative
			if (single and amount >= single) or cumulative_hit:
				base = untaxed + amount
				if cumulative_hit and excess_only:
					base = untaxed + amount - cumulative
				tds = pct(rate, base) if base > 0 else D(0)
			else:
				tds = D(0)
		if tds > 0:
			deducted = True
		elif not deducted:
			untaxed += amount
		out.append(tds)
	return out


def check_balanced(entries):
	debit = sum((D(e[1]) for e in entries), D(0))
	credit = sum((D(e[2]) for e in entries), D(0))
	assert debit == credit, f"ledger does not balance: {debit} != {credit} in {entries}"
	return debit, credit


def gl_table(entries):
	"""Full-width ledger table; entries: (account, debit, credit). Asserts that the entry balances."""
	debit, credit = check_balanced(entries)
	rows = [["Account", f"Debit {RUPEE}", f"Credit {RUPEE}"]]
	for account, dr, cr in entries:
		rows.append([account, inr(dr) if D(dr) else "", inr(cr) if D(cr) else ""])
	rows.append(["Total", inr(debit), inr(credit)])
	return table(rows, [62, 19, 19], right_cols=(1, 2), total_row=True)


def gl_table_narrow(entries, width):
	"""Ledger table for half the page, styled like acube_pdf.table(); asserts that the entry balances."""
	debit, credit = check_balanced(entries)
	size = 8
	head = ParagraphStyle("gl_h", parent=S.CELL_HEAD, fontSize=size, leading=size * 1.35)
	cell = ParagraphStyle("gl_c", parent=S.CELL, fontSize=size, leading=size * 1.35)
	right = ParagraphStyle("gl_r", parent=S.CELL_RIGHT, fontSize=size, leading=size * 1.35)
	cell_b = ParagraphStyle("gl_cb", parent=S.CELL_BOLD, fontSize=size, leading=size * 1.35)
	right_b = ParagraphStyle("gl_rb", parent=S.CELL_RIGHT_BOLD, fontSize=size, leading=size * 1.35)
	num_w = max(stringWidth(inr(debit), "DejaVu-Bold", size), stringWidth(f"Credit {RUPEE}", "DejaVu-Bold", size))
	num_w += 12
	data = [[Paragraph("Account", head), Paragraph(f"Debit {RUPEE}", head), Paragraph(f"Credit {RUPEE}", head)]]
	for account, dr, cr in entries:
		data.append([Paragraph(account, cell), Paragraph(inr(dr) if D(dr) else "", right),
			Paragraph(inr(cr) if D(cr) else "", right)])
	data.append([Paragraph("Total", cell_b), Paragraph(inr(debit), right_b), Paragraph(inr(credit), right_b)])
	t = Table(data, colWidths=[width - 2 * num_w, num_w, num_w])
	last = len(data) - 1
	cmds = [
		("GRID", (0, 0), (-1, -1), 0.5, GRID),
		("VALIGN", (0, 0), (-1, -1), "TOP"),
		("TOPPADDING", (0, 0), (-1, -1), 3.5),
		("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
		("LEFTPADDING", (0, 0), (-1, -1), 4.5),
		("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
		("BACKGROUND", (0, 0), (-1, 0), NAVY),
		("LINEABOVE", (0, last), (-1, last), 1, NAVY),
		("BACKGROUND", (0, last), (-1, last), NAVY_LIGHT),
	]
	for r in range(2, last, 2):
		cmds.append(("BACKGROUND", (0, r), (-1, r), ZEBRA))
	t.setStyle(TableStyle(cmds))
	return t


def box(text, kind="note", title=None):
	"""Same look as acube_pdf.callout(), but the text column is sized to the space inside the box (the shared
	helper gives it 8 pt more than the padded cell, so long lines run past the right edge of the tint)."""
	fill, bar, default_title = CALLOUT_KINDS[kind]
	heading = default_title if title is None else title
	parts = text if isinstance(text, list) else [text]
	content = []
	if heading:
		content.append(Paragraph(f"<font color='{bar.hexval().replace('0x', '#')}'><b>{heading}</b></font>",
			S.CALLOUT))
	content += [Paragraph(p, S.CALLOUT) for p in parts]
	w = CONTENT_W
	inner = Table([[c] for c in content], colWidths=[w - 4 - 14])
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


# ---------------------------------------------------------------------------------------------------------------
# worked examples (all figures computed, then checked against the client's brief)
# ---------------------------------------------------------------------------------------------------------------
TDS_CONTRACTORS = "TDS Payment to Contractors - BATL"
TDS_PROFESSIONAL = "TDS Professional Services - BATL"
TDS_RENT = "TDS Rent - BATL"
TDS_GOODS = "TDS Purchase Goods - BATL"
SUPPLIER = "Supplier account (Creditors)"

# A: contractor (others, 2%), one bill of 40,000 + 18% GST (9% CGST + 9% SGST)
A_BASE = D(40000)
A_CGST = pct(9, A_BASE)
A_SGST = pct(9, A_BASE)
A_TDS = erpnext_tds([A_BASE], 2, 30000, 100000)[0]
A_GROSS = A_BASE + A_CGST + A_SGST
A_PAYABLE = A_GROSS - A_TDS
assert A_TDS == 800 == pct(2, A_BASE)
A_GL = [
	("Sub-contract / job-work expense", A_BASE, 0),
	("Input CGST (9%)", A_CGST, 0),
	("Input SGST (9%)", A_SGST, 0),
	(TDS_CONTRACTORS, 0, A_TDS),
	(SUPPLIER, 0, A_PAYABLE),
]

# B: five bills of 25,000 from one contractor (others, 2%)
B_BILLS = [D(25000)] * 5
B_TDS = erpnext_tds(B_BILLS, 2, 30000, 100000)
B_TOTAL_BASE = sum(B_BILLS)
B_TOTAL_TDS = sum(B_TDS)
assert B_TOTAL_BASE == 125000 and B_TOTAL_TDS == 2500 == pct(2, B_TOTAL_BASE)
B_FIRST = next(i for i, t in enumerate(B_TDS) if t > 0)  # index of the bill on which TDS starts
B_CATCHUP_BASE = sum(B_BILLS[: B_FIRST + 1])
assert B_TDS[B_FIRST] == pct(2, B_CATCHUP_BASE)
assert B_FIRST == 3, "ERPNext 15 starts on the 4th bill: 4 x 25,000 = 1,00,000 reaches the threshold (>=)"
B_GL = [
	("Sub-contract / job-work expense", B_BILLS[B_FIRST], 0),
	(TDS_CONTRACTORS, 0, B_TDS[B_FIRST]),
	(SUPPLIER, 0, B_BILLS[B_FIRST] - B_TDS[B_FIRST]),
]

# C: professional fees 60,000 at 10% (threshold 50,000 a year)
C_BASE = D(60000)
C_TDS = erpnext_tds([C_BASE], 10, 50000, 50000)[0]
assert C_TDS == 6000
C_GL = [("Professional fees", C_BASE, 0), (TDS_PROFESSIONAL, 0, C_TDS), (SUPPLIER, 0, C_BASE - C_TDS)]

# D: rent of building 75,000 for one month at 10% (threshold 50,000 a month -> single, 6,00,000 a year)
D_BASE = D(75000)
D_TDS = erpnext_tds([D_BASE], 10, 50000, 600000)[0]
assert D_TDS == 7500
D_GL = [("Rent – building", D_BASE, 0), (TDS_RENT, 0, D_TDS), (SUPPLIER, 0, D_BASE - D_TDS)]

# E: purchase of goods: 48 lakh then 5 lakh, 0.1% on the excess over 50 lakh
E_BILLS = [D(4800000), D(500000)]
E_LIMIT = D(5000000)
E_TDS = erpnext_tds(E_BILLS, D("0.1"), 0, E_LIMIT, excess_only=True)
E_TDS_FULL = erpnext_tds(E_BILLS, D("0.1"), 0, E_LIMIT, excess_only=False)
E_EXCESS = sum(E_BILLS) - E_LIMIT
assert E_TDS == [0, 300] and E_EXCESS == 300000 and E_TDS[1] == pct(D("0.1"), E_EXCESS)
assert E_TDS_FULL[1] == pct(D("0.1"), sum(E_BILLS)) == 5300
E_GL = [("Purchase of goods (stock / expense)", E_BILLS[1], 0), (TDS_GOODS, 0, E_TDS[1]),
	(SUPPLIER, 0, E_BILLS[1] - E_TDS[1])]

# Challan: contractor TDS of examples A and B (both code 1024)
CHALLAN = A_TDS + B_TOTAL_TDS
assert CHALLAN == 3300
CHALLAN_GL = [(TDS_CONTRACTORS, CHALLAN, 0), ("Bank account", 0, CHALLAN)]


# ---------------------------------------------------------------------------------------------------------------
# flow strip
# ---------------------------------------------------------------------------------------------------------------
class FlowStrip(Flowable):
	"""Coloured boxes joined by arrows."""

	def __init__(self, steps, height=58, gap=15):
		super().__init__()
		self.steps = steps
		self.box_h = height
		self.gap = gap
		self.width = 0

	def wrap(self, avail_width, avail_height):
		self.width = avail_width
		return avail_width, self.box_h + 4

	def draw(self):
		c = self.canv
		n = len(self.steps)
		bw = (self.width - self.gap * (n - 1)) / n
		title_style = ParagraphStyle("fs_title", fontName="DejaVu-Bold", fontSize=8.3, leading=10.2,
			textColor=colors.white, alignment=TA_CENTER)
		sub_style = ParagraphStyle("fs_sub", fontName="DejaVu", fontSize=7.3, leading=9,
			textColor=colors.HexColor("#E3F1F3"), alignment=TA_CENTER)
		for i, (title, sub) in enumerate(self.steps):
			x = i * (bw + self.gap)
			c.setFillColor(NAVY if i % 2 == 0 else TEAL)
			c.roundRect(x, 2, bw, self.box_h, 5, stroke=0, fill=1)
			paras = [Paragraph(f"{i + 1}. {title}", title_style), Paragraph(sub, sub_style)]
			heights = [p.wrap(bw - 8, self.box_h)[1] for p in paras]
			assert sum(heights) + 3 <= self.box_h - 4, f"flow box {i + 1} text does not fit"
			y = 2 + (self.box_h + sum(heights) + 3) / 2
			for p, h in zip(paras, heights):
				y -= h
				p.drawOn(c, x + 4, y)
				y -= 3
			if i < n - 1:
				ax, mid = x + bw + 3, 2 + self.box_h / 2
				c.setFillColor(GREY)
				path = c.beginPath()
				path.moveTo(ax, mid + 5)
				path.lineTo(ax + self.gap - 6, mid)
				path.lineTo(ax, mid - 5)
				path.close()
				c.drawPath(path, stroke=0, fill=1)


def h1(text):
	return [CondPageBreak(45 * mm), spacer(2), S.h1(text)]


def h2(text, room=35):
	return [CondPageBreak(room * mm), S.h2(text)]


# ---------------------------------------------------------------------------------------------------------------
# document
# ---------------------------------------------------------------------------------------------------------------
doc = Doc(OUT_PDF, title="TDS in ERPNext", short_title="TDS in ERPNext – User Guide", doc_date="18 November 2026")

story = doc.cover(
	"TDS in ERPNext",
	"How Tax Deducted at Source is set up, calculated, posted and reported automatically",
	details=[
		("Prepared for", "Accounts team, BrahMos Aerospace Thiruvananthapuram Ltd"),
		("Prepared by", "Acube Innovations Private Limited"),
		("Reference", "Observation 29 (Reports &amp; Observations Tracker)"),
		("Applies to", "ERPNext v15 with India Compliance, FY 2026-27"),
		("Date", "18 November 2026"),
	],
	contents=[
		"TDS sections and payment codes for FY 2026-27",
		"How TDS flows through ERPNext",
		"One-time setup (including BATL setup status)",
		"How automatic deduction works",
		"Worked examples with ledger entries",
		"Reports and the monthly / quarterly cycle",
		"Checklist: why TDS did not calculate",
	],
	note=(
		"Rates, thresholds and payment codes in this guide must be confirmed with BATL's tax consultant before "
		"they are entered in ERPNext. Screens and field names are as in ERPNext 15.90.1 with India Compliance "
		"15.25.6, the versions installed on 18 November 2026."
	),
)
# key message in the corrected box, just above "Contents"
_contents_at = next(i for i, f in enumerate(story) if isinstance(f, Paragraph) and f.getPlainText() == "Contents")
story.insert(_contents_at, box(
	"TDS does not have to be calculated by hand. Once each Tax Withholding Category and the Supplier master are "
	"set up, ERPNext works out the TDS on every purchase invoice and advance, checks the thresholds, posts the "
	"amount to the right TDS ledger and lists it in the TDS reports for the challan and the quarterly return.",
	"key",
))

# --- 1. sections ------------------------------------------------------------------------------------------------
story += h1("1. TDS sections and payment codes for FY 2026-27")
story += [
	S.p(
		"From 1 April 2026 TDS is governed by the <b>Income Tax Act, 2025</b>. The old sections are brought "
		"together in <b>Section 393</b>, and each kind of payment has a <b>numeric payment code</b> used in the "
		"challan and the quarterly TDS statement. The old section and the new code side by side:"
	),
	table(
		[
			["Nature of payment", "Old section (1961 Act)", "New code (2025 Act)", "TDS rate", "When TDS starts"],
			["Contractor – individual / HUF", "194C", "1023", "1%",
				f"Single bill above {RUPEE}30,000, or {RUPEE}1,00,000 in the year"],
			["Contractor – others (firm, company)", "194C", "1024", "2%",
				f"Single bill above {RUPEE}30,000, or {RUPEE}1,00,000 in the year"],
			["Technical services", "194J(a)", "1026", "2%", f"{RUPEE}50,000 in the year"],
			["Professional services", "194J(b)", "1027", "10%", f"{RUPEE}50,000 in the year"],
			["Rent – plant / machinery", "194I(a)", "1008", "2%", f"{RUPEE}50,000 a month"],
			["Rent – land / building", "194I(b)", "1009", "10%", f"{RUPEE}50,000 a month"],
			["Purchase of goods", "194Q", "1031", "0.1%",
				f"Purchases above {RUPEE}50 lakh per supplier per year (only on the excess); applies when "
				f"the buyer's turnover is above {RUPEE}10 crore"],
		],
		[29, 14, 13, 9, 35],
	),
	spacer(3),
	box(
		"Without a valid PAN a higher rate applies – generally 20% (5% for purchase of goods in India "
		"Compliance's FY 2026-27 data). Rates, thresholds and codes must be confirmed with BATL's tax "
		"consultant before they are entered in ERPNext.",
		"warn",
	),
]

# --- 2. flow ----------------------------------------------------------------------------------------------------
story += h1("2. How TDS flows through ERPNext")
story += [
	S.p("TDS is set up once and then works on its own. Five pieces link together:"),
	FlowStrip([
		("Tax Withholding Category", "rates, thresholds, TDS ledger"),
		("Supplier master", "PAN and category"),
		("Purchase Invoice / Advance", "TDS worked out on save"),
		("General Ledger", "TDS ledger credited on submit"),
		("Reports &amp; deposit", "challan entry, quarterly return"),
	]),
	spacer(4),
	KeepTogether(table(
		[
			["Step", "Where in ERPNext", "Who", "What happens"],
			["1. Tax Withholding Category", "Accounting > Tax Masters", "Accounts, yearly",
				"Rates, thresholds, dates and the TDS ledger are stored per section and supplier type."],
			["2. Supplier master", "Buying > Supplier > Tax tab", "Accounts / Purchase, once",
				"PAN and category are recorded; every bill picks them up."],
			["3. Purchase Invoice / Advance", "Purchase Invoice; Payment Entry", "Accounts, every bill",
				"Apply Tax Withholding Amount is ticked, thresholds are checked and the TDS row is added."],
			["4. General Ledger", "On submit", "Automatic",
				"The TDS ledger is credited; the supplier is credited with the bill less TDS."],
			["5. Reports &amp; deposit", "TDS reports; Journal Entry", "Accounts, monthly and quarterly",
				"Deductions are listed; the challan entry clears the TDS ledger; data for the return."],
		],
		[21, 22, 17, 40],
	)),
]

# --- 3. setup ---------------------------------------------------------------------------------------------------
story += h1("3. One-time setup")
story += h2("3.1 India Compliance version")
story += [
	S.p(
		"This site runs ERPNext 15.90.1 with India Compliance <b>15.25.6</b>. An update to India Compliance "
		"<b>15.27.1 or later</b> is recommended before FY 2026-27 TDS is relied upon:"
	),
	bullets([
		"15.27.1 (released 1 April 2026) puts the Income Tax Act, 2025 payment codes (1023, 1024 …) in the "
		"<b>Section</b> field of each Tax Withholding Category and keeps the old section in a new field, "
		"<b>Old Income Tax Section</b>.",
		"It also adds FY 2026-27 rate rows to the standard categories. In 15.25.6 the built-in TDS data ends on "
		"31 March 2026, so until the update every FY 2026-27 rate row must be entered by hand. After the update "
		"each category's rates and Accounts table should still be reviewed.",
	]),
]
story += h2("3.2 Tax Withholding Category – one per section and type of supplier", room=60)
story += [
	S.p("Path: <b>Accounting > Tax Masters > Tax Withholding Category</b>. Fields as they appear in this version:"),
	table(
		[
			["Field", "What to enter"],
			["Name / Category Name", "A clear name, e.g. \"1024 – Contractor (others)\"; the name appears as the "
				"Section Code in the TDS reports."],
			["Section, Entity (India Compliance)", "The section (the payment code after the update) and the "
				"supplier type: Individual, Company or No PAN / Invalid PAN."],
			["Rates: From Date, To Date, Tax Withholding Rate", "One row per period with the TDS %, e.g. "
				"01-04-2026 to 31-03-2027. Rows must not overlap; a bill dated outside every row stops with \"No "
				"Tax Withholding data found for the current posting date\"."],
			["Rates: Single Transaction Threshold", "TDS starts when one bill is equal to or more than this "
				"amount."],
			["Rates: Cumulative Transaction Threshold", "TDS starts when the year's bills together reach this "
				"amount (it cannot be lower than the single threshold). 0 means not used; if both are 0 ERPNext "
				f"never deducts – enter {RUPEE}1 to deduct from the first rupee."],
			["Only Deduct Tax On Excess Amount", "Tick for purchase of goods (1031): TDS only on the amount above "
				"the cumulative threshold. Leave unticked for contractors, professional fees and rent."],
			["Round Off Tax Amount", "Rounds the TDS to the nearest rupee."],
			["Consider Entire Party Ledger Amount", "Leave unticked unless the consultant advises it. When ticked, "
				"the threshold test uses invoice totals including GST and also counts unallocated advance "
				"payments."],
			["Accounts: Company, Account", f"One row for {COMPANY_NAME} with this section's TDS ledger. Without "
				"it ERPNext skips TDS (\"no associated account set for Company\")."],
		],
		[30, 70],
		font_size=8,
	),
]
story += h2("3.3 TDS ledgers – one per section", room=45)
story += [
	S.p(
		"A separate TDS payable ledger per section keeps each ledger's balance equal to the amount to deposit "
		"under that payment code. BATL already has these under <b>TDS (LIABILITY) - BATL</b>:"
	),
	table(
		[
			["Ledger", "Used for"],
			[TDS_CONTRACTORS, "Contractors – 194C (codes 1023 / 1024)"],
			[TDS_PROFESSIONAL, "Professional services – 194J(b) (code 1027)"],
			[TDS_RENT, "Rent – 194I(a) / 194I(b) (codes 1008 / 1009)"],
			[TDS_GOODS, "Purchase of goods – 194Q (code 1031)"],
			["Not yet created", "Technical services – 194J(a) (code 1026): create e.g. \"TDS Technical Services\" "
				"if such fees are paid."],
		],
		[40, 60],
		font_size=8,
	),
]
story += h2("3.4 Supplier master", room=40)
story += [
	bullets([
		"Path: <b>Buying > Supplier > Tax tab</b>. Set <b>Tax Withholding Category</b> – this one field switches "
		"TDS on for the supplier.",
		"<b>PAN</b> sits next to GSTIN / UIN (added by India Compliance). When a GSTIN is entered, the PAN is "
		"taken from it and locked.",
		"Choose the category that fits: individual / HUF contractor (1%), firm or company contractor (2%), or the "
		"No PAN / Invalid PAN category when no valid PAN is on file.",
		"For thresholds ERPNext adds up the bills of all suppliers with the same PAN, so a vendor created twice "
		"is still treated as one.",
	]),
]
story += h2("3.5 Lower Deduction Certificate", room=30)
story += [
	S.p(
		"Path: <b>Accounting > Tax Masters > Lower Deduction Certificate</b>. Enter Certificate No, Supplier, "
		"PAN No, Tax Withholding Category, Fiscal Year, Valid From, Valid Upto, Rate Of TDS As Per Certificate, "
		"Certificate Limit and Company. On bills within the validity ERPNext uses the certificate rate until the "
		"Certificate Limit is used up, then the normal rate. PAN No and category must match the supplier's."
	),
]
story += [CondPageBreak(95 * mm), S.h2("3.6 BATL setup status (read-only check, 18 November 2026)")]
story += [
	table(
		[
			["Item", "Found on the BATL site", "Action"],
			["India Compliance", "Version 15.25.6: built-in TDS data ends on 31-03-2026 and uses the old section "
				"numbers.", "Update to 15.27.1 or later; then review the categories."],
			["Tax Withholding Categories", "66 categories (63 TDS, 3 TCS), named by old sections (194C, 194JB, "
				"194Q …). Only 19 have a rate row for FY 2026-27 and 21 have a BATL account row. \"TDS - 194C - "
				"No PAN / Invalid PAN\" (32 suppliers) and the three 194JA technical-fee categories stop at "
				"31-03-2026; 194JA has no account row either.", "Add FY 2026-27 rows and the BATL account to "
				"every category in use."],
			["Thresholds", f"Contractor (194C) categories use {RUPEE}1, so TDS is taken from the first rupee, not "
				f"above {RUPEE}30,000 / {RUPEE}1,00,000. 194JB Company and No PAN still use the old "
				f"{RUPEE}30,000; \"TDS - 194JB - Individual\" has 0 / 0 and so never deducts on its own. 194Q "
				"categories have Only Deduct Tax On Excess Amount ticked (as needed) and also Consider Entire "
				"Party Ledger Amount.", "Confirm each with the tax consultant; correct where needed."],
			["TDS ledgers", "Separate ledgers for contractors, professional services, rent and goods. No deposit "
				"(challan) entries have been posted to them so far.",
				"Ledger for technical services if needed; post every challan (5.5)."],
			["Suppliers", "310 of 5,217 suppliers have a category (306 contractor, 3 goods, 1 professional); 32 of "
				"these have no PAN. 99 of the 105 suppliers billed since 1-4-2026 have no category.",
				"Review this year's suppliers; add PAN and category where TDS applies."],
			["Use in FY 2026-27", "173 submitted purchase invoices: 11 with Apply Tax Withholding Amount, 6 with "
				"TDS worked out automatically (all contractors). No Payment Entry with TDS; no Lower Deduction "
				"Certificate.", "–"],
		],
		[17, 57, 26],
		font_size=8,
	),
]

# --- 4. automatic deduction -------------------------------------------------------------------------------------
story += h1("4. How automatic deduction works")
story += h2("4.1 On the Purchase Invoice")
story += [
	numbered([
		"Select the supplier. ERPNext ticks <b>Apply Tax Withholding Amount</b> and fills <b>Tax Withholding "
		"Category</b> from the Supplier master (if the supplier has no category, the tick box is locked).",
		"Add the items. Each item row has an <b>Apply TDS</b> tick (on by default); <b>Tax Withholding Net "
		"Total</b> shows the TDS base – the net amount of the ticked items.",
		"Save. ERPNext checks the thresholds and adds a \"Deduct\" row on the category's TDS ledger in "
		"<b>Purchase Taxes and Charges</b>. The earlier untaxed bills it took into account are listed in "
		"<b>Tax Withheld Vouchers</b>.",
		"Submit. The TDS ledger is credited and the supplier is credited with the bill less TDS.",
	]),
]
story += h2("4.2 How the thresholds are applied", room=60)
story += [
	S.p("For each supplier (PAN) and category, within the dates of the rate row, ERPNext decides as follows:"),
	table(
		[
			["Situation", "TDS on this bill"],
			["TDS has already been deducted earlier in the year", "Rate × this bill – no threshold check."],
			["This bill alone is equal to or more than the Single Transaction Threshold",
				"Rate × (this bill + earlier untaxed bills of the year)."],
			["This bill plus the earlier untaxed bills reach the Cumulative Transaction Threshold",
				"Rate × (this bill + earlier untaxed bills) – the catch-up."],
			["… and Only Deduct Tax On Excess Amount is ticked", "Rate × (year total − cumulative threshold)."],
			["Neither threshold reached", "No TDS; the bill counts towards the cumulative threshold."],
		],
		[57, 43],
		font_size=8,
	),
	spacer(1.5),
	S.small(
		"Earlier bills count only if they are submitted (not draft or cancelled), are not opening entries, have "
		"Apply Tax Withholding Amount ticked and carry the same category. Advances and journal entries with TDS "
		"ticked count as well."
	),
]
story += h2("4.3 TDS on advances", room=40)
story += [
	bullets([
		"On a <b>Payment Entry</b> (Pay, Party Type Supplier) open <b>Taxes and Charges</b>, tick <b>Apply Tax "
		"Withholding Amount</b> and choose the category. ERPNext adds the TDS row in <b>Advance Taxes and "
		"Charges</b> and credits the TDS ledger on submit. For an advance against a Purchase Order the TDS base "
		"is limited to the order value without GST.",
		"When the bill arrives, pull the advance into the Purchase Invoice (<b>Get Advances Paid</b> or <b>Set "
		"Advances and Allocate (FIFO)</b>). The <b>Advance Tax</b> table shows the TDS already deducted and "
		"ERPNext reduces the bill's TDS by that amount, so TDS is not deducted twice.",
	]),
]
story += h2("4.4 Item-level Apply TDS and GST", room=30)
story += [
	bullets([
		"Untick <b>Apply TDS</b> on an item row that is not subject to TDS; that line is left out of the base.",
		"GST is never part of the TDS base: the base is the item net amounts (after discount), before GST and "
		"any other charges in the taxes table.",
	]),
]

# --- 5. examples ------------------------------------------------------------------------------------------------
def block(*flowables):
	return KeepTogether(list(flowables))


# the section heading and its introduction stay on the page of Example A
story += [
	CondPageBreak(45 * mm),
	spacer(2),
	block(
		S.h1("5. Worked examples with ledger entries"),
		S.p(
			"The figures follow the rule in 4.2 and every ledger table balances. TDS ledgers are BATL's own; "
			"expense, GST and supplier ledgers are shown generically. GST appears only in Example A, to show that "
			"it stays outside the TDS base; the other examples leave it out for simplicity."
		),
		S.h2(f"5.1 Example A – Contractor (firm), one bill of {rs(A_BASE)}"),
		S.p(
			f"Category 1024 Contractor (others), 2%, thresholds {RUPEE}30,000 / {RUPEE}1,00,000. The bill of "
			f"{rs(A_BASE)} + 18% GST is above the single-bill threshold, so TDS = 2% × {rs(A_BASE)} = "
			f"<b>{rs(A_TDS)}</b>. GST of {rs(A_CGST + A_SGST)} is not part of the base; the supplier receives "
			f"{rs(A_PAYABLE)} ({rs(A_GROSS)} − {rs(A_TDS)})."
		),
		gl_table(A_GL),
		spacer(2),
	),
]

# B: bill-by-bill table
b_rows = [["Bill", f"Amount {RUPEE}", f"Year total {RUPEE}", f"TDS {RUPEE}", f"To supplier {RUPEE}",
	"How ERPNext decides"]]
running = D(0)
for i, (amount, tds) in enumerate(zip(B_BILLS, B_TDS)):
	running += amount
	if i < B_FIRST:
		why = "Below both thresholds – no TDS"
	elif i == B_FIRST:
		why = f"Total reaches {RUPEE}1,00,000 – TDS on bills 1–{i + 1}"
	else:
		why = "TDS already deducted this year – 2% in full"
	b_rows.append([str(i + 1), inr(amount), inr(running), inr(tds) if tds else "–", inr(amount - tds), why])
b_rows.append(["Total", inr(B_TOTAL_BASE), "", inr(B_TOTAL_TDS), inr(B_TOTAL_BASE - B_TOTAL_TDS), ""])

story += [
	CondPageBreak(70 * mm),
	block(
		S.h2(f"5.2 Example B – Five bills of {rs(B_BILLS[0])} from one contractor"),
		S.p(f"Same category (2%). No single bill reaches {RUPEE}30,000, so the year total decides:"),
		table(b_rows, [7, 13, 14, 11, 14, 41], right_cols=(1, 2, 3, 4), total_row=True,
			highlight_rows=(B_FIRST + 1,), font_size=8),
		spacer(2),
	),
	box(
		f"ERPNext starts deducting when the year total <b>reaches</b> the threshold (equal to or more). The Act "
		f"speaks of amounts exceeding {RUPEE}1,00,000, so when the total lands exactly on {RUPEE}1,00,000 ERPNext "
		f"deducts one bill earlier – here on bill {B_FIRST + 1} ({rs(B_TDS[B_FIRST])} on {rs(B_CATCHUP_BASE)}) "
		f"instead of bill {B_FIRST + 2}. The TDS for the year is the same: {rs(B_TOTAL_TDS)} on "
		f"{rs(B_TOTAL_BASE)}.",
		"note",
	),
	block(
		S.p(f"Ledger entry for bill {B_FIRST + 1}:", S.H3),
		gl_table(B_GL),
		spacer(1),
		S.small(
			f"Bill {B_FIRST + 2} posts the same way with TDS {rs(B_TDS[B_FIRST + 1])} and "
			f"{rs(B_BILLS[B_FIRST + 1] - B_TDS[B_FIRST + 1])} to the supplier."
		),
	),
]

# C and D side by side
HALF = CONTENT_W / 2
cd = Table(
	[[
		[
			S.p(f"<b>Example C – Professional fees of {rs(C_BASE)}</b>"),
			S.p(f"Category 1027, 10%, threshold {RUPEE}50,000 a year. TDS = 10% × {rs(C_BASE)} = "
				f"<b>{rs(C_TDS)}</b>; later bills in the year are taxed in full."),
			gl_table_narrow(C_GL, HALF - 6),
		],
		[
			S.p(f"<b>Example D – Rent of {rs(D_BASE)} for a month</b>"),
			S.p(f"Category 1009 (land / building), 10%, Single Transaction Threshold {RUPEE}50,000 (one "
				f"month). TDS = 10% × {rs(D_BASE)} = <b>{rs(D_TDS)}</b>."),
			gl_table_narrow(D_GL, HALF - 6),
		],
	]],
	colWidths=[HALF, HALF],
)
cd.setStyle(TableStyle([
	("VALIGN", (0, 0), (-1, -1), "TOP"),
	("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 6),
	("LEFTPADDING", (1, 0), (1, 0), 6), ("RIGHTPADDING", (1, 0), (1, 0), 0),
	("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
]))
story += [CondPageBreak(60 * mm), block(S.h2("5.3 Examples C and D – Professional fees and rent"), cd, spacer(3))]

e_rows = [["Invoice", f"Amount {RUPEE}", f"Year total {RUPEE}", f"TDS {RUPEE}", "How ERPNext decides"]]
running = D(0)
for i, (amount, tds) in enumerate(zip(E_BILLS, E_TDS)):
	running += amount
	why = (f"Below {RUPEE}50 lakh – no TDS" if not tds else
		f"0.1% × excess over {RUPEE}50 lakh ({rs(running - E_LIMIT)})")
	e_rows.append([str(i + 1), inr(amount), inr(running), inr(tds) if tds else "–", why])

story += [
	CondPageBreak(60 * mm),
	block(
		S.h2("5.4 Example E – Purchase of goods: ₹48 lakh, then ₹5 lakh"),
		S.p(f"Category 1031 Purchase of goods, 0.1%, Cumulative Transaction Threshold {rs(E_LIMIT)}, <b>Only "
			"Deduct Tax On Excess Amount</b> ticked."),
		table(e_rows, [10, 16, 17, 11, 46], right_cols=(1, 2, 3), highlight_rows=(2,), font_size=8),
		spacer(2),
	),
	box(
		f"Without the Only Deduct Tax On Excess Amount tick, the second invoice would carry TDS on the full "
		f"{rs(sum(E_BILLS))}: {rs(E_TDS_FULL[1])} instead of {rs(E_TDS[1])}.",
		"warn",
	),
	block(S.p("Ledger entry for invoice 2:", S.H3), gl_table(E_GL), spacer(2)),
]
story += [
	CondPageBreak(55 * mm),
	block(
		S.h2("5.5 Depositing the TDS (challan entry)"),
		S.p(
			f"When the contractor TDS of Examples A and B (code 1024: {rs(A_TDS)} + "
			+ " + ".join(rs(t) for t in B_TDS if t)
			+ f" = <b>{rs(CHALLAN)}</b>) is paid, post a <b>Journal Entry</b> with Entry Type <b>Bank Entry</b>, "
			"the challan number as <b>Reference Number</b> and the deposit date as <b>Reference Date</b>:"
		),
		gl_table(CHALLAN_GL),
		spacer(1),
		S.small("Post one entry per challan. Afterwards the TDS ledger shows nil for the amounts deposited."),
	),
]

# --- 6. reports -------------------------------------------------------------------------------------------------
story += h1("6. Reports and the monthly / quarterly cycle")
story += [
	table(
		[
			["Report", "What it shows", "Use it for"],
			["Tax Withholding Details", "Called \"TDS Payable Monthly\" in earlier versions. One line per "
				"deduction: Section Code (the category), PAN, supplier, Entity Type, supplier invoice no. and "
				"date, TDS Rate %, Total Amount, TDS Amount and the voucher.",
				"The month's challan amount per code; detail for the quarterly statement."],
			["TDS Computation Summary", "Totals per supplier and category for any period: Total Amount and Tax "
				"Amount.", "Quarter-end check; TDS certificates to suppliers."],
			["General Ledger, Account = a TDS ledger", f"Every deduction (credit) and deposit (debit) on, e.g., "
				f"{TDS_CONTRACTORS}.", "Balance = TDS deducted but not yet deposited; it should match the next "
				"challan."],
			["Lower Deduction Certificate list", "Certificates with supplier, rate, limit and validity.",
				"Check validity and remaining limit before month-end."],
		],
		[22, 50, 28],
		font_size=8,
	),
	spacer(1),
	S.small(
		"Both TDS reports are opened from the search bar and filtered by Company, Party Type (Supplier), Party, "
		"From Date and To Date."
	),
	block(
		S.h3("Monthly and quarterly cycle"),
		table(
			[
				["When", "What to do", "In ERPNext"],
				["Every bill", "Check that the TDS row is present before submitting.", "Purchase Invoice"],
				["Monthly – deposit by the 7th of the following month", "Total the month's TDS per payment code, "
					"pay the challan and post the deposit entry.",
					"Tax Withholding Details; General Ledger; Journal Entry"],
				["Quarterly", "Reconcile TDS with the challans, file the quarterly TDS statement (return) and "
					"issue TDS certificates.", "TDS Computation Summary; Tax Withholding Details"],
			],
			[24, 46, 30],
			font_size=8,
		),
		spacer(1),
		S.small("Due dates for March deductions and for the quarterly return are as advised by the tax "
			"consultant."),
	),
]

# --- 7. checklist -----------------------------------------------------------------------------------------------
story += h1("7. Checklist: why TDS did not calculate")
story += [
	KeepTogether(table(
		[
			["#", "Check", "Where", "Fix"],
			["1", "Supplier has no Tax Withholding Category", "Supplier > Tax tab",
				"Set the category, then re-select the supplier on the draft invoice (the tick box is locked "
				"until then)."],
			["2", "Apply Tax Withholding Amount not ticked, or category blank", "Purchase Invoice, top section",
				"Tick it, choose the category and save again."],
			["3", "No rate row for the bill date", "Category > Rates",
				"Add the FY 2026-27 row (01-04-2026 to 31-03-2027). Message: \"No Tax Withholding data found "
				"for the current posting date\"."],
			["4", "No BATL account in the category", "Category > Accounts",
				"Add the BATL company row with the TDS ledger. Message: \"Skipping Tax Withholding Category …\"."],
			["5", "Threshold not reached, or both thresholds 0", "Category > Rates; earlier bills",
				"No TDS is expected below the threshold. Earlier bills count only if submitted, not opening, "
				f"ticked and in the same category. Enter {RUPEE}1 to deduct from the first rupee."],
			["6", "Items have Apply TDS unticked", "Purchase Invoice > Items",
				"Tick Apply TDS on the taxable lines; check Tax Withholding Net Total."],
			["7", "Lower Deduction Certificate applies, or PAN mismatch", "Lower Deduction Certificate; "
				"Supplier > PAN", "Check rate, limit, validity, PAN and category on the certificate."],
		],
		[4, 27, 21, 48],
		font_size=8,
	)),
	spacer(3),
	box(
		"If all seven checks pass, send the invoice number and a screenshot of its Purchase Taxes and Charges "
		"table to Acube support.",
		"note",
		title="Still stuck?",
	),
]

doc.build(story)
os.makedirs(os.path.dirname(COPY_TO), exist_ok=True)
shutil.copyfile(OUT_PDF, COPY_TO)
print(OUT_PDF)
print(COPY_TO)
