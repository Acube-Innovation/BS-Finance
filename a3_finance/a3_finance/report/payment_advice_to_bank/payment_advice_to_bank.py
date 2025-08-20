# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt
import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    # Convert to integer
    filters["payroll_month"] = int(filters.get("payroll_month") or 0)
    filters["payroll_year"] = int(filters.get("payroll_year") or 0)

    # Handle employment type filter
    emp_type_filter = ""
    if filters.get("employment_type"):
        if filters["employment_type"] == "Regular Employees":
            # Special case → Officers + Workers
            emp_type_filter = "AND e.employment_type IN ('Officers', 'Workers')"
        else:
            emp_type_filter = "AND e.employment_type = %(employment_type)s"

    columns = [
        {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Bank Account", "fieldname": "bank_account", "fieldtype": "Data", "width": 180},
        {"label": "Net Pay", "fieldname": "net_pay", "fieldtype": "Currency", "width": 120},
    ]

    data = frappe.db.sql(f"""
        SELECT 
            e.name AS employee,
            e.employee_name,
            e.bank_ac_no AS bank_account,
            ss.net_pay
        FROM `tabSalary Slip` ss
        JOIN `tabEmployee` e ON ss.employee = e.name
        WHERE 
             MONTH(ss.start_date) = %(payroll_month)s
            AND YEAR(ss.start_date) = %(payroll_year)s
            {emp_type_filter}
    """, filters, as_dict=True)

    # Manually compute total
    total = sum(row["net_pay"] for row in data)

    # Add a total row
    if data:
        data.append({
            "employee": "",
            "employee_name": "TOTAL",
            "bank_account": "",
            "net_pay": total
        })

    return columns, data
