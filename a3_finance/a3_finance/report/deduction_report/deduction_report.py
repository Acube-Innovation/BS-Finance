# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt

"""Deduction Report: the amount of one deduction component (Housing Loan, LIC Recovery, Society, ...) deducted
from each employee in the month, in the format of the Housing Loan Contribution Summary.

Amount = the component's deduction rows of the employee's submitted salary slips of the month (added up when it
appears more than once); employees with nothing deducted are left out.
"""

import frappe
from frappe.utils import flt, get_first_day, get_last_day


def execute(filters=None):
    filters = frappe._dict(filters or {})
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": "Sl No", "fieldname": "sl_no", "fieldtype": "Int", "width": 50},
        {"label": "Employee Number", "fieldname": "employee_number", "fieldtype": "Data", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": "Phone No", "fieldname": "phone_no", "fieldtype": "Data", "width": 120},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "INSTITUTION/BANK", "fieldname": "institution", "fieldtype": "Data", "width": 180},
    ]


def get_data(filters):
    if not filters.get("deduction_component"):
        return []
    month, year = int(filters.get("month")), int(filters.get("year"))
    start_date = get_first_day(f"{year}-{month:02d}-01")
    end_date = get_last_day(start_date)
    company_condition = "and ss.company = %(company)s" if filters.get("company") else ""

    rows = frappe.db.sql(
        f"""
        select ss.employee, sum(sd.amount) as amount
        from `tabSalary Detail` sd
        join `tabSalary Slip` ss on ss.name = sd.parent
        where sd.parenttype = 'Salary Slip' and sd.parentfield = 'deductions'
            and sd.salary_component = %(component)s
            and ss.docstatus = 1 and ss.start_date >= %(start_date)s and ss.end_date <= %(end_date)s
            {company_condition}
        group by ss.employee
        having sum(sd.amount) > 0
        """,
        {
            "component": filters.deduction_component,
            "start_date": start_date,
            "end_date": end_date,
            "company": filters.get("company"),
        },
        as_dict=True,
    )
    if not rows:
        return []

    fields = ["name", "employee_number", "employee_name", "cell_number"]
    if frappe.get_meta("Employee").has_field("custom_bank_name"):
        fields.append("custom_bank_name")
    employees = {
        e.name: e
        for e in frappe.get_all("Employee", filters={"name": ["in", [r.employee for r in rows]]}, fields=fields)
    }

    data, total = [], 0
    for row in sorted(rows, key=lambda r: (employees.get(r.employee) or {}).get("employee_number") or r.employee):
        emp = employees.get(row.employee) or frappe._dict()
        data.append(
            {
                "sl_no": len(data) + 1,
                "employee_number": emp.employee_number or row.employee,
                "employee_name": emp.employee_name or "",
                "phone_no": emp.cell_number or "",
                "amount": flt(row.amount),
                "institution": emp.get("custom_bank_name") or "",
            }
        )
        total += flt(row.amount)

    data.append(
        {
            "sl_no": None,
            "employee_number": "",
            "employee_name": "Total",
            "phone_no": "",
            "amount": total,
            "institution": "",
        }
    )
    return data
