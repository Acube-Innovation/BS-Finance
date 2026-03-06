// Copyright (c) 2026, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Delivery Performance Report"] = {

    filters: [

        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: frappe.defaults.get_user_default("Company")
        },

        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },

        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today()
        },

        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        },

        {
            fieldname: "item_code",
            label: "Item",
            fieldtype: "Link",
            options: "Item"
        },

        {
            fieldname: "delay_more_than",
            label: "Delay More Than (Days)",
            fieldtype: "Int"
        },

        {
            fieldname: "delay_status",
            label: "Delivery Status",
            fieldtype: "Select",
            options: "\nOn Time\nDelayed\nEarly\nPending"
        }

    ],

    formatter: function(value, row, column, data, default_formatter) {

        value = default_formatter(value, row, column, data);

        if (column.fieldname === "delay_status") {
            if (data.delay_status === "Delayed") {
                value = `<span style="color:red;font-weight:bold;">${value}</span>`;
            }
            if (data.delay_status === "On Time") {
                value = `<span style="color:green;font-weight:bold;">${value}</span>`;
            }
            if (data.delay_status === "Early") {
                value = `<span style="color:blue;">${value}</span>`;
            }
        }

        return value;
    }

};
