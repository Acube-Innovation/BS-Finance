# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_first_day, get_last_day


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Sl No", "fieldname": "sl_no", "fieldtype": "Int", "width": 50},
		{"label": "Employee Number", "fieldname": "employee_number", "fieldtype": "Data", "width": 120},
		{"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
		{"label": "Subscription Amount", "fieldname": "subscription_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Recovered Amount", "fieldname": "recovered_amount", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	month = int(filters.get("month"))
	year = int(filters.get("year"))
	start_date = get_first_day(f"{year}-{month}-01")
	end_date = get_last_day(f"{year}-{month}-01")

	employees = frappe.get_all(
    "Employee",
    filters={
        "custom_has_recreation_club_contribution": 1,
        "status": ["in", ["Active", "Suspended"]],
    },
    fields=["name", "employee_name", "employee_number", "custom_bebf_no"]
)

	data = []
	sl_no = 1
	total_subscription = 0
	total_recovered = 0

	for emp in employees:
		subscription_amount = 0
		recovered_amount = 0

		# Find salary slip in that period
		slip = frappe.db.sql(
			"""
			SELECT name, custom_brahmos_recreation_club_contribution
			FROM `tabSalary Slip`
			WHERE employee = %s
			  AND start_date >= %s
			  AND end_date <= %s
			  AND docstatus = 1
			""",
			(emp.name, start_date, end_date),
			as_dict=1,
		)

		if slip:
			subscription_amount = slip[0].custom_brahmos_recreation_club_contribution or 0

			recovered = frappe.db.sql(
				"""
				SELECT amount
				FROM `tabSalary Detail`
				WHERE parent = %s
				  AND parentfield = 'deductions'
				  AND salary_component = 'Brahmos Recreation Club Contribution'
				LIMIT 1
				""",
				(slip[0].name,),
				as_list=1,
			)

			if recovered:
				recovered_amount = recovered[0][0] or 0

		# Add totals
		total_subscription += subscription_amount
		total_recovered += recovered_amount

		# Always append, even if 0
		data.append({
			"sl_no": sl_no,
			"employee_number": emp.employee_number or emp.name,
			"employee_name": emp.employee_name,
			"subscription_amount": subscription_amount,
			"recovered_amount": recovered_amount,
		})
		sl_no += 1

	# Add TOTAL row
	data.append({
		"sl_no": "",
		"employee_number": "",
		"employee_name": "TOTAL",
		"subscription_amount": total_subscription,
		"recovered_amount": total_recovered,
	})

	return data
