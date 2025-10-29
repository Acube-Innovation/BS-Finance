from frappe.model.document import Document
from frappe.utils import getdate, flt
import frappe
from a3_finance.utils.math_utils import round_half_up
import calendar
import json
from datetime import datetime, timedelta
from frappe.utils import getdate, nowdate

import math



class ArrearBreakupLog(Document):

    def validate(self):
        # If salary_slip is selected, fetch components
        if self.salary_slip:
            # self.first_month_zero()
            self.fetch_salary_slip_components()


    def fetch_salary_slip_components(self):
        if not self.salary_slip:
            return



        MONTHS = [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ]

        if not self.effective_from or not self.arrear_month:
                    return



        effective_date = getdate(self.effective_from)
        effective_month_num = effective_date.month
        arrear_month= MONTHS.index(self.arrear_month.strip()) + 1
        is_first_month = effective_month_num == arrear_month


        # 🔹 Fetch Employee Overtime Wages (if exists) for arrear month/year
        employee_overtime = frappe.get_all(
            "Employee Overtime Wages",
            filters={
                "employee_id": self.employee,
                "payroll_month": self.arrear_month,
                "payroll_year": self.payroll_year,
                "quarter_details": [">=", self.arrear_quarter_applicable]
                # "quarter_details": self.arrear_quarter_applicable
            },
            fields=["overtime_hours", "total_amount"],
            
            limit=1
        )
        print("Employee Overtime fetched:", employee_overtime)
        # overtime_hours = self.convert_overtime_hours(float(self.overtime_hours or 0))
        overtime_hours = self.convert_overtime_hours(float(employee_overtime[0].overtime_hours) if employee_overtime else 0)

        print("overtime_hours from doc:", overtime_hours)
        


        overtime_hours_val = flt(employee_overtime[0].overtime_hours) if employee_overtime else 0
        # print("Overtime Hours fetched:", overtime_hours_val)
        overtime_amount_val = flt(employee_overtime[0].total_amount) if employee_overtime else 0
        overtime_amount_val = round_half_up(overtime_amount_val, 0)
        self.overtime_hours = overtime_hours


        if is_first_month:
            self.lop_in_hours = 0
            self.leave_without_pay = 0
            
            print("First month detected. Zeroed LOP, Leave Without Pay, and OT.")
        print("Overtime Hours set to:", self.overtime_hours)

        # 🔹 Fetch Salary Slip
        slip = frappe.get_doc("Salary Slip", self.salary_slip)

        self.set("earnings", [])
        self.set("deductions", [])

        effective_date = getdate(self.effective_from)
        print ("Effective Date:", effective_date)
        effective_month = effective_date.month
        print ("Effective Month:", effective_month)
        


        earnings_components = [
            "Basic Pay",
            "Service Weightage",
            "Variable DA",
            "House Rent Allowance",
            "LOP Refund / Reimbursement",
            "Overtime Wages",
            "Medical Allowance"
        ]

        deductions_components = [
            "LOP (in Hours) Deduction",
            "Employee PF",
            "Other deductions"
        ]

        # -------------------------
        # 🔹 Payable Calculations
        # -------------------------
        leave_without_pay = flt(self.leave_without_pay or 0)
        overtime_hours = flt(self.overtime_hours or 0)
        current_base = flt(self.current_base or 0)
        hra_percent = flt(self.hra_ or 0)
        payroll_days = flt(self.payroll_days or 30)
        lop_in_hours = flt(self.lop_in_hours or 0)  # LOP in hours from doc
        da_percent = self.dearness_allowance_ or 0  # DA percentage in decimal (e.g., 10% = 0.1)
        pf_rate = 0.12
        old_base = flt(self.old_base or 0)
        previous_base = flt(self.previous_base or 0)
        
        

        # 1. Payable Basic Pay
        payable_bp = (current_base / 30) * (30 - leave_without_pay)
        payable_bp = math.ceil(payable_bp)
        # 1.1 Paid Basic Pay
        

        # Fetch Service Weightage (from earnings child after loop, but here we assume 0 for now)
        service_weightage = 0
        for row in slip.earnings:
            if row.salary_component == "Service Weightage":
                service_weightage = flt(row.amount or 0)
                actual_service_weightage = flt(row.custom_actual_amount or 0)
                break
        print("Service Weightage:", service_weightage)


        paid_value_bp = (previous_base / 30) * (30 - leave_without_pay)
        paid_da	=	(previous_base + actual_service_weightage)/30 * (30 - leave_without_pay) * da_percent
        paid_da = round_half_up(paid_da, 0)
        paid_hra = (paid_value_bp + actual_service_weightage) * hra_percent
        paid_hra = round_half_up(paid_hra, 0)
        paid_ot = (previous_base + actual_service_weightage + paid_da) * (overtime_hours / 240)
        paid_ot = round_half_up(paid_ot, 0)
        paid_lop = (previous_base + ((previous_base + actual_service_weightage) * da_percent) + actual_service_weightage) / 240 * lop_in_hours
        paid_lop = round_half_up(paid_lop, 0)
        if is_first_month:
            paid_pf = ((previous_base + paid_da + actual_service_weightage) - paid_lop + 0 + 0) * pf_rate
            print("paid First month PF calculation used previous_base:", previous_base)
        else:
            paid_pf = ((paid_value_bp + paid_da + service_weightage) - paid_lop + 0 + 0) * pf_rate
            print("paid Normal month PF calculation used payable_bp:", payable_bp)
        paid_pf = round_half_up(paid_pf, 0)
        print("Paid Basic Pay:", paid_value_bp)
        print("service_weightage:", service_weightage)
        print("Paid DA:", paid_da)
        print("Paid HRA:", paid_hra)
        print("Paid OT:", paid_ot)
        print("Paid LOP:", paid_lop)
        print("Paid PF:", paid_pf)


        # 2. Payable DA
        payable_da = (((current_base + actual_service_weightage) / 30) * (30 - leave_without_pay) * da_percent)
        payable_da = round_half_up(payable_da, 0)

        # 3. Payable HRA
        if is_first_month:
            payable_hra = ((payable_bp + actual_service_weightage) * hra_percent)
        else:
            payable_hra = ((payable_bp + service_weightage) * hra_percent)
        payable_hra = round_half_up(payable_hra, 0)

        # 4. Payable OT
        payable_ot = ((payable_bp + service_weightage + payable_da) * (overtime_hours / 240))
        payable_ot = round_half_up(payable_ot)

        # 5. Medical Allowance
        medical_allowance = 0
        settings = frappe.get_all(
            "Payroll Master Setting",
            filters={"payroll_month": self.payroll_month, "payroll_year": self.payroll_year},
            limit=1
        )
        if settings:
            settings_doc = frappe.get_doc("Payroll Master Setting", settings[0].name)

            if leave_without_pay < 10:
                # Compare with slab
                for row in settings_doc.medical_allowance:
                    if current_base >= row.from_base_pay and current_base <= row.to_base_pay:
                        medical_allowance = flt(row.amount)
                        break
            else:
                worked_days = payroll_days - leave_without_pay
                medical_allowance = current_base * (worked_days / 30)
        medical_allowance = round_half_up(medical_allowance)
        # 6. LOP Deduction (in hours)
        payable_lop = ((current_base + ((current_base + actual_service_weightage) * da_percent) + actual_service_weightage) / 240) * lop_in_hours
        payable_lop = round_half_up(payable_lop, 0)

        # 7. Payable PF
        if is_first_month:
            payable_pf = ((current_base + payable_da + actual_service_weightage ) - payable_lop + 0 + 0) * pf_rate
            print("First month PF calculation used current_base:", current_base)
        else:
            payable_pf = ((payable_bp + payable_da + service_weightage )- payable_lop + 0 + 0) * pf_rate
            print("Normal month PF calculation used payable_bp:", payable_bp)
        payable_pf = round_half_up(payable_pf, 0)

        # # 7. Paid PF
        # if is_first_month:
        # 	paid_pf = ((previous_base + payable_da + actual_service_weightage) - payable_lop + 0 + 0) * pf_rate
        # 	print("First month PF calculation used previous_base:", previous_base)
        # else:
        # 	paid_pf = ((payable_bp + payable_da + service_weightage) - payable_lop + 0 + 0) * pf_rate
        # 	print("Normal month PF calculation used payable_bp:", payable_bp)

        # paid_pf = round_half_up(paid_pf, 0)




        # basic_pay_paid_value = previous_base - (old_base / 30 * leave_without_pay) - (previous_base / 30 * leave_without_pay)
        basic_pay_paid_value = (previous_base/30) * (30 - leave_without_pay)
        basic_pay_paid_value = round_half_up(basic_pay_paid_value, 0)

        # 🔹 Build a paid_value map for easy access in the loop
        paid_value_map = {
            "Basic Pay": basic_pay_paid_value,
            "Overtime Wages": overtime_amount_val if overtime_amount_val else 0
        }


         
        print("Basic Pay Paid Value:1111", basic_pay_paid_value)
        print("Overtime Wages Paid Value:1111", overtime_amount_val if overtime_amount_val else 0)




        print("Leave Without Pay (in days):", leave_without_pay)
        print("Payable Basic Pay:", payable_bp)
        print("Payable DA:", payable_da)
        print("Payable HRA:", payable_hra)
        print("Payable OT:", payable_ot)
        print("Medical Allowance:", medical_allowance)
        print("Payable LOP Deduction (in hours):", payable_lop)

        print("current_base:", current_base)
        print("actual_service_weightage:", actual_service_weightage)
        print("da_percent:", da_percent)
        print("lop_in_hours:", lop_in_hours)
        print("Payable PF:", payable_pf)

        # -------------------------
        # Keep your existing loop (earnings/deductions append) below
        # -------------------------


        payable_map = {
            "Basic Pay": payable_bp,
            "Service Weightage": actual_service_weightage if is_first_month else service_weightage,
            "Variable DA": payable_da,
            "House Rent Allowance": payable_hra,
            "LOP Refund / Reimbursement": 0,
            "Overtime Wages": payable_ot,
            "Medical Allowance": medical_allowance,
            "LOP (in Hours) Deduction": payable_lop,
            "Employee PF": payable_pf,
        }


        for row in slip.earnings:
            if row.salary_component in earnings_components:
                # Fetch the pre-calculated paid_value from the map or fallback
                paid_value = paid_value_map.get(row.salary_component, row.custom_actual_amount if is_first_month else row.amount)

                self.append("earnings", {
                    "salary_component": row.salary_component,
                    "salary_slip_start_date": slip.start_date,
                    "payable": payable_map.get(row.salary_component),
                    "amount": payable_map.get(row.salary_component) - paid_value,
                    "paid": paid_value
                })




        # for row in slip.earnings:
        # 	if row.salary_component in earnings_components:
        # 		amount = row.amount
        # 		if row.salary_component == "Overtime Wages":
        # 			paid_value = overtime_amount_val if overtime_amount_val else 0
        # 		else:
        # 			paid_value = row.custom_actual_amount if is_first_month else amount

        # 		print("paid_value:", paid_value)

        # 		self.append("earnings", {
        # 			"salary_component": row.salary_component,
        # 			"salary_slip_start_date": slip.start_date,
        # 			"payable": payable_map.get(row.salary_component),
        # 			"amount": payable_map.get(row.salary_component) - paid_value,
        # 			"paid": paid_value
        # 		})


        for row in slip.deductions:
            if row.salary_component in deductions_components:
                if row.salary_component == "Employee PF":
                    paid_value = paid_pf  # Use the calculated paid_pf
                else:
                    paid_value = row.amount  # Use actual deduction amount for others

                self.append("deductions", {
                    "salary_component": row.salary_component,
                    "salary_slip_start_date": slip.start_date,
                    "payable": payable_map.get(row.salary_component),
                    "paid": paid_value,
                    "amount": 0 if not payable_map.get(row.salary_component) else (payable_map.get(row.salary_component) - paid_value)
                })
                print("Deduction - Component:", row.salary_component, "Paid Value:", paid_value)


        # -------------------------
        # Totals + New Condition
        # -------------------------
        total_earnings = sum(flt(row.amount or 0) for row in self.earnings)
        total_deductions = sum(flt(row.amount or 0) for row in self.deductions)

        # store totals
        self.total_earnings = round_half_up(total_earnings)
        self.total_deductions = round_half_up(total_deductions)

        # gross pay = total earnings - (all deductions except PF)
        otherthan_pf = sum(flt(row.amount or 0) for row in self.deductions if row.salary_component != "Employee PF")
        otherthan_pf_12 = otherthan_pf * 0.12
        print("Other than PF Deductions:", otherthan_pf)

        pf = sum(flt(row.amount or 0) for row in self.deductions if row.salary_component == "Employee PF")
        print("PF Deduction:", pf)

        self.gross_pay = flt(self.total_earnings) - flt(otherthan_pf)
        self.pf_wages = round_half_up(flt(pf))
        self.net_pay = round_half_up(flt(self.gross_pay - self.pf_wages))



    def convert_overtime_hours(self, time_value):
        hours = int(time_value)
        minutes = round((time_value - hours) * 100)
        if minutes not in [0, 15, 30, 45]:
            frappe.throw("Overtime minutes must be one of: .00, .15, .30, or .45")
        return hours + (minutes / 60)



    
    def first_month_zero(self):
        MONTHS = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        if not self.effective_from or not self.arrear_month:
                    return

        effective_month_num = getdate(self.effective_from).month
        arrear_month_num = MONTHS.index(self.arrear_month) + 1  # Convert month name to number

        if effective_month_num == arrear_month_num:
            self.lop_in_hours = 0
            self.leave_without_pay = 0
            self.overtime_hours = 0

@frappe.whitelist()
def get_employee_arrear_details(employee, effective_from):
    from frappe.utils import getdate

    effective_from_date = getdate(effective_from)

    # 1️⃣ Get latest active Salary Structure Assignment
    ssa = frappe.get_all('Salary Structure Assignment',
                         filters={
                             'employee': employee,
                             'custom_inactive': 0,
                             'from_date': ['>=', effective_from_date]
                         },
                         order_by='from_date desc',
                         limit_page_length=1,
                         fields=['name', 'salary_structure'])
    ssa = ssa[0] if ssa else None

    return {
        'salary_structure_assignment': ssa,
    }






