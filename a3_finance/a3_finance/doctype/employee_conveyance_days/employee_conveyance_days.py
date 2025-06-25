# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
import math
from frappe.model.document import Document


class EmployeeConveyanceDays(Document):
	def validate(self):
		if not self.employee or not self.present_days or not self.total_working_days:
			return

		# Fetch vehicle type from Employee
		self.vehicle_type = frappe.db.get_value("Employee", self.employee, "custom_vehicle_type")

		if not self.vehicle_type:
			return

		# Get payroll month/year from a date field (e.g., self.start_date)
		# if not self.start_date:
		# 	frappe.throw("Start Date is required to determine Payroll Master Setting.")

		# start = getdate(self.start_date)
		# month_number = start.month
		# year = start.year

		# Fetch the applicable Payroll Master Setting
		setting = get_previous_payroll_master_setting(self.payroll_year, self.payroll_date)
		if not setting:
			frappe.throw("No applicable Payroll Master Setting found for the given start date.")

		# Match vehicle type (case-insensitive) in the child table
		monthly_amount = 0
		for row in setting.conveyance_allowance:
			if row.type_of_vehicles.strip().lower() == self.vehicle_type.strip().lower():
				monthly_amount = row.amount_per_month
				break

		self.monthly_conveyance_amount = monthly_amount  # Or however you're storing this field
		# Calculate minimum working days (75% of total), rounded up
		self.minimum_working_days = math.ceil(0.75 * self.total_working_days)

		# Apply rules
		if self.present_days < 10:
			self.conveyance_charges = 0
			self.pro_rata_charges = 0

		elif self.present_days >= self.minimum_working_days:
			self.conveyance_charges = monthly_amount
			self.pro_rata_charges = round((monthly_amount/self.total_working_days)*self.present_days,2)

		else:
			prorated_amount = (monthly_amount / self.minimum_working_days) * self.present_days
			self.conveyance_charges = monthly_amount
			self.pro_rata_charges = round(prorated_amount, 2)

@staticmethod
def get_previous_payroll_master_setting(year, month_number):
    import calendar

    year = int(year)

    # Convert month name to number if needed
    if isinstance(month_number, str):
        month_number = list(calendar.month_name).index(month_number)

    years_to_consider = [year, year - 1]

    settings = frappe.get_all(
        "Payroll Master Setting",
        filters={"payroll_year": ["in", years_to_consider]},
        fields=["name", "payroll_year", "payroll_month_number"],
        order_by="payroll_year desc, payroll_month_number desc",
        limit=20
    )

    for record in settings:
        ry = int(record["payroll_year"])
        rm = int(record["payroll_month_number"])
        if ry < year or (ry == year and rm <= month_number):
            return frappe.get_doc("Payroll Master Setting", record["name"])

    return None
