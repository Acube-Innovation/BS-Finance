// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

// Trial Balance: every group account in bold, on screen and in Print / PDF (BrahMos tracker point 27).
// ERPNext's formatter (erpnext.financial_statements.formatter) bolds only the top-level heads - the rows without a
// parent account - and the total. A group account is a row that other rows have as their parent account; those rows
// are bolded too, after ERPNext's own formatting, which is kept as it is. ledgers stay normal weight.
// The Excel export bolds the same rows (a3_finance.overrides.report_export).
(() => {
	const REPORT = "Trial Balance";
	const FLAG = "a3_is_group";
	// ERPNext's print template (accounts/report/financial_statements.html) bolds a row with this class when it has no
	// parent account; group rows get the class too. If ERPNext changes the line, the print falls back to its own bold.
	const PRINT_ROW_CLASS =
		'var row_class = data[j].parent_account || data[j].parent_section ? "" : "financial-statements-important";';
	const PRINT_ROW_CLASS_GROUPS = `var row_class = (data[j].parent_account || data[j].parent_section) && !data[j].${FLAG} ? "" : "financial-statements-important";`;

	let flagged_data = null;

	// marks the group rows of the report's data (once per run of the report)
	const flag_groups = (data) => {
		if (!Array.isArray(data) || data === flagged_data) return;
		const parents = new Set(data.map((row) => row && row.parent_account).filter(Boolean));
		for (const row of data) {
			if (row && row.account) row[FLAG] = parents.has(row.account) ? 1 : 0;
		}
		flagged_data = data;
	};

	const extend = (settings) => {
		if (!settings) return;
		if (!settings.__a3_bold_groups && typeof settings.formatter === "function") {
			const formatter = settings.formatter;
			settings.formatter = function (value, row, column, data, default_formatter, filter) {
				let html = formatter.apply(this, arguments);
				// top-level heads and the total are bold already
				if (data && data.account && data.parent_account) {
					flag_groups(frappe.query_report && frappe.query_report.data);
					if (data[FLAG]) html = `<span style="font-weight: bold">${html}</span>`;
				}
				return html;
			};
			settings.__a3_bold_groups = true;
		}
		if (settings.html_format && !settings.html_format.includes(FLAG)) {
			settings.html_format = settings.html_format.replace(PRINT_ROW_CLASS, PRINT_ROW_CLASS_GROUPS);
		}
	};

	frappe.provide("frappe.query_reports");
	let settings = frappe.query_reports[REPORT];
	extend(settings);
	Object.defineProperty(frappe.query_reports, REPORT, {
		configurable: true,
		enumerable: true,
		get: () => settings,
		set: (value) => {
			// set by the report's script, and again by the report view once the print template is loaded
			extend(value);
			settings = value;
		},
	});
})();
