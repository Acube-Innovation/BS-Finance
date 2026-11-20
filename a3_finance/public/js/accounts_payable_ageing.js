// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

// "GRN Date" in Ageing Based On of Accounts Payable and Accounts Payable Summary (a3_finance.overrides.accounts_payable_ageing).
// ERPNext's report script registers itself with frappe.query_reports["<report>"] = {...}; the option is added as it
// does, so ERPNext's own filters are used as they are and stay in step with its updates.
(() => {
	const REPORTS = ["Accounts Payable", "Accounts Payable Summary"];
	const OPTION = "GRN Date";

	const add_option = (settings) => {
		const filter = (settings && settings.filters || []).find((f) => f.fieldname === "ageing_based_on");
		if (!filter) return;
		const options = (filter.options || "").split("\n").filter(Boolean);
		if (!options.includes(OPTION)) filter.options = [...options, OPTION].join("\n");
	};

	frappe.provide("frappe.query_reports");
	for (const name of REPORTS) {
		let settings = frappe.query_reports[name];
		add_option(settings);
		Object.defineProperty(frappe.query_reports, name, {
			configurable: true,
			enumerable: true,
			get: () => settings,
			set: (value) => {
				add_option(value);
				settings = value;
			},
		});
	}
})();
