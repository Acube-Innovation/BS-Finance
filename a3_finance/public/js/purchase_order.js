frappe.ui.form.on("Purchase Order", {
	onload(frm) {
		apply_purchase_order_date_restrictions(frm);
	},
	refresh(frm) {
		apply_purchase_order_date_restrictions(frm);
	},
});

function apply_purchase_order_date_restrictions(frm) {
	if (!frm.is_new()) {
		if (!frappe.user.has_role("Accounts Manager")) {
			frm.set_df_property("transaction_date", "read_only", 1);
			frm.set_df_property("schedule_date", "read_only", 1);
		}
	}
}
