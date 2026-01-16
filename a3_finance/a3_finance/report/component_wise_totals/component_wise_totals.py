# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = [
        {
            "label": "Sl No",
            "fieldname": "sl_no",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": "Employee ID",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Amount",
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 150
        },
    ]

    conditions = "1=1"
    values = {}

    if filters.get("from_date"):
        conditions += " AND ss.start_date >= %(from_date)s"
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions += " AND ss.end_date <= %(to_date)s"
        values["to_date"] = filters.get("to_date")

    if filters.get("salary_component"):
        conditions += " AND sse.salary_component = %(salary_component)s"
        values["salary_component"] = filters.get("salary_component")

    result = frappe.db.sql(f"""
        SELECT 
            ss.employee,
            ss.employee_name,
            sse.amount
        FROM `tabSalary Slip` ss
        INNER JOIN `tabSalary Detail` sse 
            ON ss.name = sse.parent
        WHERE {conditions}
          AND sse.amount != 0
          AND ss.docstatus = 1
        ORDER BY ss.employee
    """, values, as_dict=True)

    data = []

    for idx, row in enumerate(result, start=1):
        row["sl_no"] = idx
        data.append(row)

    # TOTAL row 
    total_amount = sum(d.amount for d in data)
    if total_amount:
        data.append({
            "sl_no": None,          
            "employee": "",
            "employee_name": "TOTAL",
            "amount": total_amount
        })

    return columns, data
