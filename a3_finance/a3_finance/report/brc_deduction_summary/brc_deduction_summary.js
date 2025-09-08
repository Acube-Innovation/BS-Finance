// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["BRC Deduction Summary"] = {
	"filters": [
        {
            "fieldname": "month",
            "label": "Month",
            "fieldtype": "Select",
            "options": ["01","02","03","04","05","06","07","08","09","10","11","12"],
            "default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1
        },
        {
            "fieldname": "year",
            "label": "Year",
            "fieldtype": "Int",
            "default": frappe.datetime.get_today().split("-")[0]
        }
    ]
};
