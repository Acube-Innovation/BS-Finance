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
        {"label": "Phone No", "fieldname": "phone_no", "fieldtype": "Data", "width": 120},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "INSTITUTION/BANK", "fieldname": "institution", "fieldtype": "Data", "width": 180},
    ]


def get_data(filters):
    month = int(filters.get("month"))
    year = int(filters.get("year"))
    start_date = get_first_day(f"{year}-{month}-01")
    end_date = get_last_day(f"{year}-{month}-01")

    add_sal = frappe.get_all(
        "Additional Salary",
        filters={
            "salary_component": "Housing Loan",
            "is_recurring": 1,
            "disabled": 0,
            "docstatus": 1,
        },
        fields=["*"],
    )

    data = []
    sl_no = 1
    total_amount = 0

    for d in add_sal:
        # find salary slip for this employee in the given month
        salary_slip = frappe.db.sql(
            """
            SELECT name FROM `tabSalary Slip`
            WHERE employee = %s AND start_date >= %s AND end_date <= %s AND docstatus = 1
            LIMIT 1
            """,
            (d.employee, start_date, end_date),
            as_dict=True,
        )

        if salary_slip:
            loan_amount = frappe.db.sql(
                """
                SELECT amount FROM `tabSalary Detail`
                WHERE parent = %s AND salary_component = %s
                """,
                (salary_slip[0].name, "Housing Loan"),
                as_dict=True,
            )

            deducted_amount = loan_amount[0].amount if loan_amount else 0

            emp = frappe.db.get_value(
                "Employee",
                d.employee,
                ["employee_number", "employee_name", "cell_number"],
                as_dict=True,
            )

            # safely fetch bank name (skip if field not exists)
            bank_name = None
            try:
                bank_name = frappe.db.get_value("Employee", d.employee, "custom_bank_name")
            except Exception:
                pass

            data.append({
                "sl_no": sl_no,
                "employee_number": emp.employee_number if emp else "",
                "employee_name": emp.employee_name if emp else "",
                "phone_no": emp.cell_number if emp else "",
                "amount": deducted_amount,
                "institution": bank_name or "",
            })

            sl_no += 1
            total_amount += deducted_amount

    # add total row
    data.append({
        "sl_no": None,
        "employee_number": "",
        "employee_name": "Total",
        "phone_no": "",
        "amount": total_amount,
        "institution": "",
    })

    return data
