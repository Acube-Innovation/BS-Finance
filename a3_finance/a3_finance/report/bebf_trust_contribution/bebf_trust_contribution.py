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
        {"label": "Member No", "fieldname": "member_no", "fieldtype": "Data", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": "EE Contribution", "fieldname": "ee_contribution", "fieldtype": "Currency", "width": 120},
        {"label": "ER Contribution", "fieldname": "er_contribution", "fieldtype": "Currency", "width": 120},
        {"label": "Total", "fieldname": "total", "fieldtype": "Currency", "width": 120},
    ]

def get_data(filters):
    month = int(filters.get("month"))
    year = int(filters.get("year"))

    start_date = get_first_day(f"{year}-{month}-01")
    end_date = get_last_day(f"{year}-{month}-01")

    # ✅ get all employees with a member number
    employees = frappe.get_all(
        "Employee",
        filters={"custom_has_benevolent_fund_contribution": 1},
        fields=["name", "employee_name", "custom_bebf_no", "employee_number"]
    )

    data = []
    sl_no = 1
    ee_total = 0
    er_total = 0
    for emp in employees:
        # fetch salary slip (if exists)
        slip = frappe.db.sql("""
            SELECT name
            FROM `tabSalary Slip`
            WHERE employee = %s
              AND start_date >= %s
              AND end_date <= %s
              AND docstatus = 1
            LIMIT 1
        """, (emp.name, start_date, end_date), as_dict=1)

        amount = 0
        if slip:
            benevolent = frappe.db.sql("""
                SELECT amount
                FROM `tabSalary Detail`
                WHERE parent = %s
                  AND parentfield = 'deductions'
                  AND salary_component = 'BENEVOLENT FUND'
                LIMIT 1
            """, slip[0].name)
            if benevolent:
                amount = benevolent[0][0] or 0
                ee_total += amount

        data.append({
            "sl_no": sl_no,
            "employee_number": emp.employee_number or emp.name,
            "member_no": emp.custom_bebf_no,
            "employee_name": emp.employee_name,
            "ee_contribution": amount,
            "er_contribution": amount,
            "total": amount * 2
        })
        sl_no += 1
	
    data.append({
		"sl_no": None,
		"employee_number": "",
		"member_no": "",
		"employee_name": "TOTAL",
		"ee_contribution": ee_total,
		"er_contribution": ee_total,
		"total": ee_total + ee_total
	})

    return data
