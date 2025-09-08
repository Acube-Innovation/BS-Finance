# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [ 
		{"label":"Sl No", "fieldname": "sl_no", "fieldtype": "Int", "width": 50},
		{"label":"EC", "fieldname": "ec", "fieldtype": "Data", "width": 120},
		{"label":"Employee Name", "fieldname": "employee_name", "fieldtype" : "Data", "width": 200},
		{"label":"PAN", "fieldname": "pan", "fieldtype": "Data", "width": 120},
		{"label":"Gross Salary", "fieldname":"gross_salary", "fieldtype": "Currency", "width": 120},
		{"label":"Standard Deduction", "fieldname":"standard_deduction", "fieldtype": "Currency", "width": 150},
		{"label":"Final Taxable Income", "fieldname":"final_taxable_income", "fieldtype": "Currency", "width": 150},
		{"label":"Tax(NEW)", "fieldname":"tax_new", "fieldtype": "Currency", "width": 120},
		{"label":"Marginal Relief", "fieldname":"marginal_relief", "fieldtype": "Currency", "width": 120},
		{"label":"Cess", "fieldname":"cess", "fieldtype": "Currency", "width": 120},
		{"label":"Final Income Tax", "fieldname":"final_income_tax", "fieldtype": "Currency", "width": 150},
		{"label":"TDS", "fieldname":"tds", "fieldtype": "Currency", "width": 120},
		{"label":"Tax Deducted", "fieldname":"tax_deducted", "fieldtype": "Currency", "width": 120},
		{"label":"Balance Tax", "fieldname":"balance_tax", "fieldtype": "Currency", "width": 120},
	]

def get_data(filters):
	# frappe.throw(str(filters))
	month = int(filters.get("month"))
	year = int(filters.get("year"))

	data = []
	sl_no = 1

	# get all employees
	employees = frappe.get_all(
		"Employee",
		filters={"status": ["in", ["Active", "Suspended"]]},
		fields=["name", "employee_name", "employee_number", "pan_number"]
	)

	for emp in employees:
		# find salary slip for this employee in the given month
		salary_slip = frappe.db.sql(
			"""
			SELECT name, custom_current_net_total_earnings, custom_current_total_tax_paid, custom_income_tax, custom_std_deduction,custom_deputation_allowance,custom_tax,custom_marginal_relief,custom_cess
			FROM `tabSalary Slip`
			WHERE employee = %s AND start_date >= %s AND end_date <= %s AND docstatus = 1
			LIMIT 1
			""",
			(emp.name, f"{year}-{month}-01", f"{year}-{month}-31"),
			as_dict=True,
		)

		if salary_slip and salary_slip[0].custom_income_tax:

			row = {
				"sl_no": sl_no,
				"ec": emp.employee_number or 0,
				"employee_name": emp.employee_name,
				"pan": emp.pan_number,
				"gross_salary": salary_slip[0].custom_current_net_total_earnings,
				"standard_deduction": salary_slip[0].custom_std_deduction or 0,
				"final_taxable_income": (salary_slip[0].custom_current_net_total_earnings - salary_slip[0].custom_std_deduction) or 0,
				"tax_new": salary_slip[0].custom_tax,
				"marginal_relief": salary_slip[0].custom_marginal_relief or 0,
				"cess": salary_slip[0].custom_cess or 0,
				"final_income_tax": salary_slip[0].custom_deputation_allowance or 0,
				"tds": salary_slip[0].custom_income_tax or 0,
				"tax_deducted":(salary_slip[0].custom_current_total_tax_paid + salary_slip[0].custom_income_tax )or 0,
				"balance_tax": (salary_slip[0].custom_deputation_allowance - (salary_slip[0].custom_current_total_tax_paid + salary_slip[0].custom_income_tax)) or 0,
			}
			sl_no+=1
			data.append(row)
	return data