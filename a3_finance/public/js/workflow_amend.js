// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

// An amendment starts at the first state of its workflow (a3_finance.overrides.workflow_amend): Amend copies the cancelled
// document's state (Rejected ...), which a new document may not have; the form shows "Prepared By" before saving.
(() => {
	const DOCTYPES = ["Purchase Invoice", "Payment Entry", "Journal Entry"];

	const reset_state = (frm) => {
		if (!frm.is_new() || !frm.doc.amended_from) return;
		const field = frappe.workflow.get_state_fieldname(frm.doctype);
		const workflow = frappe.workflow.workflows[frm.doctype];
		const first_state = field && workflow && workflow.states && workflow.states.length && workflow.states[0].state;
		if (!first_state || frm.doc[field] === first_state) return;
		frm.doc[field] = first_state;
		frm.refresh_field(field);
		frm.states && frm.states.refresh();
	};

	for (const doctype of DOCTYPES) {
		frappe.ui.form.on(doctype, { onload: reset_state, refresh: reset_state });
	}
})();
