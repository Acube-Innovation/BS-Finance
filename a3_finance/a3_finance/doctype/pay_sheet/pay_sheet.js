// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt


frappe.ui.form.on('Pay Sheet', {
    refresh: function(frm) {
        // Show button only after verification
    
            frm.add_custom_button(__('Preview Report'), function() {
                let report_name = "Pay Sheet"; // Your existing report name
                let filters = {
                    "start_date": frm.doc.start_date,
                    "end_date": frm.doc.end_date,
                    "employment_subtype":frm.doc.employment_subtype,
                    "company":frm.doc.company,
                    "prepared_by":frm.doc.prepared_by,
                    "checked_by":frm.doc.checked_by,
                    "verified_by":frm.doc.verified_by,
                    "approved_by":frm.doc.approved_by,

                };

                // Redirect to the report with filters
                frappe.set_route('query-report', report_name, filters);
            });
        
    }
});
