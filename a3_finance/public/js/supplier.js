frappe.ui.form.on('Supplier', {
    refresh(frm) {
        frm.set_df_property('custom_customer', 'only_select', true);

        frm.set_query('custom_customer', () => {
            if (!frm.doc.supplier_primary_address) {
                frappe.msgprint(__('Please select Supplier Primary Address first.'));
                return {
                    filters: {
                        name: '' // no customer has empty name, so nothing will show
                    }
                };
            }

            return {
                filters: {
                    customer_primary_address: frm.doc.supplier_primary_address
                }
            };
        });
    }
});
