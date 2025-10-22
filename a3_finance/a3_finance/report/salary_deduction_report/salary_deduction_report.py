# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data




# import frappe

# def execute(filters=None):
#     if not filters:
#         filters = {}

#     # Prepare SQL conditions for filtering Salary Slips
#     conditions = "1=1"
#     if filters.get("from_date") and filters.get("to_date"):
#         conditions += " AND posting_date BETWEEN %(from_date)s AND %(to_date)s"
#     if filters.get("employee"):
#         conditions += " AND employee = %(employee)s"
#     if filters.get("status"):
#         conditions += " AND status = %(status)s"
#     if filters.get("department"):
#         conditions += " AND department = %(department)s"

#     # Fetch distinct deduction heads dynamically
#     deduction_heads = frappe.db.sql_list(f"""
#         SELECT DISTINCT sd.salary_component
#         FROM `tabSalary Detail` sd
#         WHERE sd.parenttype = 'Salary Slip'
#         AND sd.parent IN (
#             SELECT name FROM `tabSalary Slip`
#             WHERE docstatus = 1 AND {conditions}
#         )
#         ORDER BY sd.salary_component
#     """, filters)

#     # Base columns
#     columns = [
#         {"label": "Employee ID", "fieldname": "employee_id", "fieldtype": "Data", "width": 120},
#         {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
#         {"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 150},
#         {"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 150},
#         {"label": "Total Salary", "fieldname": "total_salary", "fieldtype": "Currency", "width": 120},
#         {"label": "Total Deductions", "fieldname": "total_deductions", "fieldtype": "Currency", "width": 120},
#     ]

#     # Add deduction heads dynamically as columns
#     for head in deduction_heads:
#         columns.append({
#             "label": head,
#             "fieldname": frappe.scrub(head),  # e.g. 'Professional Tax' -> 'professional_tax'
#             "fieldtype": "Currency",
#             "width": 120,
#         })

#     # Fetch salary slips matching filters
#     salary_slips = frappe.db.sql(f"""
#         SELECT
#             ss.employee,
#             ss.employee_name,
#             ss.designation,
#             ss.department,
#             ss.gross_pay as total_salary,
#             ss.total_deduction as total_deductions,
#             ss.name as slip_name
#         FROM `tabSalary Slip` ss
#         WHERE ss.docstatus = 1 AND {conditions}
#         ORDER BY ss.employee_name
#     """, filters, as_dict=True)

#     data = []

#     # For each salary slip, fetch deduction amounts by head
#     for slip in salary_slips:
#         row = {
#             "employee_id": slip.employee,
#             "employee_name": slip.employee_name,
#             "designation": slip.designation,
#             "department": slip.department,
#             "total_salary": slip.total_salary,
#             "total_deductions": slip.total_deductions,
#         }

#         # Initialize deduction heads with 0
#         for head in deduction_heads:
#             row[frappe.scrub(head)] = 0.0

#         # Fetch deductions for this slip
#         deductions = frappe.db.sql(f"""
#             SELECT salary_component, amount
#             FROM `tabSalary Detail`
#             WHERE parenttype = 'Salary Slip' AND parent = %(slip_name)s
#             AND amount < 0
#         """, {"slip_name": slip.slip_name}, as_dict=True)

#         # Add deductions to respective columns
#         for d in deductions:
#             fieldname = frappe.scrub(d.salary_component)
#             # Store absolute value for deduction
#             row[fieldname] = abs(d.amount)

#         data.append(row)

#     return columns, data


import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    deduction_components = get_deduction_components()
    data = get_data(filters, deduction_components)

    # Extend columns for each deduction head dynamically
    for component in deduction_components:
        columns.append({
            "label": component,
            "fieldname": frappe.scrub(component),
            "fieldtype": "Currency",
            "width": 130
        })

    return columns, data


def get_columns():
    return [
        {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 150},
        {"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 150},
        {"label": "Start Date", "fieldname": "start_date", "fieldtype": "Date", "width": 120},
        {"label": "End Date", "fieldname": "end_date", "fieldtype": "Date", "width": 120},
        {"label": "Total Deduction", "fieldname": "total_deduction", "fieldtype": "Currency", "width": 150},
    ]


def get_deduction_components():
    """Fetch all deduction salary components"""
    return frappe.get_all(
        "Salary Component",
        filters={"type": "Deduction"},
        pluck="name"
    )


def get_data(filters, deduction_components):
    conditions = ""
    if filters.get("from_date"):
        conditions += f" and ss.start_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        conditions += f" and ss.end_date <= '{filters.get('to_date')}'"
    if filters.get("employee"):
        conditions += f" and ss.employee = '{filters.get('employee')}'"

    # Fetch salary slips
    salary_slips = frappe.db.sql(f"""
        SELECT ss.name, ss.employee, ss.employee_name, ss.department, ss.designation,
               ss.start_date, ss.end_date, ss.total_deduction
        FROM `tabSalary Slip` ss
        WHERE ss.docstatus = 1 {conditions}
        ORDER BY ss.employee
    """, as_dict=True)

    data = []
    for slip in salary_slips:
        # Base row data
        row = {
            "employee": slip.employee,
            "employee_name": slip.employee_name,
            "designation": slip.designation,
            "department": slip.department,
            "start_date": slip.start_date,
            "end_date": slip.end_date,
            "total_deduction": slip.total_deduction,
        }

        # Initialize all deduction columns to 0
        for comp in deduction_components:
            row[frappe.scrub(comp)] = 0

        # Fetch deduction details from child table
        deduction_details = frappe.db.sql("""
            SELECT sd.salary_component, sd.amount
            FROM `tabSalary Detail` sd
            WHERE sd.parent = %s AND sd.amount > 0
        """, slip.name, as_dict=True)

        for d in deduction_details:
            if d.salary_component in deduction_components:
                row[frappe.scrub(d.salary_component)] += d.amount

        data.append(row)

    return data
