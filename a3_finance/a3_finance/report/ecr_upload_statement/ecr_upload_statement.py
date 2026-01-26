# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "S.No", "fieldname": "sno", "fieldtype": "Int", "width": 50},
        {"label": "EC", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": "UAN", "fieldname": "uan_number", "fieldtype": "Data", "width": 140},
        {"label": "PF A/c", "fieldname": "pf_ac", "fieldtype": "Data", "width": 120},
        {"label": "EPF WAGES", "fieldname": "epf_wages", "fieldtype": "Currency", "width": 120},
        {"label": "EPS WAGES", "fieldname": "eps_wages", "fieldtype": "Currency", "width": 120},
        {"label": "EDLI WAGES", "fieldname": "edli_wages", "fieldtype": "Currency", "width": 120},
        {"label": "EPF", "fieldname": "epf", "fieldtype": "Currency", "width": 100},
        {"label": "EPS", "fieldname": "eps", "fieldtype": "Currency", "width": 100},
        {"label": "PF", "fieldname": "pf", "fieldtype": "Currency", "width": 100},
        {"label": "Voluntary PF", "fieldname": "voluntary_pf", "fieldtype": "Currency", "width": 120},
        {"label": "PF", "fieldname": "pf_dup", "fieldtype": "Currency", "width": 100},
        {"label": "VPF+PF", "fieldname": "vpf_pf", "fieldtype": "Currency", "width": 120},
        {"label": "EPS", "fieldname": "eps_dup", "fieldtype": "Currency", "width": 100},
        {"label": "ER", "fieldname": "er", "fieldtype": "Currency", "width": 100},
        {"label": "NCP", "fieldname": "ncp", "fieldtype": "Float", "width": 80},
    ]


def get_data(filters):
    filters = filters or {}
    conditions = []
    values = {}

    if filters.get("payroll_month"):
        conditions.append("payroll_month = %(payroll_month)s")
        values["payroll_month"] = filters["payroll_month"]

    if filters.get("payroll_year"):
        conditions.append("payroll_year = %(payroll_year)s")
        values["payroll_year"] = filters["payroll_year"]

    if filters.get("employee"):
        conditions.append("employee = %(employee)s")
        values["employee"] = filters["employee"]

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    records = frappe.db.sql(
        f"""
        SELECT
            employee,
            employee_name,
            uan_number,
            base,
            da,
            service_weightage,
            lop_refund,
            lop_in_hours,
            epf_wages,
            eps_wages,
            edli_wages,
            pf,
            eps,
            voluntary_pf,
            er,
            lop_days
        FROM `tabPF Detailed Log`
        {where_clause}
        ORDER BY employee_name
        """,
        values,
        as_dict=True
    )

    data = []
    sno = 1

    for d in records:
        total_earnings = (
            flt(d.total_earnings)
            
        
        )

        data.append({
            "sno": sno,
            "employee": d.employee,
            "employee_name": d.employee_name,
            "uan_number": d.uan_number,
            "pf_ac": d.employee,
            "epf_wages": d.epf_wages,
            "eps_wages": d.eps_wages,
            "edli_wages": d.edli_wages,
            "epf": d.pf,
            "eps": d.eps,
            "pf": d.pf,
            "voluntary_pf": d.voluntary_pf,
            "pf_dup": d.pf,
            "vpf_pf": flt(d.pf) + flt(d.voluntary_pf),
            "eps_dup": d.eps,
            "er": d.er,
            "ncp": d.lop_days,
        })

        sno += 1

    return data
