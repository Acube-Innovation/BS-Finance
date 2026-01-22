frappe.query_reports["TDS Statement"] = {

	filters: [
		{
			fieldname: "month",
			label: "Month",
			fieldtype: "Select",
			options: ["01","02","03","04","05","06","07","08","09","10","11","12"],
			default: "01"
		},
		{
			fieldname: "year",
			label: "Year",
			fieldtype: "Int",
			default: frappe.datetime.get_today().split("-")[0]
		}
	],

	onload: function (report) {

		// ---------------- ADD PRINT BUTTON ----------------
		report.page.add_inner_button("Print Report", function () {
			print_tds_report(report);
		});

		// ---------------- UI TITLE ----------------
		setTimeout(() => {
			update_ui_title(report);

			report.page.wrapper
				.find(".filter-area input, .filter-area select")
				.on("change", () => update_ui_title(report));
		}, 200);
	}
};


// --------------------------------------------------
// UPDATE SCREEN TITLE
// --------------------------------------------------
function update_ui_title(report) {
	const values = report.get_values();
	if (!values?.month || !values?.year) return;

	const subtitle = `For the Month of ${get_month_name(values.month)} ${values.year}`;

	if (report.page?.set_title) {
		report.page.set_title("TDS Statement", subtitle);
	}
}


// --------------------------------------------------
// PRINTABLE HTML
// --------------------------------------------------
frappe.query_reports["TDS Statement"].printable_html = async function (report) {

	let filters = report.get_values();
	let data = report.data || [];
	let columns = report.columns || [];

	let month_name = get_month_name(filters.month);

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
	<div style="font-size:18px; font-weight:bold;">TDS Statement</div>
	<div style="font-size:14px;">
		For the Month of <b>${month_name} ${filters.year}</b>
	</div>
</div>

<table>
<thead><tr>
`;

	columns.forEach(col => {
		html += `<th>${col.label}</th>`;
	});

	html += `</tr></thead><tbody>`;

	data.forEach(row => {

		let is_total = row.employee_name === "Total";
		html += `<tr class="${is_total ? 'total-row' : ''}">`;

		columns.forEach(col => {

			// 🔴 Hide Sl No for Total row
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

<p style="text-align:right; margin-top:25px; font-size:9px;">
	Printed on ${frappe.datetime.str_to_user(
		frappe.datetime.get_datetime_as_string()
	)}
</p>
`;

	return html;
};


// --------------------------------------------------
// PRINT FUNCTION
// --------------------------------------------------
async function print_tds_report(report) {

	let html = await frappe.query_reports["TDS Statement"]
		.printable_html(report);

	let print_window = window.open("", "PRINT", "height=700,width=900");

	print_window.document.write(html);
	print_window.document.close();
	print_window.focus();
	print_window.print();
	print_window.close();
}


// --------------------------------------------------
// MONTH NAME HELPER
// --------------------------------------------------
function get_month_name(month) {
	const month_map = {
		"01": "January", "02": "February", "03": "March",
		"04": "April", "05": "May", "06": "June",
		"07": "July", "08": "August", "09": "September",
		"10": "October", "11": "November", "12": "December"
	};
	return month_map[month];
}
