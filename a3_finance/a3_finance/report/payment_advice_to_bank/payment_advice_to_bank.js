// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Payment Advice To Bank"] = {
    "filters": [
        {
            fieldname: "payroll_month",
            label: "Payroll Month",
            fieldtype: "Select",
            options: [
                { "label": "January", "value": 1 },
                { "label": "February", "value": 2 },
                { "label": "March", "value": 3 },
                { "label": "April", "value": 4 },
                { "label": "May", "value": 5 },
                { "label": "June", "value": 6 },
                { "label": "July", "value": 7 },
                { "label": "August", "value": 8 },
                { "label": "September", "value": 9 },
                { "label": "October", "value": 10 },
                { "label": "November", "value": 11 },
                { "label": "December", "value": 12 }
            ],
            default: (function () {
                let d = new Date();
                return d.getMonth() === 0 ? 12 : d.getMonth(); // previous month
            })()
        },
        {
            fieldname: "payroll_year",
            label: "Payroll Year",
            fieldtype: "Data",
            default: new Date().getFullYear().toString()
        },
        {
            fieldname: "employment_type",
            label: "Employment Type",
            fieldtype: "Select",
            options: [
                { "label": "", "value": "" },
                { "label": "Regular Employees", "value": "Regular Employees" },
                { "label": "Apprentice", "value": "Apprentice" },
                { "label": "Canteen Employee", "value": "Canteen Employee" }
            ],
        }
    ]
};
