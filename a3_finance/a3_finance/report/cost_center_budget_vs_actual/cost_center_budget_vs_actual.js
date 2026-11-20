// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

// Cost Center Budget vs Actual (BrahMos tracker point 26): Cost Center → Account → Voucher, every amount opens the
// General Ledger of that cost center, account(s) and period.
frappe.query_reports["Cost Center Budget vs Actual"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
			reqd: 1,
			on_change: (report) => {
				const fiscal_year = report.get_filter_value("fiscal_year");
				if (!fiscal_year) return;
				frappe.db
					.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"])
					.then(({ message }) => {
						if (!message) return;
						const today = frappe.datetime.get_today();
						report.set_filter_value({
							from_date: message.year_start_date,
							to_date: today < message.year_end_date && today > message.year_start_date
								? today
								: message.year_end_date,
						});
					});
			},
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "MultiSelectList",
			get_data: (txt) =>
				frappe.xcall(
					"a3_finance.a3_finance.report.cost_center_budget_vs_actual.cost_center_budget_vs_actual.get_cost_center_options",
					{ txt, company: frappe.query_report.get_filter_value("company") }
				),
		},
		{
			fieldname: "account",
			label: __("Account"),
			fieldtype: "Link",
			options: "Account",
			get_query: () => ({
				filters: {
					company: frappe.query_report.get_filter_value("company"),
					report_type: "Profit and Loss",
				},
			}),
		},
		{
			fieldname: "budgeted_only",
			label: __("Budgeted accounts only"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_vouchers",
			label: __("Show Vouchers"),
			fieldtype: "Check",
		},
	],

	tree: true,
	initial_depth: 1,

	formatter(value, row, column, data, default_formatter) {
		let html = default_formatter(value, row, column, data);
		if (!data) return html;
		const amount_fields = ["annual_budget", "budget_to_date", "actual", "variance", "balance"];
		if (["variance", "balance"].includes(column.fieldname) && data[column.fieldname] < 0) {
			html = `<span style="color: var(--red-500)">${html}</span>`;
		}
		if (column.fieldname === "utilised" && data.utilised > 100) {
			html = `<span style="color: var(--red-500)">${html}</span>`;
		}
		// amounts of cost center and account rows open the General Ledger
		if (amount_fields.includes(column.fieldname) && data.cost_center && data.indent < 2) {
			html = `<a class="a3-cc-drill" data-cost-center="${encodeURIComponent(data.cost_center)}"
				data-account="${encodeURIComponent(data.account || "")}"
				title="${__("Open the General Ledger")}">${html}</a>`;
		}
		if (data.indent === 0) html = `<b>${html}</b>`;
		return html;
	},

	onload(report) {
		$(report.page.wrapper).on("click", ".a3-cc-drill", function (e) {
			e.preventDefault();
			const cost_center = decodeURIComponent($(this).attr("data-cost-center"));
			let account = decodeURIComponent($(this).attr("data-account"));
			let accounts = account ? [account] : [];
			if (!account) {
				// a cost center row: the accounts listed under it
				accounts = (report.data || [])
					.filter((row) => row.indent === 1 && row.cost_center === cost_center && row.account)
					.map((row) => row.account);
			}
			frappe.route_options = {
				company: report.get_filter_value("company"),
				from_date: report.get_filter_value("from_date"),
				to_date: report.get_filter_value("to_date"),
				account: accounts,
				cost_center: [cost_center],
				group_by: "Group by Voucher (Consolidated)",
			};
			frappe.set_route("query-report", "General Ledger");
		});
	},
};
