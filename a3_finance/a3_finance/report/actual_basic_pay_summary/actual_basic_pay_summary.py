# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.utils import getdate
from datetime import datetime
from dateutil.relativedelta import relativedelta

def execute(filters=None):
    # Filters
    employee = filters.get("employee")
    employment_type = filters.get("employment_type")
    department = filters.get("department")

    # Define month range
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 7, 1)  # Change this as needed

    months = []
    d = start_date
    while d <= end_date:
        months.append(d.strftime("%b %Y"))  # e.g., Apr 2025
        d += relativedelta(months=1)

    # Columns: Employee, Employee Name, Month columns
    columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee"},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data"}
    ]
    columns += [{"label": m, "fieldname": m, "fieldtype": "Currency"} for m in months]

    # Build dynamic condition
    conditions = "a.docstatus = 1 AND a.base IS NOT NULL"
    if employee:
        conditions += f" AND a.employee = {frappe.db.escape(employee)}"

    # Fetch salary assignments joined with Employee
    sql = f"""
        SELECT a.employee, e.employee_name, a.base, a.from_date
        FROM `tabSalary Structure Assignment` a
        JOIN `tabEmployee` e ON a.employee = e.name
        WHERE {conditions}
        {f"AND e.employment_type = {frappe.db.escape(employment_type)}" if employment_type else ""}
        {f"AND e.department = {frappe.db.escape(department)}" if department else ""}
        ORDER BY a.employee, a.from_date
    """
    assignments = frappe.db.sql(sql, as_dict=True)

    # Group by employee
    assignment_map = {}
    employee_names = {}
    for a in assignments:
        emp = a.employee
        employee_names[emp] = a.employee_name
        if emp not in assignment_map:
            assignment_map[emp] = []
        assignment_map[emp].append({
            "base": a.base,
            "from_date": getdate(a.from_date)
        })

    # Build report data
    data = []
    for emp, assignment_list in assignment_map.items():
        row = {
            "employee": emp,
            "employee_name": employee_names.get(emp)
        }
        assignment_list.sort(key=lambda x: x["from_date"])
        for m in months:
            month_date = datetime.strptime(m, "%b %Y").date()
            effective_assignment = None
            for a in assignment_list:
                if a["from_date"] <= month_date:
                    effective_assignment = a
                else:
                    break
            if effective_assignment:
                row[m] = effective_assignment["base"]
        data.append(row)

    return columns, data
