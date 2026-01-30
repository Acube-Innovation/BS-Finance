frappe.query_reports["Pay Sheet"] = {

    onload: function (report) {
        let today = frappe.datetime.get_today();
        report.set_filter_value("start_date", frappe.datetime.month_start(today));
        report.set_filter_value("end_date", frappe.datetime.month_end(today));

        report.page.add_inner_button("Print Report", function () {
            print_custom_report(report);
        });
    },

    filters: [
        { fieldname: "start_date", label: "Start Date", fieldtype: "Date", reqd: 1 },
        { fieldname: "end_date", label: "End Date", fieldtype: "Date", reqd: 1 },
        { fieldname: "employment_subtype", label: "Employment Subtype", fieldtype: "Link", options: "Employment Sub Type" },
        { fieldname: "company", label: "Company", fieldtype: "Link", options: "Company" },
        { fieldname: "prepared_by", label: "Prepared By", fieldtype: "Link", options: "Employee" },
        { fieldname: "checked_by", label: "Checked By", fieldtype: "Link", options: "Employee" },
        { fieldname: "verified_by", label: "Verified By", fieldtype: "Link", options: "Employee" },
        { fieldname: "approved_by", label: "Approved By", fieldtype: "Link", options: "Employee" }
    ],

    printable_html: async function (report) {

        let filters = frappe.query_report.get_filter_values();
        let data = report.data || [];
        let columns = report.columns || [];

        /* ---------------- EMPLOYEE NAMES ---------------- */
        let emp_ids = [
            filters.prepared_by,
            filters.checked_by,
            filters.verified_by,
            filters.approved_by
        ].filter(Boolean);

        let emp_map = {};
        if (emp_ids.length) {
            let emps = await frappe.db.get_list("Employee", {
                filters: { name: ["in", emp_ids] },
                fields: ["name", "employee_name", "designation"]
            });

            emps.forEach(e => {
                emp_map[e.name] =
                    `${e.employee_name}${e.designation ? " - " + e.designation : ""}`;
            });
        }

        filters.prepared_by = emp_map[filters.prepared_by] || "";
        filters.checked_by  = emp_map[filters.checked_by]  || "";
        filters.verified_by = emp_map[filters.verified_by] || "";
        filters.approved_by = emp_map[filters.approved_by] || "";

        /* ---------------- MONTH YEAR ---------------- */
        let d = frappe.datetime.str_to_obj(filters.start_date);
        let month_year = d
            ? d.toLocaleString("en-IN", { month: "long", year: "numeric" })
            : "";

        /* ---------------- ZOOM ---------------- */
        let zoom = 0.9;
        if (columns.length > 15) zoom = 0.8;
        if (columns.length > 20) zoom = 0.7;

        /* ---------------- HTML ---------------- */
        let html = `
<style>
@page {
    size: A4 landscape;
    margin: 10mm;
}

@media print {

    body {
        zoom: ${zoom};
        -webkit-print-color-adjust: exact;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }

    thead {
        display: table-header-group;
    }

    tr {
        page-break-inside: avoid;
    }

    /* ---------- PAY SHEET TABLE ---------- */

    .pay-sheet-table {
        font-size: 12.5px;
    }

    .pay-sheet-table th,
    .pay-sheet-table td {
        border: 1px solid #000;
        padding: 10px 6px;
        line-height: 1.8;
        vertical-align: middle;
    }

    .pay-sheet-table th {
        font-size: 11.5px;
        font-weight: 700;
        text-align: center;
        white-space: normal;
    }

    .pay-sheet-table td {
        font-size: 13px;
        font-weight: 500;
        text-align: right;
        white-space: nowrap;
    }

    .pay-sheet-table th:first-child,
    .pay-sheet-table td:first-child {
        text-align: left;
        font-weight: 600;
        white-space: normal;
    }
}
</style>

<div style="text-align:center;">
    <div style="font-size:18px;font-weight:bold;">
        ${filters.company || ""}
    </div>
    <div style="font-size:13px;margin-top:6px;">
        SUMMARY STATEMENT OF SALARY – 
        ${filters.employment_subtype || "ALL"} – ${month_year}
    </div>
</div>

<hr>

<table class="pay-sheet-table">
<thead>
<tr>
    <th style="width:210px;">Particulars</th>
`;

        columns.slice(1).forEach(col => {
            html += `<th>${col.label}</th>`;
        });

        html += `
</tr>
</thead>
<tbody>
`;

        /* ---------------- DATA ---------------- */
        data.forEach(row => {
            html += `<tr>`;
            html += `<td>${row.employment_subtype || ""}</td>`;

            columns.slice(1).forEach(col => {
                let val = Math.round(row[col.fieldname] || 0);
                html += `<td>${val.toLocaleString("en-IN")}</td>`;
            });

            html += `</tr>`;
        });

        html += `
</tbody>
</table>

<br><br>

<table style="width:100%;text-align:center;font-size:11px;">
<tr>
    <td><b>Prepared By</b></td>
    <td><b>Checked By</b></td>
    <td><b>Verified By</b></td>
    <td><b>Approved By</b></td>
</tr>
<tr style="height:55px;"></tr>
<tr>
    <td>${filters.prepared_by}</td>
    <td>${filters.checked_by}</td>
    <td>${filters.verified_by}</td>
    <td>${filters.approved_by}</td>
</tr>
</table>

<p style="text-align:right;font-size:10px;margin-top:20px;">
    Printed on ${frappe.datetime.str_to_user(
        frappe.datetime.get_datetime_as_string()
    )}
</p>
`;

        return html;
    }
};


/* ---------------- PRINT FUNCTION ---------------- */
async function print_custom_report(report) {
    let html = await frappe.query_reports["Pay Sheet"].printable_html(report);
    let w = window.open("", "PRINT", "height=800,width=1100");
    w.document.write(html);
    w.document.close();
    w.focus();
    w.print();
    w.close();
}
