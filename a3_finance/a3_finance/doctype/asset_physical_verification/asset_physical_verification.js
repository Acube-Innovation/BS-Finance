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


frappe.ui.form.on('Asset Physical Verification', {
    get_assets: function (frm) {
        if (!frm.doc.location) {
            frappe.msgprint(__('Please select a Location first.'));
            return;
        }

        frappe.call({
            method: "a3_finance.a3_finance.doctype.asset_physical_verification.asset_physical_verification.get_assets_by_location",
            args: {
                location: frm.doc.location
            },
            callback: function (r) {
                if (r.message) {
                    frm.clear_table("asset");

                    (r.message || []).forEach(function (asset) {
                        let child = frm.add_child("asset");
                        child.asset = asset.name;
                        child.asset_category = asset.asset_category;
                        child.item_name = asset.item_name;
                        child.last_inspection_date = asset.custom_last_inspection_date;
                        child.status = asset.status;

                        // Set status based on asset status
                        // if (asset.status === "Scrapped") {
                        //     child.status = "Scrapped";
                        // } 
                        // else if (asset.status === "Out of Order"){
                        //     child.status = "Repaired";
                        // }
                        // else {
                        //     child.status = "Ok"; // For submitted or other valid assets
                        // }
                    });

                    

                    frm.refresh_field("asset");
                    // frappe.msgprint(__(`${r.message.length} asset(s) added.`));
                }
            }
        });
    }
});



