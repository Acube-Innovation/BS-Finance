// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Employee Reimbursement Wages", {
// 	refresh(frm) {

// 	},
// });
// frappe.ui.form.on('Employee Reimbursement Wages', {
//     reimbursement_date: function(frm) {
//         const cutoff = new Date('2025-01-01');
//         const reimbursement_date = frappe.datetime.str_to_obj(frm.doc.reimbursement_date);

//         if (reimbursement_date < cutoff) {
//             frm.set_value('reimbursement_basic_pay', '');
//         } else if (frm.doc.employee_id) {
//             // Fetch manually
//             frappe.db.get_value('Employee', frm.doc.employee_id, 'custom_basic_pay')
//                 .then(r => {
//                     if (r && r.message) {
//                         frm.set_value('reimbursement_basic_pay', r.message.custom_basic_pay);
//                     }
//                 });
//         }
//     }
// });

// frappe.ui.form.on('Employee Reimbursement Wages', {
//     reimbursement_date: function(frm) {
//         const cutoff = new Date('2025-01-01');
//         const reimbursement_date = frappe.datetime.str_to_obj(frm.doc.reimbursement_date);

//         if (!frm.doc.reimbursement_date || !frm.doc.employee_id) return;

//         if (reimbursement_date >= cutoff) {
//             // Step 1: Fetch Basic Pay
//             frappe.db.get_value('Employee', frm.doc.employee_id, 'custom_basic_pay')
//                 .then(r => {
//                     if (r && r.message && r.message.custom_basic_pay) {
//                         const basic_pay = parseFloat(r.message.custom_basic_pay);
//                         const service_weightage = parseFloat(frm.doc.reimbursement_service_weightage || 0);

//                         // Step 2: Fetch DA percent
//                         frappe.call({
//                             method: "frappe.client.get_value",
//                             args: {
//                                 doctype: "Dearness Allowance Backlog",
//                                 filters: {
//                                     payroll_start_date: ["<=", frm.doc.reimbursement_date],
//                                     payroll_end_date: [">=", frm.doc.reimbursement_date]
//                                 },
//                                 fieldname: "dearness_allowance_percent"
//                             },
//                             callback: function(response) {
//                                 if (response.message) {
//                                     const da_percent = parseFloat(response.message.dearness_allowance_percent || 0);
//                                     const da = (basic_pay + service_weightage) * (da_percent / 100);

//                                     frappe.msgprint(`🧮 Calculated DA (not saved): ₹${da.toFixed(2)} @ ${da_percent}%`);
//                                     console.log(`DA = (${basic_pay} + ${service_weightage}) * ${da_percent}% = ₹${da.toFixed(2)}`);
//                                 } else {
//                                     frappe.msgprint("❌ No matching DA percent found.");
//                                 }
//                             }
//                         });
//                     } else {
//                         frappe.msgprint("❌ Basic Pay not found for employee.");
//                     }
//                 });
//         } else {
//             frappe.msgprint("❌ No calculation: Date is before 01-Jan-2025.");
//         }
//     }
// });
