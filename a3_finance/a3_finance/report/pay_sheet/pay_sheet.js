frappe.query_reports["Pay Sheet"] = {

    onload: function (report) {
        console.log("🔵 Pay Sheet Report: onload triggered");

        let today = frappe.datetime.get_today();
        let start = frappe.datetime.month_start(today);
        let end = frappe.datetime.month_end(today);

        console.log("📅 Default Start:", start, "End:", end);

        report.set_filter_value("start_date", start);
        report.set_filter_value("end_date", end);

        // -------------------------------
        // ✅ ADD CUSTOM PRINT BUTTON HERE
        // -------------------------------
        report.page.add_inner_button("Print Report", function () {
            console.log("🟣 Print Button Clicked");
            print_custom_report(report);
        });

        console.log("🟢 Custom Print Button Added");
    },

    filters: [
        {
            fieldname: "start_date",
            label: "Start Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start(frappe.datetime.get_today()),
            onchange: function (val) {
                console.log("🟡 Start Date Changed:", val);

                if (val) {
                    let start = new Date(val);
                    let end = new Date(start.getFullYear(), start.getMonth() + 1, 0);

                    console.log("➡ Auto-set End Date:", end);

                    frappe.query_report.set_filter_value("end_date", frappe.datetime.obj_to_str(end));
                }
            }
        },
        {
            fieldname: "end_date",
            label: "End Date",
            fieldtype: "Date",
            reqd: 1
        },
        {
            fieldname: "employment_subtype",
            label: "Employment Subtype",
            fieldtype: "Link",
            options: "Employment Sub Type"
        },
        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company"
        },
        {
            fieldname: "prepared_by",
            label: "Prepared by",
            fieldtype: "Link",
            options: "Employee"
        },
        {
            fieldname: "checked_by",
            label: "Checked by",
            fieldtype: "Link",
            options: "Employee"
        },
        {
            fieldname: "verified_by",
            label: "Verified by",
            fieldtype: "Link",
            options: "Employee"
        },
        {
            fieldname: "approved_by",
            label: "Approved by",
            fieldtype: "Link",
            options: "Employee"
        },
    ],

printable_html: async function (report) {

    let filters = frappe.query_report.get_filter_values();
    let data = report.data || [];
    let columns = report.columns || [];

    // -----------------------------
    // FETCH EMPLOYEE DISPLAY NAMES
    // -----------------------------
    let employee_ids = [
        filters.prepared_by,
        filters.checked_by,
        filters.verified_by,
        filters.approved_by
    ].filter(Boolean);

    let employee_map = {};
    if (employee_ids.length) {
        let employees = await frappe.db.get_list("Employee", {
            filters: { name: ["in", employee_ids] },
            fields: ["name", "employee_name", "designation"]
        });

        employees.forEach(e => {
            employee_map[e.name] =
                `${e.employee_name}${e.designation ? " - " + e.designation : ""}`;
        });
    }

    filters.prepared_by = employee_map[filters.prepared_by] || "";
    filters.checked_by  = employee_map[filters.checked_by]  || "";
    filters.verified_by = employee_map[filters.verified_by] || "";
    filters.approved_by = employee_map[filters.approved_by] || "";

    // -----------------------------
    // MONTH YEAR
    // -----------------------------
    let d = frappe.datetime.str_to_obj(filters.start_date || filters.end_date);
    let month_year = d
        ? d.toLocaleString("en-IN", { month: "long", year: "numeric" })
        : "";

    // -----------------------------
    // DYNAMIC ZOOM BASED ON COLUMNS
    // -----------------------------
    let col_count = columns.length;
    let zoom = 0.85;
    if (col_count > 15) zoom = 0.75;
    if (col_count > 20) zoom = 0.65;

    // -----------------------------
    // HTML START
    // -----------------------------
    let html = `
<style>

@page {
    size: A4 landscape;
    margin: 8mm;
}

@media print {

    body {
        zoom: ${zoom};
        -webkit-print-color-adjust: exact;
    }

    table {
        width: 100% !important;
        border-collapse: collapse !important;
        table-layout: fixed !important;
    }

    thead {
        display: table-header-group;
    }

    tr {
        page-break-inside: avoid !important;
    }

    .pay-sheet-table {
        font-size: 8px !important;
    }

    .pay-sheet-table th,
    .pay-sheet-table td {
        border: 1px solid #000 !important;
        padding: 2px !important;
        vertical-align: middle !important;
    }

    .pay-sheet-table th {
        text-align: center;
        white-space: normal !important;
        word-break: break-word;
    }

    .pay-sheet-table td {
        text-align: right;
        white-space: nowrap;
    }

    .pay-sheet-table td:first-child {
        text-align: left;
        font-weight: bold;
    }
}

</style>

<div style="text-align:center;">
    <div style="font-size:18px;font-weight:bold;">${filters.company || ""}</div>
    <div style="font-size:12px;">CHACKAI, BEACH.P.O., AIRPORT ROAD, THIRUVANANTHAPURAM</div>

    <div style="font-size:15px;font-weight:bold;margin-top:10px;">
        SUMMARY STATEMENT OF SALARY – ${filters.employment_subtype || "ALL"} – ${month_year}
    </div>

    <div style="font-size:13px;margin-top:4px;">
        BREAKUP OF EARNINGS FOR THE MONTH OF ${month_year}
    </div>
</div>

<hr>

<table class="pay-sheet-table">
<thead>
<tr>
    <th style="width:160px;">Particulars</th>
`;

    // -----------------------------
    // COLUMN HEADERS
    // -----------------------------
    columns.slice(1).forEach(col => {
        html += `<th>${col.label}</th>`;
    });

    html += `</tr></thead><tbody>`;

    // -----------------------------
    // DATA ROWS
    // -----------------------------
    data.forEach(row => {
        html += `<tr>`;
        html += `<td>${row.employment_subtype || ""}</td>`;

        columns.slice(1).forEach(col => {
            let val = Math.round(row[col.fieldname] || 0);
            html += `<td>${frappe.format(val, { fieldtype: "Currency" })}</td>`;
        });

        html += `</tr>`;
    });

    html += `
</tbody>
</table>

<br><br>

<table style="width:100%;text-align:center;font-size:10px;">
<tr>
    <td><b>Prepared By</b></td>
    <td><b>Checked By</b></td>
    <td><b>Verified By</b></td>
    <td><b>Approved By</b></td>
</tr>
<tr style="height:50px;"></tr>
<tr>
    <td>${filters.prepared_by}</td>
    <td>${filters.checked_by}</td>
    <td>${filters.verified_by}</td>
    <td>${filters.approved_by}</td>
</tr>
</table>

<p style="text-align:right;font-size:9px;margin-top:20px;">
    Printed on ${frappe.datetime.str_to_user(frappe.datetime.get_datetime_as_string())}
</p>
`;

    return html;
}
}


// -----------------------------------------------------
// ✅ CUSTOM PRINT FUNCTION
// -----------------------------------------------------
async function print_custom_report(report) {
    console.log("🟣 print_custom_report() called!");

    let html = await frappe.query_reports["Pay Sheet"].printable_html(report);

    let print_window = window.open("", "PRINT", "height=700,width=900");
    print_window.document.write(html);
    print_window.document.close();
    print_window.focus();
    print_window.print();
    print_window.close();
}
