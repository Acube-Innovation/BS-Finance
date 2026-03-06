// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["GRN Ageing Report"] = {
	
    filters: [
        {
            fieldname: "date",
            label: "Date",
            fieldtype: "Date"
        },
        {
            fieldname: "supplier",
            label: "Supplier",
            fieldtype: "Link",
            options: "Supplier"
        },
        {
            fieldname: "supplier_invoice_no",
            label: "Supplier Invoice No",
            fieldtype: "Data"
        },
        {
            fieldname: "purchase_invoice",
            label: "Purchase Invoice",
            fieldtype: "Link",
            options: "Purchase Invoice"
        },
		 {
            fieldname: "purchase_order",
            label: "Purchase Order",
            fieldtype: "Link",
            options: "Purchase Order"
        },
        {
            fieldname: "grn_number",
            label: "GRN Number",
            fieldtype: "Link",
            options: "Purchase Receipt"
        }
    ]
};