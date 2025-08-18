# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from dateutil.relativedelta import relativedelta
from datetime import datetime
from frappe.utils import getdate, add_months, get_first_day, flt
import frappe
class FestivalAdvanceDisbursement(Document):

        # Ensure valid advance amount

    def validate(self):
        # 1) basic guard
        if not self.festival_advance_amount or flt(self.festival_advance_amount) <= 0:
            frappe.throw("Festival Advance Amount must be greater than 0.")

        # 2) per-month amount (nominal), 10 months
        nominal_monthly = round(flt(self.festival_advance_amount) / 10.0, 2)
        self.monthly_deduction_amount = nominal_monthly

        # 3) parse disbursement date
        if not self.disbursement_month:
            return
        disb_date = getdate(self.disbursement_month)

        # 4) first recovery = 1st of next month
        start_recovery = get_first_day(add_months(disb_date, 1))

        # 5) reset child table to avoid duplicate rows
        self.set("festival_advance_recovery", [])

        # 6) build 10 rows; adjust the last to fix rounding drift
        total_so_far = 0.0
        for i in range(10):
            payroll_date = get_first_day(add_months(start_recovery, i))
            if i < 9:
                amount = nominal_monthly
            else:
                # last installment = principal - sum(previous 9), rounded to 2 decimals
                amount = round(flt(self.festival_advance_amount) - flt(total_so_far), 2)

            self.append("festival_advance_recovery", {
                "payroll_date": payroll_date,
                "recovery_amount": amount,
            })
            total_so_far += amount

        # 7) optional header fields if present
        if hasattr(self, "start_recovery_from"):
            self.start_recovery_from = start_recovery
        if hasattr(self, "recovery_end_date"):
            self.recovery_end_date = get_first_day(add_months(start_recovery, 9))

            


    # def on_submit(self):
        # # 1. Create Festival Advance - Lump sum
        # advance = frappe.get_doc({
        #     "doctype": "Additional Salary",
        #     "employee": self.employee,
        #     "salary_component": self.earning_component,
        #     "payroll_date": self.disbursement_month,
        #     "amount": self.festival_advance_amount,
        #     "overwrite_salary_structure_amount": 1,
        #     "company": frappe.db.get_value("Employee", self.employee, "company")
        # })
        # advance.insert(ignore_permissions=True)
        # advance.submit()
        # self.earning_reference=advance.name

        # 2. Create Festival Advance Recovery - Recurring
        # recovery = frappe.get_doc({
        #     "doctype": "Additional Salary",
        #     "employee": self.employee,
        #     "salary_component": self.deduction_component,
        #     "amount": self.monthly_deduction_amount,
        #     "is_recurring": 1,
        #     "from_date": self.start_recovery_from,
        #     "to_date": self.recovery_end_date,
        #     "overwrite_salary_structure_amount": 0,
        #     "company": frappe.db.get_value("Employee", self.employee, "company")
        # })
        # recovery.insert(ignore_permissions=True)
        # recovery.submit()
        # self.deduction_reference = recovery.name
        # self.save()
    
    # def on_cancel(self):
    #     print("ggggggggggggggggggggggggggggggggggggggggggggggggggggggg")
    #     if self.earning_reference:
    #         try:
    #             ad_sa = frappe.get_doc('Additional Salary', self.earning_reference)
                # if ad_sa.docstatus == 1:
    #                 ad_sa.cancel()
    #         except Exception as e:
    #             frappe.log_error(frappe.get_traceback(), f"Error cancelling earning: {self.earning_reference}")

    #     if self.deduction_reference:
    #         try:
    #             ded_sal = frappe.get_doc('Additional Salary', self.deduction_reference)
    #             if ded_sal.docstatus == 1:
    #                 ded_sal.cancel()
    #         except Exception as e:
    #             frappe.log_error(frappe.get_traceback(), f"Error cancelling deduction: {self.deduction_reference}")


