# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from dateutil.relativedelta import relativedelta
from datetime import datetime

class FestivalAdvanceDisbursement(Document):

        # Ensure valid advance amount
    def validate(self):
        if not self.festival_advance_amount or self.festival_advance_amount <= 0:
            frappe.throw("Festival Advance Amount must be greater than 0.")

        # Calculate Monthly Deduction
        self.monthly_deduction_amount = round(self.festival_advance_amount / 10, 2)

        # Convert disbursement_month string to date object
        if self.disbursement_month:
            disbursement_date = datetime.strptime(self.disbursement_month, "%Y-%m-%d").date()

            # Set Start Recovery From (1st of next month)
            next_month = disbursement_date + relativedelta(months=1)
            self.start_recovery_from = next_month.replace(day=1)

            # Set End Recovery Date (10 months total = start + 9 months)
            self.recovery_end_date = self.start_recovery_from + relativedelta(months=9)
            


    def on_submit(self):
        # 1. Create Festival Advance - Lump sum
        advance = frappe.get_doc({
            "doctype": "Additional Salary",
            "employee": self.employee,
            "salary_component": self.earning_component,
            "payroll_date": self.disbursement_month,
            "amount": self.festival_advance_amount,
            "overwrite_salary_structure_amount": 1,
            "company": frappe.db.get_value("Employee", self.employee, "company")
        })
        advance.insert(ignore_permissions=True)
        advance.submit()

        # 2. Create Festival Advance Recovery - Recurring
        recovery = frappe.get_doc({
            "doctype": "Additional Salary",
            "employee": self.employee,
            "salary_component": self.deduction_component,
            "amount": self.monthly_deduction_amount,
            "is_recurring": 1,
            "from_date": self.start_recovery_from,
            "to_date": self.recovery_end_date,
            "overwrite_salary_structure_amount": 1,
            "company": frappe.db.get_value("Employee", self.employee, "company")
        })
        recovery.insert(ignore_permissions=True)
        recovery.submit()

