// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Item Group Wise Stock"] = {
    filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            reqd: 1
        },
        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company"
        }
    ]
};
