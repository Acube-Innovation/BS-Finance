frappe.ui.form.on('Supplier', {
    refresh(frm) {
        // 1️⃣ Hide “Create New” and “Advanced Search” for this link field
        frm.set_df_property('custom_customer', 'only_select', true); 
        // (this removes the + and the “Advanced” option) :contentReference[oaicite:0]{index=0}

        // 2️⃣ Only list Customers whose primary address matches the Supplier’s
        frm.set_query('custom_customer', () => {
            return {
                filters: {
                    customer_primary_address: frm.doc.supplier_primary_address || ''
                }
            };
        });
    }
});
