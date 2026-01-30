// © 2025 ACUBE

frappe.query_reports["Payment Advice To Bank"] = {

    filters: [
        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company"
        },
        {
            fieldname: "payroll_month",
            label: "Payroll Month",
            fieldtype: "Select",
            options: [
                { label: "January", value: 1 }, { label: "February", value: 2 }, { label: "March", value: 3 },
                { label: "April", value: 4 },   { label: "May", value: 5 },      { label: "June", value: 6 },
                { label: "July", value: 7 },    { label: "August", value: 8 },   { label: "September", value: 9 },
                { label: "October", value: 10 },{ label: "November", value: 11 },{ label: "December", value: 12 }
            ],
            default: new Date().getMonth() + 1
        },
        {
            fieldname: "payroll_year",
            label: "Payroll Year",
            fieldtype: "Data",
            default: new Date().getFullYear().toString()
        },
        {
            fieldname: "employment_type",
            label: "Employment Type",
            fieldtype: "Link",
            options: "Employment Type"
        },
        {
            fieldname: "prepared_by",
            label: "Prepared by",
            fieldtype: "Link",
            options: "Employee"
        },
        // {
        //     fieldname: "checked_by",
        //     label: "Checked by",
        //     fieldtype: "Link",
        //     options: "Employee"
        // },
        // {
        //     fieldname: "verified_by",
        //     label: "Verified by",
        //     fieldtype: "Link",
        //     options: "Employee"
        // },
        {
            fieldname: "approved_by",
            label: "Approved by",
            fieldtype: "Link",
            options: "Employee"
        }
    ],

    onload(report) {
        report.page.add_inner_button("Print Report", async function () {

            const data = frappe.query_report.data || [];
            if (!data.length) {
                frappe.msgprint("No data to print.");
                return;
            }

            const html = await frappe.query_reports["Payment Advice To Bank"].printable_html(data);

            let win = window.open("", "_blank");
            win.document.write(`<html><head><title>Payment Advice</title></head><body>${html}</body></html>`);
            win.document.close();
            win.print();
        });
    },

    async printable_html(data) {

        // Collect filter values
        const f = name => frappe.query_report.get_filter_value(name);
        const filters = {
            prepared: f("prepared_by"),
            checked:  f("checked_by"),
            verified: f("verified_by"),
            approved: f("approved_by"),
            company:  f("company")
        };

        // -- Fetch employee details ------------------------------------------------
        const emp_ids = [filters.prepared, filters.checked, filters.verified, filters.approved].filter(Boolean);
        let emp_map = {};

        if (emp_ids.length) {
            const employees = await frappe.db.get_list("Employee", {
                filters: { name: ["in", emp_ids] },
                fields: ["name", "employee_name", "designation"]
            });

            employees.forEach(e => {
                emp_map[e.name] = `${e.employee_name}${e.designation ? " - " + e.designation : ""}`;
            });
        }

        const prepared = emp_map[filters.prepared] || "";
        const checked  = emp_map[filters.checked]  || "";
        const verified = emp_map[filters.verified] || "";
        const approved = emp_map[filters.approved] || "";

        // -- Date --------------------------------------------
        const month = f("payroll_month");
        const year  = f("payroll_year");

        const monthName = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ][month];

        // -- HTML OUTPUT -------------------------------------------------------------
        return `
            <div style="text-align:center; font-family:Arial;">
                <h2>${filters.company || ""}</h2>
                <div style="font-size:13px;">CHACKAI, BEACH P.O., AIRPORT ROAD, THIRUVANANTHAPURAM</div>
                <h3 style="margin-top:10px;">Payment Advice To Bank</h3>
                <h4>${monthName} ${year}</h4>
            </div>

            <table border="1" cellspacing="0" cellpadding="6" width="100%"
                style="font-family:Arial; font-size:12px; border-collapse:collapse; margin-top:20px;">
                <thead style="background:#f5f5f5; font-weight:bold;">
                    <tr>
                        <th>Sl No</th>
                        <th>Employee ID</th>
                        <th>Employee Name</th>
                        <th>Bank Account</th>
                        <th style="text-align:right;">Net Pay</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(r => `
                        <tr>
                            <td>${r.sl_no || ""}</td>
                            <td>${r.employee || ""}</td>
                            <td>${r.employee_name || ""}</td>
                            <td>${r.bank_account || ""}</td>
                            <td style="text-align:right;">${r.net_pay || 0}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>

            <br><br>

          <table width="100%" style="font-family: Arial; font-size: 12px; text-align: center;">
    <tr>
        <!-- Left: Authorized -->
        <td width="50%">
            <b>Authorized Signatory & Designation</b>
            <div style="height:55px;"></div>
        </td>

      
    </tr>

    <tr>
        <!-- Prepared below Authorized -->
        <td>
            
            <div style="height:55px;"></div>
            ${prepared}
        </td>

        <td width="50%">
           
            <div style="height:55px;"></div>
            ${approved}
        </td>

        <!-- Empty cell to keep structure -->
        <td></td>
    </tr>
</table>

        `;
    }
};
