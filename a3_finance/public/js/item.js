frappe.ui.form.on('Item', {
    onload: function(frm) {
        frm.set_query('asset_category', () => {
            return {
                filters: {
                    custom_is_group: 0
                }
            };
        });
    }
});
