// frappe.ui.form.on('Arrear Breakup Log', {
//     employee: function(frm) {
//         if (!frm.doc.employee) return;

//         // 1️⃣ Filter Salary Structure Assignment
//         frm.set_query('salary_structure_assignment', function() {
//             return {
//                 filters: {
//                     employee: frm.doc.employee,
//                     custom_inactive: 0,
//                     from_date: ['>=', frm.doc.effective_from || frappe.datetime.get_today()]
//                 }
//             };
//         });

//         // Auto-fetch latest SSA
//         frappe.db.get_list('Salary Structure Assignment', {
//             filters: {
//                 employee: frm.doc.employee,
//                 custom_inactive: 0,
//                 from_date: ['>=', frm.doc.effective_from || frappe.datetime.get_today()]
//             },
//             order_by: 'from_date desc',
//             limit: 1,
//             fields: ['name', 'salary_structure']
//         }).then(assignments => {
//             if (assignments.length > 0) {
//                 const ssa = assignments[0];
//                 frm.set_value('salary_structure_assignment', ssa.name);
//                 frm.set_value('salary_structure', ssa.salary_structure);
//             } else {
//                 frm.set_value('salary_structure_assignment', '');
//                 frm.set_value('salary_structure', '');
//             }
//         });

//         // 2️⃣ Salary Slip filter (employee + effective_from inside slip range)
//         frm.set_query('salary_slip', () => {
//             if (!frm.doc.employee || !frm.doc.effective_from) return {};
//             return {
//                 filters: [
//                     ["Salary Slip", "employee", "=", frm.doc.employee],
//                     ["Salary Slip", "start_date", "<=", frm.doc.effective_from],
//                     ["Salary Slip", "end_date", ">=", frm.doc.effective_from]
//                 ]
//             };
//         });
//     },

//     effective_from: function(frm) {
//         // Refresh filters when effective_from changes
//         frm.trigger('employee');
//         frm.set_value('salary_slip', ''); // reset slip to avoid mismatch
//     },

//     salary_slip: function(frm) {
//         // Validate Salary Slip selection belongs to correct employee & date range
//         if (frm.doc.salary_slip && frm.doc.employee && frm.doc.effective_from) {
//             frappe.db.get_value('Salary Slip', frm.doc.salary_slip, ['employee', 'start_date', 'end_date'])
//                 .then(r => {
//                     if (r && r.message) {
//                         const slip = r.message;
//                         if (
//                             slip.employee !== frm.doc.employee ||
//                             frappe.datetime.str_to_obj(frm.doc.effective_from) < frappe.datetime.str_to_obj(slip.start_date) ||
//                             frappe.datetime.str_to_obj(frm.doc.effective_from) > frappe.datetime.str_to_obj(slip.end_date)
//                         ) {
//                             frappe.msgprint('Selected Salary Slip does not match Employee or Effective From date range.');
//                             frm.set_value('salary_slip', '');
//                         }
//                     }
//                 });
//         }
//     }
// });
// frappe.ui.form.on('Arrear Breakup Log', {
//     onload: function(frm) {
//         // If values are pre-set (from SSA submit), trigger employee logic
//         if(frm.doc.employee && frm.doc.effective_from) {
//             frm.trigger('employee');
//         }
//     },

//     employee: function(frm) {
//         if (!frm.doc.employee) return;

//         // Always reset SSA and Salary Slip to avoid mismatch
//         frm.set_value('salary_structure_assignment', '');
//         frm.set_value('salary_structure', '');
//         frm.set_value('salary_slip', '');

//         // 1️⃣ Filter Salary Structure Assignment
//         frm.set_query('salary_structure_assignment', function() {
//             return {
//                 filters: {
//                     employee: frm.doc.employee,
//                     custom_inactive: 0,
//                     from_date: ['>=', frm.doc.effective_from || frappe.datetime.get_today()]
//                 }
//             };
//         });

//         // Auto-fetch latest SSA
//         frappe.db.get_list('Salary Structure Assignment', {
//             filters: {
//                 employee: frm.doc.employee,
//                 custom_inactive: 0,
//                 from_date: ['>=', frm.doc.effective_from || frappe.datetime.get_today()]
//             },
//             order_by: 'from_date desc',
//             limit: 1,
//             fields: ['name', 'salary_structure']
//         }).then(assignments => {
//             if (assignments.length > 0) {
//                 const ssa = assignments[0];
//                 frm.set_value('salary_structure_assignment', ssa.name);
//                 frm.set_value('salary_structure', ssa.salary_structure);
//             }
//         });

//         // 2️⃣ Salary Slip filter (employee + effective_from inside slip range)
//         frm.set_query('salary_slip', () => {
//             if (!frm.doc.employee || !frm.doc.effective_from) return {};
//             return {
//                 filters: [
//                     ["Salary Slip", "employee", "=", frm.doc.employee],
//                     ["Salary Slip", "start_date", "<=", frm.doc.effective_from],
//                     ["Salary Slip", "end_date", ">=", frm.doc.effective_from]
//                 ]
//             };
//         });
//     },

//     effective_from: function(frm) {
//         // Re-run employee logic to refresh SSA and Salary Slip filters
//         if(frm.doc.employee) {
//             frm.trigger('employee');
//         }
//     },

//     salary_slip: function(frm) {
//         // Validate Salary Slip selection belongs to correct employee & date range
//         if (frm.doc.salary_slip && frm.doc.employee && frm.doc.effective_from) {
//             frappe.db.get_value('Salary Slip', frm.doc.salary_slip, ['employee', 'start_date', 'end_date'])
//                 .then(r => {
//                     if (r && r.message) {
//                         const slip = r.message;
//                         if (
//                             slip.employee !== frm.doc.employee ||
//                             frappe.datetime.str_to_obj(frm.doc.effective_from) < frappe.datetime.str_to_obj(slip.start_date) ||
//                             frappe.datetime.str_to_obj(frm.doc.effective_from) > frappe.datetime.str_to_obj(slip.end_date)
//                         ) {
//                             frappe.msgprint('Selected Salary Slip does not match Employee or Effective From date range.');
//                             frm.set_value('salary_slip', '');
//                         }
//                     }
//                 });
//         }
//     }
// });



frappe.ui.form.on('Arrear Breakup Log', {
    onload: function(frm) {
        // If values are pre-set, fetch details from server
        if (frm.doc.employee && frm.doc.effective_from && frm.new()) {
            frm.trigger('fetch_employee_details');
        }
    },

    employee: function(frm) {
        if(frm.doc.employee && frm.doc.effective_from) {
            frm.trigger('fetch_employee_details');
        }
    },

    effective_from: function(frm) {
        if(frm.doc.employee && frm.doc.effective_from) {
            frm.trigger('fetch_employee_details');
        }
    },

    fetch_employee_details: function(frm) {
        if (!frm.doc.employee || !frm.doc.effective_from) return;

        // Reset dependent fields first
        frm.set_value('salary_structure_assignment', '');
        frm.set_value('salary_structure', '');
        // frm.set_value('salary_slip', '');

        // Call server-side method
        frappe.call({
            method:  'a3_finance.a3_finance.doctype.arrear_breakup_log.arrear_breakup_log.get_employee_arrear_details', // <-- you need to create this Python method
          
            args: {
                employee: frm.doc.employee,
                effective_from: frm.doc.effective_from
            },
            callback: function(r) {
                if (r.message) {
                    const data = r.message;

                    // Set SSA & Salary Structure
                    if (data.salary_structure_assignment) {
                        frm.set_value('salary_structure_assignment', data.salary_structure_assignment.name);
                        frm.set_value('salary_structure', data.salary_structure_assignment.salary_structure);
                    }

                    // Set Salary Slip if found
                    if (data.salary_slip) {
                        // frm.set_value('salary_slip', data.salary_slip.name);
                    }
                }
            }
        });
    }
});
