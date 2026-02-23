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
		{"label":"Gross Salary", "fieldname":"gross_salary", "fieldtype": "Float", "width": 120, "precision": 2},
		{"label":"Standard Deduction", "fieldname":"standard_deduction", "fieldtype": "Float", "width": 150, "precision": 2},
		{"label":"Final Taxable Income", "fieldname":"final_taxable_income", "fieldtype": "Float", "width": 150, "precision": 2},
		{"label":"Tax(NEW)", "fieldname":"tax_new", "fieldtype": "Float", "width": 120, "precision": 2},
		{"label":"Marginal Relief", "fieldname":"marginal_relief", "fieldtype": "Float", "width": 120, "precision": 2},
		{"label":"Cess", "fieldname":"cess", "fieldtype": "Float", "width": 120, "precision": 2},
		{"label":"Final Income Tax", "fieldname":"final_income_tax", "fieldtype": "Float", "width": 150, "precision": 2},
		{"label":"TDS", "fieldname":"tds", "fieldtype": "Float", "width": 120, "precision": 2},
		{"label":"Tax Deducted", "fieldname":"tax_deducted", "fieldtype": "Float", "width": 120, "precision": 2},
		{"label":"Balance Tax", "fieldname":"balance_tax", "fieldtype": "Float", "width": 120, "precision": 2},
	]

def get_data(filters):
	# frappe.throw(str(filters))
	month = int(filters.get("month"))
	year = int(filters.get("year"))
	company = filters.get("company")

	data = []
	sl_no = 1
	totals = {
		"gross_salary": 0,
		"standard_deduction": 0,
		"final_taxable_income": 0,
		"tax_new": 0,
		"marginal_relief": 0,
		"cess": 0,
		"final_income_tax": 0,
		"tds": 0,
		"tax_deducted": 0,
		"balance_tax": 0,
	}

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
			WHERE employee = %s
				AND start_date >= %s
				AND end_date <= %s
				AND docstatus = 1
				AND (%s IS NULL OR company = %s)
			LIMIT 1
			""",
			(emp.name, f"{year}-{month}-01", f"{year}-{month}-31", company, company),
			as_dict=True,
		)

		if salary_slip and salary_slip[0].custom_income_tax:
			slip = salary_slip[0]
			gross_salary = slip.custom_current_net_total_earnings or 0
			standard_deduction = slip.custom_std_deduction or 0
			tax_new = slip.custom_tax or 0
			marginal_relief = slip.custom_marginal_relief or 0
			cess = slip.custom_cess or 0
			final_income_tax = slip.custom_deputation_allowance or 0
			tds = slip.custom_income_tax or 0
			tax_deducted = (slip.custom_current_total_tax_paid or 0) + tds
			balance_tax = final_income_tax - tax_deducted
			final_taxable_income = gross_salary - standard_deduction

			row = {
				"sl_no": sl_no,
				"ec": emp.employee_number or 0,
				"employee_name": emp.employee_name,
				"pan": emp.pan_number,
				"gross_salary": gross_salary,
				"standard_deduction": standard_deduction,
				"final_taxable_income": final_taxable_income,
				"tax_new": tax_new,
				"marginal_relief": marginal_relief,
				"cess": cess,
				"final_income_tax": final_income_tax,
				"tds": tds,
				"tax_deducted": tax_deducted,
				"balance_tax": balance_tax,
			}
			for key in totals:
				totals[key] += row.get(key, 0) or 0

			sl_no+=1
			data.append(row)

	if data:
		data.append(
			{
				"sl_no": "",
				"ec": "",
				"employee_name": "Total",
				"pan": "",
				**totals,
			}
		)

	return data
