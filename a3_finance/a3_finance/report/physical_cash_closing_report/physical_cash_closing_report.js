// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt


frappe.query_reports["Physical Cash Closing Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
        },
        {
            fieldname: "cashier",
            label: "Cashier",
            fieldtype: "Link",
            options: "Employee",
        },
        {
            fieldname: "cash_account",
            label: "Cash Account",
            fieldtype: "Link",
            options: "Account",
        },
    ]
};
