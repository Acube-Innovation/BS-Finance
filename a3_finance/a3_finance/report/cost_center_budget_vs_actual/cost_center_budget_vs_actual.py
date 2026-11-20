# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt
"""Cost Center Budget vs Actual (BrahMos Reports & Observations Tracker point 26).

A tree: Cost Center → Account → (optionally) Voucher, with the annual budget, the budget up to the To Date (the
budget's monthly distribution, else twelfth parts - as ERPNext's budget check counts it), the actual amount booked in
the period, the variance, the share used and the balance of the annual budget. Every amount drills down: clicking it
opens the General Ledger for that cost center, account(s) and period; with "Show Vouchers" the vouchers are listed
under each account and open on click.

Budgets: submitted Budgets against Cost Center for the fiscal year. Actuals: General Ledger entries (not cancelled,
not opening) on income and expense accounts - expense as debit less credit, income as credit less debit. Accounts
without a budget are listed too (budget 0), unless "Budgeted accounts only" is ticked, so that spending booked
without a budget is seen.
"""

import frappe
from erpnext.accounts.doctype.budget.budget import get_accumulated_monthly_budget
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	cost_centers = get_cost_centers(filters)
	if not cost_centers:
		return get_columns(filters), []

	budgets = get_budgets(filters, cost_centers)
	actuals = get_actuals(filters, cost_centers)
	vouchers = get_vouchers(filters, cost_centers) if filters.show_vouchers else {}

	data = []
	grand = new_amounts()
	for cost_center in cost_centers:
		accounts = set(budgets.get(cost_center, {}))
		if not filters.budgeted_only:
			accounts |= set(actuals.get(cost_center, {}))
		if not accounts:
			continue
		cc_row = frappe._dict(
			label=cost_center, cost_center=cost_center, indent=0, is_group_row=1, accounts=[], **new_amounts()
		)
		data.append(cc_row)
		for account in sorted(accounts):
			budget = budgets.get(cost_center, {}).get(account, {})
			row = frappe._dict(
				label=account,
				cost_center=cost_center,
				account=account,
				parent_label=cost_center,
				indent=1,
				annual_budget=flt(budget.get("annual")),
				budget_to_date=flt(budget.get("to_date")),
				actual=flt(actuals.get(cost_center, {}).get(account)),
			)
			finish(row)
			data.append(row)
			cc_row.accounts.append(account)
			for field in AMOUNT_FIELDS:
				cc_row[field] += row[field]
			for voucher in vouchers.get((cost_center, account), []):
				data.append(
					frappe._dict(
						label=voucher.voucher_no,
						cost_center=cost_center,
						account=account,
						indent=2,
						posting_date=voucher.posting_date,
						voucher_type=voucher.voucher_type,
						voucher_no=voucher.voucher_no,
						party=voucher.party,
						remarks=voucher.remarks,
						actual=flt(voucher.amount),
					)
				)
		finish(cc_row)
		for field in AMOUNT_FIELDS:
			grand[field] += cc_row[field]

	if data:
		total = frappe._dict(label=_("Total"), indent=0, is_total_row=1, **grand)
		finish(total)
		data.append(total)

	return get_columns(filters), data, None, None, get_summary(grand)


AMOUNT_FIELDS = ("annual_budget", "budget_to_date", "actual")


def new_amounts():
	return {field: 0.0 for field in AMOUNT_FIELDS}


def finish(row):
	row.variance = flt(row.budget_to_date) - flt(row.actual)
	row.balance = flt(row.annual_budget) - flt(row.actual)
	row.utilised = flt(row.actual) / flt(row.budget_to_date) * 100 if flt(row.budget_to_date) else None


def validate_filters(filters):
	if not filters.company or not filters.fiscal_year:
		frappe.throw(_("Company and Fiscal Year are required"))
	year_start, year_end = frappe.get_cached_value(
		"Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"]
	)
	filters.from_date = getdate(filters.from_date or year_start)
	filters.to_date = getdate(filters.to_date or year_end)
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))
	if filters.from_date < getdate(year_start) or filters.to_date > getdate(year_end):
		frappe.throw(
			_("From Date and To Date must be within the Fiscal Year {0}").format(filters.fiscal_year)
		)
	filters.year_start = getdate(year_start)


def get_cost_centers(filters):
	"""Selected cost centers (a group selects the cost centers under it), else all of the company."""
	conditions = {"company": filters.company, "is_group": 0}
	selected = frappe.parse_json(filters.cost_center) if filters.cost_center else []
	if isinstance(selected, str):
		selected = [selected]
	if selected:
		names = set()
		for name in selected:
			lft, rgt = frappe.get_cached_value("Cost Center", name, ["lft", "rgt"])
			names.update(
				frappe.get_all(
					"Cost Center",
					filters={**conditions, "lft": (">=", lft), "rgt": ("<=", rgt)},
					pluck="name",
				)
			)
		return sorted(names)
	return frappe.get_all("Cost Center", filters=conditions, pluck="name", order_by="lft")


def account_condition(filters, alias):
	if not filters.account:
		return "", {}
	lft, rgt = frappe.get_cached_value("Account", filters.account, ["lft", "rgt"])
	return f" and {alias}.lft >= %(account_lft)s and {alias}.rgt <= %(account_rgt)s", {
		"account_lft": lft,
		"account_rgt": rgt,
	}


def get_budgets(filters, cost_centers):
	"""{cost center: {account: {"annual": amount, "to_date": amount}}}"""
	condition, values = account_condition(filters, "acc")
	rows = frappe.db.sql(
		f"""
		select b.cost_center, ba.account, ba.budget_amount, b.monthly_distribution
		from `tabBudget` b
		join `tabBudget Account` ba on ba.parent = b.name
		join `tabAccount` acc on acc.name = ba.account
		where b.docstatus = 1 and b.budget_against = 'Cost Center' and b.company = %(company)s
			and b.fiscal_year = %(fiscal_year)s and b.cost_center in %(cost_centers)s {condition}
		""",
		{
			"company": filters.company,
			"fiscal_year": filters.fiscal_year,
			"cost_centers": cost_centers,
			**values,
		},
		as_dict=True,
	)
	budgets = {}
	for row in rows:
		entry = budgets.setdefault(row.cost_center, {}).setdefault(
			row.account, {"annual": 0.0, "to_date": 0.0}
		)
		entry["annual"] += flt(row.budget_amount)
		entry["to_date"] += get_accumulated_monthly_budget(
			row.monthly_distribution, filters.to_date, filters.fiscal_year, flt(row.budget_amount)
		)
	return budgets


def gl_conditions(filters, cost_centers):
	condition, values = account_condition(filters, "acc")
	return (
		f"""
		gle.company = %(company)s and gle.is_cancelled = 0 and ifnull(gle.is_opening, 'No') = 'No'
		and gle.posting_date between %(from_date)s and %(to_date)s
		and gle.cost_center in %(cost_centers)s and acc.report_type = 'Profit and Loss' {condition}
		""",
		{
			"company": filters.company,
			"from_date": filters.from_date,
			"to_date": filters.to_date,
			"cost_centers": cost_centers,
			**values,
		},
	)


AMOUNT_SQL = "sum(if(acc.root_type = 'Income', gle.credit - gle.debit, gle.debit - gle.credit))"


def get_actuals(filters, cost_centers):
	"""{cost center: {account: amount}}"""
	where, values = gl_conditions(filters, cost_centers)
	rows = frappe.db.sql(
		f"""
		select gle.cost_center, gle.account, {AMOUNT_SQL} as amount
		from `tabGL Entry` gle join `tabAccount` acc on acc.name = gle.account
		where {where}
		group by gle.cost_center, gle.account
		""",
		values,
		as_dict=True,
	)
	actuals = {}
	for row in rows:
		actuals.setdefault(row.cost_center, {})[row.account] = flt(row.amount)
	return actuals


def get_vouchers(filters, cost_centers):
	"""{(cost center, account): [vouchers, by date]}"""
	where, values = gl_conditions(filters, cost_centers)
	rows = frappe.db.sql(
		f"""
		select gle.cost_center, gle.account, gle.voucher_type, gle.voucher_no,
			min(gle.posting_date) as posting_date, max(gle.party) as party, max(gle.remarks) as remarks,
			{AMOUNT_SQL} as amount
		from `tabGL Entry` gle join `tabAccount` acc on acc.name = gle.account
		where {where}
		group by gle.cost_center, gle.account, gle.voucher_type, gle.voucher_no
		order by posting_date, gle.voucher_no
		""",
		values,
		as_dict=True,
	)
	vouchers = {}
	for row in rows:
		if row.remarks and len(row.remarks) > 140:
			row.remarks = row.remarks[:137] + "..."
		vouchers.setdefault((row.cost_center, row.account), []).append(row)
	return vouchers


def get_columns(filters):
	columns = [
		{
			"label": _("Cost Center / Account / Voucher"),
			"fieldname": "label",
			"fieldtype": "Data",
			"width": 330,
		},
		{
			"label": _("Cost Center"),
			"fieldname": "cost_center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 150,
		},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 220,
		},
		{"label": _("Annual Budget"), "fieldname": "annual_budget", "fieldtype": "Currency", "width": 140},
		{"label": _("Budget to Date"), "fieldname": "budget_to_date", "fieldtype": "Currency", "width": 140},
		{"label": _("Actual"), "fieldname": "actual", "fieldtype": "Currency", "width": 140},
		{
			"label": _("Variance (Budget to Date - Actual)"),
			"fieldname": "variance",
			"fieldtype": "Currency",
			"width": 160,
		},
		{"label": _("Utilised %"), "fieldname": "utilised", "fieldtype": "Percent", "width": 100},
		{
			"label": _("Balance (Annual - Actual)"),
			"fieldname": "balance",
			"fieldtype": "Currency",
			"width": 150,
		},
	]
	if filters.show_vouchers:
		columns += [
			{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
			{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 130},
			{
				"label": _("Voucher No"),
				"fieldname": "voucher_no",
				"fieldtype": "Dynamic Link",
				"options": "voucher_type",
				"width": 170,
			},
			{"label": _("Party"), "fieldname": "party", "fieldtype": "Data", "width": 160},
			{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 220},
		]
	return columns


def get_summary(grand):
	if not any(grand.values()):
		return []
	balance = flt(grand["annual_budget"]) - flt(grand["actual"])
	return [
		{"value": grand["annual_budget"], "label": _("Annual Budget"), "datatype": "Currency"},
		{"value": grand["budget_to_date"], "label": _("Budget to Date"), "datatype": "Currency"},
		{
			"value": grand["actual"],
			"label": _("Actual"),
			"datatype": "Currency",
			"indicator": "Red" if grand["actual"] > grand["budget_to_date"] else "Green",
		},
		{
			"value": balance,
			"label": _("Balance of Annual Budget"),
			"datatype": "Currency",
			"indicator": "Red" if balance < 0 else "Blue",
		},
	]


@frappe.whitelist()
def get_cost_center_options(txt="", company=None):
	"""Cost centers of the company for the Cost Center filter (groups too: a group selects those under it)."""
	filters = {"disabled": 0}
	if company:
		filters["company"] = company
	if txt:
		filters["name"] = ("like", f"%{txt}%")
	return [
		{"value": name, "description": ""}
		for name in frappe.get_all("Cost Center", filters=filters, pluck="name", order_by="lft", limit=100)
	]
