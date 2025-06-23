// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Payroll Master Setting", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Payroll Master Setting", {
    before_save: function(frm) {
        const month_map = {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12
        };

        const month = frm.doc.payroll_month;
        if (month && month_map[month]) {
            frm.set_value("payroll_month_number", month_map[month]);
        } else {
            frm.set_value("payroll_month_number", null);
        }
    }
});
