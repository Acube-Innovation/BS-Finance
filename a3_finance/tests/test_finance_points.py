# Copyright (c) 2026, Acube and Contributors
# See license.txt
"""BrahMos Reports & Observations Tracker: report export (points 4, 5), Trial Balance in bold (27) and the Purchase
Invoice / Payment Entry / Journal Entry workflows (10, 11).

bench --site batl run-tests --module a3_finance.tests.test_finance_points

Runs on the site's own data (a test is skipped when there is none); everything it changes is rolled back.
"""

import json
from io import BytesIO

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
WORKFLOW_DOCTYPES = ("Purchase Invoice", "Payment Entry", "Journal Entry")
RETURNED = "Returned for Correction"


def company():
	return frappe.defaults.get_global_default("company") or frappe.get_all("Company", pluck="name")[0]


def export(report, filters, file_format="Excel", visible_idx=None, include_indentation=0):
	from a3_finance.overrides.report_export import export_query

	frappe.local.response = frappe._dict()
	frappe.local.form_dict = frappe._dict(
		report_name=report,
		custom_columns="[]",
		file_format_type=file_format,
		filters=json.dumps(filters),
		applied_filters=json.dumps({"Company": filters.get("company")}),
		visible_idx=json.dumps(visible_idx or []),
		csv_delimiter=",",
		csv_quoting="2",
		include_indentation=include_indentation,
		include_filters=0,
		export_in_background=0,
	)
	export_query()
	return frappe.local.response


def sheet_of(response):
	from openpyxl import load_workbook

	return load_workbook(BytesIO(response.filecontent)).active


def ageing_filters(party_type, **extra):
	return {
		"company": company(),
		"report_date": today(),
		"ageing_based_on": "Posting Date",
		"calculate_ageing_with": "Report Date",
		"range": "30, 60, 90, 120",
		"party_type": party_type,
		**extra,
	}


class TestExportPermission(FrappeTestCase):
	"""Points 3-5: the Accounts and Stock roles may export the ageing reports (Export on the reference doctype)."""

	def user_with(self, role, without="System Manager"):
		return frappe.db.sql(
			"""
			select u.name from tabUser u
			where u.enabled = 1 and u.user_type = 'System User'
				and exists (select 1 from `tabHas Role` r where r.parent = u.name and r.role = %s)
				and not exists (select 1 from `tabHas Role` r where r.parent = u.name and r.role = %s)
			limit 1
			""",
			(role, without),
		)

	def test_roles_can_export(self):
		for role, doctypes in {
			"Accounts User": ("Sales Invoice", "Purchase Invoice", "Item"),
			"Stock User": ("Item",),
		}.items():
			user = self.user_with(role)
			if not user:
				continue
			frappe.set_user(user[0][0])
			try:
				for doctype in doctypes:
					self.assertTrue(
						frappe.permissions.can_export(doctype), f"{role} ({user[0][0]}): {doctype}"
					)
			finally:
				frappe.set_user("Administrator")


class TestAgeingExports(FrappeTestCase):
	"""Points 4 and 5: Accounts Receivable (and Summary, with and without Group by Customer) and Stock Ageing
	export as a typed .xlsx download."""

	def assert_xlsx(self, response, amount_label):
		self.assertEqual(response.type, "download")
		self.assertEqual(response.display_content_as, "attachment")
		self.assertEqual(response.content_type, XLSX)
		self.assertTrue(response.filename.endswith(".xlsx") and response.filename.isascii())
		sheet = sheet_of(response)
		header = [c.value for c in sheet[1]]
		self.assertIn(amount_label, header)
		self.assertEqual(sheet.freeze_panes, "A2")
		column = header.index(amount_label) + 1
		values = [sheet.cell(r, column) for r in range(2, sheet.max_row + 1)]
		numbers = [c for c in values if c.value not in (None, "")]
		for cell in numbers[:50]:
			self.assertIsInstance(cell.value, int | float)
			self.assertEqual(cell.number_format, "#,##0.00")
		return sheet

	def test_accounts_receivable(self):
		for report in ("Accounts Receivable", "Accounts Receivable Summary"):
			for group_by in (0, 1):
				filters = ageing_filters("Customer")
				if report == "Accounts Receivable":
					filters["group_by_party"] = group_by
				elif group_by:
					continue
				response = export(report, filters)
				self.assert_xlsx(response, "Outstanding Amount")

	def test_stock_ageing(self):
		# a prepared report: run directly here (the user's export reads the prepared result of the same filters)
		frappe.db.set_value("Report", "Stock Ageing", "prepared_report", 0)
		item = frappe.db.get_value("Bin", {"actual_qty": (">", 0)}, "item_code")
		if not item:
			self.skipTest("no stock")
		filters = {"company": company(), "to_date": today(), "range": "30, 60, 90", "item_code": item}
		sheet = self.assert_xlsx(export("Stock Ageing", filters), "Available Qty")
		header = [c.value for c in sheet[1]]
		self.assertIn("Average Age", header)
		# the ageing buckets: quantity and value per range, as numbers
		self.assertIn("Value (0 - 30)", header)
		column = header.index("Value (0 - 30)") + 1
		for r in range(2, sheet.max_row + 1):
			cell = sheet.cell(r, column)
			if cell.value not in (None, ""):
				self.assertIsInstance(cell.value, int | float)
				self.assertEqual(cell.number_format, "#,##0.00")


class TestTrialBalanceExport(FrappeTestCase):
	"""Point 27: group accounts bold in the Trial Balance export, ledgers not."""

	def test_group_rows_bold(self):
		fiscal_year = frappe.db.get_value(
			"Fiscal Year",
			{"year_start_date": ("<=", today()), "year_end_date": (">=", today())},
			["name", "year_start_date", "year_end_date"],
			as_dict=True,
		)
		if not fiscal_year:
			self.skipTest("no fiscal year")
		filters = {
			"company": company(),
			"fiscal_year": fiscal_year.name,
			"from_date": str(fiscal_year.year_start_date),
			"to_date": str(fiscal_year.year_end_date),
			"with_period_closing_entry_for_opening": 1,
			"with_period_closing_entry_for_current_period": 1,
			"include_default_book_entries": 1,
			"show_net_values": 1,
		}
		response = export("Trial Balance", filters)
		self.assertEqual(response.content_type, XLSX)
		sheet = sheet_of(response)
		groups = set(frappe.get_all("Account", filters={"company": company(), "is_group": 1}, pluck="name"))
		checked_group = checked_ledger = False
		for row in sheet.iter_rows(min_row=2):
			account = row[0].value
			if not account or account == "'Total'":
				continue
			if account in groups:
				self.assertTrue(row[0].font.b, account)
				checked_group = True
			elif frappe.db.exists("Account", account):
				self.assertFalse(row[0].font.b, account)
				checked_ledger = True
		self.assertTrue(checked_group and checked_ledger)


class TestWorkflowReject(FrappeTestCase):
	"""Points 10 and 11: a draft can be rejected (Returned for Correction), approved again, rejected after approval
	(Rejected, cancelled) and amended (back to Prepared By, with Save for the Accounts User)."""

	def run_flow(self, doctype):
		from frappe.model.workflow import apply_workflow, get_transitions

		approver = frappe.db.sql(
			"""select u.name from tabUser u where u.enabled = 1
			and exists (select 1 from `tabHas Role` r where r.parent = u.name and r.role = 'Accounts Manager')
			and exists (select 1 from `tabHas Role` r where r.parent = u.name and r.role = 'Accounts User')
			limit 1"""
		)
		self.assertTrue(approver, "no user with Accounts Manager and Accounts User")
		drafts = frappe.get_all(
			doctype,
			filters={"docstatus": 0, "workflow_state": "Prepared By"},
			order_by="modified desc",
			pluck="name",
			limit=40,
		)
		for name in drafts:
			frappe.db.savepoint("flow")
			frappe.set_user(approver[0][0])
			try:
				doc = frappe.get_doc(doctype, name)
				self.assertIn("Reject", [t.action for t in get_transitions(doc)])
				doc = apply_workflow(doc.as_json(), "Reject")
				self.assertEqual((doc.workflow_state, doc.docstatus), (RETURNED, 0))
				try:
					doc = apply_workflow(doc.as_json(), "Approve")
				except frappe.ValidationError:
					continue  # this draft does not pass the doctype's own checks: try the next one
				self.assertEqual((doc.workflow_state, doc.docstatus), ("Checked By", 1))
				doc = apply_workflow(doc.as_json(), "Reject")
				self.assertEqual((doc.workflow_state, doc.docstatus), ("Rejected", 2))
				amended = frappe.copy_doc(doc)
				amended.amended_from = doc.name
				amended.insert()
				self.assertEqual((amended.workflow_state, amended.docstatus), ("Prepared By", 0))
				return
			finally:
				frappe.set_user("Administrator")
				frappe.db.rollback(save_point="flow")
		self.skipTest(f"no {doctype} draft that can be submitted")

	def test_purchase_invoice(self):
		self.run_flow("Purchase Invoice")

	def test_payment_entry(self):
		self.run_flow("Payment Entry")

	def test_journal_entry(self):
		self.run_flow("Journal Entry")

	def test_reject_offered_only_where_it_can_run(self):
		from frappe.model.workflow import get_transitions

		for doctype in WORKFLOW_DOCTYPES:
			# a submitted document left in Prepared By (opening entries): rejecting would turn it back into a draft
			name = frappe.db.get_value(doctype, {"docstatus": 1, "workflow_state": "Prepared By"})
			if name:
				actions = [t.action for t in get_transitions(frappe.get_doc(doctype, name))]
				self.assertNotIn("Reject", actions, f"{doctype} {name}")
			# a draft left in Checked By: rejecting would cancel a draft ("Illegal Document Status")
			name = frappe.db.get_value(doctype, {"docstatus": 0, "workflow_state": "Checked By"})
			if name:
				actions = [t.action for t in get_transitions(frappe.get_doc(doctype, name))]
				self.assertNotIn("Reject", actions, f"{doctype} {name}")


class TestCostCenterRule(FrappeTestCase):
	"""Point 26: income / expense lines a user enters need a department Cost Center, not the company default; the
	system's own documents are not checked."""

	def setUp(self):
		self.default = frappe.get_cached_value("Company", company(), "cost_center")
		self.expense = frappe.db.get_value(
			"Account", {"company": company(), "root_type": "Expense", "is_group": 0, "disabled": 0}
		)
		self.bank = frappe.db.get_value(
			"Account", {"company": company(), "account_type": "Bank", "is_group": 0, "disabled": 0}
		)
		self.department = frappe.db.get_value(
			"Cost Center", {"company": company(), "is_group": 0, "name": ("!=", self.default), "disabled": 0}
		)
		if not (self.default and self.expense and self.bank and self.department):
			self.skipTest("accounts / cost centers missing")
		self.saved_request = getattr(frappe.local, "request", None)
		self.saved_form = frappe.local.form_dict

	def tearDown(self):
		frappe.local.request = self.saved_request
		frappe.local.form_dict = self.saved_form

	def journal(self, cost_center):
		doc = frappe.new_doc("Journal Entry")
		doc.company = company()
		doc.posting_date = today()
		doc.append(
			"accounts",
			{"account": self.expense, "debit_in_account_currency": 100, "cost_center": cost_center},
		)
		doc.append("accounts", {"account": self.bank, "credit_in_account_currency": 100})
		return doc

	def as_form_save(self, doc):
		frappe.local.request = frappe._dict()
		frappe.local.form_dict = frappe._dict(
			cmd="frappe.desk.form.save.savedocs",
			doc=json.dumps({**json.loads(doc.as_json()), "__islocal": 1}),
			action="Save",
		)

	def test_company_default_refused_on_user_entry(self):
		from a3_finance.overrides.cost_center_mandatory import validate_cost_center

		doc = self.journal(self.default)
		self.as_form_save(doc)
		with self.assertRaises(frappe.ValidationError):
			validate_cost_center(doc)

		doc = self.journal(None)
		self.as_form_save(doc)
		with self.assertRaises(frappe.ValidationError):
			validate_cost_center(doc)

		doc = self.journal(self.department)
		self.as_form_save(doc)
		validate_cost_center(doc)  # a department: accepted

	def test_system_documents_not_checked(self):
		from a3_finance.overrides.cost_center_mandatory import validate_cost_center

		# made by code (no form request): not checked
		frappe.local.request = None
		validate_cost_center(self.journal(self.default))
		# exchange gain / loss journal: not checked even from a form
		doc = self.journal(self.default)
		doc.voucher_type = "Exchange Gain Or Loss"
		self.as_form_save(doc)
		validate_cost_center(doc)
		# a different document than the one the form saves: not checked
		doc = self.journal(self.default)
		frappe.local.request = frappe._dict()
		frappe.local.form_dict = frappe._dict(
			cmd="frappe.desk.form.save.savedocs",
			doc=json.dumps({"doctype": "Petty Labour Payment", "name": "x"}),
		)
		validate_cost_center(doc)


class TestTransferDifferenceAccount(FrappeTestCase):
	"""Points 33 and 34: transfer rows post their rounding difference to Stock Adjustment."""

	def test_transfer_rows(self):
		from a3_finance.overrides.stock_entry_transfer import set_transfer_difference_account

		adjustment = frappe.get_cached_value("Company", company(), "stock_adjustment_account")
		if not adjustment:
			self.skipTest("no Stock Adjustment Account")
		doc = (
			frappe.get_doc("Stock Entry", "MAT-STE-01139")
			if frappe.db.exists("Stock Entry", "MAT-STE-01139")
			else None
		)
		if not doc:
			self.skipTest("MAT-STE-01139 not on this site")
		doc = frappe.copy_doc(doc)  # not saved
		self.assertNotEqual(doc.items[0].expense_account, adjustment)
		set_transfer_difference_account(doc)
		self.assertEqual(doc.items[0].expense_account, adjustment)

		doc.purpose = doc.stock_entry_type = "Material Issue"
		doc.items[0].expense_account = "x"
		set_transfer_difference_account(doc)
		self.assertEqual(doc.items[0].expense_account, "x")  # issues keep their consumption account

	def test_rate_shown_to_four_decimals(self):
		self.assertEqual(frappe.get_meta("Stock Entry Detail").get_field("basic_rate").precision, "4")


class TestColumnWidths(FrappeTestCase):
	"""Amount columns wide enough for their largest number (no ### in Excel)."""

	def test_amounts_fit(self):
		from openpyxl.utils import get_column_letter

		from a3_finance.overrides.report_export import make_xlsx

		columns = [{"fieldtype": "Data"}, {"fieldtype": "Currency"}]
		table = [["Account", "Opening (Dr)"], ["Bank", 252634524.66], ["Cash", 3758.0]]
		content = make_xlsx("Test", table, columns, [30, 12], bold_rows={0})
		from openpyxl import load_workbook

		sheet = load_workbook(BytesIO(content)).active
		width = sheet.column_dimensions[get_column_letter(2)].width
		self.assertGreaterEqual(width, len("252,634,524.66") + 2)
