"""Options paper: the same item bought under one Item Group and sold under another (Observation 35).

Client-facing PDF for the BrahMos Aerospace Thiruvananthapuram Accounts and Stores teams, prepared by
Acube Innovations. Uses the shared layout in acube_pdf.py. Every amount is computed below and every GL table is
checked to balance before the PDF is built.

Run with a Python that has reportlab (not the bench env):
    <venv>/bin/python same_item_two_item_groups.py
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from acube_pdf import (  # noqa: E402
	CondPageBreak,
	Doc,
	KeepTogether,
	S,
	bullets,
	callout,
	key_value,
	numbered,
	spacer,
	table,
	mm,
)

OUT = os.path.join(HERE, "Same Item in Two Item Groups - Options.pdf")
COPY = "/home/acubeadmin/Downloads/BATL ERP - Same Item in Two Item Groups - Options.pdf"


# --- numbers --------------------------------------------------------------------------------------------------
def inr(n):
	"""Indian digit grouping: 224000 -> 2,24,000."""
	neg = n < 0
	s = str(abs(int(round(n))))
	if len(s) > 3:
		head, tail = s[:-3], s[-3:]
		groups = []
		while len(head) > 2:
			groups.insert(0, head[-2:])
			head = head[:-2]
		if head:
			groups.insert(0, head)
		s = ",".join(groups) + "," + tail
	return ("-" if neg else "") + s


def rs(n):
	return "₹" + inr(n)


QTY = 10
BUY_RATE = 5000
BUY_AMT = QTY * BUY_RATE  # 50,000
PAINT = 4000
SELL_RATE = 7000
SELL_AMT = QTY * SELL_RATE  # 70,000
PAINT_PER_UNIT = PAINT / QTY  # 400
FG_RATE = (BUY_AMT + PAINT) / QTY  # 5,400 (Repack: outgoing cost / finished qty + additional cost / qty)
FG_AMT = QTY * FG_RATE  # 54,000
assert BUY_AMT == 50000 and SELL_AMT == 70000 and FG_RATE == 5400 and FG_AMT == 54000

OPT1_MARGIN_SHOWN = SELL_AMT - BUY_AMT  # 20,000: sales less COGS, painting outside COGS
TRUE_MARGIN = SELL_AMT - BUY_AMT - PAINT  # 16,000
OPT2_MARGIN = SELL_AMT - FG_AMT  # 16,000
assert OPT2_MARGIN == TRUE_MARGIN

# BATL accounts (from the BATL company and chart of accounts)
STOCK = "Stock In Hand - BATL"
SRBNB = "Stock Received But Not Billed - BATL"
COGS = "Cost of Goods Sold - BATL"
INCOME = "INCOME FROM SALE OF GOODS - BATL"
EIIV = "Expenses Included In Valuation - BATL"
PAINT_EXP = "Sub Contract Charges for Job Works - BATL"
CRED_P = "Creditors for Purchases - BATL"
CRED_E = "Creditors for Expense - BATL"
DEBTORS = "Debtors - BATL"
STOCK_ADJ = "Stock Adjustment - BATL"
WH_SCD = "SCD Store-Restricted"
WH_FG = "Finished Goods Store-Restricted"
GRP_BUY = "SCD Store"
GRP_SELL = "Finished Good (Sales)"


def gl_table(entries):
	"""entries: list of (document, [(account, debit, credit), ...]). Asserts each document and the total balance;
	returns the table flowable."""
	rows = [["Document", "Account", "Debit ₹", "Credit ₹"]]
	total_dr = total_cr = 0
	shade = []
	for i, (doc_name, lines) in enumerate(entries):
		dr = sum(d for _, d, _ in lines)
		cr = sum(c for _, _, c in lines)
		assert dr == cr, f"{doc_name} does not balance: {dr} vs {cr}"
		total_dr += dr
		total_cr += cr
		for j, (acc, d, c) in enumerate(lines):
			if i % 2 == 1:
				shade.append(len(rows))
			rows.append([doc_name if j == 0 else "", acc, inr(d) if d else "", inr(c) if c else ""])
	assert total_dr == total_cr
	rows.append(["Total", "", inr(total_dr), inr(total_cr)])
	return table(rows, [27, 47, 13, 13], right_cols=(2, 3), total_row=True, zebra=False, highlight_rows=shade,
		font_size=8)




def co(text, kind="note", title=None):
	"""A callout as a plain list of flowables, safe to put inside KeepTogether (callout() itself returns a
	KeepTogether, which reports an infinite height when nested and forces a page break)."""
	return list(callout(text, kind, title=title)._content)


def keep(*parts):
	flat = []
	for p in parts:
		flat.extend(p if isinstance(p, list) else [p])
	return KeepTogether(flat)


# --- document -------------------------------------------------------------------------------------------------
doc = Doc(OUT, title="Same Item in Two Item Groups – Options", short_title="Same Item in Two Item Groups – Options",
	doc_date="18 November 2026")

KEY = ("If the item is sold exactly as bought, keep one item code (Option 1). If it is painted or serviced before "
	"sale, use a purchase item and a sales item linked by a Repack entry, so the painting cost becomes part of its "
	"stock value (Option 2). Move to subcontracting (Option 3) only if painting is later outsourced at volume.")

story = doc.cover(
	"Same Item in Two Item Groups",
	"Options for an item bought as an SCD item and sold as a finished product, without the Manufacturing module",
	details=[
		("Prepared for", "BrahMos Aerospace Thiruvananthapuram Limited – Accounts and Stores teams"),
		("Prepared by", "Acube Innovations Private Limited"),
		("Reference", "Observation 35, Reports &amp; Observations Tracker"),
		("Question", "“If the same item will come under both finished product and SCD item, what is the solution?”"),
		("System", "ERPNext v15 (15.90.1) with India Compliance; Manufacturing (Work Orders) not in use"),
		("Date", "18 November 2026"),
		("Status", "Options for decision. Nothing has been changed in the system."),
	],
	key_message=KEY,
	contents=[
		"The question and what ERPNext allows",
		"Option 1 – One item code, accounts set separately",
		"Option 2 – Two item codes linked by a Repack entry",
		"Option 3 – Subcontracting (later phase)",
		"Comparison and decision guide",
	],
	note="All amounts in this document exclude GST. Account, warehouse and Item Group names are BATL's own.",
)

# 1 ------------------------------------------------------------------------------------------------------------
story += [
	S.h1("1. The question and what ERPNext allows"),
	S.p(f"The same physical item is bought from vendors under a purchase-side Item Group (for example "
		f"<b>{GRP_BUY}</b>) and sold under a sales-side Item Group (for example <b>{GRP_SELL}</b>). Sometimes it is "
		f"painted or otherwise serviced before it is sold."),
	bullets([
		"<b>An item has exactly one Item Group.</b> The group drives reports, filters and the default warehouse and "
		"accounts, so one item code cannot sit in two groups.",
		"<b>Defaults are picked in this order:</b> the item's own Item Defaults row, then the Item Group's defaults, "
		"then the company defaults – so purchase and sales accounts can differ even with one Item Group.",
		f"<b>For a stock item the purchase always goes to the store's stock account</b> ({STOCK}); the item's "
		f"Default Expense Account is used as Cost of Goods Sold when it is delivered.",
		f"At BATL the sales-side groups (Finished Goods, {GRP_SELL}) already default to {WH_FG} and {INCOME}; "
		f"SCD Store items default to {WH_SCD} on the item itself.",
	]),
	S.h2("Example used in this document"),
	key_value([
		("Purchase", f"{QTY} Nos at {rs(BUY_RATE)} = <b>{rs(BUY_AMT)}</b>, received into {WH_SCD}"),
		("Painting", f"Done by an outside painter, bill <b>{rs(PAINT)}</b> ({rs(PAINT_PER_UNIT)} per unit)"),
		("Sale", f"{QTY} Nos at {rs(SELL_RATE)} = <b>{rs(SELL_AMT)}</b>"),
		("Notes", "Purchase Receipt then Purchase Invoice; Delivery Note then Sales Invoice, as BATL works today. "
			"GST is excluded: it is posted to the GST accounts by the tax templates and changes no stock value or "
			"margin shown here."),
	], widths=(16, 84)),
	spacer(2),
]

# 2 ------------------------------------------------------------------------------------------------------------
opt1_gl = gl_table([
	("Purchase Receipt", [(STOCK, BUY_AMT, 0), (SRBNB, 0, BUY_AMT)]),
	("Purchase Invoice (vendor)", [(SRBNB, BUY_AMT, 0), (CRED_P, 0, BUY_AMT)]),
	("Purchase Invoice (painter)", [(PAINT_EXP, PAINT, 0), (CRED_E, 0, PAINT)]),
	("Delivery Note", [(COGS, BUY_AMT, 0), (STOCK, 0, BUY_AMT)]),
	("Sales Invoice", [(DEBTORS, SELL_AMT, 0), (INCOME, 0, SELL_AMT)]),
])

story += [
	CondPageBreak(60 * mm),
	S.h1("2. Option 1 – One item code, accounts set separately"),
	S.h3("How it works"),
	S.p("The item keeps one code and one Item Group. Purchase and sales are separated by accounts, not by groups: "
		"the item's Item Defaults row tells ERPNext which store, cost centres, Cost of Goods Sold account and income "
		"account to use. Painting is bought as a separate service and booked as an expense; it is <b>not</b> added "
		"to the item's stock value."),
	S.h3("Setup (one time)"),
	numbered([
		f"Keep the item in the one Item Group it is controlled under – normally {GRP_BUY}, or {GRP_SELL} if it is "
		f"mainly a sales item.",
		f"Item &gt; Item Defaults (company BATL): Default Warehouse ({WH_SCD}), Default Buying Cost Center, Default "
		f"Expense Account ({COGS}, used on delivery), Default Selling Cost Center, Default Income Account "
		f"({INCOME}). These override the Item Group's defaults for this item only.",
		"For the second view in reports, report by account, or add one custom field on Item (for example “Also "
		"sold as finished product”) and use it as a report filter.",
		f"Use a non-stock service item (Services items group) for painting, with an expense account such as "
		f"{PAINT_EXP}.",
	]),
	keep(S.h3("Transaction flow"),
		S.p(f"Purchase Order → Purchase Receipt into {WH_SCD} → Purchase Invoice. Painting: service Purchase Order "
			f"and Purchase Invoice to the painter. Optional Material Transfer to {WH_FG}. Sales Order → Delivery "
			f"Note → Sales Invoice.")),
	keep(S.h3("Stock and accounting impact – worked example"), opt1_gl, spacer(2)),
	callout(f"Stock is valued at {rs(BUY_RATE)} per unit before and after painting. Cost of Goods Sold shows "
		f"{rs(BUY_AMT)} and the {rs(PAINT)} painting sits in {PAINT_EXP}, so the item's own margin looks like "
		f"{rs(OPT1_MARGIN_SHOWN)} although the real margin is {rs(TRUE_MARGIN)}. Painted items still in store at "
		f"month-end carry no painting cost.", "ok"),
	keep(
		table([
			["Advantages", "Limitations"],
			[bullets(["No new item codes; simplest for Stores.",
				"No extra stock entry per batch.",
				"Existing reports and Item Group defaults keep working."], S.CELL),
			bullets(["Reports show one Item Group; the second view needs account-wise reports or a custom field.",
				"Painting is outside stock value and Cost of Goods Sold: item margin overstated, painted stock "
				"understated (AS 2 / Ind AS 2 include conversion costs in inventory cost).",
				"Painted and unpainted units cannot be told apart in one store."], S.CELL)],
		], [42, 58], zebra=False),
		spacer(2),
		co("The item is sold exactly as bought (no painting or service), or the service cost is too small to be "
			"worth carrying in stock.", "note", title="When to use Option 1"),
	),
]

# 3 ------------------------------------------------------------------------------------------------------------
repack_rows = [
	["Row", "Item (Item Group)", "Warehouse", "Qty", "Basic rate ₹", "Additional cost ₹", "Valuation rate ₹",
		"Amount ₹"],
	["1 – consumed", f"Purchase item ({GRP_BUY})", f"Source: {WH_SCD}", str(QTY), inr(BUY_RATE), "–",
		inr(BUY_RATE), inr(BUY_AMT)],
	["2 – produced (Is Finished Item)", f"Sales item ({GRP_SELL})", f"Target: {WH_FG}", str(QTY),
		inr(BUY_AMT / QTY), inr(PAINT), inr(FG_RATE), inr(FG_AMT)],
]
assert BUY_AMT / QTY * QTY + PAINT == FG_AMT
repack_table = table(repack_rows, [15, 17, 19, 6, 10, 11, 11, 11], right_cols=(3, 4, 5, 6, 7), font_size=7.8)

opt2_gl = gl_table([
	("Purchase Receipt", [(STOCK, BUY_AMT, 0), (SRBNB, 0, BUY_AMT)]),
	("Purchase Invoice (vendor)", [(SRBNB, BUY_AMT, 0), (CRED_P, 0, BUY_AMT)]),
	("Purchase Invoice (painter)", [(EIIV, PAINT, 0), (CRED_E, 0, PAINT)]),
	("Stock Entry – Repack", [(STOCK + " (sales item in)", FG_AMT, 0), (STOCK + " (purchase item out)", 0, BUY_AMT),
		(EIIV, 0, PAINT)]),
	("Delivery Note (sales item)", [(COGS, FG_AMT, 0), (STOCK, 0, FG_AMT)]),
	("Sales Invoice", [(DEBTORS, SELL_AMT, 0), (INCOME, 0, SELL_AMT)]),
])
EIIV_NET = PAINT - PAINT  # Dr by the painter's bill, Cr by the Repack
assert EIIV_NET == 0

story += [
	CondPageBreak(60 * mm),
	S.h1("3. Option 2 – Two item codes linked by a Repack entry"),
	S.h3("How it works"),
	S.p(f"Keep the purchase item code in {GRP_BUY} and create a sales item code in {GRP_SELL} for the same physical "
		f"item. When the item is painted or serviced and ready for sale, Stores post one <b>Stock Entry of type "
		f"Repack</b>: it consumes the purchase item and receives the sales item. The painting bill goes into the "
		f"entry's <b>Additional Costs</b> table and so into the sales item's valuation. No Manufacturing module, "
		f"BOM or Work Order is needed (BATL already uses Repack entries for cutting raw material)."),
	S.h3("Setup (one time)"),
	numbered([
		f"Create the sales item: duplicate the purchase item, give it a linked code (for example the same code "
		f"with “-FG”), Item Group {GRP_SELL}, Maintain Stock ticked, same UOM. It takes the group's defaults "
		f"({WH_FG}, {INCOME}).",
		f"Painting service item: a non-stock item (Services items group) whose Default Expense Account is "
		f"<b>{EIIV}</b> – BATL's company default for costs included in stock valuation, and the account to use in "
		f"the Repack's Additional Costs.",
		f"Keep the Difference Account on both Repack rows as {STOCK_ADJ} (the company default), not a Cost of Goods "
		f"Sold account.",
	]),
	keep(S.h3("Transaction flow"),
		S.p(f"Purchase Order → Purchase Receipt of the purchase item into {WH_SCD} → Purchase Invoice. Painter: "
			f"service Purchase Order → Purchase Invoice. Stock Entry (Repack): purchase item out, sales item in, "
			f"painting in Additional Costs. Sales Order → Delivery Note of the sales item → Sales Invoice.")),
	keep(
		S.h3("The Repack entry in the example"),
		repack_table,
		S.small(f"Additional Costs: Expense Account {EIIV} · Description “Painting – painter's bill no.” · Amount "
			f"{rs(PAINT)}. Incoming {rs(FG_AMT)} – outgoing {rs(BUY_AMT)} = value difference "
			f"{rs(FG_AMT - BUY_AMT)}."),
	),
	callout([
		"• Every row of a Repack with only a target warehouse is marked <b>Is Finished Item</b> automatically.",
		f"• Its basic rate = cost of the items consumed ÷ finished quantity ({rs(BUY_AMT)} ÷ {QTY} = "
		f"{rs(BUY_AMT / QTY)}).",
		f"• Additional Costs are spread <b>only over the finished rows</b>, in proportion to their basic amount; the "
		f"consumed row gets none. Valuation rate = {rs(BUY_AMT / QTY)} + {rs(PAINT)} ÷ {QTY} = {rs(FG_RATE)}.",
		"• If one Repack produces two different sales items, enter each row's rate (Set Basic Rate Manually); the "
		"automatic rate works for one finished item only.",
	], "note", title="How ERPNext values the Repack (checked in the installed code, 15.90.1)"),
	keep(S.h3("Stock and accounting impact – worked example"), opt2_gl, spacer(2)),
	callout([
		f"Cost of Goods Sold is {rs(FG_AMT)} and the margin {rs(OPT2_MARGIN)}, the real figure; painted stock in "
		f"store is valued at {rs(FG_RATE)} per unit. {EIIV} clears to nil (Dr by the painter's bill, Cr by the "
		f"Repack); a balance on it flags a painting bill not yet taken into stock, or the reverse.",
		f"The General Ledger report nets lines on one account, so the Repack shows there as {STOCK} Dr "
		f"{rs(FG_AMT - BUY_AMT)} / {EIIV} Cr {rs(PAINT)} ({STOCK_ADJ} lines cancel out); the Stock Ledger shows "
		f"the full {rs(BUY_AMT)} out and {rs(FG_AMT)} in.",
	], "ok"),
	keep(
		table([
			["Advantages", "Limitations"],
			[bullets([f"Each Item Group reports naturally: purchases under {GRP_BUY}, sales under {GRP_SELL}.",
				"Painting cost is inside stock value and Cost of Goods Sold.",
				"Separate stock balances for unpainted and painted items.",
				"One Repack links purchase item, sales item and painting cost (audit trail)."], S.CELL),
			bullets(["Two item codes per physical item; needs a naming rule.",
				"One extra entry (Repack) per batch.",
				"The painting amount is needed at Repack time; if the bill comes later, use the Purchase Order "
				"value and review the clearing account.",
				"Until the Repack is posted the sales item has no stock, so the Delivery Note is blocked."], S.CELL)],
		], [50, 50], zebra=False),
		spacer(2),
		co("The item is painted or serviced before sale, or the sales side must be reported and valued separately "
			"from the purchase side.", "note", title="When to use Option 2"),
	),
]

# 4 ------------------------------------------------------------------------------------------------------------
story += [
	CondPageBreak(55 * mm),
	S.h1("4. Option 3 – Subcontracting (later phase)"),
	S.p("If painting moves to the painter's premises at volume, ERPNext's subcontracting flow tracks the material "
		"sent out and the painted item received back:"),
	numbered([
		"Purchase Order with <b>Is Subcontracted</b> ticked: painting service item, with the sales item as Finished "
		"Good Item and its quantity; then a Subcontracting Order is created from it.",
		"Stock Entry <b>Send to Subcontractor</b>: the purchase item moves to the job worker's warehouse.",
		f"Subcontracting Receipt: the sales item comes back valued at material cost + service cost "
		f"({rs(BUY_RATE)} + {rs(PAINT_PER_UNIT)} = {rs(FG_RATE)} per unit, {rs(FG_AMT)} in all – the same stock "
		f"value as Option 2); then the Purchase Invoice for the service against the Purchase Order.",
	]),
	callout([
		"In ERPNext 15.90.1 a subcontracted Purchase Order row must name a Finished Good Item that has “Supply Raw "
		"Materials for Purchase” ticked and a <b>Default BOM</b>, and the BOM is mandatory on the Subcontracting "
		"Order. A <b>Subcontracting BOM</b> document type exists (finished good, its BOM and the service item), but "
		"it too needs the finished good's BOM. So a BOM is required; Work Orders and Job Cards are not.",
		"BATL already keeps BOMs and uses subcontracted Purchase Orders for some Finished Goods items, so the steps "
		"are familiar; painting would need a one-line BOM per sales item and five documents per batch (three in "
		"Option 2).",
	], "warn", title="Requirement checked in the installed version"),
	S.p("<b>When to use:</b> painting or other services are routinely done at a vendor's premises and the material "
		"held there must be tracked. Suggested as a later phase, after Option 2 is in use."),
]

# 5 ------------------------------------------------------------------------------------------------------------
comparison = [
	["Criterion", "Option 1 – one item code", "Option 2 – Repack", "Option 3 – subcontracting"],
	["Item codes", "One", "Two (purchase + sales)", "Two, plus a BOM for the sales item"],
	["Stock accuracy", f"Painted stock at purchase cost ({rs(BUY_RATE)})",
		f"Painted stock includes painting ({rs(FG_RATE)})",
		f"Includes painting ({rs(FG_RATE)}); also tracks stock at the painter"],
	["Cost capture", "Painting booked as an expense, outside item cost",
		"Painting in valuation via Additional Costs", "Painting in valuation via the service rate"],
	["Effort", "Lowest: no extra entries", "Moderate: one Repack per batch",
		"Highest: five documents per batch, BOM upkeep"],
	["Reporting", "One Item Group; second view by account or custom field",
		f"Purchases under {GRP_BUY}, sales under {GRP_SELL}", "As Option 2"],
	["Audit trail", "Receipt → Delivery; painting bill separate",
		"Receipt → Repack (purchase item, sales item, painting) → Delivery",
		"Full job-work trail incl. material sent out"],
	["Manufacturing module", "Not needed", "Not needed", "BOM needed; no Work Orders"],
]

story += [
	keep(S.h1("5. Comparison and decision guide"), table(comparison, [17, 27, 28, 28], font_size=8), spacer(3)),
	keep(
		S.h2("Decision guide"),
		table([
			["If the item …", "Use", "Why"],
			["is sold exactly as bought", "Option 1", "No conversion happens; one code keeps Stores simple."],
			["is painted or serviced before sale", "Option 2",
				"Painting goes into stock value and Cost of Goods Sold; each side has its own Item Group."],
			["is painted at the painter's premises at volume", "Option 3 (later)",
				"Tracks material held by the vendor; needs a BOM per sales item."],
		], [30, 16, 54], highlight_rows=(2,)),
		spacer(3),
	),
	callout([
		"1. BATL Stores and Accounts list the items sold as bought and those painted or serviced before sale.",
		f"2. For Option 2, agree the sales item naming rule, the painting service item and the use of {EIIV}.",
		"3. Acube sets up and tests the agreed option on a test copy, then walks Stores through one Repack.",
	], "key", title="Suggested next steps"),
]

doc.build(story)
os.makedirs(os.path.dirname(COPY), exist_ok=True)
shutil.copyfile(OUT, COPY)
print("written", OUT)
print("copied ", COPY)
