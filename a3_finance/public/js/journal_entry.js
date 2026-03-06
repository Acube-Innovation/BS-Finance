frappe.ui.form.on("Journal Entry Account", {
	party: set_party_name,
	party_type: set_party_name,
	form_render: set_party_name   // triggers when row opens
});

function set_party_name(frm, cdt, cdn) {
	const row = locals[cdt][cdn];

	// Clear if no party
	if (!row.party) {
		frappe.model.set_value(cdt, cdn, "custom_party_name", "");
		return;
	}

	// Only for Employee
	if (row.party_type === "Employee") {
		frappe.db.get_value("Employee", row.party, "employee_name")
			.then(r => {
				frappe.model.set_value(
					cdt,
					cdn,
					"custom_party_name",
					r?.message?.employee_name || ""
				);
			});
	} else {
		frappe.model.set_value(cdt, cdn, "custom_party_name", "");
	}
}
