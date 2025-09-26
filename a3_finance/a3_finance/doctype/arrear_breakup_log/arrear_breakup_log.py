# -*- coding: utf-8 -*-
"""
Arrear Breakup Log
==================

Builds a month-wise arrear breakup (earnings & deductions) across a range of
salary slips by comparing:
  - what was actually posted on each slip (after LOP etc.),
  - versus what should have been payable under a revised base (self.current_base).

Key formulas & assumptions
--------------------------
1) DA/HRA base:
   - DA and HRA are conceptually computed on (BP + SW).
   - HRA here continues to use your earlier logic (monthly computation with LOP adjustment).
   - **DA has been updated** to exactly mirror your salary-component formula (see below).

2) DA (Dearness Allowance) — EXACT match to your salary component:
   - Let:
       base := self.current_base
       custom_actual_sw := slip.custom_actual_sw (fallback to actual SW if None)
       custom_payroll_days := slip.custom_payroll_days
       custom_uploaded_leave_without_pay := slip.custom_uploaded_leave_without_pay
       custom_dearness_allowence_percentage := slip.custom_dearness_allowence_percentage
         (Assumed decimal, e.g., 0.16 for 16%. If you store 16 for 16%, divide by 100.)
       custom_dearness_allowance_ := "DA actually paid" on the slip (if present),
         else we fall back to the DA component read from child table.
   - Then:
       if custom_uploaded_leave_without_pay == 30:
           expected_da_payable = 0
       else:
           expected_da_payable =
               round_half_up( ((base + custom_actual_sw)/30) * custom_payroll_days * DA% )

     DA arrear (to be booked) =
       round_half_up(expected_da_payable) - round_half_up(actual_DA_on_slip)

   Notes:
   - This removes DA’s dependence on LOP rows. Proration is by `custom_payroll_days`.
   - We keep HRA and other components as they were (including LOP logic).

3) HRA (House Rent Allowance):
   - expected_hra = round_half_up((base + SW) * HRA%)
   - HRA arrear is LOP-adjusted for months after the effective month (30-day divisor used).

4) PF arrear (per slip) uses expected PF wages:
   - pf_wages_expected =
       (arrear_actual_bp + arrear_actual_sw + arrear_actual_da)
       - round_half_up(time_loss_expected_total)
       + round_half_up(reimbursement_total)
       - round_half_up(reimbursement_hra_total)

     expected_pf = round_half_up(pf_wages_expected * 0.12)

   - "Actual PF" for comparison is recomputed using **real** paid components:
       actual_pf = round_half_up(
         (real_bp + real_sw + real_da
          - round_half_up(time_loss_expected_total)
          + round_half_up(reimbursement_total)
          - round_half_up(reimbursement_hra_total)) * 0.12
       )

5) Denominators:
   - Day-based proration uses 30 days.
   - Hour-based proration uses 240 hours per month.

6) Quarter label:
   - f"Q{((month - 1)//3)}" yields Q0..Q3; add +1 if you need Q1..Q4.

This file retains your prints and structure for traceability.
"""

from frappe.model.document import Document
from frappe.utils import getdate, flt
import frappe
from a3_finance.utils.math_utils import round_half_up
import calendar
import json
# from hrms.payroll.doctype.salary_structure.salary_structure import AdditionalSalary


class ArrearBreakupLog(Document):
    """Parent doctype that holds arrear earnings/deductions rows and rollups."""

    def validate(self) -> None:
        """Frappe lifecycle hook. Recompute arrears on save/submit."""
        self.calculate_arrears()

    def calculate_arrears(self) -> None:
        """
        Compute arrears across all Salary Slips in [effective_from, from_date].

        Steps (per slip):
        1) Read actual components (BP, SW, DA, HRA, MA, PF).
        2) Compute expected BP/HRA from revised base (self.current_base) and slip SW.
           - HRA keeps your LOP adjustment logic (first month no LOP, later months prorated).
        3) **DA is computed EXACTLY like your salary component formula** using:
              custom_actual_sw, custom_payroll_days, custom_uploaded_leave_without_pay,
              custom_dearness_allowence_percentage, custom_dearness_allowance_.
        4) Build “earnings” rows for Basic Pay, Variable DA, HRA (paid vs payable vs arrear).
        5) Handle reimbursements (LOP refunds) — day-based includes HRA portion; hour-based does not.
        6) Time Loss (in hours) — expected deduction = (BP + SW + DA) * (hours/240).
        7) Overtime arrears — expected OT = (current_base + SW + expected DA) * (hours/240).
        8) PF arrear — compute expected vs actual using the PF wages formula above.
        9) Medical Allowance — find slab in Payroll Master Setting and book any difference.
        10) Update totals (total_earnings, total_deductions, gross_pay, pf_wages, net_pay).
        """
        if not self.effective_from or not self.from_date or not self.current_base:
            frappe.throw("Effective From, From Date, and Current Base are required.")

        # Reset child tables for a fresh recompute
        self.set("earnings", [])
        self.set("deductions", [])

        # Aggregates across all slips
        total_da_diff = 0.0
        total_hra_diff = 0.0
        total_pf_diff = 0.0
        total_bp_diff = 0.0
        total_earnings = 0.0
        total_deductions = 0.0
        reimbursement_diff = 0.0
        actual_ma_total = 0.0   # track actual MA credited across slips

        # Pull slips within date range, oldest first for traceability
        salary_slips = frappe.get_all(
            "Salary Slip",
            filters={
                "employee": self.employee,
                "start_date": [">=", self.effective_from],
                "end_date": ["<=", self.from_date],
            },
            fields=["name", "start_date"],
            order_by="start_date asc",
        )

        print("salary_slips@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", salary_slips)

        i = 0  # slip index (affects earnings read preference for custom_actual_amount on first slip)
        for slip_data in salary_slips:
            # Load the full Salary Slip document
            slip = frappe.get_doc("Salary Slip", slip_data.name)

            # Per-slip trackers (BP/SW LOP are kept; DA LOP is NOT used anymore)
            actual_bp_loss = 0.0
            actual_sw_loss = 0.0
            new_bp_loss = 0.0

            # Convenience for month/year
            slip_month = slip.start_date.strftime("%B")
            slip_year = getdate(slip.start_date).year

            # Percentages are stored as decimals (e.g., 0.16 == 16%)
            da_percent = flt(slip.get("custom_dearness_allowence_percentage") or 0)
            hra_percent = flt(slip.get("custom_hra") or 0.16)
            print("da_percent@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", da_percent)
            print("slip_month@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", slip_month)

            # Actuals from the slip. For i==0, earnings prefer custom_actual_amount if present.
            actual_bp  = self.get_component_value(slip, "Basic Pay", i)
            actual_sw  = self.get_component_value(slip, "Service Weightage", i)
            actual_da_component = self.get_component_value(slip, "Variable DA", i)  # fallback DA if custom field absent
            actual_hra = self.get_component_value(slip, "House Rent Allowance", i)
            actual_pf1 = self.get_component_value(slip, "Employee PF", i)

            print("actual_bp@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", actual_bp)
            print("actual_sw@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", actual_sw)

            # Actual Medical Allowance on this slip (for per-slip MA arrear)
            actual_ma = self.get_component_value(slip, "Medical Allowance", i)
            actual_ma_total += flt(actual_ma)

            # Revised base for arrears (expected BP)
            expected_bp = self.current_base

            # HRA expected monthly (no proration yet)
            expected_hra = round_half_up((float(expected_bp) + float(actual_sw)) * float(hra_percent))

            # ----------------------------
            # LOP: only BP/SW use LOP rows
            # ----------------------------
            lops = frappe.get_all(
                "Lop Per Request",
                filters={
                    "employee_id": self.employee,
                    "payroll_month": slip_month,
                    "payroll_year": slip_year,
                    "start_date": [">", self.effective_from],
                },
                fields=[
                    "lop_amount",
                    "employee_service_weightage_loss",
                    "no__of_days",
                ],
            )
            if lops:
                for lop in lops:
                    # Actual booked losses
                    actual_bp_loss += flt(lop.lop_amount)
                    actual_sw_loss += flt(lop.employee_service_weightage_loss)
                    # Expected loss for BP by days (30-day divisor)
                    new_bp_loss += (float(expected_bp) * (flt(lop.no__of_days) / 30.0))

            # Real amounts after subtracting actual booked losses for BP/SW
            real_bp = round_half_up(actual_bp - actual_bp_loss)
            real_sw = round_half_up(actual_sw - actual_sw_loss)

            # "Arrear context" expected amounts after expected losses for BP/SW
            arrear_actual_bp = round_half_up(flt(expected_bp) - flt(new_bp_loss))
            arrear_actual_sw = round_half_up(flt(actual_sw) - flt(actual_sw_loss))

            # ----------------------------
            # DA: EXACT salary-component formula
            # ----------------------------
            payroll_days = flt(slip.get("custom_payroll_days") or 0)                 # paid days for the month
            uploaded_lwp = flt(slip.get("custom_uploaded_leave_without_pay") or 0)   # days of LWP uploaded

            # SW for formula: prefer slip.custom_actual_sw; fallback to actual SW component
            sw_for_formula = (
                flt(slip.get("custom_actual_sw"))
                if slip.get("custom_actual_sw") is not None
                else flt(actual_sw)
            )

            # If your DB stores whole percents (e.g., 16 for 16%), uncomment:
            # da_percent = da_percent / 100.0

            # Monthly DA for reference (not used in payable; left as trace/debug)
            expected_da_monthly = round_half_up((flt(expected_bp) + sw_for_formula) * da_percent)

            # DA expected payable by your payroll formula (prorated by payroll days),
            # or zero if uploaded LWP is entire month.
            if uploaded_lwp == 30:
                expected_da_payable = 0.0
            else:
                expected_da_payable = round_half_up(
                    ((flt(expected_bp) + sw_for_formula) / 30.0) * payroll_days * da_percent
                )

            # Actual DA posted on slip: prefer explicit field if present, else the component value
            actual_da_on_slip = (
                flt(slip.get("custom_dearness_allowance_"))
                if slip.get("custom_dearness_allowance_") is not None
                else round_half_up(flt(actual_da_component))
            )

            # DA arrear delta (what we will book)
            crct_da = round_half_up(expected_da_payable) - round_half_up(actual_da_on_slip)

            # For PF formula below:
            real_da = round_half_up(actual_da_on_slip)                 # what was actually posted on slip
            arrear_actual_da = round_half_up(expected_da_payable)      # what should have been payable per formula

            # ----------------------------
            # HRA arrear (keep your LOP logic)
            # ----------------------------
            hra_diff_raw = round_half_up(expected_hra - actual_hra)
            crct_hra = hra_diff_raw

            total_lop_days = 0
            if lops:
                total_lop_days = sum(flt(lop.no__of_days) for lop in lops)
                # For months after effective month, reduce HRA proportionally for LOP days
                crct_hra = hra_diff_raw - (flt(hra_diff_raw) / 30 * total_lop_days)

            if (slip.start_date.month == getdate(self.effective_from).month
                and slip.start_date.year == getdate(self.effective_from).year):
                hra_amount = hra_diff_raw  # no LOP adjustment in the effective month
            else:
                hra_amount = crct_hra      # LOP-adjusted HRA for later months
                total_lop_days = 0         # reset so payable display below stays consistent

            # ----------------------------
            # Accumulate key differences
            # ----------------------------
            # BP delta (expected after LOP vs actual)
            crct_bp = round_half_up(expected_bp - new_bp_loss) - round_half_up(actual_bp)
            # DA delta already computed as crct_da
            bp_diff = crct_bp
            da_diff = crct_da
            hra_diff = hra_amount

            total_bp_diff  += bp_diff
            total_da_diff  += da_diff
            total_hra_diff += hra_diff

            # ----------------------------
            # Earnings rows
            # ----------------------------
            # Basic Pay arrear
            self.append("earnings", {
                "salary_component": "Basic Pay",
                "salary_slip_start_date": slip_data.start_date,
                "paid": round_half_up(actual_bp),                     # what slip paid
                "payable": round_half_up(expected_bp - new_bp_loss),  # what should be paid after LOP
                "amount": round_half_up(flt(crct_bp)),                # arrear delta
            })
            total_earnings += flt(crct_bp)

            # Variable DA arrear (formula-aligned)
            self.append("earnings", {
                "salary_component": "Variable DA",
                "salary_slip_start_date": slip_data.start_date,
                "paid": round_half_up(actual_da_on_slip),
                "payable": round_half_up(expected_da_payable),
                "amount": round_half_up(flt(crct_da)),
            })
            total_earnings += flt(crct_da)

            # HRA arrear
            self.append("earnings", {
                "salary_component": "House Rent Allowance",
                "salary_slip_start_date": slip_data.start_date,
                "paid": round_half_up(actual_hra),
                "payable": (
                    round_half_up(expected_hra)
                    if (slip.start_date.month == getdate(self.effective_from).month
                        and slip.start_date.year == getdate(self.effective_from).year)
                    else round_half_up(expected_hra - (expected_hra / 30 * total_lop_days))
                ),
                "amount": round_half_up(hra_amount),
            })
            total_earnings += flt(hra_amount)

            # ----------------------------
            # Reimbursement (LOP Refund)
            #   - Day-based: includes BP, SW, DA, HRA (HRA portion tracked for PF wages)
            #   - Hour-based: includes BP+SW+DA (no HRA on hourly)
            # ----------------------------
            reimbursement_total = 0.0
            reimbursement_hra_total = 0.0
            actual_paid = 0.0

            # Day-based reimbursements (bounded by effective range)
            day_reimbursements = frappe.get_all(
                "Employee Reimbursement Wages",
                filters={
                    "employee_id": self.employee,
                    "reimbursement_month": slip_month,
                    "reimbursement_year": slip_year,
                    "reimbursement_date": ["between", [self.effective_from, self.from_date]],
                },
                fields=["name", "no_of_days", "lop_refund_amount", "reimbursement_service_weightage"],
            )
            refund_sw = 0.0
            refund_bp = 0.0
            refund_da = 0.0
            days = 0.0

            for reimb in day_reimbursements:
                actual_paid += flt(reimb.lop_refund_amount)
                refund_sw += flt(reimb.reimbursement_service_weightage)
                days = flt(reimb.no_of_days)

                # Day-based proportional refunds (30-day divisor)
                refund_bp += ((expected_bp / 30.0) * days)
                # Use formula-based monthly DA for fairness in refund proration
                refund_da += ((expected_da_monthly / 30.0) * days)
                reimbursement_hra_total += ((expected_hra / 30.0) * days)

            reimbursement_total = round_half_up(refund_bp + refund_sw + refund_da + reimbursement_hra_total)

            # Hour-based reimbursements (no HRA in hourly calculation)
            hour_reimbursements = frappe.get_all(
                "Employee Reimbursement Wages",
                filters={
                    "employee_id": self.employee,
                    "reimbursement_month": slip_month,
                    "reimbursement_year": slip_year,
                    "tl_month": ["!=", ""],
                },
                fields=["name", "tl_month", "tl_hours", "lop_refund_amount"],
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
                            # 240 hours/month convention; use formula-based monthly DA in the sum
                            hourly_total = (expected_bp + actual_sw + expected_da_monthly) * (tl_hours / 240.0)
                            reimbursement_total += round_half_up(hourly_total)
                    except ValueError:
                        pass

            reimbursement_diff = round_half_up(reimbursement_total - actual_paid)
            crct_reimb = round_half_up(reimbursement_total) - round_half_up(actual_paid)

            if reimbursement_diff > 0:
                self.append("earnings", {
                    "salary_component": "LOP Refund",
                    "salary_slip_start_date": slip_data.start_date,
                    "paid": round_half_up(actual_paid),
                    "payable": round_half_up(reimbursement_total),
                    "amount": flt(crct_reimb),
                })
                total_earnings += flt(crct_reimb)

            # ----------------------------
            # Time Loss (hours) Deduction (also feeds PF wages)
            # expected deduction = (BP + SW + DA) * (hours/240)
            # Here we use DA = expected_da_monthly (formula-based monthly)
            # ----------------------------
            time_loss_expected_total = 0.0
            time_losses = frappe.get_all(
                "Employee Time Loss",
                filters={
                    "employee_id": self.employee,
                    "payroll_month": slip_month,
                    "payroll_year": slip_year,
                    "time_loss_month": getdate(self.effective_from).strftime("%B"),
                },
                fields=["time_loss_hours"],
            )
            for tl in time_losses:
                tl_hours = flt(tl.time_loss_hours)
                tl_da_monthly = expected_da_monthly
                deduction_amount = (flt(expected_bp) + flt(actual_sw) + flt(tl_da_monthly)) * (flt(tl_hours) / 240.0)
                actual_amount = self.get_component_value(slip, "LOP (in Hours) Deduction", i)
                crct_tl = round_half_up(deduction_amount) - round_half_up(actual_amount)

                # PF wages use rounded expected deduction
                time_loss_expected_total += round_half_up(deduction_amount)

                self.append("deductions", {
                    "salary_component": "LOP (in Hours) Deduction",
                    "salary_slip_start_date": slip_data.start_date,
                    "paid": round_half_up(actual_amount),
                    "payable": round_half_up(deduction_amount),
                    "amount": round_half_up(crct_tl),
                })
                total_deductions += round_half_up(crct_tl)

            # ----------------------------
            # Overtime Arrears
            # expected OT = (current_base + SW + expected DA monthly) * (hours / 240)
            # ----------------------------
            from_quarter = f"Q{((getdate(self.effective_from).month - 1) // 3)}"
            print("from_quarterrrrrrrrrrrrrrrrrrrrrrrrrrr", from_quarter)
            from_year = getdate(self.effective_from).year

            overtime_entries = frappe.get_all(
                "Employee Overtime Wages",
                filters={
                    "employee_id": self.employee,
                    "payroll_month": slip_month,
                    "payroll_year": slip_year,
                    "quarter_year": from_year,
                    "quarter_details": from_quarter,
                },
                fields=["overtime_hours", "basic_pay", "service_weightage", "variable_da", "total_amount"],
            )
            for ot in overtime_entries:
                ot_hours = flt(ot.overtime_hours)
                ot_actual_amount = flt(ot.total_amount)
                ot_expected_amount = (flt(self.current_base) + flt(ot.service_weightage) + flt(expected_da_monthly)) * (ot_hours / 240.0)
                crct_ot = round_half_up(ot_expected_amount) - round_half_up(ot_actual_amount)

                self.append("earnings", {
                    "salary_component": "Overtime Wages",
                    "salary_slip_start_date": slip_data.start_date,
                    "paid": round_half_up(ot_actual_amount),
                    "payable": round_half_up(ot_expected_amount),
                    "amount": crct_ot,
                })
                total_earnings += crct_ot

            # ----------------------------
            # PF Arrear using PF wages formula (see top docstring)
            # ----------------------------
            pf_wages_expected = (
                arrear_actual_bp
                + arrear_actual_sw
                + arrear_actual_da
                - round_half_up(time_loss_expected_total)
                + round_half_up(reimbursement_total)
                - round_half_up(reimbursement_hra_total)
            )
            expected_pf = round_half_up(pf_wages_expected * 0.12)

            actual_pf_recomputed = round_half_up(
                (real_bp + real_sw + real_da
                 - round_half_up(time_loss_expected_total)
                 + round_half_up(reimbursement_total)
                 - round_half_up(reimbursement_hra_total)) * 0.12
            )

            print(f"Expected PF: {expected_pf}, Actual PF (recomputed): {actual_pf_recomputed}")

            pf_diff = expected_pf - actual_pf_recomputed
            crct_pf = round_half_up(expected_pf) - round_half_up(actual_pf1)  # posted on slip vs expected

            if pf_diff:
                self.append("deductions", {
                    "salary_component": "Employee PF",
                    "salary_slip_start_date": slip_data.start_date,
                    "paid": round_half_up(actual_pf1),
                    "payable": round_half_up(expected_pf),
                    "amount": crct_pf,
                })
                total_deductions += crct_pf
                total_pf_diff += crct_pf

            # ----------------------------
            # Medical Allowance arrear (slab-based)
            # ----------------------------
            expected_ma_per_month = 0.0
            pms = frappe.get_all(
                "Payroll Master Setting",
                filters={"payroll_year": getdate(self.effective_from).year},
                fields=["name"],
            )
            if pms:
                pms_doc = frappe.get_doc("Payroll Master Setting", pms[0].name)
                for row in pms_doc.medical_allowance:
                    if flt(row.from_base_pay) <= flt(self.current_base) <= flt(row.to_base_pay):
                        expected_ma_per_month = flt(row.amount)
                        break

            expected_ma = expected_ma_per_month
            actual_ma_val = self.get_component_value(slip, "Medical Allowance", i)
            ma_diff = expected_ma - actual_ma_val
            if ma_diff:
                self.append("earnings", {
                    "salary_component": "Medical Allowance",
                    "salary_slip_start_date": slip_data.start_date,
                    "paid": round_half_up(actual_ma_val),
                    "payable": round_half_up(expected_ma),
                    "amount": ma_diff,
                })
                total_earnings += ma_diff

            # ----------------------------
            # Non-PF deductions and PF totals for final fields
            # ----------------------------
            otherthan_pf = 0.0
            pf = 0.0
            for row in self.get("deductions") or []:
                if row.salary_component == "Employee PF":
                    pf += flt(row.amount)
                else:
                    otherthan_pf += flt(row.amount)

            otherthan_pf_12 = otherthan_pf * 0.12  # 12% of non-PF deductions (as per your rollup)

            # Next slip
            i += 1

        # ----------------------------
        # Final rollups on parent
        # ----------------------------
        self.total_earnings = round_half_up(flt(total_earnings))
        self.total_deductions = round_half_up(flt(total_deductions))
        # Gross = total earnings - non-PF deductions
        self.gross_pay = flt(total_earnings) - flt(otherthan_pf)
        # PF wages (custom summary) = PF - 12% of non-PF deductions
        self.pf_wages = flt(pf) - flt(otherthan_pf_12)
        # Net = gross - pf_wages
        self.net_pay = round_half_up(flt(self.gross_pay - self.pf_wages))

    def get_component_value(self, slip, component_name: str, i: int) -> float:
        """
        Return a component value from a Salary Slip.

        Parameters
        ----------
        slip : Document
            Salary Slip document (with .earnings and .deductions child tables).
        component_name : str
            Name of the salary component to fetch (e.g., "Basic Pay").
        i : int
            Slip index in the processing order. For i == 0, if the earnings row
            has `custom_actual_amount`, that value is preferred over `amount`.

        Returns
        -------
        float
            The component value found, else 0.0.

        Notes
        -----
        - Earnings (i == 0): prefer `custom_actual_amount` if present, to capture
          original posted amounts before downstream adjustments.
        - Earnings (i > 0): use `amount`.
        - Deductions: always use `amount`.
        """
        for comp in slip.earnings:
            if comp.salary_component == component_name:
                if i == 0 and hasattr(comp, "custom_actual_amount") and comp.custom_actual_amount is not None:
                    return flt(comp.custom_actual_amount)
                return flt(comp.amount)
        for comp in slip.deductions:
            if comp.salary_component == component_name:
                return flt(comp.amount)
        return 0.0
