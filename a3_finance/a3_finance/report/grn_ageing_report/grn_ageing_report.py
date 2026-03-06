import frappe

def execute(filters=None):

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():

    return [

        {"label": "GRN Number", "fieldname": "grn_number", "fieldtype": "Link", "options": "Purchase Receipt", "width": 160},
        {"label": "GRN Date", "fieldname": "grn_date", "fieldtype": "Date", "width": 120},

        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 200},

        {"label": "PO ID", "fieldname": "po_id", "fieldtype": "Link", "options": "Purchase Order", "width": 160},
        {"label": "PO Date", "fieldname": "po_date", "fieldtype": "Date", "width": 120},
        {"label": "PO Schedule Date", "fieldname": "po_schedule_date", "fieldtype": "Date", "width": 140},

      

        {"label": "Purchase Invoice", "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 180},
        {"label": "Invoice Date", "fieldname": "invoice_date", "fieldtype": "Date", "width": 120},

        {"label": "Supplier Invoice No", "fieldname": "supplier_invoice_no", "fieldtype": "Data", "width": 160},
        {"label": "Supplier Invoice Date", "fieldname": "supplier_invoice_date", "fieldtype": "Date", "width": 150},
          {"label": "PO Delay ", "fieldname": "po_delay", "fieldtype": "Int", "width": 180},

        {"label": "Delay after Received", "fieldname": "delay_after_received", "fieldtype": "Int", "width": 170},
        {"label": "Delay after Supplier Invoiced", "fieldname": "delay_supplier_invoice", "fieldtype": "Int", "width": 200},
        {"label": "Delay after Invoiced", "fieldname": "delay_after_invoice", "fieldtype": "Int", "width": 180}

    ]


def get_conditions(filters):

    conditions = ""

    if filters.get("supplier"):
        conditions += " AND pr.supplier = %(supplier)s"

    if filters.get("grn_number"):
        conditions += " AND pr.name = %(grn_number)s"

    if filters.get("purchase_invoice"):
        conditions += " AND pi.name = %(purchase_invoice)s"

    if filters.get("supplier_invoice_no"):
        conditions += " AND pi.bill_no = %(supplier_invoice_no)s"

    if filters.get("date"):
        conditions += " AND pr.posting_date <= %(date)s"

    return conditions


def get_data(filters):

    conditions = get_conditions(filters)

    return frappe.db.sql(f"""

        SELECT

            pr.name AS grn_number,
            pr.posting_date AS grn_date,
            pr.supplier,

            poi.parent AS po_id,
            po.transaction_date AS po_date,
            poi.schedule_date AS po_schedule_date,

            DATEDIFF(pr.posting_date, poi.schedule_date) AS po_delay,

            pi.name AS purchase_invoice,
            pi.posting_date AS invoice_date,
            pi.bill_no AS supplier_invoice_no,
            pi.bill_date AS supplier_invoice_date,

            DATEDIFF(%(date)s, pr.posting_date) AS delay_after_received,
            DATEDIFF(%(date)s, pi.bill_date) AS delay_supplier_invoice,
            DATEDIFF(%(date)s, pi.posting_date) AS delay_after_invoice

        FROM
            `tabPurchase Receipt` pr

        LEFT JOIN
            `tabPurchase Receipt Item` pri
            ON pri.parent = pr.name

        LEFT JOIN
            `tabPurchase Order Item` poi
            ON poi.name = pri.purchase_order_item

        LEFT JOIN
            `tabPurchase Order` po
            ON po.name = poi.parent

        LEFT JOIN
            `tabPurchase Invoice Item` pii
            ON pii.purchase_receipt = pr.name

        LEFT JOIN
            `tabPurchase Invoice` pi
            ON pi.name = pii.parent

        WHERE
            pr.docstatus = 1
            {conditions}

        ORDER BY
            pr.posting_date DESC

    """, filters, as_dict=1)
