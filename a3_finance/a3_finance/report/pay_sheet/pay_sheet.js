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
        console.log("🟣 printable_html() called!");

        let filters = frappe.query_report.get_filter_values();
        let data = report.data;
        let columns = report.columns;

        console.log("📌 Filters:", filters);
        console.log("📌 Columns:", columns);
        console.log("📌 Data:", data);

        // Fetch employee full names
        let employee_ids = [filters.prepared_by, filters.checked_by, filters.verified_by, filters.approved_by].filter(Boolean);
        let employees = [];
        if (employee_ids.length > 0) {
            employees = await frappe.db.get_list("Employee", {
                filters: { name: ["in", employee_ids] },
                fields: ["name", "employee_name", "designation"]
            });
        }

        let employee_map = {};
        employees.forEach(emp => {
            employee_map[emp.name] = `${emp.employee_name}${emp.designation ? ' - ' + emp.designation : ''}`;
        });

        // Replace IDs with full names
        filters.prepared_by = employee_map[filters.prepared_by] || filters.prepared_by || "";
        filters.checked_by = employee_map[filters.checked_by] || filters.checked_by || "";
        filters.verified_by = employee_map[filters.verified_by] || filters.verified_by || "";
        filters.approved_by = employee_map[filters.approved_by] || filters.approved_by || "";

      let month_year = "";
        try {
            let date_str = filters.start_date || filters.end_date;

            // Convert frappe date string ("2025-11-01") into a JS Date object
            let d = frappe.datetime.str_to_obj(date_str);

            const months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ];

            month_year = months[d.getMonth()] + " " + d.getFullYear();
            console.log("📅 Computed Month-Year:", month_year);
        } catch (e) {
            console.error("❌ Month-Year Computation Error:", e);
        }

        let col_count = columns.length;
        let first_width = 100 - (col_count - 1) * 10;
        console.log("📐 Column Count:", col_count, "First Width:", first_width);

        // ------- START HTML GENERATION -------
        let html = `
<style>
@media print {
    table {
        border-collapse: collapse !important;
        width: 100% !important;
        table-layout: auto !important;
        page-break-inside: auto;
        font-size: 9px !important;
    }

    .pay-sheet-table,
    .pay-sheet-table th,
    .pay-sheet-table td {
        border: 1px solid #000 !important;
        box-sizing: border-box;
        padding: 2px !important;
        vertical-align: middle !important;
    }

    /* Last column right border */
    .pay-sheet-table th:last-child,
    .pay-sheet-table td:last-child {
        border-right: 1px solid #000 !important;
    }

    tr {
        page-break-inside: avoid !important;
    }

    /* Wrap header text */
    .pay-sheet-table th {
        white-space: normal !important;
        text-align: center !important;
        font-size: 9px !important;
        padding: 2px !important;
    }

    /* Keep amounts on single line */
    .pay-sheet-table td:not(:first-child) {
        white-space: nowrap;
        text-align: right;
    }

    /* First column left align */
    .pay-sheet-table td:first-child {
        text-align: left;
        font-weight: bold;
    }
}
</style>


<div style="text-align: center; width: 100%; margin-bottom: 10px;">
    <div style="font-size: 20px; font-weight: bold;">
        ${filters.company }
    </div>
    <div style="font-size: 14px;">
        CHACKAI, BEACH.P.O., AIRPORT ROAD, THIRUVANANTHAPURAM
    </div>

  <div style="font-size: 18px; font-weight: bold; margin-top: 12px;">
    SUMMARY STATEMENT OF SALARY – ${filters.employment_subtype || "All Employment Subtypes"} – ${month_year}
</div>


    <div style="font-size: 16px; margin-top: 5px;">
        BREAKUP OF EARNINGS FOR THE MONTH OF – ${month_year}
    </div>
</div>

<hr>


<hr>

<table class="table table-bordered pay-sheet-table">
<thead>
<tr>
<th style="width:${first_width}%;">Particulars</th>
`;

        columns.slice(1).forEach(col => {
            html += `<th style="width:10%;">${col.label}</th>`;
        });

        html += `</tr></thead><tbody>`;

        data.forEach(row => {
            html += `<tr><td><b>${row.employment_subtype || ""}</b></td>`;

            columns.slice(1).forEach(col => {
                html += `<td class="text-right"> ${frappe.format(row[col.fieldname], col)} </td>`;
            });

            html += `</tr>`;
        });

        html += `
</tbody>
</table>



<div style="height:40px;"></div>

<table style="width:100%; margin-top:10px; text-align:center;">
    <tr>
        <td style="font-weight:bold;font-size: 12px">Prepared By</td>
        <td style="font-weight:bold;font-size: 12px">Checked By</td>
        <td style="font-weight:bold;font-size: 12px">Verified By</td>
        <td style="font-weight:bold;font-size: 12px">Approved By</td>
    </tr>

    <!-- Space for handwritten signature -->
    <tr style="height:50px;font-size: 11px"></tr>

    <tr>
        <td style="font-size: 11px">${filters.prepared_by}</td>
        <td style="font-size: 11px">${filters.checked_by}</td>
        <td style="font-size: 11px">${filters.verified_by}</td>
        <td style="font-size: 11px">${filters.approved_by}</td>
    </tr>
</table>

<p class="text-right" style="margin-top:30px; font-size:9px;">
    Printed on ${frappe.datetime.str_to_user(frappe.datetime.get_datetime_as_string())}
</p>

`;

        console.log("✅ Printable HTML generated successfully.");
        return html;
    }
};


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
