// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Asset Physical Verification", {
// 	refresh(frm) {

// 	},
// });

// frappe.ui.form.on('Asset Physical Verification', {
//     refresh: function (frm) {
//         if (!frm.is_new()) return;

//         frm.add_custom_button(__('Get Assets'), function () {
//             if (!frm.doc.location) {
//                 frappe.msgprint(__('Please select a Location first.'));
//                 return;
//             }

//             frappe.call({
//                 method: "a3_finance.a3_finance.doctype.asset_physical_verification.asset_physical_verification.get_assets_by_location",
//                 args: {
//                     location: frm.doc.location
//                 },
//                 callback: function (r) {
//                     if (r.message) {
//                         frm.clear_table("asset");

//                         (r.message || []).forEach(function (asset) {
//                             let child = frm.add_child("asset");
//                             child.asset = asset.name;
//                             child.asset_category = asset.asset_category;
//                             child.item_name = asset.item_name;
//                             child.last_inspection_date = asset.custom_last_inspection_date;
//                             // child.status = "Present";  // Default value
//                         });

//                         frm.refresh_field("asset");
//                         frappe.msgprint(__(`${r.message.length} asset(s) added.`));
//                     }
//                 }
//             });
//         });
//     }
// });


// frappe.ui.form.on('Asset Physical Verification', {
//     get_assets: function (frm) {
//         if (!frm.doc.location) {
//             // frappe.msgprint(__('Please select a Location first.'));
//             return;
//         }

//         frappe.call({
//             method: "a3_finance.a3_finance.doctype.asset_physical_verification.asset_physical_verification.get_assets_by_location",
//             args: {
//                 location: frm.doc.location
//             },
//             callback: function (r) {
//                 if (r.message) {
//                     frm.clear_table("asset");

//                     (r.message || []).forEach(function (asset) {
//                         let child = frm.add_child("asset");
//                         child.asset = asset.name;
//                         child.asset_category = asset.asset_category;
//                         child.item_name = asset.item_name;
//                         // child.last_inspection_date = asset.custom_last_inspection_date;
//                         child.status = asset.status;

//                         // Set status based on asset status
//                         // if (asset.status === "Scrapped") {
//                         //     child.status = "Scrapped";
//                         // } 
//                         // else if (asset.status === "Out of Order"){
//                         //     child.status = "Repaired";
//                         // }
//                         // else {
//                         //     child.status = "Ok"; // For submitted or other valid assets
//                         // }
//                     });

                    

//                     frm.refresh_field("asset");
//                     // frappe.msgprint(__(`${r.message.length} asset(s) added.`));
//                 }
//             }
//         });
//     }
// });


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
            // callback: function(r) {
            //     if (r.message) {
            //         frm.clear_table("asset");

            //         r.message.forEach(asset => {
            //             let row = frm.add_child("asset");
            //             row.asset = asset.name;
            //             row.asset_name = asset.asset_name;
            //             row.asset_category = asset.asset_category;
            //             row.item_name = asset.item_name;
            //             row.location = asset.location;
            //             row.last_inspection_date = asset.custom_last_inspection_date;
            //             row.shop = asset.shop;
            //             row.section = asset.section;
            //             row.floor = asset.floor;
            //             row.status = asset.status;
            //             // Add other fields if required
            //         });

            //         frm.refresh_field("asset");
            //     }
            // }
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



// frappe.ui.form.on('Asset Verification Item', {
//     new_status: function (frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         let grid_row = frm.fields_dict["asset"].grid.get_row(cdn);

//         if (row.new_status === "OK") {
//             grid_row.toggle_editable("last_inspection_date", true);
//         } else {
//             grid_row.toggle_editable("last_inspection_date", false);
//         }

//         // Refresh the grid row to apply changes
//         frm.fields_dict["asset"].grid.refresh_row(cdn);
//     }
// });

