# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt


import frappe
from frappe.utils import flt, getdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data
def get_columns():
    return [
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 200},

        {"label": "Opening Qty", "fieldname": "opening_qty", "fieldtype": "Float", "width": 120},
        {"label": "Opening Value", "fieldname": "opening_value", "fieldtype": "Currency", "width": 140},

        {"label": "In Qty", "fieldname": "in_qty", "fieldtype": "Float", "width": 120},
        {"label": "In Value", "fieldname": "in_value", "fieldtype": "Currency", "width": 140},

        {"label": "Out Qty", "fieldname": "out_qty", "fieldtype": "Float", "width": 120},
        {"label": "Out Value", "fieldname": "out_value", "fieldtype": "Currency", "width": 140},

        {"label": "Balance Qty", "fieldname": "balance_qty", "fieldtype": "Float", "width": 120},
        {"label": "Balance Value", "fieldname": "balance_value", "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    company = filters.get("company")

    conditions = ""
    if company:
        conditions += " AND sle.company = %(company)s"

    sle = frappe.db.sql("""
        SELECT
            i.item_group,
            sle.posting_date,
            sle.actual_qty,
            sle.stock_value_difference
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` i ON sle.item_code = i.name
        WHERE sle.is_cancelled = 0
        AND sle.posting_date <= %(to_date)s
        {conditions}
    """.format(conditions=conditions), filters, as_dict=1)

    item_group_map = {}

    for row in sle:
        ig = row.item_group

        if ig not in item_group_map:
            item_group_map[ig] = {
                "item_group": ig,
                "opening_qty": 0,
                "opening_value": 0,
                "in_qty": 0,
                "in_value": 0,
                "out_qty": 0,
                "out_value": 0,
                "balance_qty": 0,
                "balance_value": 0,
            }

        posting_date = row.posting_date
        qty = flt(row.actual_qty)
        value_diff = flt(row.stock_value_difference)

        # Opening
        if posting_date < from_date:
            item_group_map[ig]["opening_qty"] += qty
            item_group_map[ig]["opening_value"] += value_diff

        # Movement in period
        if from_date <= posting_date <= to_date:
            if qty > 0:
                item_group_map[ig]["in_qty"] += qty
                item_group_map[ig]["in_value"] += value_diff
            else:
                item_group_map[ig]["out_qty"] += abs(qty)
                item_group_map[ig]["out_value"] += abs(value_diff)

        # Balance till to_date
        if posting_date <= to_date:
            item_group_map[ig]["balance_qty"] += qty
            item_group_map[ig]["balance_value"] += value_diff

    return list(item_group_map.values())
