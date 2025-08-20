// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.ui.form.on('Asset Physical Verification', {
    get_assets: function(frm) {
        // Check if at least one filter is selected
        if (!frm.doc.shop && !frm.doc.section && !frm.doc.floor && !frm.doc.location) {
            frappe.msgprint(__('Please select at least one filter: Shop, Section, Floor, or Location'));
            return;
        }
        frappe.call({
            method: 'a3_finance.a3_finance.doctype.asset_physical_verification.asset_physical_verification.get_filtered_assets',
            args: {
                shop: frm.doc.shop,
                section: frm.doc.section,
                floor: frm.doc.floor,
                location: frm.doc.location
            },
            callback: function(r) {
                frm.clear_table("asset");

                if (r.message && r.message.length > 0) {
                    r.message.forEach(asset => {
                        let row = frm.add_child("asset");
                        row.asset = asset.name;
                        row.asset_name = asset.asset_name;
                        row.asset_category = asset.asset_category;
                        row.item_name = asset.item_name;
                        row.location = asset.location;
                        row.last_inspection_date = asset.custom_last_inspection_date;
                        row.shop = asset.shop;
                        row.section = asset.section;
                        row.floor = asset.floor;
                        row.status = asset.status;
                        // Add other fields if required
                    });
                    frm.refresh_field("asset");
                } else {
                    frappe.msgprint(__('No assets found for the selected filters.'));
                }
            }
        });
    }
});


