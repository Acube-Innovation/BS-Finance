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
        report.page.add_inner_button("Print Custom Format", function () {
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
            let d = filters.start_date ? new Date(filters.start_date) : new Date(filters.end_date);
            month_year = frappe.datetime.month_name(d.getMonth()) + "-" + d.getFullYear();
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
    .pay-sheet-table th, .pay-sheet-table td {
        padding: 6px !important;
        vertical-align: middle !important;
    }
</style>

<h3 class="text-center">BRAHMOS AEROSPACE THIRUVANANTHAPURAM LTD</h3>
<h4 class="text-center">CHACKAI, BEACH.P.O., AIRPORT ROAD, THIRUVANANTHAPURAM</h4>

<h3 class="text-center">SUMMARY STATEMENT OF SALARY - ${month_year}</h3>
<h4 class="text-center">BREAKUP OF EARNINGS FOR THE MONTH OF- ${month_year}</h4>

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

<br><br>

<table style="width:100%; margin-top:20px;">
<tr>
    <th>Prepared By</th>
    <th>Checked By</th>
    <th>Verified By</th>
    <th>Approved By</th>
</tr>
<tr>
    <td>${filters.prepared_by}</td>
    <td>${filters.checked_by}</td>
    <td>${filters.verified_by}</td>
    <td>${filters.approved_by}</td>
</tr>
</table>

<p class="text-right" style="margin-top:30px;">
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
