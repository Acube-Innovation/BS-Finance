# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, flt
import calendar
from datetime import datetime

class EmployeeOvertimeWages(Document):
    def validate(self):
        self.validate_inputs()
        self.process_overtime_calculation()

    def validate_inputs(self):
        if not self.employee_id:
            frappe.throw("Employee is required.")
        if not self.quarter_details or not self.quarter_year:
            frappe.throw("Please select both Quarter Details and Quarter Year.")
        if self.overtime_hours is None:
            frappe.throw("Overtime Hours must be provided.")

    def process_overtime_calculation(self):
        quarter = self.quarter_details.upper()
        fy_year = int(self.quarter_year)
        overtime_hours = self.convert_overtime_hours(float(self.overtime_hours or 0))

        # 1. Get quarter date range
        quarter_ranges = {
            "Q1": (f"{fy_year}-04-01", f"{fy_year}-06-30"),
            "Q2": (f"{fy_year}-07-01", f"{fy_year}-09-30"),
            "Q3": (f"{fy_year}-10-01", f"{fy_year}-12-31"),
            "Q4": (f"{fy_year + 1}-01-01", f"{fy_year + 1}-03-31"),
        }

        if quarter not in quarter_ranges:
            frappe.throw("Invalid Quarter selected.")

        end_date = getdate(quarter_ranges[quarter][1])
        start_date = getdate(quarter_ranges[quarter][0])
        is_current_quarter = self.is_current_quarter(end_date)

        # 2. Get Base Pay
        self.basic_pay = self.get_base_salary(start_date)

        # 3. Get Service Weightage
        self.service_weightage = self.get_service_weightage(start_date, is_current_quarter)

        # 4. Get DA %
        da_percent = self.get_da_percentage(start_date, quarter)

        # 5. Compute VDA
        self.variable_da = (self.basic_pay + self.service_weightage) * da_percent

        # 6. Compute Final Amount
        self.total_amount = (
            (self.basic_pay + self.service_weightage + self.variable_da)
            * overtime_hours / 240
        )

    def convert_overtime_hours(self, time_value):
        hours = int(time_value)
        minutes = round((time_value - hours) * 100)
        if minutes not in [0, 15, 30, 45]:
            frappe.throw("Overtime minutes must be one of: .00, .15, .30, or .45")
        return hours + (minutes / 60)

    def is_current_quarter(self, start_date):
        today = datetime.today().date()
        return start_date <= today <= getdate(start_date.replace(month=start_date.month + 2, day=calendar.monthrange(start_date.year, start_date.month + 2)[1]))

    def get_base_salary(self, ssa_date):
        # Use SSA as of quarter start
        base = frappe.db.get_value(
            "Salary Structure Assignment",
            {
                "employee": self.employee_id,
                "from_date": ["<=", ssa_date],
                "docstatus": 1
            },
            "base",
            order_by="from_date desc"
        )
        return flt(base or 0)

    def get_service_weightage(self, s_date, is_current):
        if is_current:
            return flt(frappe.db.get_value("Employee", self.employee_id, "custom_service_weightage_emp") or 0)

        # Use historical SW based on quarter logic
        sw_month = "April" if self.quarter_details.upper() == "Q1" else "March"
        sw_year = self.quarter_year

        sw = frappe.db.get_value(
            "Employee Service Weightage",
            {
                "employee_id": self.employee_id,
                "payroll_month": sw_month,
                "payroll_year": str(sw_year)
            },
            "service_weightage"
        )
        # if sw:
        #     return flt(sw)
        return flt(frappe.db.get_value("Employee", self.employee_id, "custom_service_weightage_emp") or 0)

    def get_da_percentage(self, ssa_date, quarter):
        if quarter == "Q1":
            month_number = 4
            year_number = int(self.quarter_year)
        elif quarter == "Q4":
            month_number = 3  # Use March for consistency
            year_number = int(self.quarter_year)
        else:
            month_number = ssa_date.month
            year_number = ssa_date.year

        da_setting = frappe.get_all(
            "Payroll Master Setting",
            filters={
                "payroll_month_number": month_number,
                "payroll_year": year_number
            },
            fields=["dearness_allowance_"],
            limit=1
        )
        return flt(da_setting[0].dearness_allowance_) if da_setting else 0
