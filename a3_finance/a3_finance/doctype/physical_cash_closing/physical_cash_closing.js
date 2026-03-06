// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Physical Cash Closing", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Cash Denomination Detail", {
    count: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.amount = row.denomination * row.count;
        frm.refresh_field("cash_denomination_detail");
        calculate_total(frm);
    },
    denomination: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.amount = row.denomination * row.count;
        frm.refresh_field("cash_denomination_detail");
        calculate_total(frm);
    }
});

function calculate_total(frm) {
    let total = 0;
    frm.doc.cash_denomination_detail.forEach(d => total += d.amount);
    frm.set_value("total_cash_counted", total);
}
