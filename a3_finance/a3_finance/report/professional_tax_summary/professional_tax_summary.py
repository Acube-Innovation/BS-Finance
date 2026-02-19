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
		{"label":"Sl No", "fieldname": "sl_no", "fieldtype": "Int", "width": 50},
		{"label":"EC", "fieldname": "ec", "fieldtype": "Data", "width": 120},
		{"label":"Employee Name", "fieldname": "employee_name", "fieldtype" : "Data", "width": 200},
		{"label":"Basic Pay 4 Months" , "fieldname": "basic_pay", "fieldtype": "Currency", "width": 120},
		{"label": "Normal Basic Pay", "fieldname": "normal_basic_pay", "fieldtype": "Currency", "width": 150},
		{"label": "Estimated for 2 Months", "fieldname": "estimated_basic_pay", "fieldtype": "Currency", "width": 180},
		{"label":"BP 6 Months", "fieldname": "bp_6_months", "fieldtype": "Currency", "width": 120},
		{"label":"VDA 4 Months", "fieldname": "vda", "fieldtype": "Currency", "width": 120},
		{"label": "Normal VDA", "fieldname": "normal_vda", "fieldtype": "Currency", "width": 120},
		{"label": "Estimated for 2 Months", "fieldname": "estimated_vda", "fieldtype": "Currency", "width": 180},
		{"label":"VDA 6 Months", "fieldname": "vda_6_months", "fieldtype": "Currency", "width": 120},
		{"label":"Total (BP + VDA) 6 Months", "fieldname": "total_bp_vda", "fieldtype": "Currency", "width": 180},
		{"label":"Professional Tax", "fieldname": "professional_tax", "fieldtype": "Currency", "width": 120},
	]

def get_data(filters=None):
	month = int(filters.get("month"))
	year = int(filters.get("year"))
	company = filters.get("company")
	start_date = get_first_day(f"{year}-{month}-01")

	data = []
	sl_no = 1
	total_bp=0
	total_normal_bp=0
	total_estimated_bp=0
	total_bp_6_months=0
	total_vda=0
	total_normal_vda=0
	total_estimated_vda=0
	total_vda_6_months=0
	total_total_bp_vda=0
	total_professional_tax=0
	salary_slip = frappe.db.sql(
		"""
		SELECT name, employee, employee_name
		FROM `tabSalary Slip`
		WHERE start_date = %s
		  AND docstatus = 1
		  AND (%s IS NULL OR company = %s)""",
		(start_date, company, company),
		as_dict=True,
	)
	for slip in salary_slip:
		proffessional_tax = frappe.db.sql(""" SELECT amount FROM `tabSalary Detail` WHERE parent = %s AND parentfield="deductions" AND salary_component = "Professional Tax" """, slip.name	)
		if proffessional_tax:
			bp= frappe.db.sql(""" SELECT amount,year_to_date,custom_actual_amount FROM `tabSalary Detail` WHERE parent = %s AND parentfield="earnings" AND salary_component = 'Basic Pay' """, slip.name	)
			vda = frappe.db.sql(""" SELECT amount,year_to_date,custom_actual_amount FROM `tabSalary Detail` WHERE parent = %s AND parentfield="earnings" AND salary_component = 'Variable DA' """, slip.name	)
			data.append({
			"sl_no": sl_no,
			"ec": slip.employee,
			"employee_name": slip.employee_name,
			"basic_pay": bp[0][1] if bp else 0,
			"normal_basic_pay": bp[0][2] if bp else 0,
			"estimated_basic_pay": (bp[0][2]*2) if bp else 0,
			"bp_6_months": (bp[0][1] + (bp[0][2])*2) if bp else 0,
			"vda": vda[0][1] if vda else 0,
			"normal_vda": vda[0][2] if vda else 0,
			"estimated_vda": (vda[0][2])*2 if	 vda else 0,
			"vda_6_months": (vda[0][1] + (vda[0][2])*2) if vda else 0,
			"total_bp_vda": ((bp[0][1] + (bp[0][2])*2) + (vda[0][1] + (vda[0][2])*2)) if bp and vda else 0,
			"professional_tax": proffessional_tax[0][0] if proffessional_tax else 0
			})
			total_bp += bp[0][1] if bp else 0
			total_normal_bp += bp[0][2] if bp else 0
			total_estimated_bp += (bp[0][2]*2) if bp else 0
			total_bp_6_months += (bp[0][1] + (bp[0][2])*2) if bp else 0
			total_vda += vda[0][1] if vda else 0
			total_normal_vda += vda[0][2] if vda else 0
			total_estimated_vda += (vda[0][2])*2 if	 vda else 0
			total_vda_6_months += (vda[0][1] + (vda[0][2])*2) if vda else 0
			total_total_bp_vda += ((bp[0][1] + (bp[0][2])*2) + (vda[0][1] + (vda[0][2])*2)) if bp and vda else 0
			total_professional_tax += proffessional_tax[0][0] if proffessional_tax else 0
			sl_no += 1
	data.append({
		"sl_no": "",
		"ec": "Total",
		"employee_name": "",
		"basic_pay": total_bp,
		"normal_basic_pay": total_normal_bp,
		"estimated_basic_pay": total_estimated_bp,
		"bp_6_months": total_bp_6_months,
		"vda": total_vda,
		"normal_vda": total_normal_vda,
		"estimated_vda": total_estimated_vda,
		"vda_6_months": total_vda_6_months,
		"total_bp_vda": total_total_bp_vda,
		"professional_tax": total_professional_tax
	})
	return data
