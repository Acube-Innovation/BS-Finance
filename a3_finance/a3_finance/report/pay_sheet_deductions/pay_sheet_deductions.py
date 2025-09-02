# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe.utils import getdate

# Full list of Deduction components
ALL_DEDUCTION_COMPONENTS = [
    "Subsistence PF", "ESI", "PF Deduction", "Other Recovery", "TL Deduction", "Employee PF",
    "Professional Tax", "Society", "BENEVOLENT FUND", "Brahmos Recreation Club Contribution",
    "Voluntary PF", "LWP Deduction", "Labour Welfare Fund", "Income Tax",
    "Advance Recovery(TA)", "PLI Recovery", "Canteen Coupon Deduction", "LIC Recovery",
    "LOP (Days) Deduction", "Canteen Recovery","Housing Loan","Festival Advance Recovery","Other Recovery","LOP (in Hours) Deduction"
]


def execute(filters=None):
    if not filters:
        filters = {}

    start_date = getdate(filters.get("start_date"))
    end_date = getdate(filters.get("end_date"))
    subtype_filter = filters.get("employment_subtype")
    emp_type_filter = filters.get("employment_type")

    # Get data
    data, totals = get_data(start_date, end_date, subtype_filter, emp_type_filter)

    # Dynamically build columns based on used components
    columns = get_columns(totals)

    # Filter result data by used components only
    filtered_data = []
    for row in data:
        filtered_row = {
            "employment_subtype": row["employment_subtype"]
        }
        for comp in totals:
            if comp != "total":
                filtered_row[comp] = row.get(comp)
        filtered_row["total"] = row.get("total")
        filtered_data.append(filtered_row)

    return columns, filtered_data


def get_columns(totals):
    label_map = {
        "subsistence_pf": "Subsistence PF",
        "esi": "ESI",
        "pf_deduction": "PF Deduction",
        "other_recovery": "Other Recovery",
        "tl_deduction": "TL Deduction",
        "employee_pf": "Employee PF",
        "professional_tax": "Professional Tax",
        "society": "Society",
        "benevolent_fund": "BENEVOLENT FUND",
        "brahmos_recreation_club_con": "Brahmos Recreation Club Con",
        "voluntary_pf": "Voluntary PF",
        "lwp_deduction": "LWP Deduction",
        "labour_welfare_fund": "Labour Welfare Fund",
        "income_taxbatl": "Income Tax(BATL)",
        "advance_recoveryta": "Advance Recovery(TA)",
        "pli_recovery": "PLI Recovery",
        "canteen_coupon_deduction": "Canteen Coupon Deduction",
        "lic_recovery": "LIC Recovery",
        "lop_hours_deduction": "LOP (in Hours) Deduction",
        "canteen_recovery": "Canteen Recovery",
		"housing_loan":"Housing Loan",
		"festival_advance_recovery":"Festival Advance Recovery",
		"other_recovery":"Other Recovery"
    }

    columns = [
        {"label": "Particulars", "fieldname": "employment_subtype", "fieldtype": "Data", "width": 160}
    ]
    for comp in totals:
        if comp not in ("employment_subtype", "total"):
            columns.append({
                "label": label_map.get(comp, comp.replace("_", " ").title()),
                "fieldname": comp,
                "fieldtype": "Currency",
                "width": 130
            })

    columns.append({
        "label": "Total Deductions", "fieldname": "total", "fieldtype": "Currency", "width": 130
    })
    return columns


def get_data(start_date, end_date, subtype_filter=None, emp_type_filter=None):
    conditions = """
        s.docstatus IN (0,1)
        AND s.start_date >= %(start_date)s AND s.end_date <= %(end_date)s
        AND sd.parentfield = 'deductions'
        AND e.custom_employment_sub_type IS NOT NULL
    """

    if subtype_filter:
        conditions += " AND e.custom_employment_sub_type = %(subtype_filter)s"
    if emp_type_filter:
        conditions += " AND e.employment_type = %(employment_type)s"

    # Build select clause dynamically
    component_sums = []
    for comp in ALL_DEDUCTION_COMPONENTS:
        field = comp.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "").replace(".", "")
        component_sums.append(
            f"SUM(CASE WHEN sd.salary_component = '{comp}' THEN sd.amount END) AS `{field}`"
        )

    select_clause = ",\n            ".join(component_sums)

    query = f"""
        SELECT
            e.custom_employment_sub_type AS employment_subtype,
            {select_clause},
            SUM(sd.amount) AS total
        FROM `tabSalary Slip` s
        JOIN `tabSalary Detail` sd ON sd.parent = s.name
        JOIN `tabEmployee` e ON s.employee = e.name
        WHERE {conditions}
        GROUP BY e.custom_employment_sub_type
        ORDER BY e.custom_employment_sub_type
    """

    params = {
        "start_date": start_date,
        "end_date": end_date,
        "subtype_filter": subtype_filter,
        "employment_type": emp_type_filter
    }

    results = frappe.db.sql(query, params, as_dict=True)

    # Calculate grand totals and detect which components are actually used
    used_components = {}
    if results:
        grand_total = {"employment_subtype": "Grand Total"}
        for key in results[0].keys():
            if key != "employment_subtype":
                grand_total[key] = sum((r.get(key) or 0) for r in results)
                if grand_total[key] != 0:
                    used_components[key] = True
        results.append(grand_total)

    return results, used_components

