# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import flt
from a3_finance.utils.math_utils import round_half_up
from a3_finance.a3_finance.doctype.employee_pension_scheme.employee_pension_scheme import (
    CEILING_EPS_ER,
    CEILING_EPS_FULL_ER,
    CEILING_ER_ONLY,
    EPS_9_49,
    EPS_HIGHER_WAGES,
    ER_12,
)

# Statutory wage ceiling when the Payroll Master Setting has none
DEFAULT_WAGE_CEILING = 15000


def get_wage_ceiling(payroll_month, payroll_year):
    """Statutory Wage Ceiling of the Payroll Master Setting of the payroll month (the latest one up to that
    month, as the salary slip takes its settings); Rs. 15,000 when it is not set."""
    try:
        month, year = int(payroll_month), int(payroll_year)
    except (TypeError, ValueError):
        return DEFAULT_WAGE_CEILING
    for setting in frappe.get_all(
        "Payroll Master Setting",
        filters={"payroll_year": ["in", [str(year), str(year - 1)]]},
        fields=["payroll_year", "payroll_month_number", "edli_wages"],
        order_by="payroll_year desc, payroll_month_number desc",
    ):
        if (int(setting.payroll_year), int(setting.payroll_month_number or 0)) <= (year, month):
            return flt(setting.edli_wages) or DEFAULT_WAGE_CEILING
    return DEFAULT_WAGE_CEILING


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

        # Compute EPF wages
        self.epf_wages = round_half_up(
            self.base
            + self.service_weightage
            + self.da
            - (self.lop_in_hours or 0)
            + (self.lop_refund or 0)
            - (self.reimbursement_hra or 0)
        )
        self.eps_wages = self.epf_wages

        # Statutory wage ceiling of the month (Payroll Master Setting): EDLI wages are the EPF wages up to it,
        # and the schemes on the ceiling contribute 8.33% (EPS) / 12% (PF) of it at most
        # (Rs. 1,250 / Rs. 1,800 at Rs. 15,000)
        ceiling = get_wage_ceiling(self.payroll_month, self.payroll_year)
        eps_cap = round_half_up(ceiling * 8.33 / 100)
        pf_cap = round_half_up(ceiling * 12 / 100)
        er_cap = pf_cap - eps_cap
        self.edli_wages = min(self.epf_wages, ceiling)

        # The scheme works by its Calculation, so its name can be anything (Employee Pension Scheme)
        scheme = frappe.db.get_value("Employee", self.employee, "custom_employee_pension_scheme")
        calculation = frappe.db.get_value("Employee Pension Scheme", scheme, "calculation") if scheme else None
        eps_addl = frappe.db.get_value("Employee", self.employee, "custom_eps_addl") or 0
        if self.epf_wages > 0:
            if calculation == EPS_9_49:
                self.eps = self.epf_wages * 9.49 / 100
                self.er = round_half_up(self.epf_wages * 2.51 / 100)

            elif calculation == ER_12:
                self.eps = 0
                self.eps_wages = 0
                # 12% of epf wages for ER
                self.er = round_half_up(self.epf_wages * 12 / 100)

            elif calculation == CEILING_EPS_ER:
                if self.epf_wages < ceiling:
                    self.eps = (eps_cap / ceiling) * self.epf_wages
                    self.er = round_half_up((er_cap / ceiling) * self.epf_wages)
                else:
                    self.eps = eps_cap
                    self.er = er_cap
                    self.epf_wages = ceiling
                    self.edli_wages = ceiling
                    self.eps_wages = ceiling

            elif calculation == CEILING_ER_ONLY:
                # PF on the wages up to the ceiling, all as ER
                self.epf_wages = self.edli_wages
                self.eps_wages = 0
                self.eps = 0
                if self.epf_wages < ceiling:
                    self.er = round_half_up((pf_cap / ceiling) * self.epf_wages)
                else:
                    self.er = pf_cap
                    self.epf_wages = ceiling
                    self.edli_wages = ceiling

            elif calculation == CEILING_EPS_FULL_ER:
                epf_wages_12 = self.epf_wages * 12 / 100
                if self.epf_wages < ceiling:
                    self.eps = (eps_cap / ceiling) * self.epf_wages
                    self.er = round_half_up(epf_wages_12 - (eps_cap / ceiling) * self.epf_wages)
                    self.eps_wages = self.epf_wages
                else:
                    self.eps = eps_cap
                    self.er = round_half_up(epf_wages_12 - eps_cap)
                    self.eps_wages = ceiling

            elif calculation == EPS_HIGHER_WAGES and eps_addl != 0:
                # EPS on the full wages: 8.33%, plus 1.16% on the wages above the ceiling
                if self.epf_wages > ceiling:
                    self.eps = round_half_up(self.epf_wages * 8.33 / 100) + round_half_up((self.epf_wages - ceiling) * 1.16 / 100)
                    self.er = round_half_up((self.epf_wages) * 12 / 100 - self.eps)
                else:
                    self.eps = (self.epf_wages) * 8.33 / 100
                    self.er = round_half_up((self.epf_wages) * 12 / 100 - self.eps)
        else:
            self.eps = 0
            self.er = 0
            self.edli_wages = 0
