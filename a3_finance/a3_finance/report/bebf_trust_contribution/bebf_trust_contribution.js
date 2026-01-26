// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["BEBF Trust Contribution"] = {

    onload: function(report) {

        // Add Print button
        report.page.add_inner_button("Print Report", function () {
            print_bebf_trust_contribution(report);
        });

        // Optional: hide Sl No column in report view
        setTimeout(() => {
            const wrapper = report.page.wrapper;
            wrapper.find(".dt-header .dt-cell--col-0").hide();
            wrapper.find(".dt-body .dt-cell--col-0").hide();
        }, 300);
    },

    after_datatable_render: function(datatable) {
        datatable.columnmanager.columns[0].hidden = true;
        datatable.refresh();
    },

    filters: [
        {
            fieldname: "month",
            label: "Month",
            fieldtype: "Select",
            options: ["01","02","03","04","05","06","07","08","09","10","11","12"],
            default: frappe.datetime.get_today().split("-")[1]
        },
        {
            fieldname: "year",
            label: "Year",
            fieldtype: "Int",
            default: frappe.datetime.get_today().split("-")[0]
        }
    ],

    // ---------------- PRINTABLE HTML ----------------
    printable_html: async function(report) {

        let filters = frappe.query_report.get_filter_values();
        let data = report.data || [];
        let columns = report.columns || [];

        const month_names = [
            "January","February","March","April","May","June",
            "July","August","September","October","November","December"
        ];
        let month_name = month_names[parseInt(filters.month) - 1];

        let html = `
<style>
@media print {
    table { border-collapse: collapse; width: 100%; font-size: 10px; }
    th, td { border: 1px solid #000; padding: 3px; }
    th { text-align: center; font-weight: bold; }
    td { text-align: left; }
    td.num { text-align: right; }
    tr.total-row td { font-weight: bold; }
}
</style>

<div style="text-align:center; margin-bottom:12px;">
    <div style="font-size:18px; font-weight:bold;">
        BEBF Trust Contribution
    </div>
    <div style="font-size:13px; margin-top:4px;">
        Month: <b>${month_name}</b> &nbsp; | &nbsp;
        Year: <b>${filters.year}</b>
    </div>
</div>

<table>
    <thead>
        <tr>
`;

        columns.forEach(col => {
            html += `<th>${col.label}</th>`;
        });

        html += `</tr></thead><tbody>`;

        data.forEach(row => {
            let is_total = row.employee_name === "TOTAL";
            let row_class = is_total ? "total-row" : "";
            html += `<tr class="${row_class}">`;
            columns.forEach(col => {
                let value = row[col.fieldname] ?? "";
                let cls = col.fieldtype === "Currency" ? "num" : "";
                html += `<td class="${cls}">${frappe.format(value, col)}</td>`;
            });
            html += `</tr>`;
        });

        html += `
    </tbody>
</table>

<p style="text-align:right; margin-top:20px; font-size:9px;">
    Printed on ${frappe.datetime.str_to_user(
        frappe.datetime.get_datetime_as_string()
    )}
</p>
`;

        return html;
    }
};

// ---------------- CUSTOM PRINT FUNCTION ----------------
async function print_bebf_trust_contribution(report) {
    let html = await frappe.query_reports["BEBF Trust Contribution"]
        .printable_html(report);

    let print_window = window.open("", "PRINT", "height=700,width=1000");
    print_window.document.write(html);
    print_window.document.close();
    print_window.focus();
    print_window.print();
    print_window.close();
}
