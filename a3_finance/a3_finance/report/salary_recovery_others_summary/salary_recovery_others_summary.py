# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_first_day, get_last_day


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data


def get_columns():
    return [
        {"label": "Sl No", "fieldname": "sl_no", "fieldtype": "Int", "width": 50},
        {"label": "Employee Number", "fieldname": "employee_number", "fieldtype": "Data", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": "Phone No", "fieldname": "phone_no", "fieldtype": "Data", "width": 120},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
    ]


def get_data(filters):
    month = int(filters.get("month"))
    year = int(filters.get("year"))
    company = filters.get("company") or None
    start_date = get_first_day(f"{year}-{month}-01")
    end_date = get_last_day(f"{year}-{month}-01")

    # Other Recovery actually deducted on the month's submitted salary slips
    recoveries = frappe.db.sql(
        """
        SELECT e.employee_number, e.employee_name, e.cell_number, SUM(sd.amount) AS amount
        FROM `tabSalary Slip` ss
        JOIN `tabSalary Detail` sd
            ON sd.parent = ss.name AND sd.parenttype = 'Salary Slip' AND sd.parentfield = 'deductions'
        JOIN `tabEmployee` e ON e.name = ss.employee
        WHERE ss.docstatus = 1
            AND ss.start_date >= %(start_date)s
            AND ss.end_date <= %(end_date)s
            AND (%(company)s IS NULL OR ss.company = %(company)s)
            AND sd.salary_component = 'Other Recovery'
            AND sd.amount > 0
        GROUP BY ss.employee, e.employee_number, e.employee_name, e.cell_number
        ORDER BY e.employee_number
        """,
        {"start_date": start_date, "end_date": end_date, "company": company},
        as_dict=True,
    )

    data = []
    total_amount = 0

    for sl_no, d in enumerate(recoveries, start=1):
        data.append({
            "sl_no": sl_no,
            "employee_number": d.employee_number or "",
            "employee_name": d.employee_name or "",
            "phone_no": d.cell_number or "",
            "amount": d.amount,
        })
        total_amount += d.amount

    # add total row
    data.append({
        "sl_no": None,
        "employee_number": "",
        "employee_name": "Total",
        "phone_no": "",
        "amount": total_amount,
    })

    return data
