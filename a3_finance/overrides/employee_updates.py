import frappe
from frappe.utils import today, date_diff

def update_years_of_service_for_all_employees():
    employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "date_of_joining"])
    for emp in employees:
        if emp.date_of_joining:
            years = int(date_diff(today(), emp.date_of_joining) / 365)
            frappe.db.set_value("Employee", emp.name, "custom_years_of_service", years)


def autoname(self, method=None):
    self.name = self.employee_number

def create_suspension(self, method=None):
    if self.custom_supension_effective_from:
        # frappe.throw("Please set the Payroll Effective From date before saving.")
    
        # Check if a suspension record already exists for the same employee + payroll effective from
        existing = frappe.db.exists(
            "Employee Suspension History",
            {
                "employee": self.name,
                "payroll_effective_from": self.custom_payroll_effected_from,
                "suspension_effective_from": self.custom_supension_effective_from,
            },
        )

        if existing:
            # Load existing record
            suspension = frappe.get_doc("Employee Suspension History", existing)

            # Check if any field values are different
            has_changes = (
                suspension.suspension_effective_from != self.custom_supension_effective_from
                or suspension.payroll_effective_from != self.custom_payroll_effected_from
                or suspension.suspension_effective_to != self.custom_supension_effective_to
                or suspension.payroll_effective_to != self.custom_payroll_effected_to
            )

            if has_changes:
                suspension.suspension_effective_from = self.custom_supension_effective_from
                suspension.payroll_effective_from = self.custom_payroll_effected_from
                suspension.suspension_effective_to = self.custom_supension_effective_to
                suspension.payroll_effective_to = self.custom_payroll_effected_to
                suspension.save(ignore_permissions=True)

                frappe.msgprint(
                    f"Suspension record for {self.name} has been updated (Effective From: {self.custom_supension_effective_from})."
                )

        else:
            # Create a new record
            suspension = frappe.new_doc("Employee Suspension History")
            suspension.employee = self.name
            suspension.suspension_effective_from = self.custom_supension_effective_from
            suspension.payroll_effective_from = self.custom_payroll_effected_from
            suspension.suspension_effective_to = self.custom_supension_effective_to
            suspension.payroll_effective_to = self.custom_payroll_effected_to
            suspension.insert(ignore_permissions=True)
            # suspension.submit()

            frappe.msgprint(
                f"Suspension record created for {self.name} effective from {self.custom_supension_effective_from}."
            )
