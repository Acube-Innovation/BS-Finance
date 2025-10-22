// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Pay Sheet Deductions"] = {
    onload: function (report) {
        let today = frappe.datetime.get_today();
        let start = frappe.datetime.month_start(today);
        let end = frappe.datetime.month_end(today);

        report.set_filter_value("start_date", start);
        report.set_filter_value("end_date", end);
    },

    filters: [
        {
            fieldname: "start_date",
            label: "Start Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start(frappe.datetime.get_today()),
            onchange: function (val) {
                if (val) {
                    let start = new Date(val);
                    let end = new Date(start.getFullYear(), start.getMonth() + 1, 0);
                    frappe.query_report.set_filter_value("end_date", frappe.datetime.obj_to_str(end));
                }
            }
        },
        {
            fieldname: "end_date",
            label: "End Date",
            fieldtype: "Date",
            reqd: 1
        },
        {
            fieldname: "employment_subtype",
            label: "Employment Subtype",
            fieldtype: "Link",
            options: "Employment Sub Type"
        }
    ]
};

