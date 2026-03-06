frappe.query_reports["Cash Book"] = {

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
            reqd: 1,
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "bank_accounts",
            label: "Bank/Cash Accounts",
            fieldtype: "MultiSelectList",
            get_data: function (txt) {
                return frappe.db.get_link_options("Account", txt, {
                    account_type: ["in", ["Bank", "Cash"]]
                });
            }
        }
    ],

    tree: true,
    name_field: "particulars",
    parent_field: "parent",
    initial_depth: 1,

    formatter: function (value, row, column, data, default_formatter) {

        value = default_formatter(value, row, column, data);

        if (column.fieldname === "particulars"
            && data.account
            && data.indent === 1) {

            value = `<a class="cashbook-ledger-link"
                        data-account="${data.account}"
                        style="cursor:pointer">
                        ${value}
                    </a>`;
        }

        return value;
    },

    onload: function (report) {

        $(document).on("click", ".cashbook-ledger-link", function () {

            let account = $(this).data("account");

            let filters = frappe.query_report.get_filter_values();

            frappe.set_route("query-report", "General Ledger", {
                company: filters.company,
                account: account,
                from_date: filters.from_date,
                to_date: filters.to_date
            });

        });

    }

};
