"""Finance Testing Guide: every point of the BrahMos Reports & Observations Tracker (Sl 1 to 35) - your point, the
action taken, how it was done, and how the Accounts team checks or tests it, with screenshots.

    python finance_testing_guide.py [screenshots folder]

The screenshots (desk pages of the batl site, and the exported workbooks as LibreOffice shows them) are cropped into
testing_screenshots/ next to this script; given a folder, they are taken from it first. Run with a Python that has
reportlab and Pillow (not the bench env).
"""

import glob
import os
import shutil
import sys

from PIL import Image, ImageChops

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acube_pdf import (  # noqa: E402
	S,
	CondPageBreak,
	Doc,
	KeepTogether,
	PageBreak,
	bullets,
	callout,
	image,
	key_value,
	mm,
	numbered,
	spacer,
	table,
)

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "testing_screenshots")
OUT = os.path.join(HERE, "Finance Testing Guide.pdf")
COPY = "/home/acubeadmin/Downloads/BATL ERP - Reports and Observations Tracker - Finance Testing Guide.pdf"

FULL = (80, 55, 1345, 900)  # a report page below the navigation bar
FORM_TOP = (40, 0, 1400, 420)  # a form's title, status and actions
# source file (#suffix to crop one file twice) -> (cropped name, crop box or "auto" for the white margins)
CROPS = {
	"q01_cash_flow_summary.png": ("01_cash_flow_summary.png", (40, 55, 1400, 830)),
	"q02_tb_total.png": ("02_tb_opening.png", (80, 55, 1345, 560)),
	"p3_ap_grn.png": ("03_ap_grn_date.png", FULL),
	"Accounts Payable.png": ("03_ap_excel.png", "auto"),
	"p4_ar_menu.png": ("04_ar_menu.png", (80, 55, 1345, 520)),
	"p4_ar_export_dialog.png": ("04_export_dialog.png", (420, 28, 995, 337)),
	"p4_perm_sales_invoice.png": ("04_permission_sales_invoice.png", (80, 55, 1345, 820)),
	"Accounts Receivable.png": ("04_ar_excel.png", "auto"),
	"p5_perm_item.png": ("05_permission_item.png", (80, 55, 1345, 780)),
	"Stock Ageing.png": ("05_stock_ageing_excel.png", "auto"),
	"q06_company_exchange.png": ("06_company_exchange.png", (300, 330, 1345, 560)),
	"q07_msme_ageing.png": ("07_msme_ageing.png", FULL),
	"q08_payment_advice.png": ("08_payment_advice.png", (400, 180, 1175, 1050)),
	"q09_neft.png": ("09_neft.png", (410, 170, 1230, 1180)),
	"p10_1_draft_actions.png": ("10_1_draft_actions.png", FORM_TOP),
	"p10_2_returned.png": ("10_2_returned.png", FORM_TOP),
	"p10_3_checked_actions.png": ("10_3_checked_actions.png", FORM_TOP),
	"p10_4_rejected_amend.png": ("10_4_rejected_amend.png", FORM_TOP),
	"p10_5_amended.png": ("10_5_amended.png", FORM_TOP),
	"p11_1_pe_amended.png": ("11_1_pe_amended.png", FORM_TOP),
	"p11_3_pe_transitions.png": ("11_3_pe_transitions.png", (300, 80, 1345, 540)),
	"q12_employee_advance_summary.png": ("12_employee_advance_summary.png", (80, 55, 1345, 480)),
	"q13_brs.png": ("13_brs.png", (80, 55, 1345, 880)),
	"q14_budget_variance.png": ("14_budget_variance.png", (80, 55, 1345, 880)),
	"q15_profit_loss.png": ("15_profit_loss.png", FULL),
	"q16_balance_sheet.png": ("16_balance_sheet.png", FULL),
	"q17_asset_category.png": ("17_asset_category.png", (300, 200, 1350, 730)),
	"q18_advance_ageing.png": ("18_advance_ageing.png", FULL),
	"q19_staff_advance_gl.png": ("19_staff_advance_gl.png", FULL),
	"q19_staff_advance_by_employee.png": ("19_staff_advance_by_employee.png", FULL),
	"q20_supplier_group.png": ("20_supplier_group.png", (300, 370, 1340, 600)),
	"q23_create_menu.png": ("23_create_menu.png", FORM_TOP),
	"q24_item_group_defaults.png": ("24_item_group_defaults.png", (300, 130, 1320, 790)),
	"q25_stock_in_hand.png": ("25_stock_in_hand.png", FULL),
	"p26_1_save_refused.png": ("26_1_save_refused.png", (40, 0, 1400, 660)),
	"p26_2_report.png": ("26_2_report.png", FULL),
	"p26_3_report_vouchers.png": ("26_3_report_vouchers.png", FULL),
	"p26_4_gl_drill.png": ("26_4_gl_drill.png", (80, 55, 1345, 850)),
	"p26_5_workspace.png": ("26_5_workspace.png", (300, 370, 1340, 640)),
	"p27_1_tb_screen.png": ("27_1_tb_screen.png", FULL),
	"p27_2_tb_print.png": ("27_2_tb_print.png", (140, 30, 1040, 1000)),
	"Trial Balance.png": ("27_3_tb_excel.png", "auto"),
	"q23_create_menu.png#28": ("28_full_names.png", (40, 40, 760, 500)),
	"q30_stock_balance.png": ("30_stock_balance.png", FULL),
	"q31_generate.png": ("31_1_generate.png", (80, 55, 1345, 420)),
	"q31_stock_balance_item.png": ("31_2_stock_balance_item.png", (80, 55, 1345, 600)),
	"q32_item_valuation.png": ("32_1_item_valuation.png", (140, 60, 1360, 520)),
	"q32_stock_ledger.png": ("32_2_stock_ledger.png", FULL),
	"p33_1_stock_entry.png": ("33_1_stock_entry_rates.png", (330, 380, 1310, 900)),
	"p33_3_gl.png": ("33_3_gl.png", (80, 55, 1345, 690)),
}


def prepare_screenshots(source):
	os.makedirs(SHOTS, exist_ok=True)
	if not source:
		return
	for old in glob.glob(os.path.join(SHOTS, "*.png")):
		os.remove(old)
	for key, (name, box) in CROPS.items():
		path = os.path.join(source, key.split("#")[0])
		if not os.path.exists(path):
			print("missing", key)
			continue
		im = Image.open(path).convert("RGB")
		if box == "auto":
			bg = Image.new("RGB", im.size, (255, 255, 255))
			left, top, right, bottom = ImageChops.difference(im, bg).getbbox()
			box = (max(left - 8, 0), max(top - 8, 0), min(right + 8, im.width), min(bottom + 8, im.height))
		im.crop(box).save(os.path.join(SHOTS, name), optimize=True)


def shot(name, caption, width_mm=None, max_height_mm=105):
	flowable = image(os.path.join(SHOTS, name), width_mm=width_mm, max_height_mm=max_height_mm, caption=caption)
	flowable.is_screenshot = True
	return flowable


def esc(text):
	return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def sub(title):
	return [CondPageBreak(32 * mm), S.h2(title)]


def record_table():
	return KeepTogether(
		[
			spacer(2),
			table(
				[["Checked by", "Date", "Result (OK / Not OK)", "Remarks"], ["", "", "", ""]],
				[22, 16, 22, 40],
				zebra=False,
			),
			spacer(4),
		]
	)


def point(number, title, tracker, client, remark, action, body=(), record=True):
	"""One tracker point: heading, your point and our remark (from the tracker), the action taken, then how it was
	done / how to check with screenshots, and a box to record the check."""
	flow = [
		CondPageBreak(75 * mm),
		S.h1(f"Point {number} – {esc(title)}"),
		S.small(f"Tracker: {esc(tracker)}"),
		spacer(1),
		key_value([("Your point", esc(client)), ("Our remark (tracker)", esc(remark))], widths=(22, 78)),
		spacer(2),
		callout(action, "ok", title="Action taken"),
	]
	body = list(body)
	if record:
		# the record box follows the steps, before the screenshots, so that it stays with its point
		first_shot = next((i for i, f in enumerate(body) if getattr(f, "is_screenshot", False)), len(body))
		body.insert(first_shot, record_table())
	return flow + body


TRAINING = (
	"Training has been provided and {} has been implemented by Ajin. The Accounts team is required to complete User "
	"Acceptance Testing (UAT) with their own data."
)

# Sl, point, tracker resolution, action taken, status now
GLANCE = [
	("1", "Cash Flow", "Completed", "New report Cash Flow Summary in the Tally format", "Done – in use"),
	("2", "Trial Balance (OB difference)", "Completed", "Opening difference re-checked: ₹15,17,38,044.97",
		"Your action"),
	("3", "Ageing – Creditors", "In progress", "GRN Date ageing; Excel export fixed", "Done – please test"),
	("4", "Ageing – Debtors", "In progress", "Export permission and Excel export fixed", "Done – please test"),
	("5", "Ageing – Stock", "In progress", "Export permission and Excel export fixed", "Done – please test"),
	("6", "Forex fluctuation", "Completed", "Explained; Exchange Gain/Loss accounts checked", "Explained"),
	("7", "MSME Report", "Completed", "New report MSME Ageing; MSME category on suppliers", "Done – in use"),
	("8", "Payment advice", "Completed", "Bank Payment Advice corrected, and the fix made permanent",
		"Done – in use"),
	("9", "NEFT advice", "In progress", "NEFT print format (Canara Bank NF-959) created", "Done – please review"),
	("10", "Workflow – Purchase Invoice", "In progress", "Draft rejection → Returned for Correction",
		"Done – please test"),
	("11", "Workflow – Payment", "In progress", "Amend after rejection starts at Prepared By, with Save",
		"Done – please test"),
	("12", "Staff advance summary", "Pending", "Awaiting your format", "Awaiting your format"),
	("13", "BRS", "Completed", "Implemented; training given", "UAT with your data"),
	("14", "Budget", "Completed", "Implemented; training given; new report (point 26)", "UAT with your data"),
	("15", "P&amp;L account", "Completed", "Implemented; training given", "UAT with your data"),
	("16", "BS", "Completed", "Implemented; training given", "UAT with your data"),
	("17", "Depreciation", "Completed", "Implemented; training given", "UAT with your data"),
	("18", "Advance pending list with ageing", "Completed", "Accounts Receivable on the advance account",
		"Explained"),
	("19", "Staff advance ledger vs summary", "Pending", "Cause found; employee-wise view shown",
		"Awaiting your format"),
	("20", "PJG voucher under SCD group", "Completed", "Supplier Group filters on Indent and SCR", "Done"),
	("23", "Payment or Payment Request", "Completed", "Use “Payment”", "Explained"),
	("24", "Expense heads under COGS", "Completed", "Expense accounts set on the Item Groups", "Done"),
	("25", "Opening stock", "Completed", "Shown in Stock In Hand", "Explained"),
	("26", "Cost Center (Main - BATL)", "Pending", "Cost Center required; new budget report", "Done – please test"),
	("27", "Trial Balance – bold groups", "Pending", "Bold on screen, in print and in Excel", "Done – please test"),
	("28", "Full names instead of codes", "Completed", "Full names shown", "Done"),
	("29", "TDS", "Pending", "User guide “TDS in ERPNext”; setup gaps listed", "Guide sent"),
	("30", "Stock ledger totals / summary", "Completed", "Use Stock Balance", "Explained"),
	("31", "Stock balance view under item", "Completed", "Click Generate New Report", "Explained"),
	("32", "Valuation rate zero", "Completed", "Explained with an example", "Explained"),
	("33", "MAT-STE-01139 – ledger", "Pending", "Cause found; transfers now use Stock Adjustment",
		"Done – please test"),
	("34", "MAT-STE-01139 – totals", "Pending", "Cause found; rates shown to 4 decimals", "Done – please test"),
	("35", "Same item, two item groups", "Pending", "Options document", "For your decision"),
]


def glance_table():
	rows = [["Sl", "Point", "Tracker", "Action taken", "Status now"]]
	shaded = []
	for i, (sl, name, tracker, action, now) in enumerate(GLANCE, 1):
		rows.append([sl, name, tracker, action, f"<b>{now}</b>"])
		if now.startswith("Done – please"):
			shaded.append(i)
	return table(rows, [6, 24, 13, 39, 18], highlight_rows=shaded, font_size=8)


# ------------------------------------------------------------------------------------------------ reports 1 - 18
def points_1_2():
	flow = point(
		1, "Cash Flow", "Required format not available · Completed",
		"Cash Flow – required format not available.",
		"The Cash Flow Statement has been corrected as per the required format and submitted to the Accounts "
		"department.",
		"A new report, <b>Cash Flow Summary</b>, gives the cash flow in your Tally format: opening cash and bank, "
		"inflows on the left, outflows on the right, and closing cash and bank.",
		[
			*sub("How it was done"),
			bullets([
				"The report reads every entry in the cash and bank ledgers for the period and sorts the other side of "
				"each entry by its account group (Current Liabilities, Current Assets and so on), as Tally does.",
				"Each head expands to its ledgers and each ledger to its vouchers; Expand All / Collapse All open or "
				"close every level.",
				"Filters: Company, From and To date, and one or more cash / bank accounts. The print keeps the "
				"two-column layout.",
			]),
			*sub("How to check"),
			numbered([
				"Search for <b>Cash Flow Summary</b> and choose a month.",
				"The opening and closing cash / bank figures agree with the bank and cash ledgers.",
				"Expand a head down to its vouchers; print the report.",
			]),
			shot("01_cash_flow_summary.png", "Cash Flow Summary: inflow and outflow side by side"),
		],
	)
	flow += point(
		2, "Trial Balance – opening balance difference", "Not tallied – OB difference · Completed",
		"Trial Balance not tallied – opening balance (OB) difference.",
		"The client has indicated that the OB difference in the Trial Balance is likely due to incomplete data entry "
		"on their end. The client will verify the opening entries and carry out the necessary corrections.",
		"No system change is needed; the Trial Balance adds up the opening entries as entered. Re-checked for this "
		"guide: for 2026-27 the opening Debit total is <b>₹2,28,27,27,958.20</b> and the opening Credit total is "
		"<b>₹2,43,44,66,003.17</b>. The opening entries are still short on the debit side by "
		"<b>₹15,17,38,044.97</b>.",
		[
			*sub("How to check"),
			numbered([
				"Accounting › Trial Balance for 2026-2027; fold the tree to the top heads.",
				"Compare Opening (Dr) and Opening (Cr) on the Total line. They are equal once all opening balances "
				"are entered.",
				"Compare each head's opening with your 31-03-2026 closing figures, and correct the Opening Entry "
				"journals (OB-JV series).",
			]),
			shot("02_tb_opening.png", "Trial Balance 2026-27, top heads: the opening totals do not yet agree",
				max_height_mm=80),
		],
	)
	return flow


def points_3_to_5():
	flow = point(
		3, "Ageing – Creditors: GRN Date and Excel export", "In progress → done, please test",
		"With invoice date – available; with GRN date – not available; with accounting date – available; group by "
		"supplier – available; unable to export the reports into Excel.",
		"An additional ageing option based on GRN date (Purchase Receipt posting date) will be added to the “Ageing "
		"Based On” filter of the Accounts Payable report. The issue in exporting the report to Excel will be "
		"checked.",
		"“GRN Date” added to Ageing Based On in Accounts Payable and Accounts Payable Summary. The Excel export "
		"downloads as a proper .xlsx file.",
		[
			*sub("How it was done"),
			bullets([
				"A purchase invoice is aged from the date of its GRN (Purchase Receipt). With several GRNs, the latest "
				"is used; with none, the invoice's posting date. Payments, journals and advances age from their "
				"posting date. The other options, the ranges, Group By Supplier and the Summary are unchanged.",
				"The rule extends ERPNext's own ageing calculation; the report is not copied, so it stays in step "
				"with ERPNext updates.",
				"<b>Excel:</b> the file was produced, but a malformed header in the standard ERPNext download made the "
				"browser save it under a random name with no extension. The export is now sent as an Excel "
				"attachment, for example “Accounts Payable.xlsx”. Amounts are numbers with 2 decimals, dates are "
				"dates, and the header row is bold and frozen.",
			]),
			*sub("How to test"),
			numbered([
				"Accounting › Accounts Payable: set Ageing Based On to <b>GRN Date</b>.",
				"An invoice made from a GRN is aged from the GRN date; one without a GRN from its own date.",
				"Tick Group By Supplier; compare with Accounts Payable Summary (GRN Date).",
				"⋯ › Export › Excel › Download, and open the file in Excel.",
			]),
			shot("03_ap_grn_date.png", "Accounts Payable with Ageing Based On = GRN Date"),
			shot("03_ap_excel.png", "The exported file as a spreadsheet shows it", max_height_mm=75),
		],
	)
	flow += point(
		4, "Ageing – Debtors: Excel export", "In progress → done, please test",
		"Available – unable to export the report into Excel.",
		"The issue in exporting the Accounts Receivable ageing report to Excel will be checked.",
		"Export allowed for the Accounts User and Accounts Manager roles; the export downloads as a proper .xlsx "
		"file.",
		[
			*sub("How it was done"),
			bullets([
				"<b>Cause 1 – permission.</b> ERPNext offers Export in a report only to roles with Export on the "
				"report's document type, Sales Invoice for Accounts Receivable. Neither Accounts User nor Accounts "
				"Manager had it, so Export did not appear.",
				"Export is now ticked for both roles on Sales Invoice, and on Purchase Invoice (point 3). Nothing else "
				"was changed.",
				"<b>Cause 2</b> was the download fault of point 3, fixed the same way.",
			]),
			*sub("How to test"),
			numbered([
				"As a member of the Accounts team (not a System Manager), open Accounts Receivable: ⋯ shows "
				"<b>Export</b>.",
				"Export to Excel without, then with, Group By Customer. Repeat with Accounts Receivable Summary.",
			]),
			shot("04_ar_menu.png", "Accounts Receivable: Export in the ⋯ menu", max_height_mm=80),
			shot("04_export_dialog.png", "Export dialog: File Format Excel, then Download", width_mm=105),
			shot("04_permission_sales_invoice.png", "Export ticked for Accounts User and Accounts Manager on Sales "
				"Invoice", max_height_mm=95),
			shot("04_ar_excel.png", "The exported file, grouped by customer", max_height_mm=75),
		],
	)
	flow += point(
		5, "Ageing – Stock: Excel export", "In progress → done, please test",
		"Available – unable to export the report into Excel.",
		"The issue in exporting the Stock Ageing report to Excel will be checked.",
		"Export allowed for the Stock User, Stock Manager and Accounts User roles; the export downloads as a proper "
		".xlsx file with every ageing range as numbers.",
		[
			*sub("How it was done"),
			bullets([
				"Same causes as point 4: Stock Ageing's export needs Export on Item, which these roles did not have. It "
				"is now ticked for them.",
				"Each range's quantity (“Age (0 - 30)”) and value (“Value (0 - 30)”) is a number in Excel.",
				"Stock Ageing is a <b>prepared report</b>: click Generate New Report, wait until it is ready, then "
				"export.",
			]),
			*sub("How to test"),
			numbered([
				"Stock › Stock Ageing as a Stock or Accounts user: set the filters and generate the report.",
				"⋯ › Export › Excel: “Stock Ageing.xlsx” opens in Excel.",
			]),
			shot("05_permission_item.png", "Export ticked on Item for Accounts User, Stock Manager and Stock User",
				max_height_mm=95),
			shot("05_stock_ageing_excel.png", "The exported Stock Ageing file", max_height_mm=70),
		],
	)
	return flow


def points_6_to_9():
	flow = point(
		6, "Forex fluctuation", "Clarification needed · Completed",
		"Forex fluctuation – clarification needed.",
		"ERPNext handles this through multi-currency accounting. The Purchase Invoice is recorded in USD at the "
		"exchange rate on the invoice date; the Payment Entry at the rate on the payment date. The difference is the "
		"realized exchange gain/loss, posted to the Exchange Gain/Loss account of the Company master. For balances "
		"still open at month-end or year-end, the Exchange Rate Revaluation tool posts the unrealized gain/loss.",
		"Explained (see the remark). In the Company master the <b>Exchange Gain / Loss Account</b> is set "
		"(Exchange Gain/Loss - BATL), but the <b>Unrealized Exchange Gain/Loss Account</b> is empty. It must be set "
		"before Exchange Rate Revaluation is used (Appendix).",
		[
			*sub("How to check"),
			numbered([
				"Make a USD Purchase Invoice for a supplier billed in USD, then a Payment Entry at a different rate.",
				"After submitting, the ledger shows the difference on Exchange Gain/Loss - BATL.",
				"At month-end, run Accounting › Exchange Rate Revaluation for the open USD balances.",
			]),
			shot("06_company_exchange.png", "Company master: Exchange Gain / Loss set; Unrealized account empty",
				max_height_mm=60),
		],
	)
	flow += point(
		7, "MSME Report", "Not available · Completed",
		"MSME Report – not available.",
		"(Marked Completed in the tracker.)",
		"A new report, <b>MSME Ageing</b> (Accounting › Payables › Reports), lays out the MSME position as in "
		"your MSME Excel sheet.",
		[
			*sub("How it was done"),
			bullets([
				"Two views: <b>Form I (Supplier-wise)</b> and <b>Invoice-wise</b>. Filters: company, period (half year "
				"by default), suppliers, MSME category, Ageing Based On (Posting Date, Supplier Invoice Date or GRN "
				"Date), payment days (45) and interest rate.",
				"Payments are the Payment Entries and bank journals; adjustments are other journals and debit notes. "
				"Interest for delay = amount × rate × (days − 45) ÷ 365.",
				"An <b>MSME Category</b> field (Micro / Small / Medium) was added to the Supplier. The 112 suppliers of "
				"your MSME list found in the ERP were updated with their MSME number and category; those not found "
				"were sent to you in a separate sheet.",
			]),
			*sub("How to check"),
			numbered([
				"Open MSME Ageing for the half year, Form I: the amounts agree with Accounts Payable for the MSME "
				"suppliers.",
				"Switch to Invoice-wise and check the days and the interest of a late invoice.",
			]),
			shot("07_msme_ageing.png", "MSME Ageing – Form I (Supplier-wise)"),
		],
	)
	flow += point(
		8, "Payment advice", "Wrong report · Completed",
		"Payment advice – wrong report.",
		"The issue was identified in the Payment Advice print format and has been rectified.",
		"The <b>Bank Payment Advice</b> print (Payment Entry › Print) was corrected. While preparing this guide we "
		"found that the correction was being replaced by an older copy each time the ERP was updated. That is now "
		"fixed, so the correction stays; the same was done for the Goods Receipt Note print.",
		[
			*sub("How it was done"),
			bullets([
				"One line per invoice: several references to the same invoice are added together.",
				"An “On Account / Advance” line for any amount not allocated to an invoice.",
				"A single Total line with the bill amount, deductions and amount paid.",
			]),
			*sub("How to check"),
			numbered([
				"Open a supplier Payment Entry › Print › Bank Payment Advice.",
				"Each invoice appears once, and one Total line agrees with the amount paid.",
			]),
			shot("08_payment_advice.png", "Bank Payment Advice: one line per invoice, one Total", max_height_mm=115),
		],
	)
	flow += point(
		9, "NEFT advice", "Not possible · In progress",
		"NEFT advice – not possible.",
		"The issue relates to the NEFT Advice print format. The client will provide the required format.",
		"From your NEFT format sheet, a new print format <b>NEFT</b> was created on the Payment Entry: the Canara "
		"Bank NEFT / RTGS application (NF-959), filled from the payment. Please review it.",
		[
			*sub("How it was done"),
			bullets([
				"From the payment: date, amount in figures and words, mode (cash, cheque with number and date, or debit "
				"to account) and the remitter account.",
				"From the company: the remitter name, address, phone and PAN.",
				"From the supplier's Bank Account: beneficiary name, account number, bank, IFSC and branch address. "
				"These stay blank for a supplier with no Bank Account in the ERP, as in the sample below (Appendix).",
			]),
			*sub("How to check"),
			numbered([
				"Open a supplier Payment Entry › Print › choose <b>NEFT</b>.",
				"Check every box against the form you fill by hand today, and print on A4.",
			]),
			shot("09_neft.png", "NEFT print (Canara Bank NF-959)", max_height_mm=135),
		],
	)
	return flow


def points_10_11():
	flow = point(
		10, "Workflow – Purchase Invoice: “Illegal Document Status for Rejected”",
		"Prepared / Approval – 2 level · In progress → done, please test",
		"When attempting to reject a purchase invoice prepared against a GRN, the system generates an “illegal "
		"document status for rejected” error message.",
		"Invoice rejection is permissible provided the document undergoes formal approval prior to the rejection "
		"action.",
		"A draft can now be rejected: it goes to a new state, <b>Returned for Correction</b>, and is corrected and "
		"approved again. Rejecting after approval still cancels the invoice. The Payment Entry and Journal Entry "
		"workflows were changed the same way.",
		[
			*sub("Why it happened"),
			S.p(
				"A prepared invoice is a <b>draft</b> in “Prepared By”. Reject moved it to “Rejected”, which "
				"<b>cancels</b> a document, and ERPNext can only cancel a submitted one. The workflow could not send "
				"drafts elsewhere because “Prepared By” had been marked as a submitted state; ERPNext refuses a draft "
				"state that leads to a cancelled one."
			),
			*sub("The workflow now"),
			table(
				[
					["Stage", "Approve", "Reject"],
					["Prepared By (draft, Accounts User edits)", "→ Checked By (the invoice is submitted)",
						"→ <b>Returned for Correction</b> (still a draft)"],
					["Returned for Correction (draft, Accounts User edits)", "→ Checked By (submitted)", "–"],
					["Checked By (submitted)", "→ Verified By", "→ Rejected (cancelled)"],
					["Verified By (submitted)", "→ Approved", "→ Rejected (cancelled)"],
					["Rejected (cancelled)", "Amend → a new draft at Prepared By", "–"],
				],
				[34, 33, 33],
			),
			spacer(2),
			S.p(
				"Older documents whose state does not match their status are not offered Reject: submitted ones still "
				"in “Prepared By” (mostly opening entries) and drafts left in “Checked By”. They can be approved "
				"forward (Appendix)."
			),
			*sub("How to test (Accounts User prepares, Accounts Manager checks)"),
			numbered([
				"Accounts User: make a Purchase Invoice from a GRN and save it (Prepared By).",
				"Accounts Manager: Actions › Reject → <b>Returned for Correction</b>, no error, still a draft.",
				"Accounts User: correct, save, Actions › Approve → submitted in Checked By.",
				"Accounts Manager: Reject at Checked By or Verified By → cancelled in Rejected.",
				"Amend → the new draft is at Prepared By and can be saved (point 11).",
				"Run the normal path once: Prepared By → Checked By → Verified By → Approved.",
			]),
			shot("10_1_draft_actions.png", "A draft in Prepared By: Reject is offered", max_height_mm=58),
			shot("10_2_returned.png", "After Reject: Returned for Correction, still a draft", max_height_mm=58),
			shot("10_3_checked_actions.png", "A submitted invoice in Checked By: Approve or Reject", max_height_mm=58),
			shot("10_4_rejected_amend.png", "A rejected (cancelled) invoice: Amend", max_height_mm=58),
			shot("10_5_amended.png", "The amendment starts at Prepared By, with Save", max_height_mm=58),
		],
	)
	flow += point(
		11, "Workflow – Payment: errors after rejection and amendment",
		"Prepared / Checked / Verified / Authorized / Approved · In progress → done, please test",
		"A payment entry was prepared, checked, verified and rejected. After amendment the system blocks saving "
		"(“workflow state transition not allowed from prepared to rejected”), and for other users the Save button "
		"disappears.",
		"Issue recorded against the Payment Entry workflow (5 levels).",
		"An amended Payment Entry (and Purchase Invoice and Journal Entry) now starts at <b>Prepared By</b>, so it "
		"saves without the error and the Accounts User sees Save. The point 10 change applies to payments too.",
		[
			*sub("Why it happened"),
			S.p(
				"Amend copied the cancelled document's state “Rejected”. A new document may only start at the first "
				"state, so saving was refused. “Rejected” is editable only by the Chief Finance Officer, so the copied "
				"state also hid Save from everyone else."
			),
			*sub("How to test"),
			numbered([
				"Prepare a Payment Entry, approve it to Checked By and Verified By, then Reject (Accounts Manager).",
				"As an Accounts User, click Amend: <b>Save</b> is shown; save it. No error; the state is Prepared By.",
				"Approve it to Approved. Repeat a rejection at Authorized By (Chief Finance Officer).",
				"Repeat steps 1 and 2 for a Journal Entry.",
			]),
			shot("11_1_pe_amended.png", "An amended Payment Entry: Prepared By, Save available", max_height_mm=58),
			shot("11_3_pe_transitions.png", "The Payment Entry workflow after the change", max_height_mm=80),
		],
	)
	return flow


def points_12_to_18():
	flow = point(
		12, "Staff advance summary", "Wrong report · Pending",
		"Staff advance summary – wrong report.",
		"The client will provide the required format for the Staff Advance Summary report, including a summary view "
		"with drill-down options to view the respective vouchers for each salary advance.",
		"Awaiting your format. Until then, the standard <b>Employee Advance Summary</b> lists the Employee Advance "
		"documents; point 19 explains why it differs from the ledger and shows the employee-wise ledger view.",
		[shot("12_employee_advance_summary.png", "Employee Advance Summary (standard report)", max_height_mm=60)],
		record=False,
	)
	flow += point(
		13, "BRS", "To be checked · Completed",
		"BRS – to be checked.",
		TRAINING.format("the Bank Reconciliation Statement (BRS)"),
		"Implemented and training given; UAT with your data is pending.",
		[
			*sub("How to check"),
			numbered([
				"Accounting › Bank Clearance: enter the clearance dates of the month's entries from the bank statement.",
				"Accounting › Bank Reconciliation Statement: choose the bank account and the statement date; “Balance "
				"as per bank” agrees with the bank statement.",
			]),
			shot("13_brs.png", "Bank Reconciliation Statement, Canara Bank account"),
		],
	)
	flow += point(
		14, "Budget", "To be checked · Completed",
		"Budget – to be checked.",
		TRAINING.format("Budget"),
		"Implemented and training given; UAT with your data is pending. Budgets for 2026-27 are set per cost center "
		"and project; for drill-down to the vouchers use the new report of point 26.",
		[
			*sub("How to check"),
			numbered([
				"Accounting › Budget Variance Report: 2026-2027, Budget Against Cost Center. Compare a cost center's "
				"budget with its Budget record.",
				"Accounting › Cost Center Budget vs Actual (point 26): budget, actual and balance with drill-down.",
			]),
			shot("14_budget_variance.png", "Budget Variance Report 2026-27 by cost center"),
		],
	)
	flow += point(
		15, "P&L account", "To be checked · Completed",
		"P&L account – to be checked.",
		TRAINING.format("the Profit & Loss Statement"),
		"Implemented and training given; UAT with your data is pending.",
		[
			*sub("How to check"),
			numbered([
				"Accounting › Profit and Loss Statement for 2026-2027. Expand a head to its ledgers; a ledger opens "
				"its General Ledger.",
				"Compare the heads with your own working for the same period.",
			]),
			shot("15_profit_loss.png", "Profit and Loss Statement 2026-27"),
		],
	)
	flow += point(
		16, "BS", "To be checked · Completed",
		"Balance Sheet – to be checked.",
		TRAINING.format("the Balance Sheet"),
		"Implemented and training given; UAT with your data is pending. The opening difference of point 2 shows in "
		"the Balance Sheet until the opening entries are completed.",
		[
			*sub("How to check"),
			numbered(["Accounting › Balance Sheet for 2026-2027: expand the heads and compare with the Trial Balance."]),
			shot("16_balance_sheet.png", "Balance Sheet 2026-27"),
		],
	)
	flow += point(
		17, "Depreciation", "To be checked · Completed",
		"Depreciation – to be checked.",
		TRAINING.format("Depreciation"),
		"Implemented and training given; UAT with your data is pending. The 20 asset categories carry the "
		"depreciation method, number of depreciations, frequency and accounts; each asset's schedule follows its "
		"category.",
		[
			*sub("How to check"),
			numbered([
				"Assets › Asset Category: check the method, life and accounts of each category.",
				"Open an asset › Depreciation Schedule: the amounts and dates; posted months link to their journal "
				"entries.",
				"Assets › Asset Depreciation Ledger: the depreciation booked for the period.",
			]),
			shot("17_asset_category.png", "Asset Category: depreciation method, life and accounts", max_height_mm=80),
		],
	)
	flow += point(
		18, "Advance pending list with ageing", "Not available · Completed",
		"Advance pending list with ageing – not available.",
		"Available through the standard Accounts Receivable report: set Receivable Account to “Advance from "
		"customers - BATL” and Ageing Based On to “Posting Date”; enable Group by Customer for subtotals per "
		"customer.",
		"Explained. In the ERP the account is named <b>All advance from customers - BATL</b>. Each row is an "
		"advance not yet adjusted against an invoice, with customer, receipt, date, age and ageing range.",
		[
			*sub("How to check"),
			numbered([
				"Accounting › Accounts Receivable: Receivable Account = All advance from customers - BATL; Ageing "
				"Based On = Posting Date.",
				"Tick Group By Customer for subtotals; Export gives the Excel (point 4).",
			]),
			shot("18_advance_ageing.png", "Accounts Receivable on the customer advance account"),
		],
	)
	return flow


# --------------------------------------------------------------------------------------------- observations 19 - 35
def points_19_to_25():
	flow = point(
		19, "Staff advance ledger vs Employee Advance Summary", "Issue reported · Pending",
		"The staff advance ledger reflects a debit balance of Rs. 6,17,000; however, an employee-wise report is "
		"currently unavailable, and the balances in the standalone employee advance summary report do not "
		"reconcile with the main ledger (Annexure A1, A2).",
		"This will be addressed along with point 12. The client will provide the required format for the "
		"employee-wise Staff Advance report, with a summary view and drill-down to the vouchers for each advance.",
		"We found why the two differ, and the employee-wise balance can already be seen. The new report will follow "
		"your format.",
		[
			*sub("Why they differ"),
			bullets([
				"Staff advance - BATL stood at <b>₹6,17,678.30</b> on 1-4-2026 and <b>₹6,00,678.30</b> on 18-11-2026. "
				"<b>₹5,83,751</b> of it was brought in by opening journal entries; the rest by journal, payment and "
				"expense claim entries.",
				"The Employee Advance Summary reads only <b>Employee Advance</b> documents. There are 5 of them "
				"(₹58,700 advanced, ₹37,700 paid), so it cannot match the ledger.",
				"Every ledger line carries the employee (39 employees). The General Ledger with Party Type = Employee "
				"and Categorize by Party gives each employee's opening, entries and balance with the vouchers.",
			]),
			*sub("How to check"),
			numbered([
				"General Ledger: account Staff advance - BATL, Party Type Employee, Categorize by Party.",
				"The employees' balances add up to the ledger balance.",
			]),
			shot("19_staff_advance_gl.png", "General Ledger of Staff advance - BATL (opening ₹6,17,678.30)"),
			shot("19_staff_advance_by_employee.png", "The same, categorized by employee (Party)"),
		],
		record=False,
	)
	flow += point(
		20, "PJG voucher grouped under SCD purchase", "Clarification sought · Completed",
		"Transaction was executed by selecting Purchase Journal – Goods (PJG) voucher type, but the system "
		"automatically grouped the entry under SCD Purchase due to the underlying party master configuration. "
		"Advise whether same party has to be created under both group.",
		"Filters and validations based on Supplier Group have already been applied for Indent and SCR "
		"transactions.",
		"Supplier Group filters applied: in the <b>Indent</b> the supplier list shows only “Creditors for "
		"Purchases”. In the <b>Sub-Contract Request</b> it follows Materials Issuance: Brahmos → “Creditors for "
		"Sub-contract”; Sub-Contractor → “Creditors for Purchases”.",
		[
			*sub("How it works"),
			S.p(
				"A supplier's ledger (creditors account) comes from its Supplier Group: each group has its Default "
				"Payable Account, such as Creditors for Sub-contract - BATL. The voucher type does not change it. With "
				"the filters, a supplier of the wrong group can no longer be picked on an Indent or SCR."
			),
			*sub("How to check"),
			numbered([
				"Open a new Indent: the supplier list offers only Creditors for Purchases suppliers.",
				"Open a new SCR: change Materials Issuance and see the supplier list change.",
			]),
			shot("20_supplier_group.png", "Supplier Group: its Default Payable Account", max_height_mm=55),
		],
	)
	flow += point(
		23, "Payment or Payment Request", "Clarification sought · Completed",
		"When generating a payment transaction from a purchase invoice, there are “Payment” and “Payment Request” "
		"options available. Kindly advise the need for these two options and which option is to be selected.",
		"The Payment Request option is not used in the BrahMos process; users are advised to disregard this option "
		"and use the “Payment” option to create the Payment Entry against the Purchase Invoice.",
		"Explained: use <b>Create › Payment</b>.",
		[shot("23_create_menu.png", "Purchase Invoice › Create: use Payment; ignore Payment Request",
			max_height_mm=58)],
		record=False,
	)
	flow += point(
		24, "Expense heads under Cost of Goods Sold", "Clarification sought · Completed",
		"Several operational expense heads have been configured under the Cost of Goods Sold group, so purchase "
		"entries debit COGS directly. Please advise the need of creating ledger under the group Cost of Goods Sold.",
		"The Cost of Goods Sold account was selected by default because no default Expense Account was set in the "
		"respective Item Group. Once the Expense Account is set in the Item Group, it is fetched in the voucher. The "
		"Item Group configuration has been rectified accordingly.",
		"Done: Default Expense Accounts set on the Item Groups. For example, Chemicals → Consumption of Tools &amp; "
		"General Stores; Computer Stationery → Printing &amp; Stationery Expenses; Raw Material/Components → "
		"Consumption of Raw Materials.",
		[
			*sub("How to check"),
			numbered([
				"Stock › Item Group › open a group › Item Group Defaults: the Default Expense Account is set.",
				"A new Purchase Invoice or Stock Entry (issue) for an item of that group fetches that account.",
			]),
			shot("24_item_group_defaults.png", "Item Group Chemicals: Default Expense Account", max_height_mm=85),
		],
	)
	flow += point(
		25, "Opening stock", "Change request · Completed",
		"Opening stock to be fetched automatically.",
		"The client was referring to the “Opening Stock” account, assuming it holds the stock value. In ERPNext, "
		"the stock value, including opening stock, is reflected in the “Stock In Hand” ledger, which should be "
		"checked in the Trial Balance and other financial reports.",
		"Explained: the opening stock value is the opening balance of <b>Stock In Hand - BATL</b>.",
		[
			*sub("How to check"),
			numbered([
				"General Ledger for Stock In Hand - BATL from 01-04-2026: the Opening line is the opening stock value.",
				"Stock Balance (point 30) for the same date gives the same value item-wise.",
			]),
			shot("25_stock_in_hand.png", "Stock In Hand - BATL: the Opening line is the opening stock"),
		],
		record=False,
	)
	return flow


def points_26_27():
	flow = point(
		26, "Cost Center – “Main - BATL”", "Clarification sought · Pending → done, please test",
		"Please clarify what is “Main BATL” under cost centre.",
		"“Main - BATL” is the default Cost Center created by ERPNext for the company, auto-applied when no Cost "
		"Center is selected. (1) Cost Center will be made mandatory in transactions; (2) the default Cost Center will "
		"be removed from the Company master; (3) budget reports will include Cost Center-wise columns and filters "
		"with drill-down to the vouchers.",
		"(1) Expense and income lines now need a department Cost Center. (2) The company default is kept only for "
		"the system's own entries. (3) A new report, <b>Cost Center Budget vs Actual</b>, drills down to the "
		"vouchers.",
		[
			*sub("What we found"),
			S.p(
				"Since 1 April 2026, <b>407 of 486</b> income and expense ledger lines (<b>₹25.23 crore</b>) were "
				"booked to Main - BATL, including every Stock Entry issue and Purchase Invoice expense line. This "
				"spending is outside the department budgets."
			),
			*sub("How it was done"),
			bullets([
				"<b>(1)</b> On save or submit, every line posting to an income or expense account needs a Cost Center "
				"other than Main - BATL. This covers Purchase Invoice and Sales Invoice items, Journal Entry lines, "
				"Payment Entry deductions, Stock Entry Material Issue and Receipt lines, and Expense Claim lines. "
				"Purchase Orders and Material Requests show a warning only, because they are made from Indents "
				"automatically.",
				"<b>(2)</b> ERPNext needs the company default for the entries it makes on its own: exchange gain/loss "
				"and revaluation journals, payment reconciliation and advance journals, TDS rows, and the cost center "
				"of a Payment Entry. Removing it would make these fail, for example on foreign-currency payments, so it "
				"stays for the system while (1) keeps users from posting to it.",
				"<b>(3)</b> Cost Center → Account → Voucher, with Annual Budget, Budget to Date, Actual, Variance, "
				"Utilised % and Balance. Every amount opens the General Ledger for that cost center, account and "
				"period. It is on Accounting › Cost Center and Budgeting.",
			]),
			*sub("How to test"),
			numbered([
				"Journal Entry with an expense line on Main - BATL › Save: refused (“Cost Center required”). With "
				"CIVIL (for example): saved.",
				"The same with a service Purchase Invoice and a Stock Entry (Material Issue). A Purchase Invoice of "
				"stock items against a GRN, and a Payment Entry without deductions, save as before.",
				"Open Cost Center Budget vs Actual for 2026-2027 and compare it with the Budget records and the "
				"General Ledger.",
				"Select one cost center and tick Show Vouchers; click an Actual amount to open the General Ledger.",
			]),
			shot("26_1_save_refused.png", "Main - BATL on an expense line is refused, naming the row",
				max_height_mm=85),
			shot("26_2_report.png", "Cost Center Budget vs Actual (Main - BATL has no budget)"),
			shot("26_3_report_vouchers.png", "One cost center with its accounts and vouchers"),
			shot("26_4_gl_drill.png", "An amount opens the General Ledger, already filtered"),
			shot("26_5_workspace.png", "The report on the Accounting workspace", max_height_mm=45),
		],
	)
	flow += point(
		27, "Trial Balance – group ledgers in bold", "Change request · Pending → done, please test",
		"All primary group heads within the Trial Balance to be rendered in bold formatting to enhance structural "
		"scannability.",
		"The group ledgers in the Trial Balance report will be displayed in bold font to improve readability and "
		"distinguish them from individual ledgers.",
		"Every group ledger is in <b>bold</b>, from the primary heads down, on screen, in Print / PDF and in the "
		"Excel export. Individual ledgers stay normal.",
		[
			*sub("How it was done"),
			S.p(
				"ERPNext's own Trial Balance is used, with a small formatting extension; its figures are unchanged. The "
				"Excel export also sizes the amount columns to the largest balance, so Excel shows no “###”."
			),
			*sub("How to test"),
			numbered([
				"Trial Balance for 2026-2027: groups bold, ledgers not; expand and collapse; tick Show zero values.",
				"⋯ › Print and ⋯ › PDF: groups bold.",
				"Export to Excel: groups and the total bold, every amount in full.",
			]),
			shot("27_1_tb_screen.png", "Trial Balance on screen"),
			shot("27_2_tb_print.png", "Print"),
			shot("27_3_tb_excel.png", "Excel export"),
		],
	)
	return flow


def points_28_to_35():
	flow = point(
		28, "Full names instead of employee codes", "Change request · Completed",
		"System usernames to be updated to display the full name of the employee rather than an alphanumeric "
		"employee code, to facilitate immediate personal identification and improve operational clarity.",
		"The employee's full name is now displayed. The underlying link continues to reference the User ID and "
		"opens the respective User record when clicked. This has been rectified.",
		"Done. All 897 active users carry the employee's full name, which the ERP shows in place of the user ID "
		"(for example “Revathy Mohan created this”).",
		[shot("28_full_names.png", "Full names shown on a document", max_height_mm=70)],
	)
	flow += point(
		29, "TDS", "Issue reported · Pending",
		"Under the Sundry Creditors (SCD) bill accounting process, TDS must be manually calculated and deducted, as "
		"the system does not currently feature an automated tax calculation or deduction mechanism.",
		"TDS is calculated and deducted automatically once the Tax Withholding Category is configured and assigned "
		"to the supplier. A detailed user guide, “TDS in ERPNext”, has been prepared.",
		"The guide <b>TDS in ERPNext</b> (8 pages) is sent with this document. It was checked against the installed "
		"ERPNext and India Compliance, and lists what to fix before TDS runs automatically.",
		[
			*sub("Setup items found"),
			bullets([
				"“TDS - 194C - No PAN / Invalid PAN” (32 suppliers) and the 194J(a) categories have no rate for "
				"2026-27; invoices for those suppliers with TDS ticked stop with “No Tax Withholding data found”.",
				"99 of the 105 suppliers invoiced since 1 April 2026 have no Tax Withholding Category.",
				"India Compliance 15.27.1 or later brings the Income Tax Act 2025 codes and the 2026-27 rates; an "
				"update is recommended.",
			]),
			*sub("How to test"),
			numbered([
				"Set up one category and assign it to one supplier as in the guide.",
				"Make a bill over the threshold: the TDS row is added and the TDS ledger is credited.",
			]),
		],
	)
	flow += point(
		30, "Stock ledger totals and stock summary", "Issue reported · Completed",
		"The system has a stock ledger, but it does not show the total sum. The running total value does not show "
		"opening stock value. Stock summary is not available.",
		"The requirement is met by the Stock Balance report, which shows item-wise opening quantity and value, "
		"inward and outward movement, closing balance and totals for the selected period.",
		"Explained: use <b>Stock Balance</b>.",
		[
			*sub("How to check"),
			numbered([
				"Stock › Stock Balance: set the dates (and a warehouse or item group); click Generate New Report.",
				"Each item shows Opening Qty / Value, In, Out and Balance Qty / Value; the last line is the Total.",
			]),
			shot("30_stock_balance.png", "Stock Balance: opening, in, out, balance and totals"),
		],
	)
	flow += point(
		31, "Stock balance view under each item", "Issue reported · Completed",
		"There is a stock balance view facility under each item. However, it does not work properly.",
		"The Stock Balance view under the Item opens the report with the item filter applied; the “Generate Report” "
		"button must be clicked to load the data. As this step was missed, no data was displayed. The facility is "
		"working as intended.",
		"Explained: click <b>Generate New Report</b>.",
		[
			shot("31_1_generate.png", "Stock Balance opened for one item: click Generate New Report", max_height_mm=60),
			shot("31_2_stock_balance_item.png", "The item's balance after generating", max_height_mm=75),
		],
	)
	flow += point(
		32, "Valuation rate zero in the item master", "Clarification sought · Completed",
		"Valuation rate is put as zero. Please advise the consequence. And valuation method is not selected in all "
		"cases.",
		"The Valuation Rate field in the Item master is not where the item's valuation is maintained, and it is not "
		"updated by transactions. The actual valuation rate is calculated from stock transactions and shown in the "
		"stock reports, such as Stock Balance and Stock Ledger.",
		"Explained: a zero in the item master has no effect on the stock value. Where an item has no valuation "
		"method, the company's method in Stock Settings applies.",
		[
			S.p(
				"Example: Gas: High Pure Helium shows Valuation Rate 0.00 in the item master, while the Stock Ledger "
				"values it at ₹4,000 to ₹4,058.44 per unit from its receipts."
			),
			shot("32_1_item_valuation.png", "Item master: Valuation Rate 0.00", max_height_mm=70),
			shot("32_2_stock_ledger.png", "Stock Ledger: the actual valuation rate and value"),
		],
		record=False,
	)
	flow += point(
		"33 and 34", "MAT-STE-01139: ₹0.01 in Consumption of Tools & General Stores; amount vs Grand Total",
		"Clarification sought / Issue reported · Pending → done, please test",
		"33: why was the material transfer entry with wrong amount fetched in the ledger Consumption of Tools and "
		"General Store (Annexure B1)? 34: the amount under the item differs from the grand total (Annexure B2).",
		"MAT-STE-01139 has posted a value of ₹0.01 to the Consumption of Tools & General Store ledger, which is "
		"incorrect. The entry will be checked and rectified (34: same as 33).",
		"Cause found: a 1-paisa rounding difference. Transfers now post any rounding to <b>Stock Adjustment</b>, "
		"and Stock Entry rates show 4 decimals. MAT-STE-01139 itself is unchanged; correcting it needs your "
		"approval (Appendix).",
		[
			*sub("What happened"),
			table(
				[
					["", "Figures"],
					["Item, quantity", "Gas: High Pure Helium, 50, Consumable Store-Restricted → Consumable "
						"Store-Unrestricted, 08-10-2026"],
					["True rate (moving average)", "₹4,05,843.75 ÷ 100 units = <b>₹4,058.4375</b> per unit"],
					["Value leaving the source store", "₹4,05,843.75 − ₹2,02,921.88 left behind = <b>₹2,02,921.87</b>"],
					["Value entering the target store", "50 × ₹4,058.4375 = ₹2,02,921.875 → <b>₹2,02,921.88</b>"],
					["Difference", "₹0.01 (rounding to the paisa on each side)"],
					["Rate shown on screen (before)", "₹4,058.44 (2 decimals) → 50 × 4,058.44 = ₹2,02,922.00"],
				],
				[30, 70],
			),
			spacer(2),
			bullets([
				"<b>33.</b> Both stores post to Stock In Hand, so only the 1-paisa rounding reached the ledger. ERPNext "
				"books it to the line's Difference Account, which was Consumption of Tools &amp; General Stores from the "
				"Item Group default.",
				"<b>34.</b> The stored amount and the Grand Total (₹2,02,921.88) are correct, using the true rate; the "
				"screen rounded the rate to ₹4,058.44.",
			]),
			*sub("How to test"),
			numbered([
				"Open MAT-STE-01139's item line: the rates show ₹4,058.4375, and 50 × 4,058.4375 = ₹2,02,921.88 = "
				"Grand Total.",
				"Save a new Material Transfer: the line's Difference Account is Stock Adjustment - BATL.",
				"Material Issue lines keep their consumption account.",
			]),
			shot("33_1_stock_entry_rates.png", "MAT-STE-01139: the rate shows 4 decimals; the amounts agree",
				max_height_mm=90),
			shot("33_3_gl.png", "General Ledger of MAT-STE-01139: the ₹0.01", max_height_mm=70),
		],
	)
	flow += point(
		35, "Same item in two item groups", "Clarification sought · Pending",
		"If the same item will come under both finished product and SCD item, what is the solution?",
		"The same item is purchased under a purchase-related Item Group and sold under a sales-related Item Group, "
		"and may undergo painting or other services before sale. As the Manufacturing module is not in use, Acube "
		"will share a PDF outlining the options available in ERPNext.",
		"The options document <b>Same Item in Two Item Groups</b> (6 pages) is sent with this document. Nothing was "
		"changed in the system; please choose an option.",
		[
			bullets([
				"<b>Option 1, single item code:</b> when the item is sold as bought.",
				"<b>Option 2, two item codes linked by a Repack entry:</b> when it is painted or serviced before sale; "
				"the painting cost goes into the stock value through Additional Costs.",
				"<b>Option 3, subcontracting:</b> later, if painting is outsourced at volume.",
			]),
		],
		record=False,
	)
	return flow


def appendix():
	return [
		PageBreak(),
		S.h1("Appendix – Items that need your decision or action"),
		table(
			[
				["Point", "What we found", "Proposal"],
				["2", "Opening Dr ₹2,28,27,27,958.20 and Opening Cr ₹2,43,44,66,003.17 for 2026-27 (difference "
					"₹15,17,38,044.97).", "Complete and correct the opening entries; Acube can help trace the "
					"heads."],
				["6", "The Unrealized Exchange Gain/Loss Account is empty in the Company master.",
					"Set it before using Exchange Rate Revaluation."],
				["9", "The company bank account record “402202000013 - CANARA BANK” (used on the NEFT and payment "
					"advice prints) has account number 402202000013, while its ledger is Canara Bank(40063050000013) "
					"- BATL. Very few suppliers have a Bank Account in the ERP.",
					"Confirm the correct account number. Enter supplier bank accounts so that the NEFT form fills the "
					"beneficiary."],
				["10, 11", "Workflow documents whose state does not match their status: Purchase Invoice 146 "
					"submitted in Prepared By (111 opening entries) and 53 drafts in Checked / Verified By; Payment "
					"Entry 5 and 64; Journal Entry 6 and 2.", "They can be approved forward. If you wish, Acube can "
					"move the drafts back to Prepared By (state only; nothing posted)."],
				["19", "Staff advance: ₹5,83,751 of the balance came from opening journals; every line names the "
					"employee.", "Send the format; the employee-wise report will be built on the ledger."],
				["26", "The company default Cost Center is kept for the system's own entries.",
					"Please confirm. The tracker wording “will be removed from the Company master” can read “will no "
					"longer be accepted on user entries”."],
				["29", "TDS setup gaps (see point 29).",
					"Add the 2026-27 rates, assign categories, and plan the India Compliance update."],
				["33", "₹0.01 rounding postings: MAT-STE-00493 and MAT-STE-00902 (Repairs &amp; Maintenance) and "
					"MAT-STE-01139 (Consumption of Tools &amp; General Stores).", "Immaterial. One Journal Entry can "
					"move the ₹0.03 to Stock Adjustment if you want the ledgers cleared."],
				["33", "MAT-STE-01177 (19-10-2026): SPACING WASHER (25.4), 10 Nos, left the store at ₹2,716 per unit "
					"but entered the target at ₹1,358, putting ₹13,580 into Stock Adjustment.",
					"A different cause (the rate on the transfer); to be reviewed with Stores before any correction."],
				["35", "Options document sent.", "Choose the option; Acube sets it up and trains Stores."],
			],
			[9, 51, 40],
		),
	]


def build():
	doc = Doc(
		OUT,
		title="Reports & Observations Tracker – Status, Actions and Testing Guide",
		short_title="Reports & Observations Tracker – Status and Testing Guide",
		audience_line="For the Accounts team of BrahMos Aerospace Thiruvananthapuram",
	)
	story = doc.cover(
		"Reports &amp; Observations Tracker",
		"Status of every point (1 to 35): your point, the action taken, how it was done, and how to check or test "
		"it, with screenshots",
		details=[
			("Prepared for", "Accounts team, BrahMos Aerospace Thiruvananthapuram Ltd"),
			("Prepared by", "Acube Innovations Private Limited"),
			("Covers", "All points of the Reports &amp; Observations Tracker (Sl 1 – 35; Sl 21 and 22 are not used)"),
			("System", "ERPNext v15 (15.90.1) with India Compliance"),
			("Date", "18 November 2026"),
		],
		key_message=(
			"Every tracker point has a section with your point and our remark as in the tracker, the action taken, "
			"how it was done and how to check it, with screenshots. Nine points carry ERP changes for you to test "
			"(3, 4, 5, 10, 11, 26, 27, 33, 34), shaded in the table on page 2. Points 29 and 35 are answered by the "
			"two guides sent with this document."
		),
		contents=[
			"At a glance – all points and the action taken",
			"Reports (points 1 – 18)",
			"Observations (points 19 – 35)",
			"Appendix – items that need your decision or action",
		],
	)
	story += [
		S.h1("1. At a glance"),
		S.p("Every point of the tracker, the action taken and where it stands. The points to test are shaded."),
		glance_table(),
		spacer(3),
		callout(
			[
				"• The ERP changes are available once Acube has updated the ERP. Press Ctrl+Shift+R once after the "
				"update so the browser loads the new screens.",
				"• Test with your own user. Some tests need the Accounts Manager role (rejecting) or Accounts User "
				"(preparing, editing).",
				"• Test on draft or test documents where possible: approving submits a document to the ledger, and "
				"rejecting a submitted one cancels it.",
				"• Record each result in the box at the end of the section, and send any issue with the point number, "
				"the document number and a screenshot.",
			],
			"warn",
			title="Before you start",
		),
		PageBreak(),
		S.h1("2. Reports (points 1 – 18)"),
	]
	story += points_1_2()
	story += points_3_to_5()
	story += points_6_to_9()
	story += points_10_11()
	story += points_12_to_18()
	story += [PageBreak(), S.h1("3. Observations (points 19 – 35)"),
		S.p("Sl 21 and 22 are not used in the tracker.")]
	story += points_19_to_25()
	story += points_26_27()
	story += points_28_to_35()
	story += appendix()

	doc.build(story)
	shutil.copyfile(OUT, COPY)
	print("written", OUT)
	print("copied ", COPY)


if __name__ == "__main__":
	prepare_screenshots(sys.argv[1] if len(sys.argv) > 1 else None)
	build()
