# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, add_days

def execute(filters=None):
    if not filters:
        filters = {}

    # Auto-set end date = start date + 6
    if filters.get("start_date") and not filters.get("end_date"):
        filters["end_date"] = add_days(filters["start_date"], 6)

    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "EC", "fieldname": "ec", "fieldtype": "Data", "width": 80},
        {"label": "Employee", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 120},
        {"label": "Rate/Day", "fieldname": "rate_per_day", "fieldtype": "Currency", "width": 100},
        {"label": "No of Days", "fieldname": "days", "fieldtype": "Float", "width": 90},
        {"label": "Earnings (Gross Pay)", "fieldname": "gross_pay", "fieldtype": "Currency", "width": 120},
        {"label": "PF Wages", "fieldname": "pf_wages", "fieldtype": "Currency", "width": 100},
        {"label": "Allowance", "fieldname": "allowance", "fieldtype": "Currency", "width": 100},
        {"label": "ESI Deduction", "fieldname": "esi_ded", "fieldtype": "Currency", "width": 100},
        {"label": "PF Deduction", "fieldname": "pf_ded", "fieldtype": "Currency", "width": 100},
        {"label": "Other Ded", "fieldname": "other_ded", "fieldtype": "Currency", "width": 100},
        {"label": "Total Ded", "fieldname": "total_ded", "fieldtype": "Currency", "width": 100},
        {"label": "Net Pay", "fieldname": "net_pay", "fieldtype": "Currency", "width": 120},
        {"label": "Bank A/C No", "fieldname": "bank_ac_no", "fieldtype": "Data", "width": 150},
    ]

def get_data(filters):
    employees = frappe.get_all(
        "Employee",
        filters={"employment_type": "Canteen Employee", "status": "Active"},
        fields=["name", "employee_name", "designation", "employee_number as ec", "bank_ac_no", "custom_basic_pay"]
    )

    if not employees:
        frappe.msgprint("⚠️ No employees found with Employment Type = 'Canteen employees' and Status = 'Active'")

    data = []
    for emp in employees:
        slips = frappe.get_all(
            "Salary Slip",
            filters={
                "employee": emp.name,
                "start_date": [">=", filters["start_date"]],
                "end_date": ["<=", filters["end_date"]],
            },
            fields=["gross_pay", "net_pay", "total_deduction", "payment_days", "name"]
        )

        if not slips:
            frappe.msgprint(f"⚠️ No Salary Slips found for {emp.employee_name} ({emp.name}) "
                            f"between {filters['start_date']} and {filters['end_date']}")

        for slip in slips:
            rate_per_day = (emp.custom_basic_pay or 0)
            gross_pay = slip.gross_pay or 0
            total_ded = slip.total_deduction or 0
            net_pay = slip.net_pay or 0

            # Fetch components
            components = frappe.get_all(
                "Salary Detail",
                filters={"parent": slip.name},
                fields=["salary_component", "amount", "parentfield"]
            )

            pf_wages = allowance = esi_ded = pf_ded = other_ded = 0
            for comp in components:
                if comp.salary_component == "PF Wages":
                    pf_wages = comp.amount
                elif comp.salary_component == "Allowance":
                    allowance = comp.amount
                elif comp.salary_component == "ESI Deduction":
                    esi_ded = comp.amount
                elif comp.salary_component == "PF Deduction":
                    pf_ded = comp.amount
                else:
                    if comp.parentfield == "deductions":
                        other_ded += comp.amount

            data.append({
                "ec": emp.ec,
                "employee_name": emp.employee_name,
                "designation": emp.designation,
                "rate_per_day": rate_per_day,
                "days": slip.payment_days,
                "gross_pay": gross_pay,
                "pf_wages": pf_wages,
                "allowance": allowance,
                "esi_ded": esi_ded,
                "pf_ded": pf_ded,
                "other_ded": other_ded,
                "total_ded": total_ded,
                "net_pay": net_pay,
                "bank_ac_no": emp.bank_ac_no,
            })
    return data
