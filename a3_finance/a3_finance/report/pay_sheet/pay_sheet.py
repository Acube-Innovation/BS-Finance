import frappe
from frappe.utils import getdate

# Full list of components to check
ALL_COMPONENTS = [
    "Basic Pay", "Service Weightage", "Variable DA", "House Rent Allowance",
    "Conv. Allowance", "Canteen Subsidy", "Children Education Allowance", "Medical Allowance",
    "Overtime Wages", "Washing Allowance", "Book Allowance", "LOP Refund", "Deputation Allowance",
    "Night Shift Allowance", "Stitching Allowance", "Shoe Allowance", "Spectacle Allowance",
    "EL Encashment", "Arrear", "Festival Advance", "Others Earnings",
    "LOP (In Hours) Refund", "Exgratia", "Annual Bonus (For Tax)"
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
        "basic_pay": "Basic Pay",
        "service_weightage": "Service Weightage",
        "variable_da": "Variable DA",
        "house_rent_allowance": "House Rent Allowance",
        "conv_allowance": "Conv. Allowance",
        "canteen_subsidy": "Canteen Subsidy",
        "children_education_allowance": "Children Education Allowance",
        "medical_allowance": "Medical Allowance",
        "overtime_wages": "Overtime Wages",
        "washing_allowance": "Washing Allowance",
        "book_allowance": "Book Allowance",
        "lop_refund": "LOP Refund",
        "deputation_allowance": "Deputation Allowance",
        "night_shift_allowance": "Night Shift Allowance",
        "stitching_allowance": "Stitching Allowance",
        "shoe_allowance": "Shoe Allowance",
        "spectacle_allowance": "Spectacle Allowance",
        "el_encashment": "EL Encashment",
        "arrear": "Arrear",
        "festival_advance": "Festival Advance",
        "others_earnings": "Others Earnings",
        "lop_in_hours_refund": "LOP (In Hours) Refund",
        "exgratia": "Exgratia",
        "annual_bonus_for_tax": "Annual Bonus (For Tax)"
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
        "label": "Total Earnings", "fieldname": "total", "fieldtype": "Currency", "width": 130
    })
    return columns



def get_data(start_date, end_date, subtype_filter=None, emp_type_filter=None):
    conditions = """
        s.docstatus IN (0,1)
        AND s.start_date >= %(start_date)s AND s.end_date <= %(end_date)s
        AND sd.parentfield = 'earnings'
        AND e.custom_employment_sub_type IS NOT NULL
    """

    if subtype_filter:
        conditions += " AND e.custom_employment_sub_type = %(subtype_filter)s"
    if emp_type_filter:
        conditions += " AND e.employment_type = %(employment_type)s"

    # Build select clause dynamically
    component_sums = []
    for comp in ALL_COMPONENTS:
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
