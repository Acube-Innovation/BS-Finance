// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["PLI-LIC Recovery Summary"] = {

after_datatable_render: function (datatable) {

		// Hide default row index column (index = 0)
		datatable.columnmanager.columns[0].hidden = true;

		// Re-render datatable to apply change
		datatable.refresh();
	},

	onload: function (report) {
		setTimeout(() => {
			const wrapper = report.page.wrapper;

			// Hide header cell of default row index
			wrapper.find(".dt-header .dt-cell--col-0").hide();

			// Hide body cells of default row index
			wrapper.find(".dt-body .dt-cell--col-0").hide();
		}, 300);
	},
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
