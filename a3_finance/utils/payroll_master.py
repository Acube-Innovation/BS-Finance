import frappe
from frappe import _
from frappe.model.document import Document
import calendar
from frappe.utils import getdate
def get_previous_payroll_master_setting(self, given_year, given_month_number):
    years_to_consider = [int(given_year), int(given_year) - 1]

    result = frappe.get_all(
        "Payroll Master Setting",
        filters={
            "payroll_year": ["in", years_to_consider]
        },
        fields=["name", "payroll_year", "payroll_month_number", "payroll_days"],
        order_by="payroll_year desc, payroll_month_number desc",
        limit=20
    )

    for record in result:
        year = int(record["payroll_year"])
        month = int(record["payroll_month_number"])

        if (year < given_year) or (year == given_year and month <= given_month_number):
            return frappe.get_doc("Payroll Master Setting", record["name"])

    return None
