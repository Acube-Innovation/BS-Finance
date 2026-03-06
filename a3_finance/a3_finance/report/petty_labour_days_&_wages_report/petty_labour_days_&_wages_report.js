// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Petty Labour Days & Wages Report"] = {
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
            fieldname: "petty_labour",
            label: "Labour",
            fieldtype: "Link",
            options: "Petty Labour Employees",
        },
        {
            fieldname: "contribution_type",
            label: "Contribution",
            fieldtype: "Select",
            options: "All\nESI\nPF",
            default: "All"
        }
    ]
};
