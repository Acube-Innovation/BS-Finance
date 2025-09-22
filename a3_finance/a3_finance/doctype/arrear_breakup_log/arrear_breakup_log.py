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

            actual_bp_loss = 0.0
            actual_sw_loss = 0.0
            actual_da_loss = 0.0
            new_bp_loss = 0.0
            new_da_loss = 0.0
            current_da = 0.0

            slip_month = slip.start_date.strftime("%B")
            slip_year = getdate(slip.start_date).year

            da_percent = flt(slip.get("custom_dearness_allowence_percentage") or 0)
            hra_percent = flt(slip.get("custom_hra") or 0.16)

            actual_bp = self.get_component_value(slip, "Basic Pay")
            actual_sw = self.get_component_value(slip, "Service Weightage")
            actual_da = self.get_component_value(slip, "Variable DA")
            actual_hra = self.get_component_value(slip, "House Rent Allowance")
            actual_pf = self.get_component_value(slip, "Employee PF")

            

            expected_bp = self.current_base
            expected_da = round_half_up((float(expected_bp) + float(actual_sw)) * float(da_percent))
            expected_hra = round_half_up((float(expected_bp) + float(actual_sw)) * float(hra_percent))

            
            # --- LOP within range (affects actual components paid in that month) ---
            lops = frappe.get_all("Lop Per Request",
                filters={
                    "employee_id": self.employee,
                    "payroll_month": slip_month,
                    "payroll_year": slip_year,
                    "start_date": [">", self.effective_from]
                },
                fields=["lop_amount", "employee_service_weightage_loss", "employee_da_for_payroll_period" ,"employee_da_loss_for_payroll_period","no__of_days"]
            )
            if lops:
                for lop in lops:
                    actual_bp_loss += flt(lop.lop_amount)
                    new_bp_loss = new_bp_loss + (float(expected_bp) * (flt(lop.no__of_days) / 30.0))
                    actual_sw_loss += flt(lop.employee_service_weightage_loss)
                    actual_da_loss += flt(lop.employee_da_loss_for_payroll_period)
                    current_da = ((flt(expected_bp) + flt(actual_sw)) * flt(lop.employee_da_for_payroll_period)) / 30
                    new_da_loss = new_da_loss + (flt(current_da) * (flt(lop.no__of_days)))

            # Arrear differences after LOP adjustments
            real_bp = round_half_up(actual_bp - actual_bp_loss)
            real_sw = round_half_up(actual_sw - actual_sw_loss)
            real_da = round_half_up(actual_da - actual_da_loss)
            arrear_actual_bp = round_half_up(flt(expected_bp) - flt(new_bp_loss))
            arrear_actual_sw = round_half_up(flt(actual_sw) - flt(actual_sw_loss))
            arrear_actual_da = round_half_up(flt(expected_da) - flt(new_da_loss))
            bp_diff = round_half_up(flt(expected_bp) - flt(new_bp_loss)) - round_half_up(flt(actual_bp) - flt(actual_bp_loss))
            da_diff = round_half_up(flt(expected_da) - flt(new_da_loss)) - round_half_up(flt(actual_da) - flt(actual_da_loss))
            hra_diff = round_half_up(expected_hra - actual_hra)

            print("dadsdasasdasdasdadadadadadadadadadad",actual_da_loss,expected_da,da_diff)

            total_bp_diff += bp_diff
            total_da_diff += da_diff
            total_hra_diff += hra_diff

            self.append("earnings", {
                "salary_component": "Basic Pay",
                "salary_slip_start_date": slip_data.start_date,
                "amount": round_half_up(flt(bp_diff))
            })
            total_earnings += flt(bp_diff)

            self.append("earnings", {
                "salary_component": "Variable DA",
                "salary_slip_start_date": slip_data.start_date,
                "amount": round_half_up(flt(da_diff))
            })
            total_earnings += flt(da_diff)

            self.append("earnings", {
                "salary_component": "House Rent Allowance",
                "salary_slip_start_date": slip_data.start_date,
                "amount": round_half_up(flt(hra_diff))
            })
            total_earnings += flt(hra_diff)

            # --- Reimbursement Calculation ---
            reimbursement_total = 0.0
            reimbursement_hra_total = 0.0  # needed for PF formula
            actual_paid = 0.0

            # Day-based reimbursement
            day_reimbursements = frappe.get_all("Employee Reimbursement Wages",
                filters={
                    "employee_id": self.employee,
                    "reimbursement_month": slip_month,
                    "reimbursement_year": slip_year,
                    "reimbursement_date": ["between", [self.effective_from, self.from_date]]
                },
                fields=["name", "no_of_days", "lop_refund_amount","reimbursement_service_weightage"]
            )
            refund_sw =0
            refund_bp=0
            refund_da=0
            days=0
            for reimb in day_reimbursements:
                actual_paid += flt(reimb.lop_refund_amount)
                refund_sw += flt(reimb.reimbursement_service_weightage)
                days = flt(reimb.no_of_days)

                # pms = frappe.get_all("Payroll Master Setting",
                #     filters={"payroll_month": slip_month, "payroll_year": slip_year},
                #     fields=["hra_", "dearness_allowance_"]
                # )
                # hra_pct = flt(pms[0].hra_) if pms else hra_percent
                # da_pct = flt(pms[0].dearness_allowance_) if pms else da_percent

                # expected_da_days = round_half_up((expected_bp + actual_sw) * da_pct)
                # expected_hra_days = round_half_up((expected_bp + actual_sw) * hra_pct)
                # expected_total = (expected_bp + actual_sw + expected_da_days + expected_hra_days) * (days / 30.0)
                # reimbursement_total += round_half_up(expected_total)
                # reimbursement_hra_total += round_half_up(expected_hra_days * (days / 30.0))
                refund_bp += ((expected_bp /30 * days))
                # refund_sw += (refund_sw)
                refund_da += ((expected_da/30 * days))
                reimbursement_hra_total += ((expected_hra/30 * days))
            reimbursement_total = round_half_up(refund_bp+refund_sw+refund_da+reimbursement_hra_total)

            print("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",refund_bp,refund_sw,refund_da,reimbursement_hra_total,reimbursement_total)


            # Hour-based reimbursement (no HRA in hours calc)
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

            # Time Loss deduction (used also for PF formula)
            time_loss_expected_total = 0.0
            time_losses = frappe.get_all("Employee Time Loss",
                filters={
                    "employee_id": self.employee,
                    "payroll_month": slip_month,
                    "payroll_year": slip_year,
                    "time_loss_month": getdate(self.effective_from).strftime("%B")
                },
                fields=["time_loss_hours"]
            )
            for tl in time_losses:
                tl_hours = flt(tl.time_loss_hours)
                tl_da = round_half_up((flt(expected_bp) + flt(actual_sw)) * flt(da_percent))
                deduction_amount = (flt(expected_bp) + flt(actual_sw) + flt(tl_da)) * (flt(tl_hours) / 240.0)
                actual_amount = self.get_component_value(slip, "LOP (in Hours) Deduction")
                total_lop_hrs_deduction = flt(deduction_amount - actual_amount)
                
                # For PF formula (use expected deduction, rounded)
                time_loss_expected_total += round_half_up(deduction_amount)

                self.append("deductions", {
                    "salary_component": "LOP (in Hours) Deduction",
                    "salary_slip_start_date": slip_data.start_date,
                    "amount": round_half_up(total_lop_hrs_deduction)
                })
                total_deductions += round_half_up(total_lop_hrs_deduction)

            # Overtime calculation
            from_quarter = f"Q{((getdate(self.effective_from).month - 1) // 3)}"
            print("from_quarterrrrrrrrrrrrrrrrrrrrrrrrrrr",from_quarter)
            from_year = getdate(self.effective_from).year

            overtime_entries = frappe.get_all("Employee Overtime Wages",
                filters={
                    "employee_id": self.employee,
                    "payroll_month": slip_month,
                    "payroll_year": slip_year,
                    "quarter_year": from_year,
                    "quarter_details": from_quarter
                },
                fields=["overtime_hours", "basic_pay", "service_weightage", "variable_da","total_amount"]
            )
            for ot in overtime_entries:
                ot_hours = flt(ot.overtime_hours)
                ot_actual_amount = flt(ot.total_amount)
                ot_expected_amount = (flt(self.current_base) + flt(ot.service_weightage) + flt(expected_da)) * (ot_hours / 240.0)
                ot_diff = round_half_up(ot_expected_amount - ot_actual_amount)
                self.append("earnings", {
                    "salary_component": "Overtime Wages",
                    "salary_slip_start_date": slip_data.start_date,
                    "amount": ot_diff
                })
                total_earnings += ot_diff
            
            # ---------------- PF arrear using formula ----------------
            # PF Wages = (BP + SW + VDA  - round(Time Loss Hrs Deduction)
            #              + round(Employee Reimbursement Wages) - round(Reimbursement HRA))
            pf_wages_expected = (
                arrear_actual_bp
                + arrear_actual_sw
                + arrear_actual_da
                - round_half_up(time_loss_expected_total)
                + round_half_up(reimbursement_total)
                - round_half_up(reimbursement_hra_total)
            )
            expected_pf = round_half_up(pf_wages_expected * 0.12)
            print("ppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp",arrear_actual_bp,real_bp,arrear_actual_sw,real_sw,arrear_actual_da,real_da,time_loss_expected_total,reimbursement_total,reimbursement_hra_total)
            # actual_pf = self.get_component_value(slip, "Employee PF")
            actual_pf = round_half_up((real_bp+real_sw+real_da - round_half_up(time_loss_expected_total)
                + round_half_up(reimbursement_total)
                - round_half_up(reimbursement_hra_total))*0.12)
            print(f"Expected PF: {expected_pf}, Actual PF: {actual_pf}")
            pf_diff = expected_pf - actual_pf

            # Append PF arrear (difference only)
            if pf_diff:
                self.append("deductions", {
                    "salary_component": "Employee PF",
                    "salary_slip_start_date": slip_data.start_date,
                    "amount": pf_diff
                })
                total_deductions += pf_diff
                total_pf_diff += pf_diff

            otherthan_pf = 0.0

            for row in self.get("deductions") or []:
                if row.salary_component != "Employee PF":
                    otherthan_pf += flt(row.amount)

            pf = 0.0
            for row in self.get("deductions") or []:
                if row.salary_component == "Employee PF":
                    pf += flt(row.amount)

        self.total_earnings = round_half_up(flt(total_earnings))
        self.total_deductions = round_half_up(flt(total_deductions))
        self.gross_pay = flt(total_earnings) - flt(otherthan_pf)
        self.pf_wages = flt(pf)
        self.net_pay = round_half_up(flt(total_earnings - self.pf_wages))

    def get_component_value(self, slip, component_name):
        for comp in slip.earnings:
            if comp.salary_component == component_name:
                return flt(comp.custom_actual_amount)
        for comp in slip.deductions:
            if comp.salary_component == component_name:
                return flt(comp.amount)
        return 0.0
                