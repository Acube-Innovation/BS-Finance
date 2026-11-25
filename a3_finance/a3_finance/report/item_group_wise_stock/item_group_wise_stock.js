// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

// Store -> Item Group -> item -> the item's transactions (open a row with its arrow)
frappe.query_reports["Item Group Wise Stock"] = {
	filters: [
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
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "item",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
			get_query: () => {
				const item_group = frappe.query_report.get_filter_value("item_group");
				const filters = { is_stock_item: 1 };
				if (item_group) filters.item_group = ["descendants of (inclusive)", item_group];
				return { filters: filters };
			},
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
	],
	initial_depth: 0,
	formatter(value, row, column, data, default_formatter) {
		// numeric cells the row has no value for stay empty (not 0.00)
		const numeric = ["Currency", "Float", "Int", "Percent"].includes(column.fieldtype);
		if (data && numeric && data[column.fieldname] == null) return "";
		value = default_formatter(value, row, column, data);
		if (!data) return value;
		if (column.fieldtype === "Float" && data.uom) {
			const unit = ` ${frappe.utils.escape_html(data.uom)}`;
			value = /<\/div>\s*$/.test(value) ? value.replace(/<\/div>\s*$/, `${unit}</div>`) : value + unit;
		}
		if (column.fieldname === "particulars" && data.voucher_no) {
			value = `<a href="${frappe.utils.get_form_link(data.voucher_type, data.voucher_no)}">${value}</a>`;
		}
		if (column.fieldname === "particulars" && data.item_code && data.item_code !== data.particulars) {
			value += ` <span class="text-muted">(${frappe.utils.escape_html(data.item_code)})</span>`;
		}
		return data.bold ? `<b>${value}</b>` : value;
	},
};
