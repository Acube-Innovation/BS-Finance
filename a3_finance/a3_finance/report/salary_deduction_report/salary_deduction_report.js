// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

// frappe.query_reports["Salary Deduction Report"] = {
// 	"filters": [

// 	]
// };
frappe.query_reports["Salary Deduction Report"] = {
    "filters": [
        {
            "fieldname":"employee",
            "label": "Employee ID",
            "fieldtype": "Link",
            "options": "Employee"
        },
        {
            "fieldname":"employee_name",
            "label": "Name",
            "fieldtype": "Data"
        },
        {
            "fieldname":"department",
            "label": "Department",
            "fieldtype": "Link",
            "options": "Department"
        },
        {
            "fieldname":"status",
            "label": "Status",
            "fieldtype": "Select",
            "options": ["", "Draft", "Submitted", "Cancelled"]
        },
        {
            "fieldname":"from_date",
            "label": "From Date",
            "fieldtype": "Date"
        },
        {
            "fieldname":"to_date",
            "label": "To Date",
            "fieldtype": "Date"
        }
    ]
};
