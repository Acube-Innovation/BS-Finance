# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeTimeLoss(Document):


	def validate(self):
		# ✅ Ensure required fields are not None (0 is allowed)
		if self.basic_pay is None or self.service_weightage is None or self.time_loss_hours is None:
			frappe.throw("Basic Pay, Service Weightage, and Time Loss Hours must not be empty.")

		# ✅ Fetch DA % from Payroll Master Settings
		variable_percent = frappe.db.get_single_value("Payroll Master Settings", "dearness_allowance_") or 0

		# ✅ Convert to float
		basic_pay = float(self.basic_pay)
		service_weightage = float(self.service_weightage)
		time_loss_hours = float(self.time_loss_hours)
		variable_percent = float(variable_percent)

		# ✅ Compute Variable DA
		variable_da = (basic_pay + service_weightage) * (variable_percent / 100)

		# ✅ Store result
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
