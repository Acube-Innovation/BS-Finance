// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Pay Sheet Deductions"] = {
onload: function (report) {
    let today = frappe.datetime.get_today();
    report.set_filter_value("start_date", frappe.datetime.month_start(today));
    report.set_filter_value("end_date", frappe.datetime.month_end(today));

    // ✅ Set default company
    let default_company = frappe.defaults.get_user_default("Company");
    if (default_company) {
        report.set_filter_value("company", default_company);
    }

    // Add custom print button
    report.page.add_inner_button("Print Report", function () {
        print_custom_report(report);
    });
},


    filters: [
        {
            fieldname: "start_date",
            label: "Start Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start(frappe.datetime.get_today()),
            onchange: function (val) {
                if (val) {
                    let start = new Date(val);
                    let end = new Date(start.getFullYear(), start.getMonth() + 1, 0);
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
        let data = report.data;
        let columns = report.columns;

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

        filters.prepared_by = employee_map[filters.prepared_by] || filters.prepared_by || "";
        filters.checked_by = employee_map[filters.checked_by] || filters.checked_by || "";
        filters.verified_by = employee_map[filters.verified_by] || filters.verified_by || "";
        filters.approved_by = employee_map[filters.approved_by] || filters.approved_by || "";

        // Compute Month-Year
        let month_year = "";
        try {
            let date_str = filters.start_date || filters.end_date;
            let d = frappe.datetime.str_to_obj(date_str);
            const months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ];
            month_year = months[d.getMonth()] + " " + d.getFullYear();
        } catch (e) {
            console.error("Month-Year Computation Error:", e);
        }

        let col_count = columns.length;
        let first_width = 100 - (col_count - 1) * 10;

        // HTML with proper borders for data table only
        let html = `
<style>
    .pay-sheet-table {
        border-collapse: collapse !important;
        width: 100%;
    }
    .pay-sheet-table th, .pay-sheet-table td {
        border: 1px solid black !important;
        padding: 3px !important;
        font-size: 11px !important;
        vertical-align: middle !important;
    }
    .pay-sheet-table th {
        font-weight: bold;
        background-color: #f2f2f2;
        text-align: center;
    }
    .pay-sheet-table td {
        font-size: 10px !important;
        text-align: right;
    }
    .pay-sheet-table td:first-child {
        text-align: left;
        font-weight: bold;
    }

    /* Signature table without borders */
    .signature-table {
        width: 100%;
        margin-top: 10px;
        text-align: center;
        border: none !important;
    }
    .signature-table td {
        border: none !important;
        padding: 5px;
        font-size: 11px;
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
        BREAKUP OF DEDUCTIONS FOR THE MONTH OF – ${month_year}
    </div>
</div>

<hr>

<table class="pay-sheet-table">
<thead>
<tr>
<th style="width:${first_width}%;">Particulars</th>
`;

        columns.slice(1).forEach(col => {
            html += `<th style="width:10%;">${col.label}</th>`;
        });

        html += `</tr></thead><tbody>`;

        data.forEach(row => {
            html += `<tr><td>${row.employment_subtype || ""}</td>`;

            columns.slice(1).forEach(col => {
                html += `<td> ${frappe.format(row[col.fieldname], col)} </td>`;
            });

            html += `</tr>`;
        });

        html += `
</tbody>
</table>

<div style="height:40px;"></div>

<table class="signature-table">
    <tr>
        <td style="font-weight:bold;font-size: 12px">Prepared By</td>
        <td style="font-weight:bold;font-size: 12px">Checked By</td>
        <td style="font-weight:bold;font-size: 12px">Verified By</td>
        <td style="font-weight:bold;font-size: 12px">Approved By</td>
    </tr>
    <tr style="height:50px"></tr>
    <tr>
        <td>${filters.prepared_by}</td>
        <td>${filters.checked_by}</td>
        <td>${filters.verified_by}</td>
        <td>${filters.approved_by}</td>
    </tr>
</table>

<p class="text-right" style="margin-top:30px; font-size:9px;">
    Printed on ${frappe.datetime.str_to_user(frappe.datetime.get_datetime_as_string())}
</p>
`;

        return html;
    }
};

// -----------------------------------------------------
// ✅ CUSTOM PRINT FUNCTION
// -----------------------------------------------------
async function print_custom_report(report) {
    let html = await frappe.query_reports["Pay Sheet Deductions"].printable_html(report);
    let print_window = window.open("", "PRINT", "height=700,width=900");
    print_window.document.write(html);
    print_window.document.close();
    print_window.focus();
    print_window.print();
    print_window.close();
}
