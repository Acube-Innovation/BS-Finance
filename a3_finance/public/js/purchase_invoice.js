frappe.ui.form.on("Purchase Invoice", {
	onload(frm) {
		apply_purchase_invoice_date_restrictions(frm);
	},
	refresh(frm) {
		apply_purchase_invoice_date_restrictions(frm);
	},
});

function apply_purchase_invoice_date_restrictions(frm) {
	if (!frm.is_new() && frm.doc.docstatus === 0) {
		if (!frappe.user.has_role("Accounts Manager")) {
			frm.set_df_property("posting_date", "read_only", 1);
			frm.set_df_property("set_posting_time", "read_only", 1);
		}
	}
}
