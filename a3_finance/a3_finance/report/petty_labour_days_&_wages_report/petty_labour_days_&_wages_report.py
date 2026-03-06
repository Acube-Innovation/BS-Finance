# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt


import frappe
from frappe.utils import flt




def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_columns(filters=None):
    contribution_type = filters.get("contribution_type") if filters else None

    columns = [
        {"label": "Labour", "fieldname": "labour", "fieldtype": "Link", "options": "Petty Labour Employees", "width": 200},
        {"label": "Total Days", "fieldname": "total_days", "fieldtype": "Float", "width": 100},
        {"label": "Avg Wages", "fieldname": "avg_wages", "fieldtype": "Currency", "width": 110},
        {"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 130},
    ]

    if contribution_type in (None, "All", "ESI"):
        columns += [
            {"label": "Employer ESI", "fieldname": "employer_esi", "fieldtype": "Currency", "width": 120},
            {"label": "Employee ESI", "fieldname": "employee_esi", "fieldtype": "Currency", "width": 120},
        ]

    if contribution_type in (None, "All", "PF"):
        columns += [
            {"label": "Employer PF", "fieldname": "employer_pf", "fieldtype": "Currency", "width": 120},
            {"label": "Employee PF", "fieldname": "employee_pf", "fieldtype": "Currency", "width": 120},
            {"label": "PF Admin Charges", "fieldname": "pf_admin", "fieldtype": "Currency", "width": 130},
        ]

    return columns



def get_data(filters):
    conditions = ""
    values = {}

    if filters.get("from_date"):
        conditions += " AND pl.transaction_date >= %(from_date)s"
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions += " AND pl.transaction_date <= %(to_date)s"
        values["to_date"] = filters["to_date"]

    if filters.get("petty_labour"):
        conditions += " AND pld.petty_labour = %(petty_labour)s"
        values["petty_labour"] = filters["petty_labour"]

    contribution_type = filters.get("contribution_type")

    if contribution_type == "ESI":
        conditions += " AND pld.esi = 1"
    elif contribution_type == "PF":
        conditions += " AND pld.pf = 1"

    query = f"""
        SELECT
            pld.petty_labour AS labour,
            SUM(pld.days) AS total_days,
            AVG(pld.wages) AS avg_wages,
            SUM(pld.amount) AS total_amount,

            SUM(pld.employer_contribution_esi_amount) AS employer_esi,
            SUM(pld.employee_contribution_esi_amount) AS employee_esi,

            SUM(pld.employer_contribution_pf_amount) AS employer_pf,
            SUM(pld.employee_contribution_pf_amount) AS employee_pf,

            SUM(pld.pf_administrative_charges) AS pf_admin

        FROM `tabPetty Labour Payment Details` pld
        INNER JOIN `tabPetty Labour Payment` pl
            ON pl.name = pld.parent
        WHERE pl.docstatus = 1 {conditions}
        GROUP BY pld.petty_labour
        ORDER BY pld.petty_labour
    """


    return frappe.db.sql(query, values, as_dict=True)
