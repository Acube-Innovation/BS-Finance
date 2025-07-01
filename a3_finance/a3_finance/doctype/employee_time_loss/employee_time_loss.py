# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
import calendar

class EmployeeTimeLoss(Document):


	# def validate(self):
	# 	# ✅ Ensure required fields are not None (0 is allowed)
	# 	if self.basic_pay is None or self.service_weightage is None or self.time_loss_hours is None:
	# 		frappe.throw("Basic Pay, Service Weightage, and Time Loss Hours must not be empty.")

	# 	# ✅ Fetch DA % from Payroll Master Settings
	# 	variable_percent = frappe.db.get_single_value("Payroll Master Settings", "dearness_allowance_") or 0

	# 	# ✅ Convert to float
	# 	basic_pay = float(self.basic_pay)
	# 	service_weightage = float(self.service_weightage)
	# 	time_loss_hours = float(self.time_loss_hours)
	# 	variable_percent = float(variable_percent)

	# 	# ✅ Compute Variable DA
	# 	variable_da = (basic_pay + service_weightage) * (variable_percent / 100)

	# 	# ✅ Store result
	# 	self.variable_da = variable_da

	# 	# ✅ Final Time Loss Amount calculation
	# 	self.time_loss_amount = (basic_pay + service_weightage + variable_da) * time_loss_hours / 240








	def validate(self):
		# ✅ Ensure required fields are not None (0 is allowed)
		if self.basic_pay is None or self.service_weightage is None or self.time_loss_hours is None:
			frappe.throw("Basic Pay, Service Weightage, and Time Loss Hours must not be empty.")
		if not self.time_loss_month or not self.time_loss_year:
			frappe.throw("Please select both Time Loss Month and Time Loss Year.")

		# ✅ Convert to float
		basic_pay = float(self.basic_pay)
		service_weightage = float(self.service_weightage)
		time_loss_hours = float(self.time_loss_hours)

		# ✅ Convert selected month and year into a date (e.g., 2025-April → 2025-04-01)
		try:
			month_number = list(calendar.month_name).index(self.time_loss_month)  # Converts 'April' → 4
		except ValueError:
			frappe.throw("Invalid Time Loss Month")

		target_date_str = f"{self.time_loss_year}-{month_number:02d}-01"
		target_date = getdate(target_date_str)

		# ✅ Fetch DA % from backlog where target_date falls in start and end range
		backlog = frappe.get_all(
			"Dearness Allowance Backlog",
			filters={
				"payroll_start_date": ["<=", target_date],
				"payroll_end_date": [">=", target_date]
			},
			fields=["dearness_allowance_percent"],
			limit=1
		)

		# ✅ Use found % or default to 0
		variable_percent = float(backlog[0].dearness_allowance_percent) if backlog else 0

		# ✅ Compute Variable DA
		variable_da = (basic_pay + service_weightage) * (variable_percent / 100)
		self.variable_da = variable_da

		# ✅ Final Time Loss Amount calculation
		self.time_loss_amount = (basic_pay + service_weightage + variable_da) * time_loss_hours / 240










	# def validate(self):
	# 	# ✅ Ensure all required fields are present
	# 	if not self.basic_pay or not self.service_weightage or not self.time_loss_hours:
	# 		frappe.throw("Basic Pay, Service Weightage, and Time Loss Hours are required to calculate Time Loss Amount.")

	# 	# ✅ Fetch Variable DA % from Payroll Master Settings (Single Doctype)
	# 	variable_percent = frappe.db.get_single_value("Payroll Master Settings", "dearness_allowance_") or 0

	# 	# ✅ Convert all values to float (ensures safety)
	# 	basic_pay = float(self.basic_pay or 0)
	# 	service_weightage = float(self.service_weightage or 0)
	# 	time_loss_hours = float(self.time_loss_hours or 0)
	# 	variable_percent = float(variable_percent or 0)

	# 	# ✅ Calculate Variable DA
	# 	variable_da = (basic_pay + service_weightage) * (variable_percent / 100)

	# 	# ✅ Store Variable DA
	# 	self.variable_da = variable_da

	# 	# ✅ Calculate Final Time Loss Amount
	# 	self.time_loss_amount = (basic_pay + service_weightage + variable_da) * time_loss_hours / 240
