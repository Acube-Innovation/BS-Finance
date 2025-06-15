// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

// frappe.ui.form.on("LOP Upload", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('LOP Upload', {
    refresh(frm) {
        if (frm.doc.status == "Processed" && frm.doc.upload_file) {
            frm.add_custom_button('Add Leaves', () => {
                frappe.call({
                    method: 'a3_finance.a3_finance.doctype.lop_upload.lop_upload.create_leave_applications',
                    args: {
                        docname: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(__(r.message));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint('No response received.');
                        }
                    }
                });
            });
        }
    }
});

// frappe.ui.form.on('LOP Upload', {
//     refresh(frm) {
//         if (frm.doc.status === "Processed" && frm.doc.upload_file) {
//             let label = frm.doc.process_type === "Reimbursement" ? "Create Additional Salary" : "Add Leaves";

//             frm.add_custom_button(__(label), () => {
//                 let method = frm.doc.process_type === "Reimbursement"
//                     ? 'a3_finance.a3_finance.doctype.lop_upload.lop_upload.create_additional_salary'
//                     : 'a3_finance.a3_finance.doctype.lop_upload.lop_upload.create_leave_applications';

//                 frappe.call({
//                     method: method,
//                     args: {
//                         docname: frm.doc.name
//                     },
//                     callback: function (r) {
//                         if (r.message) {
//                             frappe.msgprint(__(r.message));
//                             frm.reload_doc();
//                         } else {
//                             frappe.msgprint(__('No response received.'));
//                         }
//                     }
//                 });
//             });
//         }
//     }
// });

// frappe.ui.form.on('LOP Upload', {
//     refresh(frm) {
//         if (frm.doc.status === "Processed" && frm.doc.upload_file) {
//             let label;
//             let method;

//             if (frm.doc.process_type === "Reimbursement") {
//                 label = "Create Additional Salary";
//                 method = "a3_finance.a3_finance.doctype.lop_upload.lop_upload.create_additional_salary";
//             } else if (frm.doc.process_type === "Time Loss") {
//                 label = "Create Additional Salary (Hours)";
//                 method = "a3_finance.a3_finance.doctype.lop_upload.lop_upload.create_additional_salary";
//             } else if (frm.doc.process_type === "Leave") {
//                 label = "Add Leaves";
//                 method = "a3_finance.a3_finance.doctype.lop_upload.lop_upload.create_leave_applications";
//             }

//             if (label && method) {
//                 frm.add_custom_button(__(label), () => {
//                     frappe.call({
//                         method: method,
//                         args: {
//                             docname: frm.doc.name
//                         },
//                         callback: function (r) {
//                             if (r.message) {
//                                 frappe.msgprint(__(r.message));
//                                 frm.reload_doc();
//                             } else {
//                                 frappe.msgprint(__('No response received.'));
//                             }
//                         }
//                     });
//                 });
//             }
//         }
//     }
// });
