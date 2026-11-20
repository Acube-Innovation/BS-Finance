"""Cost Center chosen on every expense and income line (BrahMos Reports & Observations Tracker point 26).

"Main - BATL" is the Cost Center ERPNext created with the company and keeps as the company's Default Cost Center;
every line without a Cost Center of its own is given it (item defaults, then the company default), so expenses have
been booked to it instead of to the departments. Here a line that posts to an income or expense (Profit and Loss)
account must carry a Cost Center, and not the company default: the user chooses the department.

The company default itself stays in the Company master. ERPNext uses it for the entries it makes on its own - exchange
gain / loss and revaluation journals, payment reconciliation and advance adjustment journals, TDS rows, the cost
center of a Payment Entry with none - and some of those fail without it (a Profit and Loss line needs a Cost
Center). So it is only kept off the lines users enter:

	Purchase Invoice       items posting to an expense account (services, non-stock items; a stock item against a
	                       GRN posts to Stock Received But Not Billed and is not checked)
	Sales Invoice          items posting to an income account
	Journal Entry          lines on income / expense accounts (not the system journals: exchange gain or loss,
	                       revaluation, depreciation, deferred entries)
	Payment Entry          deductions / write-off lines on income / expense accounts (not exchange gain / loss)
	Stock Entry            Material Issue and Material Receipt lines (consumption and receipts charged to a
	                       department); transfers carry only rounding differences (see stock_entry_transfer.py)
	Expense Claim          expense lines
	Purchase Order,        warned, not stopped: budgets are checked on them by Cost Center, but they are also made
	Material Request       from Indents automatically

Only the document a user saves, submits or moves through its workflow from the form is checked: documents made by
the system or by other documents (payroll and petty labour journals, ION journals, imports, background jobs) are
not, and returns made against an earlier document keep that document's Cost Center. Documents already submitted
are not touched; a draft is checked when it is next saved or submitted.
"""

import frappe
from frappe import _

# doctype: (child table or None for the document itself, account field, how: "stop" or "warn")
CHECKS = {
	"Purchase Invoice": [("items", "expense_account", "stop")],
	"Sales Invoice": [("items", "income_account", "stop")],
	"Journal Entry": [("accounts", "account", "stop")],
	"Payment Entry": [("deductions", "account", "stop")],
	"Stock Entry": [("items", "expense_account", "stop")],
	"Expense Claim": [("expenses", "default_account", "stop")],
	"Purchase Order": [("items", "expense_account", "warn")],
	"Material Request": [("items", "expense_account", "warn")],
}
STOCK_ENTRY_PURPOSES = ("Material Issue", "Material Receipt")
SYSTEM_JOURNAL_TYPES = (
	"Exchange Gain Or Loss",
	"Exchange Rate Revaluation",
	"Depreciation Entry",
	"Deferred Revenue",
	"Deferred Expense",
	"Asset Disposal",
)


# requests by which a user saves / submits a document, or takes a workflow action on it, from the form
USER_ENTRY_METHODS = (
	"frappe.desk.form.save.savedocs",
	"frappe.model.workflow.apply_workflow",
	"frappe.client.save",
	"frappe.client.submit",
	"frappe.client.insert",
)


def validate_cost_center(doc, method=None):
	if doc.flags.ignore_cost_center_check or not is_user_entry(doc) or not is_checked(doc):
		return
	default = frappe.get_cached_value("Company", doc.company, "cost_center")
	for table, account_field, how in CHECKS.get(doc.doctype, ()):
		problems = []
		for row in doc.get(table) or []:
			if row.get("is_exchange_gain_loss") or not is_profit_and_loss(row.get(account_field)):
				continue
			cost_center = row.get("cost_center") or doc.get("cost_center")
			if not cost_center:
				problems.append(
					_("Row {0}: select the Cost Center for {1}").format(row.idx, row.get(account_field))
				)
			elif default and cost_center == default:
				problems.append(
					_(
						"Row {0}: {1} is the company's default Cost Center; select the department's Cost Center for {2}"
					).format(row.idx, frappe.bold(default), row.get(account_field))
				)
		if not problems:
			continue
		message = "<br>".join(problems)
		if how == "stop":
			frappe.throw(message, title=_("Cost Center required"))
		else:
			frappe.msgprint(
				message + "<br><br>" + _("Budgets are checked by Cost Center."),
				title=_("Cost Center to be selected"),
				indicator="orange",
			)


def is_user_entry(doc):
	"""Whether doc is the document of the current form request (not one made by it or by a job)."""
	if getattr(frappe.local, "request", None) is None or frappe.flags.in_import or frappe.flags.in_patch:
		return False
	if frappe.form_dict.get("cmd") not in USER_ENTRY_METHODS:
		return False
	sent = frappe.form_dict.get("doc")
	if isinstance(sent, str):
		try:
			sent = frappe.parse_json(sent)
		except Exception:
			return False
	if not isinstance(sent, dict) or sent.get("doctype") != doc.doctype:
		return False
	return sent.get("name") == doc.name or bool(sent.get("__islocal"))


def is_checked(doc):
	if doc.get("is_return") and (doc.get("return_against") or doc.get("against_stock_entry")):
		return False
	if doc.doctype == "Journal Entry":
		return (
			not doc.get("is_system_generated")
			and doc.get("voucher_type") not in SYSTEM_JOURNAL_TYPES
			and (doc.get("is_opening") != "Yes")
		)
	if doc.doctype == "Stock Entry":
		return doc.get("purpose") in STOCK_ENTRY_PURPOSES
	return True


def is_profit_and_loss(account):
	return bool(account) and frappe.get_cached_value("Account", account, "report_type") == "Profit and Loss"
