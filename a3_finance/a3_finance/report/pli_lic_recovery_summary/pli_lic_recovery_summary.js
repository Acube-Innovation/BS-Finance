// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["PLI-LIC Recovery Summary"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": "Month",
			"fieldtype": "Select",
			"options": ["01","02","03","04","05","06","07","08","09","10","11","12"],
			"default": "01"
		},
		{
			"fieldname": "year",
			"label": "Year",
			"fieldtype": "Int",
			"default": frappe.datetime.get_today().split("-")[0]	
		},
		{
			"fieldname": "type",
			"label": "Type",
			"fieldtype": "Select",
			"options": ["PLI Recovery","LIC Recovery"],
			"default": "PLI"
		}

	]
};
