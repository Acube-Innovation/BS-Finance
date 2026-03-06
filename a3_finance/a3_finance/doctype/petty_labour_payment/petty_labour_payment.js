// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

frappe.ui.form.on("Petty Labour Payment", {
    supplier: function(frm) {
        frm.set_query("reference_document", function() {
            return {
                filters: {
                    supplier: frm.doc.supplier,
                    docstatus: 1,
                    outstanding_amount: [">", 0]
                }
            };
        });
    },

    refresh: function(frm) {
        frm.set_query("reference_document", function() {
            return {
                filters: {
                    supplier: frm.doc.supplier,
                    docstatus: 1,
                    outstanding_amount: [">", 0]
                }
            };
        });
    }
});


frappe.ui.form.on("Petty Labour Payment Details", {
    petty_labour: function(frm, cdt, cdn) {
        fetch_esi_pf_and_rates(frm, cdt, cdn);
    },
    days: function(frm, cdt, cdn) {
        calculate_row_amount(frm, cdt, cdn);
         calculate_contributions(frm, cdt, cdn);
    },
    wages: function(frm, cdt, cdn) {
        calculate_row_amount(frm, cdt, cdn);
         calculate_contributions(frm, cdt, cdn);
    },
    amount: function(frm, cdt, cdn) {
        calculate_contributions(frm, cdt, cdn);
    },
    esi: function(frm, cdt, cdn) {
        calculate_contributions(frm, cdt, cdn);
    },
    pf: function(frm, cdt, cdn) {
        calculate_contributions(frm, cdt, cdn);
    },
    petty_labour_payment_details_remove: function(frm) {
        calculate_total(frm);
    }
});

function calculate_row_amount(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const amount = (row.days || 0) * (row.wages || 0);

    frappe.model.set_value(cdt, cdn, "amount", amount);

    calculate_contributions(frm, cdt, cdn);
    calculate_total(frm);
}

function calculate_total(frm) {
    let total = 0;

    (frm.doc.payment_details || []).forEach(row => {
        total += row.amount || 0;
    });

    frm.set_value("total_amount", total);
}

async function fetch_esi_pf_and_rates(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row.petty_labour) return;

    try {
        const [emp, settings] = await Promise.all([
            frappe.db.get_doc("Petty Labour Employees", row.petty_labour),
            frappe.db.get_doc("Petty Labour Settings", "Petty Labour Settings")
        ]);

        let grid_row = frm.fields_dict.payment_details.grid.grid_rows_by_docname[cdn];

        let esi_enabled = !!emp.esi;
        let pf_enabled  = !!emp.pf;

        frappe.model.set_value(cdt, cdn, "esi", esi_enabled ? 1 : 0);
        frappe.model.set_value(cdt, cdn, "pf", pf_enabled ? 1 : 0);

        grid_row.toggle_editable("esi", esi_enabled);
        grid_row.toggle_editable("pf", pf_enabled);

        if (esi_enabled) {
            frappe.model.set_value(cdt, cdn, "employer_contribution_esi_", settings.employer_contribution_esi);
            frappe.model.set_value(cdt, cdn, "employee_contribution_esi_", settings.employee_contribution_esi);
        } else {
            frappe.model.set_value(cdt, cdn, "employer_contribution_esi_", 0);
            frappe.model.set_value(cdt, cdn, "employee_contribution_esi_", 0);
        }

        if (pf_enabled) {
            frappe.model.set_value(cdt, cdn, "employer_contribution_pf_", settings.employer_contribution_pf);
            frappe.model.set_value(cdt, cdn, "employee_contribution_pf_", settings.employee_contribution_pf);
            frappe.model.set_value(cdt, cdn, "pf_administrative_charges_", settings.pf_administrative_charges);
        } else {
            frappe.model.set_value(cdt, cdn, "employer_contribution_pf_", 0);
            frappe.model.set_value(cdt, cdn, "employee_contribution_pf_", 0);
            frappe.model.set_value(cdt, cdn, "pf_administrative_charges_", 0);
        }

        frm.refresh_field("petty_labour_payment_details");

        calculate_contributions(frm, cdt, cdn);

    } catch (error) {
        console.error("Error fetching ESI/PF data:", error);
    }
}

function calculate_contributions(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let amount = flt(row.amount);

    if (!amount) return;

    if (row.esi) {
        frappe.model.set_value(
            cdt, cdn,
            "employer_contribution_esi_amount",
            (amount * flt(row.employer_contribution_esi_)) / 100
        );

        frappe.model.set_value(
            cdt, cdn,
            "employee_contribution_esi_amount",
            (amount * flt(row.employee_contribution_esi_)) / 100
        );
    } else {
        frappe.model.set_value(cdt, cdn, "employer_contribution_esi_amount", 0);
        frappe.model.set_value(cdt, cdn, "employee_contribution_esi_amount", 0);
    }

    if (row.pf) {
        frappe.model.set_value(
            cdt, cdn,
            "employer_contribution_pf_amount",
            (amount * flt(row.employer_contribution_pf_)) / 100
        );

        frappe.model.set_value(
            cdt, cdn,
            "employee_contribution_pf_amount",
            (amount * flt(row.employee_contribution_pf_)) / 100
        );

        frappe.model.set_value(
            cdt, cdn,
            "pf_administrative_charges",
            (amount * flt(row.pf_administrative_charges_)) / 100
        );
    } else {
        frappe.model.set_value(cdt, cdn, "employer_contribution_pf_amount", 0);
        frappe.model.set_value(cdt, cdn, "employee_contribution_pf_amount", 0);
        frappe.model.set_value(cdt, cdn, "pf_administrative_charges", 0);
    }
}
