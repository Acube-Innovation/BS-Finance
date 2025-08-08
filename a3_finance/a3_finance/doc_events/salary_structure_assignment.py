import frappe
from frappe.utils import flt

def create_payroll_summary(doc, method):

    # Check for existing Employee Payroll Details with same employee and start_date
    existing_epd = frappe.get_all(
        "Employee Payroll Details",
        filters={
            "employee": doc.employee,
            "start_date": doc.from_date,
            "docstatus": ["<", 2],  # Draft or Submitted
            "active": 1
        },
        fields=["name", "base_pay"],
        limit=1
    )

    if existing_epd:
        existing_name = existing_epd[0]["name"]
        existing_base = flt(existing_epd[0]["base_pay"])

        if flt(doc.base) != existing_base:
            # Disable the old doc
            epd_doc = frappe.get_doc("Employee Payroll Details", existing_name)
            epd_doc.active = 0
            epd_doc.save()

            # Create new doc
            new_epd = frappe.new_doc("Employee Payroll Details")
            new_epd.start_date = doc.from_date
            new_epd.employee = doc.employee
            new_epd.base_pay = doc.base
            new_epd.insert()
    else:
        # No existing record, just create
        new_epd = frappe.new_doc("Employee Payroll Details")
        new_epd.start_date = doc.from_date
        new_epd.employee = doc.employee
        new_epd.base_pay = doc.base
        new_epd.insert()

def update_in_employee(doc,method):
    frappe.db.set_value('Employee',doc.employee,'custom_basic_pay',doc.base)

def create_arrear_details_log(doc, method):
    """
    Create a log entry for arrear details when Salary Slip is submitted.
    """
    if doc.custom_effective_from and doc.custom_process_arrear_on:
        abl= frappe.get_doc({
            "doctype": "Arrear Breakup Log",
            "employee": doc.employee,
            "current_base": doc.base,
            "effective_from": doc.custom_effective_from,
            "payroll_month": doc.custom_process_arrear_on,
            "payroll_year": getdate(doc.custom_process_arrear_on).year})
        abl.insert(ignore_permissions=True)