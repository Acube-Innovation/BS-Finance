import frappe
from frappe import _
from hrms.payroll.doctype.payroll_entry.payroll_entry import get_employee_list

@frappe.whitelist()
def get_employees_by_employment_type(payroll_entry_name, employment_types: str):
    """Fetch employees for a payroll entry with an extra employment_type filter"""
    doc = frappe.get_doc("Payroll Entry", payroll_entry_name)
    filters = doc.make_filters()

    # IMPORTANT: change this field name if you use custom_employment_type
    filters["custom_employment_type"] = ["in", [e.strip() for e in employment_types.split(",")]]

    employees = get_employee_list(filters=filters, as_dict=True, ignore_match_conditions=True)
    doc.set("employees", [])

    if not employees:
        frappe.throw(_("No employees found for employment type {0}").format(employment_types))

    doc.set("employees", employees)
    doc.number_of_employees = len(doc.employees)
    doc.update_employees_with_withheld_salaries()
    doc.save()

    return doc.get_employees_with_unmarked_attendance()
