// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Report Of Wages to BATL Canteen Employees"] = {
	   "filters": [
        {
            "fieldname": "start_date",
            "label": "Start Date",
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -frappe.datetime.week_start()),
            "reqd": 1,
            "on_change": function(query_report) {
                let start_date = frappe.query_report.get_filter_value("start_date");
                if (start_date) {
                    let end_date = frappe.datetime.add_days(start_date, 6);
                    frappe.query_report.set_filter_value("end_date", end_date);
                }
            }
        },
        {
            "fieldname": "end_date",
            "label": "End Date",
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -frappe.datetime.week_start() + 6),
            "reqd": 1
        }
    ]
};
