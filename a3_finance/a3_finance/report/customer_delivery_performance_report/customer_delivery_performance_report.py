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
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 150},
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
        {"label": "Committed Date", "fieldname": "committed_date", "fieldtype": "Date", "width": 110},
        {"label": "Last Delivery Date", "fieldname": "delivery_date", "fieldtype": "Date", "width": 120},
        {"label": "Ordered Qty", "fieldname": "ordered_qty", "fieldtype": "Float", "width": 110},
        {"label": "Delivered Qty", "fieldname": "delivered_qty", "fieldtype": "Float", "width": 110},
        {"label": "Delay Days", "fieldname": "delay_days", "fieldtype": "Int", "width": 100},
        {"label": "Delay Status", "fieldname": "delay_status", "fieldtype": "Data", "width": 100},
    ]


# ---------------------------------------------------------

def get_conditions(filters):
    conditions = " so.docstatus = 1 "

    if filters.get("company"):
        conditions += " AND so.company = %(company)s"

    if filters.get("customer"):
        conditions += " AND so.customer = %(customer)s"

    if filters.get("from_date"):
        conditions += " AND so.transaction_date >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " AND so.transaction_date <= %(to_date)s"

    if filters.get("item_code"):
        conditions += " AND soi.item_code = %(item_code)s"

    return conditions


# ---------------------------------------------------------

def get_data(filters):

    conditions = get_conditions(filters)

    data = frappe.db.sql(f"""
        SELECT
            so.company,
            so.customer,
            so.name AS sales_order,
            soi.item_code,
            soi.delivery_date AS committed_date,
            MAX(dn.posting_date) AS delivery_date,
            soi.qty AS ordered_qty,
            IFNULL(SUM(dni.qty), 0) AS delivered_qty

        FROM `tabSales Order` so
        JOIN `tabSales Order Item` soi
            ON soi.parent = so.name

        LEFT JOIN `tabDelivery Note Item` dni
            ON dni.against_sales_order = so.name
            AND dni.item_code = soi.item_code

        LEFT JOIN `tabDelivery Note` dn
            ON dn.name = dni.parent
            AND dn.docstatus = 1

        WHERE {conditions}

        GROUP BY so.name, soi.name
    """, filters, as_dict=1)

    final_data = []

    for row in data:

        delay_days = None
        delay_status = "Pending"

        if row.delivery_date and row.committed_date:
            delay_days = (getdate(row.delivery_date) - getdate(row.committed_date)).days

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
