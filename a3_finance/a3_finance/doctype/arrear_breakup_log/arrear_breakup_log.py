# from frappe.model.document import Document
# from frappe.utils import getdate, flt
# import frappe
# from a3_finance.utils.math_utils import round_half_up
# import calendar

# class ArrearBreakupLog(Document):
#     def validate(self):
#         self.calculate_arrears()

#     def calculate_arrears(self):
#         if not self.effective_from or not self.from_date or not self.current_base:
#             frappe.throw("Effective From, From Date, and Current Base are required.")

#         self.set("earnings", [])
#         self.set("deductions", [])

#         total_da_diff = 0.0
#         total_hra_diff = 0.0
#         total_pf_diff = 0.0
#         total_bp_diff = 0.0
#         total_earnings = 0.0
#         total_deductions = 0.0
#         reimbursement_diff = 0.0

#         salary_slips = frappe.get_all("Salary Slip",
#             filters={
#                 "employee": self.employee,
#                 "start_date": [">=", self.effective_from],
#                 "end_date": ["<=", self.from_date]
#             },
#             fields=["name", "start_date"]
#         )

#         for slip_data in salary_slips:
#             slip = frappe.get_doc("Salary Slip", slip_data.name)

#             slip_month = slip.start_date.strftime("%B")
#             slip_year = getdate(slip.start_date).year

#             da_percent = flt(slip.get("custom_dearness_allowence_percentage") or 0)
#             hra_percent = flt(slip.get("custom_hra") or 0.16)

#             actual_bp = self.get_component_value(slip, "Basic Pay")
#             actual_sw = self.get_component_value(slip, "Service Weightage")
#             actual_da = self.get_component_value(slip, "Variable DA")
#             actual_hra = self.get_component_value(slip, "House Rent Allowance")
#             actual_pf = self.get_component_value(slip, "Employee PF")

#             expected_bp = self.current_base
#             expected_da = round_half_up((expected_bp + actual_sw) * da_percent)
#             expected_hra = round_half_up((expected_bp + actual_sw) * hra_percent)
#             expected_pf = round_half_up((expected_bp + actual_sw + expected_da + expected_hra) * 0.12)

#             bp_diff = expected_bp - actual_bp
#             da_diff = expected_da - actual_da
#             hra_diff = expected_hra - actual_hra
#             pf_diff = expected_pf - actual_pf

#             total_bp_diff += bp_diff
#             total_da_diff += da_diff
#             total_hra_diff += hra_diff
#             total_pf_diff += pf_diff

#             self.append("earnings", {
#                 "salary_component": "Basic Pay",
#                 "salary_slip_start_date": slip_data.start_date,
#                 "amount": flt(bp_diff)
#             })
#             total_earnings += flt(bp_diff)

#             self.append("earnings", {
#                 "salary_component": "Variable DA",
#                 "salary_slip_start_date": slip_data.start_date,
#                 "amount": flt(da_diff)
#             })
#             total_earnings += flt(da_diff)

#             self.append("earnings", {
#                 "salary_component": "House Rent Allowance",
#                 "salary_slip_start_date": slip_data.start_date,
#                 "amount": flt(hra_diff)
#             })
#             total_earnings += flt(hra_diff)

#             self.append("deductions", {
#                 "salary_component": "Employee PF",
#                 "salary_slip_start_date": slip_data.start_date,
#                 "amount": flt(pf_diff)
#             })
#             total_deductions += flt(pf_diff)

#             # --- Reimbursement Calculation ---
#             reimbursement_total = 0.0
#             actual_paid = 0.0

#             # Day-based reimbursement
#             day_reimbursements = frappe.get_all("Employee Reimbursement Wages",
#                 filters={
#                     "employee_id": self.employee,
#                     "reimbursement_month": slip_month,
#                     "reimbursement_year": slip_year,
#                     "reimbursement_date": ["between", [self.effective_from, self.from_date]]
#                 },
#                 fields=["name", "no_of_days", "lop_refund_amount"]
#             )

#             for reimb in day_reimbursements:
#                 actual_paid += flt(reimb.lop_refund_amount)
#                 days = flt(reimb.no_of_days)

#                 pms = frappe.get_all("Payroll Master Setting",
#                     filters={"payroll_month": slip_month, "payroll_year": slip_year},
#                     fields=["hra_", "dearness_allowance_"]
#                 )
#                 hra_pct = flt(pms[0].hra_) if pms else hra_percent
#                 da_pct = flt(pms[0].dearness_allowance_) if pms else da_percent

#                 expected_da = round_half_up((expected_bp + actual_sw) * da_pct)
#                 expected_hra = round_half_up((expected_bp + actual_sw) * hra_pct)
#                 expected_total = (expected_bp + actual_sw + expected_da + expected_hra) * (days / 30.0)
#                 reimbursement_total += round_half_up(expected_total)

#             # Hour-based reimbursement
#             hour_reimbursements = frappe.get_all("Employee Reimbursement Wages",
#                 filters={
#                     "employee_id": self.employee,
#                     "reimbursement_month": slip_month,
#                     "reimbursement_year": slip_year,
#                     "tl_month": ["!=", ""]
#                 },
#                 fields=["name", "tl_month", "tl_hours", "lop_refund_amount"]
#             )

#             for reimb in hour_reimbursements:
#                 tl_month = reimb.tl_month
#                 tl_hours = flt(reimb.tl_hours)
#                 if tl_month:
#                     try:
#                         tl_month_index = list(calendar.month_name).index(tl_month)
#                         effective_month_index = getdate(self.effective_from).month
#                         from_month_index = getdate(self.from_date).month

#                         if effective_month_index <= tl_month_index <= from_month_index:
#                             actual_paid += flt(reimb.lop_refund_amount)
#                             hourly_total = (expected_bp + actual_sw + expected_da) * (tl_hours / 240.0)
#                             reimbursement_total += round_half_up(hourly_total)
#                     except ValueError:
#                         pass

#                     reimbursement_diff = round_half_up(reimbursement_total - actual_paid)

#                     if reimbursement_diff > 0:
#                         self.append("earnings", {
#                             "salary_component": "LOP Refund",
#                             "salary_slip_start_date": slip_data.start_date,
#                             "amount": flt(reimbursement_diff)
#                         })
#                         total_earnings += flt(reimbursement_diff)

#             # Time Loss deduction
#             time_losses = frappe.get_all("Employee Time Loss",
#                 filters={
#                     "employee_id": self.employee,
#                     "payroll_month": slip_month,
#                     "payroll_year": slip_year
#                 },
#                 fields=["time_loss_hours"]
#             )
#             for tl in time_losses:
#                 tl_hours = flt(tl.time_loss_hours)
#                 tl_da = round_half_up((expected_bp + actual_sw) * da_percent)
#                 deduction_amount = (expected_bp + actual_sw + tl_da) * (tl_hours / 240.0)
#                 actual_amount = self.get_component_value(slip, "LOP (in Hours) Deduction")
#                 total_lop_hrs_deduction = flt(deduction_amount - actual_amount)
#                 self.append("deductions", {
#                     "salary_component": "LOP (in Hours) Deduction",
#                     "salary_slip_start_date": slip_data.start_date,
#                     "amount": round_half_up(total_lop_hrs_deduction)
#                 })
#                 total_deductions += round_half_up(total_lop_hrs_deduction)

#             # Overtime calculation
#             from_quarter = f"Q{((getdate(self.from_date).month - 1) // 3)}"
#             from_year = getdate(self.from_date).year

#             overtime_entries = frappe.get_all("Employee Overtime Wages",
#                 filters={
#                     "employee_id": self.employee,
#                     "payroll_month": slip_month,
#                     "payroll_year": slip_year,
#                     "quarter_year": from_year,
#                     "quarter_details": from_quarter
#                 },
#                 fields=["overtime_hours", "basic_pay", "service_weightage", "variable_da"]
#             )
#             for ot in overtime_entries:
#                 ot_hours = flt(ot.overtime_hours)
#                 ot_actual_amount = (flt(ot.basic_pay) + flt(ot.service_weightage) + flt(ot.variable_da)) * (ot_hours / 240.0)
#                 ot_expected_amount = (flt(self.current_base) + flt(ot.service_weightage) + flt(ot.variable_da)) * (ot_hours / 240.0)
#                 ot_diff = round_half_up(ot_expected_amount - ot_actual_amount)
#                 self.append("earnings", {
#                     "salary_component": "Overtime",
#                     "salary_slip_start_date": slip_data.start_date,
#                     "amount": ot_diff
#                 })
#                 total_earnings += ot_diff

#         self.total_earnings = flt(total_earnings)
#         self.total_deductions = flt(total_deductions)
#         self.gross_pay = flt(total_earnings)
#         self.net_pay = flt(total_earnings - total_deductions)


#     def get_component_value(self, slip, component_name):
#         for comp in slip.earnings:
#             if comp.salary_component == component_name:
#                 return flt(comp.amount)
#         for comp in slip.deductions:
#             if comp.salary_component == component_name:
#                 return flt(comp.amount)
#         return 0.0


from frappe.model.document import Document
from frappe.utils import getdate, flt
import frappe
from a3_finance.utils.math_utils import round_half_up
import calendar

class ArrearBreakupLog(Document):
    def validate(self):
        self.calculate_arrears()

    def calculate_arrears(self):
        if not self.effective_from or not self.from_date or not self.current_base:
            frappe.throw("Effective From, From Date, and Current Base are required.")

        self.set("earnings", [])
        self.set("deductions", [])

        total_da_diff = 0.0
        total_hra_diff = 0.0
        total_pf_diff = 0.0
        total_bp_diff = 0.0
        total_earnings = 0.0
        total_deductions = 0.0
        reimbursement_diff = 0.0

        salary_slips = frappe.get_all("Salary Slip",
            filters={
                "employee": self.employee,
                "start_date": [">=", self.effective_from],
                "end_date": ["<=", self.from_date]
            },
            fields=["name", "start_date"]
        )

        for slip_data in salary_slips:
            slip = frappe.get_doc("Salary Slip", slip_data.name)

            slip_month = slip.start_date.strftime("%B")
            slip_year = getdate(slip.start_date).year

            da_percent = flt(slip.get("custom_dearness_allowence_percentage") or 0)
            hra_percent = flt(slip.get("custom_hra") or 0.16)

            actual_bp = self.get_component_value(slip, "Basic Pay")
            actual_sw = self.get_component_value(slip, "Service Weightage")
            actual_da = self.get_component_value(slip, "Variable DA")
            actual_hra = self.get_component_value(slip, "House Rent Allowance")
            actual_pf = self.get_component_value(slip, "Employee PF")

            # --- Adjust actuals if LOP exists before effective date ---
            lops = frappe.get_all("Lop Per Request",
                filters={
                    "employee_id": self.employee,
                    "payroll_month": slip_month,
                    "payroll_year": slip_year,
                    "start_date": ["<", self.effective_from]
                },
                fields=["lop_amount", "employee_service_weightage_loss", "employee_da_loss_for_payroll_period"]
            )
            for lop in lops:
                actual_bp += flt(lop.base_salary)
                actual_sw += flt(lop.employee_service_weightage)
                actual_da += flt(lop.employee_da_loss)

            expected_bp = self.current_base
            expected_da = round_half_up((expected_bp + actual_sw) * da_percent)
            expected_hra = round_half_up((expected_bp + actual_sw) * hra_percent)
            expected_pf = round_half_up((expected_bp + actual_sw + expected_da + expected_hra) * 0.12)

            bp_diff = expected_bp - actual_bp
            da_diff = expected_da - actual_da
            hra_diff = expected_hra - actual_hra
            pf_diff = expected_pf - actual_pf

            total_bp_diff += bp_diff
            total_da_diff += da_diff
            total_hra_diff += hra_diff
            total_pf_diff += pf_diff

            self.append("earnings", {
                "salary_component": "Basic Pay",
                "salary_slip_start_date": slip_data.start_date,
                "amount": flt(bp_diff)
            })
            total_earnings += flt(bp_diff)

            self.append("earnings", {
                "salary_component": "Variable DA",
                "salary_slip_start_date": slip_data.start_date,
                "amount": flt(da_diff)
            })
            total_earnings += flt(da_diff)

            self.append("earnings", {
                "salary_component": "House Rent Allowance",
                "salary_slip_start_date": slip_data.start_date,
                "amount": flt(hra_diff)
            })
            total_earnings += flt(hra_diff)

            self.append("deductions", {
                "salary_component": "Employee PF",
                "salary_slip_start_date": slip_data.start_date,
                "amount": flt(pf_diff)
            })
            total_deductions += flt(pf_diff)

            # --- Reimbursement Calculation ---
            reimbursement_total = 0.0
            actual_paid = 0.0

            # Day-based reimbursement
            day_reimbursements = frappe.get_all("Employee Reimbursement Wages",
                filters={
                    "employee_id": self.employee,
                    "reimbursement_month": slip_month,
                    "reimbursement_year": slip_year,
                    "reimbursement_date": ["between", [self.effective_from, self.from_date]]
                },
                fields=["name", "no_of_days", "lop_refund_amount"]
            )

            for reimb in day_reimbursements:
                actual_paid += flt(reimb.lop_refund_amount)
                days = flt(reimb.no_of_days)

                pms = frappe.get_all("Payroll Master Setting",
                    filters={"payroll_month": slip_month, "payroll_year": slip_year},
                    fields=["hra_", "dearness_allowance_"]
                )
                hra_pct = flt(pms[0].hra_) if pms else hra_percent
                da_pct = flt(pms[0].dearness_allowance_) if pms else da_percent

                expected_da = round_half_up((expected_bp + actual_sw) * da_pct)
                expected_hra = round_half_up((expected_bp + actual_sw) * hra_pct)
                expected_total = (expected_bp + actual_sw + expected_da + expected_hra) * (days / 30.0)
                reimbursement_total += round_half_up(expected_total)

            # Hour-based reimbursement
            hour_reimbursements = frappe.get_all("Employee Reimbursement Wages",
                filters={
                    "employee_id": self.employee,
                    "reimbursement_month": slip_month,
                    "reimbursement_year": slip_year,
                    "tl_month": ["!=", ""]
                },
                fields=["name", "tl_month", "tl_hours", "lop_refund_amount"]
            )

            for reimb in hour_reimbursements:
                tl_month = reimb.tl_month
                tl_hours = flt(reimb.tl_hours)
                if tl_month:
                    try:
                        tl_month_index = list(calendar.month_name).index(tl_month)
                        effective_month_index = getdate(self.effective_from).month
                        from_month_index = getdate(self.from_date).month

                        if effective_month_index <= tl_month_index <= from_month_index:
                            actual_paid += flt(reimb.lop_refund_amount)
                            hourly_total = (expected_bp + actual_sw + expected_da) * (tl_hours / 240.0)
                            reimbursement_total += round_half_up(hourly_total)
                    except ValueError:
                        pass

            reimbursement_diff = round_half_up(reimbursement_total - actual_paid)

            if reimbursement_diff > 0:
                self.append("earnings", {
                    "salary_component": "LOP Refund",
                    "salary_slip_start_date": slip_data.start_date,
                    "amount": flt(reimbursement_diff)
                })
                total_earnings += flt(reimbursement_diff)

            # Time Loss deduction
            time_losses = frappe.get_all("Employee Time Loss",
                filters={
                    "employee_id": self.employee,
                    "payroll_month": slip_month,
                    "payroll_year": slip_year
                },
                fields=["time_loss_hours"]
            )
            for tl in time_losses:
                tl_hours = flt(tl.time_loss_hours)
                tl_da = round_half_up((expected_bp + actual_sw) * da_percent)
                deduction_amount = (expected_bp + actual_sw + tl_da) * (tl_hours / 240.0)
                actual_amount = self.get_component_value(slip, "LOP (in Hours) Deduction")
                total_lop_hrs_deduction = flt(deduction_amount - actual_amount)
                self.append("deductions", {
                    "salary_component": "LOP (in Hours) Deduction",
                    "salary_slip_start_date": slip_data.start_date,
                    "amount": round_half_up(total_lop_hrs_deduction)
                })
                total_deductions += round_half_up(total_lop_hrs_deduction)

            # Overtime calculation
            from_quarter = f"Q{((getdate(self.from_date).month - 1) // 3)}"
            from_year = getdate(self.from_date).year

            overtime_entries = frappe.get_all("Employee Overtime Wages",
                filters={
                    "employee_id": self.employee,
                    "payroll_month": slip_month,
                    "payroll_year": slip_year,
                    "quarter_year": from_year,
                    "quarter_details": from_quarter
                },
                fields=["overtime_hours", "basic_pay", "service_weightage", "variable_da"]
            )
            for ot in overtime_entries:
                ot_hours = flt(ot.overtime_hours)
                ot_actual_amount = (flt(ot.basic_pay) + flt(ot.service_weightage) + flt(ot.variable_da)) * (ot_hours / 240.0)
                ot_expected_amount = (flt(self.current_base) + flt(ot.service_weightage) + flt(ot.variable_da)) * (ot_hours / 240.0)
                ot_diff = round_half_up(ot_expected_amount - ot_actual_amount)
                self.append("earnings", {
                    "salary_component": "Overtime Wages",
                    "salary_slip_start_date": slip_data.start_date,
                    "amount": ot_diff
                })
                total_earnings += ot_diff

        self.total_earnings = flt(total_earnings)
        self.total_deductions = flt(total_deductions)
        self.gross_pay = flt(total_earnings)
        self.net_pay = flt(total_earnings - total_deductions)

    def get_component_value(self, slip, component_name):
        for comp in slip.earnings:
            if comp.salary_component == component_name:
                return flt(comp.amount)
        for comp in slip.deductions:
            if comp.salary_component == component_name:
                return flt(comp.amount)
        return 0.0
