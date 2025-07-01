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
        let month_number = null;

        if (month && month_map[month]) {
            month_number = month_map[month];
            frm.set_value("payroll_month_number", month_number);

            // Set quarter based on month
            let quarter = "";
            if ([1, 2, 3].includes(month_number)) {
                quarter = "Q4";
            } else if ([4, 5, 6].includes(month_number)) {
                quarter = "Q1";
            } else if ([7, 8, 9].includes(month_number)) {
                quarter = "Q2";
            } else if ([10, 11, 12].includes(month_number)) {
                quarter = "Q3";
            }

            frm.set_value("quarter", quarter);
        } else {
            frm.set_value("payroll_month_number", null);
            frm.set_value("quarter", null);
        }
    }
});

