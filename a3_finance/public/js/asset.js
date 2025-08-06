frappe.ui.form.on('Asset', {
    refresh: function(frm) {
        if (frm.doc.location) {
            frappe.db.get_doc('Location', frm.doc.location)
                .then(location_doc => {
                    frm.set_value('custom_shop', location_doc.custom_shop);
                    frm.set_value('custom_section', location_doc.custom_section);
                    frm.set_value('custom_floor', location_doc.custom_floor);
                });
        }
    },
    location: function(frm) {
        if (frm.doc.location) {
            frappe.db.get_doc('Location', frm.doc.location)
                .then(location_doc => {
                    frm.set_value('custom_shop', location_doc.custom_shop);
                    frm.set_value('custom_section', location_doc.custom_section);
                    frm.set_value('custom_floor', location_doc.custom_floor);
                });
        }
    }
});