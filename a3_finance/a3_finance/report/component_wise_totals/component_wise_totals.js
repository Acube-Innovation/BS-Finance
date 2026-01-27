// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Component Wise Totals"] = {

    formatter: function (value, row, column, data, default_formatter) {
        if (column.fieldname === "employee" && data && data.employee) {
            return data.employee;
        }
        return default_formatter(value, row, column, data);
    },

    onload: function(report) {
        // Add Print button
        report.page.add_inner_button("Print Report", function () {
            print_component_wise_totals(report);
        });
    },

    "filters": [
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "reqd": 1
        },
        {
            "fieldname": "salary_component",
            "label": "Salary Component",
            "fieldtype": "Link",
            "options": "Salary Component",
            "reqd": 1
        }
    ]
};

// ---------------- PRINTABLE HTML ----------------
frappe.query_reports["Component Wise Totals"].printable_html = async function(report) {
    let filters = frappe.query_report.get_filter_values();
    let data = report.data || [];
    let columns = report.columns || [];

    const from_date = filters.from_date || "";
    const to_date = filters.to_date || "";
    const component = filters.salary_component || "";

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
    <div style="font-size:18px; font-weight:bold;">Component Wise Totals</div>
    <div style="font-size:13px; margin-top:4px;">
        Salary Component: <b>${component}</b> &nbsp; | &nbsp;
        Period: <b>${from_date}</b> to <b>${to_date}</b>
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

    const is_total = row.employee_name === "TOTAL";

    html += `<tr class="${is_total ? 'total-row' : ''}">`;

    columns.forEach(col => {
        let cls = col.fieldtype === "Currency" ? "num" : "";

     
        if (is_total && col.fieldname === "sl_no") {
            html += `<td></td>`;
        } else {
            let value = row[col.fieldname] ?? "";
            html += `<td class="${cls}">${frappe.format(value, col)}</td>`;
        }
    });

    html += `</tr>`;
});


    html += `
    </tbody>
</table>

<p style="text-align:right; margin-top:20px; font-size:9px;">
    Printed on ${frappe.datetime.str_to_user(frappe.datetime.get_datetime_as_string())}
</p>
`;

    return html;
};

// ---------------- CUSTOM PRINT FUNCTION ----------------
async function print_component_wise_totals(report) {
    let html = await frappe.query_reports["Component Wise Totals"].printable_html(report);

    let print_window = window.open("", "PRINT", "height=700,width=1000");
    print_window.document.write(html);
    print_window.document.close();
    print_window.focus();
    print_window.print();
    print_window.close();
}
