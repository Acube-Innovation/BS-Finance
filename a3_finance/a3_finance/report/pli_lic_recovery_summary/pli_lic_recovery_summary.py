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
		{"label": "Policy Number", "fieldname": "policy_number", "fieldtype": "Data", "width": 120},
		{"label": "Premium", "fieldname": "premium", "fieldtype": "Currency", "width": 120},
		{"label": "Recovered", "fieldname": "recovered", "fieldtype": "Currency", "width": 120},
	]

def get_data(filters):
	month = int(filters.get("month"))
	year = int(filters.get("year"))
	comp_type = filters.get("type")   # "LIC Recovery" or "PLI Recovery"

	start_date = get_first_day(f"{year}-{month}-01")
	end_date = get_last_day(f"{year}-{month}-01")

	employees = frappe.get_all(
		"Employee",
		filters={"status": ["in", ["Active", "Suspended"]]},
		fields=["name", "employee_name", "employee_number"]
	)

	data = []
	sl_no = 1
	total_premium = 0
	total_recovered = 0

	for emp in employees:
		# Get salary slip
		slip = frappe.db.sql(
			"""
			SELECT name
			FROM `tabSalary Slip`
			WHERE employee = %s
			  AND start_date = %s
			  AND end_date = %s
			  AND docstatus = 1
			LIMIT 1
			""",
			(emp.name, start_date, end_date),
			as_dict=True,
		)

		if not slip:
			continue

		# Total recovered in slip
		recovered_row = frappe.db.sql(
			"""
			SELECT SUM(amount) as amt
			FROM `tabSalary Detail`
			WHERE parent = %s
			  AND parentfield = 'deductions'
			  AND salary_component = %s
			""",
			(slip[0].name, comp_type),
			as_dict=True,
		)

		recovered_total = recovered_row[0].amt if recovered_row and recovered_row[0].amt else 0

		# Get policies from child table
		policies = frappe.get_all(
			"Employee Policy Details",  # change to your actual child doctype
			filters={"parent": emp.name,"parentfield":"custom_policy_details", "status": "Active"},
			fields=["policy_number", "amount", "type"]
		)

		# Filter policies by type (LIC/PLI)
		policies = [p for p in policies if (p.type == "LIC" and comp_type == "LIC Recovery") or (p.type == "PLI" and comp_type == "PLI Recovery")]

		if not policies:
			continue

		# Total premium from child table
		child_total = sum(p.amount for p in policies)

		if recovered_total == 0:
			# None recovered, show 0
			for p in policies:
				data.append({
					"sl_no": sl_no,
					"employee_number": emp.employee_number,
					"employee_name": emp.employee_name,
					"policy_number": p.policy_number,
					"premium": p.amount,
					"recovered": 0,
				})
				sl_no += 1

		elif recovered_total == child_total:
			# All recovered
			for p in policies:
				data.append({
					"sl_no": sl_no,
					"employee_number": emp.employee_number,
					"employee_name": emp.employee_name,
					"policy_number": p.policy_number,
					"premium": p.amount,
					"recovered": p.amount,
				})
				sl_no += 1

		else:
			# Partial recovery → proportionally allocate
			for p in policies:
				share = round((p.amount / child_total) * recovered_total, 2) if child_total else 0
				data.append({
					"sl_no": sl_no,
					"employee_number": emp.employee_number,
					"employee_name": emp.employee_name,
					"policy_number": p.policy_number,
					"premium": p.amount,
					"recovered": share,
				})
				sl_no += 1

		total_premium += child_total
		total_recovered += recovered_total

	# Total row
	if data:
		data.append({
			"sl_no": "",
			"employee_number": "",
			"employee_name": "Total",
			"policy_number": "",
			"premium": total_premium,
			"recovered": total_recovered,
		})

	return data
