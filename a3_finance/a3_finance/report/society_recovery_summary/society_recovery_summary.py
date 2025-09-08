# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_last_day


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
        {"label": "Amount Advised", "fieldname": "subscription_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Amount Deducted", "fieldname": "recovered_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Balance to be Deducted", "fieldname": "balance_amount", "fieldtype": "Currency", "width": 180},
    ]


def get_data(filters=None):
    month = int(filters.get("month"))
    year = int(filters.get("year"))
    last_date = get_last_day(f"{year}-{month}-01")

    # get all society deductions for that payroll date
    society_deductions = frappe.get_all(
        "Society Deduction",
        filters={"payroll_date": last_date},
        fields=["name", "employee", "amount", "payroll_date"]
    )

    data = []
    sl_no = 1

    for record in society_deductions:
        advised = record.amount or 0

        # fetch salary slip of this employee for that payroll date
        salary_slip = frappe.db.sql(
            """
            SELECT name, employee, employee_name
            FROM `tabSalary Slip`
            WHERE employee = %s AND end_date = %s AND docstatus = 1
            LIMIT 1
            """,
            (record.employee, record.payroll_date),
            as_dict=True,
        )

        recovered_amount = 0
        emp = frappe.db.get_value(
            "Employee",
            record.employee,
            ["employee_number", "employee_name", "custom_baecsl_no"],
            as_dict=True,
        )

        if salary_slip:
            # try fetching from deductions first
            society_amount = frappe.db.sql(
                """
                SELECT amount FROM `tabSalary Detail`
                WHERE parent = %s 
                AND parentfield = 'deductions' 
                AND salary_component IN ('Society')
                """,
                (salary_slip[0].name,),
                as_dict=True,
            )

            if society_amount:
                recovered_amount = society_amount[0].amount or 0

        data.append({
            "sl_no": sl_no,
            "employee_number": emp.employee_number if emp else "",
            "employee_name": emp.employee_name if emp else "",
            "subscription_amount": advised,
            "recovered_amount": recovered_amount,
            "member_no": emp.custom_baecsl_no if emp else "",
            "balance_amount": advised - recovered_amount,
        })
        sl_no += 1

    # add total row
    if data:
        data.append({
            "sl_no": "",
            "employee_number": "",
            "employee_name": "Total",
            "subscription_amount": sum(d.get("subscription_amount", 0) for d in data),
            "recovered_amount": sum(d.get("recovered_amount", 0) for d in data),
            "member_no": "",
            "balance_amount": sum(d.get("balance_amount", 0) for d in data),
        })

    return data
