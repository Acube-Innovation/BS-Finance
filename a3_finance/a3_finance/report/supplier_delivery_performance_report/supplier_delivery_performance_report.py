# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt



import frappe
from frappe.utils import getdate

def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


# ---------------------------------------------------------

def get_columns():
    return [
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 150},
        {"label": "Purchase Order", "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 150},
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
        {"label": "Required Date", "fieldname": "required_date", "fieldtype": "Date", "width": 110},
        {"label": "Last Receipt Date", "fieldname": "receipt_date", "fieldtype": "Date", "width": 120},
        {"label": "Ordered Qty", "fieldname": "ordered_qty", "fieldtype": "Float", "width": 110},
        {"label": "Received Qty", "fieldname": "received_qty", "fieldtype": "Float", "width": 110},
        {"label": "Delay Days", "fieldname": "delay_days", "fieldtype": "Int", "width": 100},
        {"label": "Delay Status", "fieldname": "delay_status", "fieldtype": "Data", "width": 100},
    ]


# ---------------------------------------------------------

def get_conditions(filters):
    conditions = " po.docstatus = 1 "

    if filters.get("company"):
        conditions += " AND po.company = %(company)s"

    if filters.get("supplier"):
        conditions += " AND po.supplier = %(supplier)s"

    if filters.get("from_date"):
        conditions += " AND po.transaction_date >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " AND po.transaction_date <= %(to_date)s"

    if filters.get("item_code"):
        conditions += " AND poi.item_code = %(item_code)s"

    return conditions


# ---------------------------------------------------------

def get_data(filters):

    conditions = get_conditions(filters)

    data = frappe.db.sql(f"""
        SELECT
            po.company,
            po.supplier,
            po.name AS purchase_order,
            poi.item_code,
            poi.schedule_date AS required_date,
            MAX(pr.posting_date) AS receipt_date,
            poi.qty AS ordered_qty,
            IFNULL(SUM(pri.qty), 0) AS received_qty

        FROM `tabPurchase Order` po
        JOIN `tabPurchase Order Item` poi
            ON poi.parent = po.name
            

        LEFT JOIN `tabPurchase Receipt Item` pri
    ON pri.purchase_order = po.name
    AND pri.item_code = poi.item_code
    AND EXISTS (
        SELECT 1 FROM `tabPurchase Receipt` pr2
        WHERE pr2.name = pri.parent
        AND pr2.docstatus = 1
    )

LEFT JOIN `tabPurchase Receipt` pr
    ON pr.name = pri.parent
    AND pr.docstatus = 1


        WHERE {conditions}

        GROUP BY po.name, poi.name
    """, filters, as_dict=1)

    final_data = []

    for row in data:

        delay_days = None
        delay_status = "Pending"

        if row.receipt_date and row.required_date:
            delay_days = (getdate(row.receipt_date) - getdate(row.required_date)).days

            if delay_days > 0:
                delay_status = "Delayed"
            elif delay_days == 0:
                delay_status = "On Time"
            else:
                delay_status = "Early"

        # Delay filter
        if filters.get("delay_more_than") and delay_days is not None:
            if delay_days <= int(filters.get("delay_more_than")):
                continue

        if filters.get("delay_status") and delay_status != filters.get("delay_status"):
            continue

        row.delay_days = delay_days
        row.delay_status = delay_status

        final_data.append(row)

    return final_data
