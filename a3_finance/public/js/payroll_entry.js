// frappe.ui.form.on('Payroll Entry', {
//     refresh(frm) {
//         if (frm.doc.docstatus === 0 && !frm.is_new()) {
//             // Remove the original button
//             frm.page.clear_primary_action();

//             // Button: Get Employees (Workers + Officers)
//             frm.add_custom_button(__('Get Employees'), () => {
//                 fetch_employees(frm, ['Workers', 'Officers']);
//             }).toggleClass("btn-primary", !(frm.doc.employees || []).length);

//             // Button: Get Apprentices
//             frm.add_custom_button(__('Get Apprentice'), () => {
//                 fetch_employees(frm, ['Apprentices']);
//             });
//         }
//     }client
// });

// function fetch_employees(frm, types) {
//     frappe.call({
//         method: "a3_finance.a3_finance.doc_events.payroll_entry.get_employees_by_employment_type",
//         args: {
//             payroll_entry_name: frm.doc.name,
//             employment_types: types.join(',')
//         },
//         freeze: true,
//         freeze_message: __("Fetching Employees"),
//         callback: function(r) {
//             if (r.docs?.[0]?.employees) {
//                 frm.reload_doc();
//                 frm.scroll_to_field("employees");
//             }
//         }
//     });
// }
