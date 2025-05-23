frappe.ui.form.on('Asset Category', {
    onload: function(frm) {
        frm.set_query('custom_parent_asset_category', () => {
            return {
                filters: {
                    custom_is_group: 1
                }
            };
        });
    }
});
