# Copyright (c) 2026, Acube and Contributors
# See license.txt
"""Accounts Payable "GRN Date" ageing and the report Excel export.

bench --site batl run-tests --module a3_finance.tests.test_accounts_payable_ageing

Runs on the site's own submitted invoices and receipts (skipped when there are none); what it changes is rolled back.
"""

import json
from io import BytesIO

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, today

from a3_finance.overrides.accounts_payable_ageing import GRN_DATE, apply, get_grn_dates


def run_report(report, **filters):
	from erpnext.accounts.report.accounts_payable.accounts_payable import execute as ap
	from erpnext.accounts.report.accounts_payable_summary.accounts_payable_summary import execute as aps

	report_filters = frappe._dict(
		company=frappe.defaults.get_global_default("company") or frappe.get_all("Company", pluck="name")[0],
		report_date=today(),
		ageing_based_on="Due Date",
		calculate_ageing_with="Report Date",
		range="30, 60, 90, 120",
		party_type="Supplier",
	)
	report_filters.update(filters)
	return (ap if report == "Accounts Payable" else aps)(report_filters)[1]


def invoice_rows(rows):
	return {
		r.voucher_no: r for r in rows if isinstance(r, dict) and r.get("voucher_type") == "Purchase Invoice"
	}


class TestAccountsPayableGRNAgeing(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		apply()
		# an unpaid invoice whose GRN is dated before it, and an unpaid invoice without a GRN
		cls.with_grn = frappe.db.sql(
			"""
			select pi.name, pi.posting_date, max(pr.posting_date) as grn_date
			from `tabPurchase Invoice` pi
			join `tabPurchase Invoice Item` item on item.parent = pi.name
			join `tabPurchase Receipt` pr on pr.name = item.purchase_receipt and pr.docstatus = 1
			where pi.docstatus = 1 and pi.is_return = 0 and pi.outstanding_amount > 0
			group by pi.name
			having grn_date < pi.posting_date
			order by pi.posting_date desc limit 1
			""",
			as_dict=True,
		)
		cls.without_grn = frappe.db.sql(
			"""
			select pi.name, pi.posting_date from `tabPurchase Invoice` pi
			where pi.docstatus = 1 and pi.is_return = 0 and pi.outstanding_amount > 0
				and not exists (select 1 from `tabPurchase Invoice Item` item
					where item.parent = pi.name and ifnull(item.purchase_receipt, '') != '')
			order by pi.posting_date desc limit 1
			""",
			as_dict=True,
		)

	def setUp(self):
		if not self.with_grn or not self.without_grn:
			self.skipTest("needs an unpaid invoice with a GRN and one without")

	def test_single_grn(self):
		invoice = self.with_grn[0]
		self.assertEqual(get_grn_dates([invoice.name]), {invoice.name: invoice.grn_date})

	def test_multiple_grns_take_the_latest(self):
		invoice = self.with_grn[0]
		later = frappe.db.sql(
			"""select name, posting_date from `tabPurchase Receipt` where docstatus = 1 and posting_date > %s
			order by posting_date desc limit 1""",
			invoice.grn_date,
			as_dict=True,
		)
		if not later:
			self.skipTest("needs a receipt dated after the invoice's GRN")
		# a second item received on a later GRN (rolled back at the end of the test)
		frappe.db.savepoint("multiple_grns")
		self.addCleanup(frappe.db.rollback, save_point="multiple_grns")
		item = frappe.get_all(
			"Purchase Invoice Item", filters={"parent": invoice.name}, fields=["*"], limit=1
		)[0]
		extra = frappe.get_doc(
			dict(item, doctype="Purchase Invoice Item", name=None, idx=999, purchase_receipt=later[0].name)
		)
		extra.db_insert()
		self.assertEqual(get_grn_dates([invoice.name])[invoice.name], later[0].posting_date)

	def test_no_grn_ages_from_posting_date(self):
		invoice = self.without_grn[0]
		self.assertEqual(get_grn_dates([invoice.name]), {})
		grn = invoice_rows(run_report("Accounts Payable", ageing_based_on=GRN_DATE))[invoice.name]
		posting = invoice_rows(run_report("Accounts Payable", ageing_based_on="Posting Date"))[invoice.name]
		self.assertEqual(grn.age, posting.age)

	def test_grn_row_ages_from_grn(self):
		invoice = self.with_grn[0]
		row = invoice_rows(run_report("Accounts Payable", ageing_based_on=GRN_DATE))[invoice.name]
		self.assertEqual(row.age, (getdate(today()) - getdate(invoice.grn_date)).days)
		self.assertEqual(row.posting_date, invoice.posting_date)  # the column itself is not changed
		buckets = sum(row[f"range{i}"] for i in range(1, 6))
		self.assertAlmostEqual(buckets, row.outstanding, places=2)
		self.assertAlmostEqual(row.total_due, row.outstanding, places=2)

	def test_other_options_unchanged(self):
		from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport

		wrapped = ReceivablePayableReport.set_ageing
		for option in ("Posting Date", "Due Date", "Supplier Invoice Date"):
			ours = run_report("Accounts Payable", ageing_based_on=option)
			ReceivablePayableReport.set_ageing = wrapped.__wrapped__
			try:
				erpnext = run_report("Accounts Payable", ageing_based_on=option)
			finally:
				ReceivablePayableReport.set_ageing = wrapped

			def key(r):
				return [
					r.get(f) for f in ("voucher_no", "age", "range1", "range2", "range3", "range4", "range5")
				]

			self.assertEqual([key(r) for r in ours], [key(r) for r in erpnext], option)

	def test_summary_matches_detail(self):
		detail = run_report("Accounts Payable", ageing_based_on=GRN_DATE)
		summary = run_report("Accounts Payable Summary", ageing_based_on=GRN_DATE)
		by_party = {}
		for r in detail:
			if isinstance(r, dict) and r.get("party"):
				totals = by_party.setdefault(r.party, [0.0] * 5)
				for i in range(5):
					totals[i] += r.get(f"range{i + 1}") or 0
		for r in summary:
			for i in range(5):
				self.assertAlmostEqual(
					r[f"range{i + 1}"], by_party.get(r.party, [0.0] * 5)[i], places=2, msg=r.party
				)

	def test_group_by_party_still_works(self):
		rows = run_report("Accounts Payable", ageing_based_on=GRN_DATE, group_by_party=1)
		self.assertTrue(any(isinstance(r, dict) and r.get("party") == "Total" for r in rows) or not rows)


class TestReportExport(FrappeTestCase):
	def export(self, report, file_format="Excel", **filters):
		from a3_finance.overrides.report_export import export_query

		apply()
		filters = {
			"company": frappe.defaults.get_global_default("company")
			or frappe.get_all("Company", pluck="name")[0],
			"report_date": today(),
			"ageing_based_on": GRN_DATE,
			"calculate_ageing_with": "Report Date",
			"range": "30, 60, 90, 120",
			"party_type": "Supplier",
			**filters,
		}
		frappe.local.response = frappe._dict()
		frappe.local.form_dict = frappe._dict(
			report_name=report,
			custom_columns="[]",
			file_format_type=file_format,
			filters=json.dumps(filters),
			applied_filters=json.dumps({"Company": filters["company"], "Party": ["M/S Test, Ltd", "Jäger"]}),
			visible_idx="[]",
			csv_delimiter=",",
			csv_quoting="2",
			include_indentation=0,
			include_filters=1,
			export_in_background=0,
		)
		export_query()
		return frappe.local.response

	def test_excel_download(self):
		from openpyxl import load_workbook

		for report in ("Accounts Payable", "Accounts Payable Summary"):
			response = self.export(report)
			self.assertEqual(response.type, "download")
			self.assertEqual(response.display_content_as, "attachment")
			self.assertEqual(
				response.content_type, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
			)
			self.assertTrue(response.filename.endswith(".xlsx"))
			self.assertTrue(response.filename.isascii())
			self.assertFalse(set(response.filename) & set(',/\\:*?"<>|'))

			sheet = load_workbook(BytesIO(response.filecontent)).active
			labels = [
				c.value
				for c in next(
					r for r in sheet.iter_rows() if r[0].value == "Party Type" or r[0].value == "Posting Date"
				)
			]
			self.assertIn("Outstanding Amount", labels)
			header_row = next(
				r[0].row for r in sheet.iter_rows() if r[0].value in ("Party Type", "Posting Date")
			)
			amount_col = labels.index("Outstanding Amount") + 1
			first = sheet.cell(header_row + 1, amount_col)
			if first.value is not None:
				self.assertIsInstance(first.value, int | float)
				self.assertEqual(first.number_format, "#,##0.00")

	def test_csv_and_other_reports_are_downloads_too(self):
		response = self.export("Accounts Payable", file_format="CSV")
		self.assertEqual(response.type, "download")
		self.assertTrue(response.content_type.startswith("text/csv"))
		self.assertTrue(response.filename.endswith(".csv"))
