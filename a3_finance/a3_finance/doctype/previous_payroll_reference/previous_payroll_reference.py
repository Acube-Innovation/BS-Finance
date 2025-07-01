# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PreviousPayrollReference(Document):
	def validate(self):
		# Ensure required fields are present
		if not self.base_salary:
			frappe.throw("Base Salary is required to calculate HRA and DA.")
		if not self.service_weightage:
			self.service_weightage = 0
		if not self.hra_percent:
			self.hra_percent = 0
		if not self.da_percent:
			self.da_percent = 0

		base_total = self.base_salary + self.service_weightage

		# HRA Calculation
		self.hra_amount = round(base_total * (self.hra_percent / 100))
		self.variable_da_amount = round(base_total * (self.da_percent / 100))

