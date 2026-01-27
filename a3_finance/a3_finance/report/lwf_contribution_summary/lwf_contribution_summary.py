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
		{"label": "EE Contribution", "fieldname": "ee_contribution", "fieldtype": "Currency", "width": 120},
		{"label": "ER Contribution", "fieldname": "er_contribution", "fieldtype": "Currency", "width": 120},
		{"label": "PF. No", "fieldname": "pf_no", "fieldtype": "Data", "width": 120},
		{"label": "Aadhar No", "fieldname": "aadhar_no", "fieldtype": "Data", "width": 120},
		{"label": "Mobile No", "fieldname": "mobile_no", "fieldtype": "Data", "width": 120},
		{"label": "Account No", "fieldname": "account_no", "fieldtype": "Data", "width": 120},
		{"label": "IFSC Code", "fieldname": "ifsc_code", "fieldtype": "Data", "width": 120},
		{"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 150},
		{"label":"Branch","fieldname":"branch","fieldtype":"Data","width":150},
	]

def get_data(filters):
	month = int(filters.get("month")) if filters.get("month") else None
	year = int(filters.get("year")) if filters.get("year") else None
	start_date = get_first_day(f"{year}-{month}-01")
	end_date = get_last_day(f"{year}-{month}-01")

	employees = frappe.get_all(
	"Employee",
	filters={"custom_has_labour_welfare_fund": 1},
	fields=["name", "employee_name", "employee_number","custom_epf","custom_aadhar_no","cell_number","bank_ac_no","bank_name","ifsc_code","custom_bank_branch"])

	data = []
	sl_no = 1
	for emp in employees:
		# fetch salary slip (if exists)
		slip = frappe.db.sql("""
			SELECT name,custom_labour_welfare_fund
			FROM `tabSalary Slip`
			WHERE employee = %s
			  AND start_date >= %s
			  AND end_date <= %s
			  AND docstatus = 1
			LIMIT 1
		""", (emp.name, start_date, end_date), as_dict=1)

		ee_contribution = 0
		if slip :
			benevolent = frappe.db.sql("""
				SELECT amount
				FROM `tabSalary Detail`
				WHERE parent = %s
				  AND parentfield = 'deductions'
				  AND salary_component = 'Labour Welfare Fund'
				LIMIT 1
			""", slip[0].name, as_list=1)

			if benevolent and benevolent[0][0]:
				ee_contribution = benevolent[0][0]


				data.append({
					"sl_no": sl_no,
					"employee_number": emp.employee_number or emp.name,
					"employee_name": emp.employee_name,
					"ee_contribution": ee_contribution,
					"er_contribution": ee_contribution,
					"pf_no": emp.custom_epf,
					"aadhar_no": emp.custom_aadhar_no,
					"mobile_no": emp.cell_number,
					"account_no": emp.bank_ac_no,
					"ifsc_code": emp.ifsc_code,
					"bank": emp.bank_name,
					"branch": emp.custom_bank_branch
				})
				sl_no += 1

	return data
