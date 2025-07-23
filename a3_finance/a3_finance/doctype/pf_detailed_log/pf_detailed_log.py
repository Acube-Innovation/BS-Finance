# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import flt
from a3_finance.utils.math_utils import round_half_up
class PFDetailedLog(Document):
    def validate(self):
        self.calculate_epf_wages()

    def calculate_epf_wages(self):
        # Handle base = 0 by falling back to last submitted SSA
        if self.base is None or self.base == 0:
            alt_ssa = frappe.get_all(
                "Salary Structure Assignment",
                filters={"employee": self.employee, "docstatus": 1},
                fields=["base"],
                order_by="from_date desc",
                limit=1
            )
            self.base = flt(alt_ssa[0].base) if alt_ssa else 0

        # Continue only if base is valid
        if self.base:
            # Calculate DA (assume percentage)
            self.da = round_half_up((self.base + self.service_weightage) * (self.da_percentage or 0))
            self.edli_wages = 15000

            # Compute EPF wages
            self.epf_wages = round_half_up(
                self.base
                + self.service_weightage
                + self.da
                - (self.lop_in_hours or 0)
                + (self.lop_refund or 0)
                - (self.reimbursement_hra or 0)
            )

            scheme = frappe.db.get_value("Employee", self.employee, "custom_employee_pension_scheme")
            eps_addl = frappe.db.get_value("Employee", self.employee,"custom_eps_addl") or 0

            if scheme == "EPS-9.49  ER-2.51":
                self.eps = self.epf_wages * 9.49 / 100
                self.er = self.epf_wages * 2.51 / 100

            elif scheme == "EPS-0  ER-12":
                self.eps = 0
                self.epf_wages = 0
                self.er = 0

            elif scheme == "EPS-1250  ER-550":
                self.eps = 1250
                self.epf_wages = self.edli_wages
                self.er = 550

            elif scheme == "EPS-0  ER-1800":
                self.eps = 0
                self.epf_wages = 0
                self.er = 1800

            elif scheme == "EPS-1250  ER-12%-1250":
                self.eps = 1250
                self.epf_wages = self.edli_wages
                self.er = (self.pf if self.pf else 0) - 1250

            elif scheme == "EPS-8.33  ER-3.67" and eps_addl == 0:
                self.eps = self.epf_wages * 8.33 / 100
                self.er = self.epf_wages * 3.67 / 100
            elif scheme == "EPS-8.33  ER-3.67" and eps_addl != 0:
                self.eps = round_half_up((self.epf_wages * 8.33 / 100) + (self.epf_wages - self.edli_wages)*eps_addl/100)
                self.er = round_half_up(self.pf - self.eps)
