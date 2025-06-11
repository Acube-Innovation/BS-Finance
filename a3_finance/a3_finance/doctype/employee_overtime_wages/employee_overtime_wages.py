# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeOvertimeWages(Document):


	def validate(self):
		try:
			# Fetch basic pay and service weightage
			basic_pay = float(self.basic_pay or 0)
			service_weightage = float(self.service_weightage or 0)
			overtime_hours = float(self.overtime_hours or 0)

			# Fetch dearness_allowance from Payroll Master Settings
			da_settings = frappe.get_single("Payroll Master Settings")
			dearness_allowance = float(getattr(da_settings, "dearness_allowance_", 0))

			# Calculate variable DA
			self.variable_da = (basic_pay + service_weightage) * dearness_allowance

			# Calculate total amount
			self.total_amount = (basic_pay + service_weightage + self.variable_da) / 240 * overtime_hours

		except Exception as e:
			frappe.throw(f"Error during calculation: {e}")

