frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        // Hide Applicable On fields by default
        frm.set_df_property('custom_applicable_on_cea', 'hidden', 1);
        frm.set_df_property('custom_applicable_on_vehicle', 'hidden', 1);

        // Store initial values to track actual changes
        frm._prev_cea = frm.doc.custom_no_of_children_eligible_for_cea;
        frm._prev_vehicle = frm.doc.custom_vehicle_type;
    },

    custom_no_of_children_eligible_for_cea: function(frm) {
        // Show Applicable On field and make it required
        frm.set_df_property('custom_applicable_on_cea', 'hidden', 0);
        frm.set_df_property('custom_applicable_on_cea', 'reqd', 1);
    },

    custom_vehicle_type: function(frm) {
        // Show Applicable On field and make it required
        frm.set_df_property('custom_applicable_on_vehicle', 'hidden', 0);
        frm.set_df_property('custom_applicable_on_vehicle', 'reqd', 1);
    },

    validate: function(frm) {
        // Validate Applicable On only if the field actually changed
        if (frm._prev_cea !== frm.doc.custom_no_of_children_eligible_for_cea) {
            if (!frm.doc.custom_applicable_on_cea) {
                frappe.throw(__('Please set Applicable On (CEA) when changing Children Eligible for CEA.'));
            }
        }

        if (frm._prev_vehicle !== frm.doc.custom_vehicle_type) {
            if (!frm.doc.custom_applicable_on_vehicle) {
                frappe.throw(__('Please set Applicable On (Vehicle) when changing Vehicle Type.'));
            }
        }
    },

    after_save: function(frm) {
        // Log CEA change if actually changed
        if (frm._prev_cea !== frm.doc.custom_no_of_children_eligible_for_cea) {
            frappe.call({
                method: "a3_finance.a3_finance.doc_events.employee.employee_details_change_log",
                args: {
                    employee: frm.doc.name,
                    employee_name: frm.doc.employee_name,
                    component_type: "No. of Children for Eligible CEA",
                    value: frm.doc.custom_no_of_children_eligible_for_cea,
                    effective_from: frm.doc.custom_applicable_on_cea
                }
            });
        }

        // Log Vehicle change if actually changed
        if (frm._prev_vehicle !== frm.doc.custom_vehicle_type) {
            frappe.call({
                method: "a3_finance.a3_finance.doc_events.employee.employee_details_change_log",
                args: {
                    employee: frm.doc.name,
                    employee_name: frm.doc.employee_name,
                    component_type: "Vehicle Type",
                    value: frm.doc.custom_vehicle_type,
                    effective_from: frm.doc.custom_applicable_on_vehicle
                }
            });
        }

        // Update previous values for next save
        frm._prev_cea = frm.doc.custom_no_of_children_eligible_for_cea;
        frm._prev_vehicle = frm.doc.custom_vehicle_type;
    }
});
