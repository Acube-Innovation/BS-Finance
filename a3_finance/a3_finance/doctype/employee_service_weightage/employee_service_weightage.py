# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
import calendar

MONTH_NAME_MAP = {month: idx for idx, month in enumerate(calendar.month_name) if month}

class EmployeeServiceWeightage(Document):
    def validate(self):
        # Validate inputs
        if not self.payroll_month or not self.payroll_year:
            frappe.throw("Payroll Month and Year are required.")

        month_number = MONTH_NAME_MAP.get(self.payroll_month)
        year = int(self.payroll_year)

        if not month_number:
            frappe.throw(f"Invalid Payroll Month: {self.payroll_month}")

        # Fetch applicable Payroll Master Setting
        setting = self.get_previous_payroll_master_setting(year, month_number)
        if not setting:
            frappe.throw("No applicable Payroll Master Setting found for the given period.")

        # Set values from Payroll Master Setting
        service_weightage = setting.service_weightage or 0
        payroll_days = setting.payroll_days or 30

        self.service_weightage = service_weightage

        # Perform LOP calculation if LOP Days is entered
        if self.lop_days:
            self.service_weightage_after_lop = service_weightage - ((service_weightage / payroll_days) * self.lop_days)
        else:
            self.service_weightage_after_lop = service_weightage

        # Update Employee's custom field
        if self.employee_id:
            frappe.db.set_value(
                "Employee",
                self.employee_id,
                "custom_service_weightage",
                self.service_weightage_after_lop
            )

    def get_previous_payroll_master_setting(self, year, month_number):
        """
        Fetch the nearest previous Payroll Master Setting for given year/month.
        Limited to current and previous year for performance.
        """
        years_to_consider = [year, year - 1]

        settings = frappe.get_all(
            "Payroll Master Setting",
            filters={"payroll_year": ["in", years_to_consider]},
            fields=["name", "payroll_year", "payroll_month_number", "payroll_days", "service_weightage"],
            order_by="payroll_year desc, payroll_month_number desc",
            limit=20
        )

        for record in settings:
            ry, rm = int(record["payroll_year"]), int(record["payroll_month_number"])
            if ry < year or (ry == year and rm <= month_number):
                return frappe.get_doc("Payroll Master Setting", record["name"])

        return None
