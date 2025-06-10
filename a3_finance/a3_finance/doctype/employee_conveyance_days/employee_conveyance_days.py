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

		# Fetch amount from Payroll Master
		master = frappe.get_single("Payroll Master Settings")
		monthly_amount = 0
		for row in master.conveyance_allowance:
			if row.type_of_vehicles.strip().lower() == self.vehicle_type.strip().lower():
				monthly_amount = row.amount_per_month
				break


		# Calculate minimum working days (75% of total), rounded up
		self.minimum_working_days = math.ceil(0.75 * self.total_working_days)

		# Apply rules
		if self.present_days < 10:
			self.conveyance_charges = 0
			self.pro_rata_charges = 0

		elif self.present_days >= self.minimum_working_days:
			self.conveyance_charges = monthly_amount
			self.pro_rata_charges = monthly_amount

		else:
			prorated_amount = (monthly_amount / self.minimum_working_days) * self.present_days
			self.conveyance_charges = monthly_amount
			self.pro_rata_charges = round(prorated_amount, 2)