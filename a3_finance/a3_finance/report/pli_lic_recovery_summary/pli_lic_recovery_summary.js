frappe.query_reports["PLI-LIC Recovery Summary"] = {

	onload: function (report) {

		report.page.add_inner_button("Print Report", function () {
			print_pli_lic_report(report);
		});

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
			fieldname: "type",
			label: "Type",
			fieldtype: "Select",
			options: ["PLI Recovery","LIC Recovery"],
			default: "PLI Recovery"
		},
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
			
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
		let company_name = filters.company || "";

		if (filters.company) {
			const res = await frappe.db.get_value("Company", filters.company, "company_name");
			const company = res.message || res;
			company_name = company.company_name || filters.company;
		}

		let prepared_by_name = "";

		if (filters.prepared_by) {
			const res = await frappe.db.get_value("Employee", filters.prepared_by, [
				"employee_name",
				"designation"
			]);

			const emp = res.message || res;

			if (emp) {
				prepared_by_name = emp.employee_name || filters.prepared_by;
				if (emp.designation) {
					prepared_by_name += " - " + emp.designation;
				}
			}
		}



		const month_names = [
			"January","February","March","April","May","June",
			"July","August","September","October","November","December"
		];

		let month_name = month_names[parseInt(filters.month) - 1];

		let html = `
<style>
@media print {
	table { border-collapse: collapse; width: 100%; font-size: 11px; }
	th, td { border: 1px solid #000; padding: 4px; }
	th { text-align: center; font-weight: bold; }
	td { text-align: left; }
	td.num { text-align: right; }
	tr.total-row { font-weight: bold; }
}
</style>

<div style="text-align:center; margin-bottom:15px;">
	<div style="font-size:18px; font-weight:bold;">
	${company_name}
</div>
 <div style="font-size:13px;">CHACKAI, BEACH.P.O., AIRPORT ROAD, THIRUVANANTHAPURAM</div>
<div style="font-size:16px; font-weight:bold; margin-top:4px;">
	${filters.type} Summary
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

			let is_total = row.employee_name === "Total";
			html += `<tr class="${is_total ? 'total-row' : ''}">`;

			columns.forEach(col => {

				// Hide Sl No for Total row
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

<div style="display:flex; justify-content:flex-start; margin-top:40px; font-size:11px;">
	<div style="text-align:left;">
		<b>Prepared By</b>
		<div style="height:50px;"></div>
		
		<div style="margin-top:4px;">${prepared_by_name}</div>
	</div>
</div>


`;

		return html;
	}
};


// ---------------- CUSTOM PRINT FUNCTION ----------------
async function print_pli_lic_report(report) {

	let html = await frappe.query_reports["PLI-LIC Recovery Summary"]
		.printable_html(report);

	let print_window = window.open("", "PRINT", "height=700,width=900");

	print_window.document.write(html);
	print_window.document.close();
	print_window.focus();
	print_window.print();
	print_window.close();
}
