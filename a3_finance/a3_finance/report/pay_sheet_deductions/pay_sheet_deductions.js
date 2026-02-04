// =====================================================
// 📄 PAY SHEET DEDUCTIONS – ROTATED HEADER FINAL
// =====================================================

frappe.query_reports["Pay Sheet Deductions"] = {

    onload(report) {
        const today = frappe.datetime.get_today();
        report.set_filter_value("start_date", frappe.datetime.month_start(today));
        report.set_filter_value("end_date", frappe.datetime.month_end(today));

        const default_company = frappe.defaults.get_user_default("Company");
        if (default_company) {
            report.set_filter_value("company", default_company);
        }

        report.page.add_inner_button("Print Report", () => {
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

        const filters = frappe.query_report.get_filter_values();
        const data = report.data || [];
        const columns = report.columns || [];

        // ===============================
        // EMPLOYEE NAME + DESIGNATION
        // ===============================
        const emp_ids = [
            filters.prepared_by,
            filters.checked_by,
            filters.verified_by,
            filters.approved_by
        ].filter(Boolean);

        const emp_map = {};
        if (emp_ids.length) {
            const emps = await frappe.db.get_list("Employee", {
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

        // ===============================
        // MONTH YEAR
        // ===============================
        const d = frappe.datetime.str_to_obj(filters.start_date);
        const month_year = d
            ? d.toLocaleString("en-IN", { month: "long", year: "numeric" })
            : "";

        // ===============================
        // COLUMN WIDTHS
        // ===============================
        const firstColWidth = 22;
        const lastColWidth  = 10;
        const middleCols = columns.length - 2;
        const middleColWidth = (100 - firstColWidth - lastColWidth) / middleCols;

        // ===============================
        // HTML
        // ===============================
        let html = `
<style>
@page {
    size: A4 landscape;
    margin: 10mm;
}

@media print {
    body {
        font-family: Arial, Helvetica, sans-serif;
        -webkit-print-color-adjust: exact;
    }
.pay-sheet-table th {
    font-size: 12px !important;
}

.rotate-header {
    font-size: 12px !important;
    font-weight: 700;
}

tbody td {
    padding-top: 8px !important;
    padding-bottom: 8px !important;
    line-height: 1.4 !important;
}
.pay-sheet-table th:first-child {
    font-size: 15px !important;
    font-weight: 700;
}

    table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }

    th, td {
        border: 1px solid #000;
        padding: 5px;
    }

    thead {
        display: table-header-group;
    }

    tr {
        page-break-inside: avoid;
    }

    th {
        text-align: center;
        vertical-align: bottom;
        height: 120px;
    }

    .rotate-header {
        writing-mode: vertical-rl;
        transform: rotate(180deg);
        white-space: nowrap;
        font-size: 9px;
        font-weight: 700;
        line-height: 1;
        margin: auto;
    }

    td:first-child {
        text-align: left;
        font-weight: 600;
        font-size: 10px;
        white-space: normal;
    }

    td:not(:first-child) {
        text-align: right;
        font-size: 10px;
        white-space: nowrap;
    }

    .grand-total {
        font-weight: 700;
        background: #f2f2f2;
    }

    .approval-table td {
        border: none !important;
        padding: 6px;
        font-size: 11px;
        text-align: center;
    }

    .approval-table tr.sign-space td {
        height: 45px;
    }
}
</style>

<div style="text-align:center;">
    <div style="font-size:18px;font-weight:bold;">${filters.company || ""}</div>
    <div style="font-size:13px;">CHACKAI, BEACH.P.O., AIRPORT ROAD, THIRUVANANTHAPURAM</div>
    <div style="font-size:16px;font-weight:bold;margin-top:8px;">
        SUMMARY STATEMENT OF SALARY – ${filters.employment_subtype || "ALL"}
    </div>
    <div style="font-size:16px;margin-top:5px;">
        BREAKUP OF DEDUCTIONS FOR THE MONTH OF – ${month_year}
    </div>
</div>

<br><div style="text-align:right;"><b>(Amount in Rupees)</b></div><br>

<table class="pay-sheet-table">
<thead>
<tr>
    <th style="font-size:13px;width:${firstColWidth}%;">Particulars</th>
`;

        columns.slice(1, -1).forEach(col => {
            html += `
                <th style="width:${middleColWidth}%;">
                    <div class="rotate-header">${col.label}</div>
                </th>`;
        });

        html += `
    <th style="width:${lastColWidth}%;">
        <div class="rotate-header">${columns.at(-1).label}</div>
    </th>
</tr>
</thead>
<tbody>
`;

        data.forEach(row => {
            const isGrand = row.employment_subtype === "Grand Total";
            html += `<tr class="${isGrand ? "grand-total" : ""}">`;

            html += `<td>${row.employment_subtype || ""}</td>`;

            columns.slice(1).forEach(col => {
                const val = Math.round(row[col.fieldname] || 0).toLocaleString("en-IN");
                html += `<td>${val}</td>`;
            });

            html += `</tr>`;
        });

        html += `
</tbody>
</table>

<br><br>

<table class="approval-table" style="width:100%;table-layout:fixed;">
<tr>
    <td><b>Prepared By</b></td>
    <td><b>Checked By</b></td>
    <td><b>Verified By</b></td>
    <td><b>Approved By</b></td>
</tr>

<tr class="sign-space">
    <td></td><td></td><td></td><td></td>
</tr>

<tr>
    <td>${filters.prepared_by}</td>
    <td>${filters.checked_by}</td>
    <td>${filters.verified_by}</td>
    <td>${filters.approved_by}</td>
</tr>
</table>
`;

        return html;
    }
};

// ===============================
// PRINT HANDLER
// ===============================
async function print_custom_report(report) {
    const html = await frappe.query_reports["Pay Sheet Deductions"].printable_html(report);
    const w = window.open("", "PRINT", "width=1400,height=900");
    w.document.write(html);
    w.document.close();
    w.focus();
    w.print();
    w.close();
}
