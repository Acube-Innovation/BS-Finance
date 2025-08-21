# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, date_diff
from datetime import timedelta
from a3_finance.utils.payroll_master import get_previous_payroll_master_setting


class LopPerRequest(Document):
    def validate(self):
        if not self.start_date or not self.employee_id:
            return

        self.ensure_unique_lop_start_date_per_employee()

        # 1. Calculate LOP date range and dominant month
        start = getdate(self.start_date)
        lop_days = float(self.no__of_days or 0)

        if lop_days <= 0:
            frappe.throw("Number of LOP days must be greater than zero.")

        end = start + timedelta(days=lop_days - 1)

        # Count days per month in LOP range
        month_counts = {}
        for i in range(int(lop_days)):
            day = start + timedelta(days=i)
            key = (day.year, day.month)
            month_counts[key] = month_counts.get(key, 0) + 1

        if not month_counts:
            frappe.throw("Unable to determine LOP month range.")

        # Pick dominant month (highest overlap)
        dominant_year, dominant_month = max(month_counts.items(), key=lambda x: x[1])[0]
        dominant_month_start = getdate(f"{dominant_year}-{dominant_month:02d}-01")

        # 2. Fetch Payroll Setting
        setting = get_previous_payroll_master_setting(self, dominant_year, dominant_month)
        if not setting:
            frappe.throw("No applicable Payroll Master Setting found.")

        payroll_days = setting.payroll_days or 30
        da_percent = float(setting.dearness_allowance_ or 0)
        self.employee_da_for_payroll_period = da_percent

        # 3. Get Base Salary from SSA
        base_salary = frappe.db.get_value(
            "Salary Structure Assignment",
            {
                "employee": self.employee_id,
                "from_date": ["<=", dominant_month_start],
                "docstatus": 1
            },
            "base",
            order_by="from_date desc"
        ) or frappe.db.get_value(
            "Salary Structure Assignment",
            {
                "employee": self.employee_id,
                "docstatus": 1
            },
            "base",
            order_by="from_date desc"
        )

        if not base_salary:
            frappe.throw("No active Salary Structure Assignment found for the employee.")

        self.base_salary = base_salary

        # 4. Apprentice shortcut
        if self.employment_type == "Apprentice":
            self.lop_amount = (base_salary / payroll_days) * lop_days
            return

        # 5. Get Service Weightage (with fallback)
        service_weightage = get_effective_service_weightage(self.employee_id, dominant_year, dominant_month)
        self.employee_service_weightage = service_weightage

        # 6. LOP Calculations
        self.lop_amount = (base_salary / payroll_days) * lop_days
        self.employee_service_weightage_loss = round((service_weightage / payroll_days) * lop_days, 2)
        da_loss = ((base_salary + service_weightage) * da_percent / payroll_days) * lop_days
        self.employee_da_loss_for_payroll_period = round(da_loss, 2)

    def ensure_unique_lop_start_date_per_employee(self):
        """
        Prevent multiple LOP records for the same employee with the same start date.
        """
        existing = frappe.db.exists(
            "Lop Per Request",
            {
                "employee_id": self.employee_id,
                "start_date": self.start_date,
                "name": ["!=", self.name],
            }
        )
        if existing:
            frappe.throw(
                f"A LOP request already exists for employee <b>{self.employee_id}</b> "
                f"with start date <b>{self.start_date}</b> in <b>{self.payroll_month} {self.payroll_year}</b>. "
                f"Please check the existing records for <b>{self.payroll_month} {self.payroll_year}</b> to avoid duplication."
            )


# === Utility Function ===

def get_effective_service_weightage(employee_id, year, month):
    """
    Fetch most recent service weightage entry before or equal to the given year/month.
    Falls back to Employee.custom_service_weightage_emp if no entry is found.
    """
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }

    rows = frappe.get_all(
        "Employee Service Weightage",
        filters={"employee_id": employee_id},
        fields=["service_weightage", "payroll_year", "payroll_month"],
        order_by="payroll_year desc"
    )

    for row in rows:
        row_year = int(row.payroll_year)
        row_month = month_map.get(row.payroll_month)

        if (row_year < year) or (row_year == year and row_month <= month):
            return float(row.service_weightage or 0)

    # Fallback from Employee
    fallback = frappe.db.get_value(
        "Employee",
        {"employee": employee_id},
        "custom_service_weightage_emp"
    ) or 0.0

    return float(fallback)
