# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

# import frappe

import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
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

    data = frappe.db.sql(f"""
        SELECT 
            ss.name AS salary_slip,
            ss.employee,
            ss.employee_name,
            sse.amount
        FROM `tabSalary Slip` ss
        INNER JOIN `tabSalary Detail` sse ON ss.name = sse.parent
        WHERE {conditions}
          AND sse.amount != 0
          AND ss.docstatus = 1
        ORDER BY ss.employee ASC
    """, values, as_dict=True)

    # Add Total row
    total_amount = sum(d.amount for d in data)
    if total_amount:
        data.append({
            "employee_name": "TOTAL",
            "amount": total_amount
        })

    return columns, data

