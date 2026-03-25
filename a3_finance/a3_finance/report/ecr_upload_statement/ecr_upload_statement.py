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
        {"label": "EC", "fieldname": "employee", "fieldtype": "Data", "options": "Employee", "width": 120},
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
        {"label": "VPF+PF", "fieldname": "vpf_pf", "fieldtype": "Currency", "width": 120},
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
            epf_ac,
            employee_name,
            uan_number,
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

    # Totals dictionary
    totals = {
        "epf_wages": 0,
        "eps_wages": 0,
        "edli_wages": 0,
        "epf": 0,
        "eps": 0,
        "pf": 0,
        "voluntary_pf": 0,
        "vpf_pf": 0,
        "er": 0,
        "ncp": 0
    }

    for d in records:
        epf = flt(d.pf, 0)
        eps = flt(d.eps, 0)
        voluntary_pf = flt(d.voluntary_pf, 0)
        er = flt(d.er, 0)

        data.append({
            "sno": sno,
            "employee": d.employee,
            "employee_name": d.employee_name,
            "uan_number": d.uan_number,
            "pf_ac": d.epf_ac or " ",
            "epf_wages": flt(d.epf_wages),
            "eps_wages": flt(d.eps_wages),
            "edli_wages": flt(d.edli_wages),
            "epf": epf,
            "eps": eps,
            "pf": epf,
            "voluntary_pf": voluntary_pf,
            "vpf_pf": epf + voluntary_pf,
            "er": er,
            "ncp": flt(d.lop_days),
        })

        # Update totals
        totals["epf_wages"] += flt(d.epf_wages)
        totals["eps_wages"] += flt(d.eps_wages)
        totals["edli_wages"] += flt(d.edli_wages)
        totals["epf"] += epf
        totals["eps"] += eps
        totals["pf"] += epf
        totals["voluntary_pf"] += voluntary_pf
        totals["vpf_pf"] += epf + voluntary_pf
        totals["er"] += er
        totals["ncp"] += flt(d.lop_days)

        sno += 1

    # Append total row (no S.No)
    data.append({
        "sno": None,
        "employee": "TOTAL",
        "employee_name": "",
        "uan_number": " ",
        "pf_ac": " ",
        "epf_wages": totals["epf_wages"],
        "eps_wages": totals["eps_wages"],
        "edli_wages": totals["edli_wages"],
        "epf": totals["epf"],
        "eps": totals["eps"],
        "pf": totals["pf"],
        "voluntary_pf": totals["voluntary_pf"],
        "vpf_pf": totals["vpf_pf"],
        "er": totals["er"],
        "ncp": totals["ncp"],
    })

    return data
