import frappe
from frappe.utils import getdate, add_years, add_days

def set_apprentice_doe(self, method):
    if (
        self.employment_type == "Apprentice"
        and self.date_of_joining
        and not self.contract_end_date  # Only set if empty
    ):
        doj = getdate(self.date_of_joining)
        self.contract_end_date = add_days(add_years(doj, 1), -1)


def update_total_service(self,method):
    """
    Updates custom_total_service based on date_of_joining.
    Should be called in validate().
    """
    from datetime import datetime

    if not self.date_of_joining:
        self.custom_total_service = ""
        return

    doj = getdate(self.date_of_joining)
    today = datetime.today().date()

    if doj > today:
        self.custom_total_service = "0 Years and 0 Months"
        return

    years = today.year - doj.year
    months = today.month - doj.month

    if months < 0:
        years -= 1
        months += 12

    self.custom_total_service = (
        f"{years} Year{'s' if years != 1 else ''} and "
        f"{months} Month{'s' if months != 1 else ''}"
    )


def validate(doc, method):
    if doc.custom_supension_effective_from and doc.custom_supension_effective_to:
        doc.custom_payroll_effected_from = doc.custom_supension_effective_from
        doc.custom_payroll_effected_to = doc.custom_supension_effective_to




@frappe.whitelist()
def employee_details_change_log(employee, employee_name, component_type, value, effective_from):
    effective_from_date = getdate(effective_from)

    # Fetch previous record, if any
    prev_name = frappe.db.get_value(
        "Employee Details Change Log",
        {
            "employee_id": employee,
            "component_type": component_type,
            "effective_to": None
        },
        "name"
    )

    # Update previous record's effective_to
    if prev_name:
        prev = frappe.get_doc("Employee Details Change Log", prev_name)
        prev.effective_to = add_days(effective_from_date, -1)
        prev.save()

    # Insert new record
    doc = frappe.get_doc({
        "doctype": "Employee Details Change Log",
        "employee_id": employee,
        "employee_name": employee_name,
        "component_type": component_type,
        "value": value,
        "effective_from": effective_from_date,
        "effective_to": None
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
