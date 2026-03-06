# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import flt
from a3_finance.utils.math_utils import round_half_up


class PFDetailedLog(Document):
    def before_save(self):
        self.calculate_epf_wages()

    def get_earning_amount_from_salary_slip(self, salary_component=None, abbr=None):
        if not self.salary_slip:
            return None

        common_filters = {
            "parent": self.salary_slip,
            "parenttype": "Salary Slip",
            "parentfield": "earnings",
        }

        if salary_component:
            amount = frappe.db.get_value(
                "Salary Detail",
                {**common_filters, "salary_component": salary_component},
                "amount",
            )
            if amount is not None:
                return flt(amount)

        if abbr:
            amount = frappe.db.get_value(
                "Salary Detail",
                {**common_filters, "abbr": abbr},
                "amount",
            )
            if amount is not None:
                return flt(amount)

        return None

    def get_base_from_salary_slip(self):
        # Prefer Basic Pay row from Salary Slip earnings table.
        return self.get_earning_amount_from_salary_slip(salary_component="Basic Pay", abbr="BP")

    def get_service_weightage_from_salary_slip(self):
        return self.get_earning_amount_from_salary_slip(
            salary_component="Service Weightage", abbr="SW"
        )

    def get_da_from_salary_slip(self):
        return self.get_earning_amount_from_salary_slip(
            salary_component="Variable DA", abbr="VDA"
        )

    def get_lop_refund_from_salary_slip(self):
        return self.get_earning_amount_from_salary_slip(
            salary_component="LOP Refund", abbr="LOP Refund"
        )
        

    def calculate_epf_wages(self):
        base_from_slip = self.get_base_from_salary_slip()
        if base_from_slip is not None:
            self.base = base_from_slip

        service_weightage_from_slip = self.get_service_weightage_from_salary_slip()
        if service_weightage_from_slip is not None:
            self.service_weightage = service_weightage_from_slip

        da_from_slip = self.get_da_from_salary_slip()
        if da_from_slip is not None:
            self.da = da_from_slip

        lop_refund_from_slip = self.get_lop_refund_from_salary_slip()
        if lop_refund_from_slip is not None:
            self.lop_refund = lop_refund_from_slip

        # # Handle base = 0 by falling back to last submitted SSA
        # if self.base is None or self.base == 0:
        #     alt_ssa = frappe.get_all(
        #         "Salary Structure Assignment",
        #         filters={"employee": self.employee, "docstatus": 1},
        #         fields=["base"],
        #         order_by="from_date desc",
        #         limit=1
        #     )
        #     self.base = flt(alt_ssa[0].get("base")) if alt_ssa else 0

        # Continue only if base is valid
      
        self.base = flt(self.base)
        self.service_weightage = flt(self.service_weightage)
        if self.total_earnings and self.lop_in_hours:
            self.total_earnings_pf = self.total_earnings - self.lop_in_hours

        # Calculate DA only if Variable DA is not found in Salary Slip earnings.
        if da_from_slip is None:
            self.da = round_half_up((self.base + self.service_weightage) * (self.da_percentage or 0))

        self.da = flt(self.da)
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
        self.eps_wages = round_half_up(
            self.base
            + self.service_weightage
            + self.da
            - (self.lop_in_hours or 0)
            + (self.lop_refund or 0)
            - (self.reimbursement_hra or 0)
        )


        scheme = frappe.db.get_value("Employee", self.employee, "custom_employee_pension_scheme")
        eps_addl = frappe.db.get_value("Employee", self.employee,"custom_eps_addl") or 0
        if self.epf_wages >0:
            if scheme == "EPS-9.49  ER-2.51":
                
                self.eps = self.epf_wages * 9.49 / 100
                self.er = self.epf_wages * 2.51 / 100

            elif scheme == "EPS-0  ER-12":
                self.eps = 0
                # self.epf_wages = 0
                self.eps_wages = 0
            #  12% of epf wages for ER
                self.er = self.epf_wages * 12 / 100

            elif scheme == "EPS-1250  ER-550":
                if self.epf_wages <15000:
                    self.eps = (1250/15000)*self.epf_wages
                    self.er = (550/15000)*self.epf_wages

                else:
                    
                    self.eps =1250
                    self.er = 550
                    self.epf_wages = 15000
                    self.edli_wages = 15000
                    self.eps_wages = 15000
                
                # self.epf_wages = self.edli_wages
                # self.eps_wages = self.edli_wages
                

            elif scheme == "EPS-0  ER-1800":
                # self.eps = 0
                self.epf_wages = self.edli_wages
                self.eps_wages = 0

                if self.epf_wages <15000:
                    self.eps = (0/15000)*self.epf_wages
                    self.er = (1800/15000)*self.epf_wages

                else:
                    
                    self.eps = 0
                    self.er = 1800
                    self.epf_wages = 15000
                    self.edli_wages = 15000
                    

            elif scheme == "EPS-1250  ER-12%-1250":
                epf_wages_12 = (self.epf_wages)*12/100

                if self.epf_wages <15000:
                    self.eps = (1250/15000)*self.epf_wages
                    self.er = epf_wages_12 - (1250/15000)*self.epf_wages
                    self.eps_wages = self.epf_wages
                else:
                    self.eps = 1250
                    self.er = epf_wages_12 - 1250
                    self.eps_wages = self.edli_wages
                    
                    # self.epf_wages = self.edli_wages
            
                    # self.er = (self.pf if self.pf else 0) - 1250

            # elif scheme == "EPS-8.33  ER-3.67" and eps_addl == 0:
            #     self.eps = self.epf_wages * 8.33 / 100
            #     self.er = self.epf_wages * 3.67 / 100
            elif scheme == "EPS-8.33  ER-3.67" and eps_addl != 0:
                
                if self.epf_wages >15000:
                    self.eps = 1250 + (self.epf_wages  - 15000) *(9.49/100)
                    self.er = (self.epf_wages)*12/100 - self.eps
                else:
                    self.eps = (self.epf_wages)*8.33/100
                    self.er = (self.epf_wages)*12/100 - self.eps
                # self.eps = round_half_up((self.epf_wages * 8.33 / 100) + (self.epf_wages - self.edli_wages)*eps_addl/100)
                # self.er = round_half_up(self.pf - self.eps)
        else:
            self.eps = 0
            self.er = 0
            self.edli_wages = 0
