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
        },
        {
            "fieldname": "company",
            "label": "Company",
            "fieldtype": "Link",
            "default": frappe.defaults.get_user_default("Company"),
            "options": "Company"
        },
          {
            "fieldname": "prepared_by",
            "label": "Prepared By",
            "fieldtype": "Link",
            "options": "Employee"
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

    // ===============================
    // FETCH COMPANY DETAILS
    // ===============================
    let company_name = filters.company || "";
    let company_address = "";
    let company_contact = "";

    if (filters.company) {
        const company = await frappe.db.get_value("Company", filters.company, [
            "company_name",
          
        ]);

        company_name = company.company_name || filters.company;

        company_address = [
            company.address,
            company.city,
            company.state,
            company.country
        ].filter(Boolean).join(", ");

        company_contact = [
            company.phone_no,
            company.email
        ].filter(Boolean).join(" | ");
    }

  
// ===============================
// FETCH PREPARED BY DETAILS (FIXED)
// ===============================
let prepared_by_name = "";

if (filters.prepared_by) {
    const emp_res = await frappe.db.get_value("Employee", filters.prepared_by, [
        "employee_name",
        "designation"
    ]);

    const emp = emp_res.message || emp_res; 

    if (emp) {
        prepared_by_name = emp.employee_name || filters.prepared_by;

        if (emp.designation) {
            prepared_by_name += " - " + emp.designation;
        }
    }
}


    let html = `
<style>
@media print {
    table { border-collapse: collapse; width: 100%; font-size: 10px; }
    th, td { border: 1px solid #000; padding: 4px; }
    th { text-align: center; font-weight: bold; }
    td { text-align: left; }
    td.num { text-align: right; }
    tr.total-row td { font-weight: bold; }
    .header { text-align:center; margin-bottom:12px; }
    .footer { display:flex; justify-content:space-between; margin-top:25px; font-size:10px; }
}
</style>

<div class="header">
    <div style="font-size:18px; font-weight:bold;">${company_name}</div>
     <div style="font-size:13px;">CHACKAI, BEACH.P.O., AIRPORT ROAD, THIRUVANANTHAPURAM</div>


    <div style="font-size:16px; font-weight:bold; margin-top:8px;">
        Component Wise Totals
    </div>
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
    let width = "";

    if (col.fieldname === "sl_no") {
        width = 'style="width:40px; text-align:center;"';
    }

    html += `<th ${width}>${col.label}</th>`;
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
                // html += `<td class="${cls}">${frappe.format(value, col)}</td>`;
                let style = "";

            if (col.fieldname === "sl_no") {
                style = 'style="width:40px; text-align:center;"';
            }

            html += `<td ${style} class="${cls}">${frappe.format(value, col)}</td>`;

                
            }
        });

        html += `</tr>`;
    });

    html += `
    </tbody>
</table>

<div class="footer">
    <div>
        <b>Prepared By:</b>
        <div style="height:50px;"></div>  
   
        <div style="margin-top:4px;">${prepared_by_name}</div>
    </div>
</div>

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
