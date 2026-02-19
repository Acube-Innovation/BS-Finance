// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Professional Tax Summary"] = {

	onload: function (report) {

		// ---- PRINT BUTTON ----
		report.page.add_inner_button("Print Report", function () {
			print_professional_tax_report(report);
		});

		// Hide Sl No column visually
		setTimeout(() => {
			const wrapper = report.page.wrapper;
			wrapper.find(".dt-header .dt-cell--col-0").hide();
			wrapper.find(".dt-body .dt-cell--col-0").hide();
		}, 300);
	},

	after_datatable_render: function (datatable) {
		datatable.columnmanager.columns[0].hidden = true;
		datatable.refresh();
	},

	filters: [
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company")
		},
		{
			fieldname: "month",
			label: "Month",
			fieldtype: "Select",
			options: ["01","02","03","04","05","06","07","08","09","10","11","12"],
			default: frappe.datetime.get_today().split("-")[1]
		},
		{
			fieldname: "year",
			label: "Year",
			fieldtype: "Int",
			default: frappe.datetime.get_today().split("-")[0]
		},
		{
			fieldname: "prepared_by",
			label: "Prepared By",
			fieldtype: "Link",
			options: "Employee"
		}
	],

	// ---------------- PRINTABLE HTML ----------------
	printable_html: async function (report) {

		let filters = frappe.query_report.get_filter_values();
		let data = report.data || [];
		let columns = report.columns || [];

		const month_names = [
			"January","February","March","April","May","June",
			"July","August","September","October","November","December"
		];

		let month_name = month_names[parseInt(filters.month) - 1];
		let company_name = filters.company || "All Companies";
		let prepared_by = filters.prepared_by || "";
		let prepared_by_name = prepared_by;
		let prepared_by_designation = "";

		if (prepared_by) {
			const emp_details = await frappe.db.get_value(
				"Employee",
				prepared_by,
				["employee_name", "designation"]
			);
			prepared_by_name = emp_details?.message?.employee_name || prepared_by;
			prepared_by_designation = emp_details?.message?.designation || "";
		}

		let html = `
<style>
@page {
	margin: 10mm;
}

@media print {
	body {
		margin: 0;
	}

	table {
		border-collapse: collapse;
		width: 99%;
		font-size: 11px;
	}

	th, td {
		border: 1px solid #000;
		padding: 4px;
		box-sizing: border-box;
	}

	th {
		text-align: center;
		font-weight: bold;
	}

	td {
		text-align: left;
	}

	td.num {
		text-align: right;
	}

	tr.total-row {
		font-weight: bold;
	}
}
</style>

<div style="text-align:center; margin-bottom:15px;">
<div style="font-size:18px; font-weight:bold;">
    ${company_name}
</div>

<div style="font-size:13px;">CHACKAI, BEACH.P.O., AIRPORT ROAD, THIRUVANANTHAPURAM</div>
	<div style="font-size:18px; font-weight:bold;">
		Professional Tax Summary
	</div>
	<div style="font-size:14px; margin-top:4px;">
		
		Month: <b>${month_name}</b> &nbsp; | &nbsp;
		Year: <b>${filters.year}</b>
	</div>
</div>

<table>
	<thead>
		<tr>
`;

		columns.forEach(col => {
			html += `<th>${col.label}</th>`;
		});

		html += `</tr></thead><tbody>`;

		data.forEach(row => {

			let is_total = row.ec === "Total";
			html += `<tr class="${is_total ? 'total-row' : ''}">`;

			columns.forEach(col => {

				// Hide Sl No value for Total row
				if (col.fieldname === "sl_no" && is_total) {
					html += `<td></td>`;
					return;
				}

				let value = row[col.fieldname] ?? "";
				let cls = col.fieldtype === "Currency" ? "num" : "";

				html += `<td class="${cls}">
					${frappe.format(value, col)}
				</td>`;
			});

			html += `</tr>`;
		});

		html += `
	</tbody>
</table>

<div style="margin-top:35px; width:280px;">
	<div style="font-size:11px; font-weight:bold; margin-bottom:6px;">Prepared By</div>
	<div style="height:50px;"></div>
	
		<div><b>${prepared_by_name}</b></div>
		<div>${prepared_by_designation}</div>
	</div>
</div>




`;

		return html;
	}
};


// ---------------- CUSTOM PRINT FUNCTION ----------------
async function print_professional_tax_report(report) {

	let html = await frappe.query_reports["Professional Tax Summary"]
		.printable_html(report);

	let print_window = window.open("", "PRINT", "height=700,width=900");

	print_window.document.write(html);
	print_window.document.close();
	print_window.focus();
	print_window.print();
	print_window.close();
}
