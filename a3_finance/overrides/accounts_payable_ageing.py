"""Accounts Payable and Accounts Payable Summary: "GRN Date" in Ageing Based On.

A Purchase Invoice (also a debit note shown on its own) is aged from the posting date of its GRN - the Purchase
Receipt its items were received on; the latest one when they come from several - and from its own posting date when
it has none. Payments, journals and advances are aged from their posting date, as with "Posting Date". The other
options (Posting Date, Due Date, Supplier Invoice Date) work exactly as in ERPNext, and the buckets follow the
report's Ageing Range.

ERPNext picks the ageing date in ReceivablePayableReport.set_ageing (accounts_receivable.py), which the Accounts
Payable Summary also runs (AccountsReceivableSummary.get_data). apply() wraps that method once per process; it is
called by the before_request and before_job hooks, so it is in place for the reports and for prepared reports and
background exports. The "GRN Date" option is added to the filter by public/js/accounts_payable_ageing.js.
"""

import frappe
from frappe.query_builder.functions import Max
from frappe.utils import getdate

GRN_DATE = "GRN Date"


_unavailable = False


def apply():
	"""Wrap ReceivablePayableReport.set_ageing (once) so that "GRN Date" is understood. Should an ERPNext update
	rename it, the reports work as in ERPNext (GRN Date ages as Posting Date) and the error is logged once."""
	global _unavailable
	if _unavailable:
		return
	try:
		from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport

		original = ReceivablePayableReport.set_ageing
	except (ImportError, AttributeError):
		_unavailable = True
		frappe.log_error(title="Accounts Payable GRN Date ageing not applied (ERPNext changed set_ageing)")
		return
	if getattr(original, "a3_grn_date", False):
		return

	def set_ageing(self, row):
		if self.filters.get("ageing_based_on") == GRN_DATE:
			set_grn_ageing(self, row)
		else:
			original(self, row)

	set_ageing.a3_grn_date = True
	set_ageing.__wrapped__ = original
	ReceivablePayableReport.set_ageing = set_ageing


def set_grn_ageing(report, row):
	"""ERPNext's set_ageing with the GRN date (else the posting date) as the date the row is aged from."""
	entry_date = get_grn_date(report, row) or row.posting_date
	report.get_ageing_data(entry_date, row)

	# no amount in the buckets while the date is after the ageing date (as ERPNext does for a later due date)
	if entry_date and report.age_as_on and getdate(entry_date) > getdate(report.age_as_on):
		for i in report.range_numbers:
			row[f"range{i}"] = 0.0

	row.total_due = sum(row[f"range{i}"] for i in report.range_numbers)


def get_grn_date(report, row):
	"""The GRN date of a Purchase Invoice row; None for other rows and invoices without a GRN."""
	if row.get("voucher_type") != "Purchase Invoice":
		return None
	grn_dates = getattr(report, "a3_grn_dates", None)
	if grn_dates is None:
		# all the invoices of the report at once, on the first row
		invoices = {
			balance.voucher_no
			for balance in report.voucher_balance.values()
			if balance.get("voucher_type") == "Purchase Invoice"
		}
		grn_dates = report.a3_grn_dates = get_grn_dates(invoices)
	return grn_dates.get(row.voucher_no)


def get_grn_dates(invoices):
	"""{Purchase Invoice: posting date of its latest submitted Purchase Receipt} for the invoices that have one."""
	invoices = list(invoices)
	if not invoices:
		return {}
	item = frappe.qb.DocType("Purchase Invoice Item")
	receipt = frappe.qb.DocType("Purchase Receipt")
	grn_dates = {}
	for start in range(0, len(invoices), 1000):
		rows = (
			frappe.qb.from_(item)
			.join(receipt)
			.on(receipt.name == item.purchase_receipt)
			.select(item.parent, Max(receipt.posting_date))
			.where(item.parent.isin(invoices[start : start + 1000]) & (receipt.docstatus == 1))
			.groupby(item.parent)
		).run()
		grn_dates.update(rows)
	return grn_dates
