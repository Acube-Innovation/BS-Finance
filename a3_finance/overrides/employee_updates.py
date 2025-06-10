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
