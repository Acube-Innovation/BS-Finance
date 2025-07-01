// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.ui.form.on('In-Principle Request', {
    refresh: function(frm) {
        // Show the button only when the document is submitted
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Indent'), function() {
                frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
                            doctype: 'Indent'
                        }
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.set_route('Form', 'Material Request', r.message.name);
                        }
                    }
                });
            }, __('Create'));
        }
    }
});
