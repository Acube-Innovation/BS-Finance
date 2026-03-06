# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        "Posting Date:Date:110",
        "Cashier:Data:150",
        "Cash Account:Link/Account:180",
        "Denomination:Data:100",
        "Count:Int:80",
        "Amount:Currency:120",
        "System Balance:Currency:140",
        "Difference:Currency:120",
    ]



def get_data(filters):
    conditions = ""
    values = {}

    if filters.get("from_date"):
        conditions += " AND p.posting_date >= %(from_date)s"
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions += " AND p.posting_date <= %(to_date)s"
        values["to_date"] = filters["to_date"]

    if filters.get("cashier"):
        conditions += " AND p.cashier = %(cashier)s"
        values["cashier"] = filters["cashier"]

    if filters.get("cash_account"):
        conditions += " AND p.cash_account = %(cash_account)s"
        values["cash_account"] = filters["cash_account"]

    data = frappe.db.sql(f"""
        SELECT
            p.posting_date,
            p.cashier,
            p.cash_account,
            d.denomination,
            d.count,
            d.amount,
            p.system_balance,
            p.difference
        FROM `tabPhysical Cash Closing` p
        JOIN `tabCash Denomination Detail` d
            ON d.parent = p.name
        WHERE p.docstatus = 1
        {conditions}
        ORDER BY p.posting_date DESC, d.denomination DESC
    """, values, as_dict=True)

    return data
