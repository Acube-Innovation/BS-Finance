# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class EmployeeReimbursementWages(Document):

	def validate(self):
		# Convert reimbursement date to date object
		reimbursement_date = getdate(self.reimbursement_date)

		# Ensure required fields are available
		if not (self.reimbursement_basic_pay and self.reimbursement_service_weightage and self.no_of_days):
			frappe.throw("Basic Pay, Service Weightage, and No. of Days are mandatory to calculate LOP Refund Amount.")

		# Parse values
		basic_pay = float(self.reimbursement_basic_pay or 0)
		service_weightage = float(self.reimbursement_service_weightage or 0)

		# Calculate HRA: (BP + SW) * 0.16
		hra = (basic_pay + service_weightage) * 0.16
		self.reimbursement_hra = hra

		# Fetch DA Percent from "Dearness Allowance Backlog"
		dearness_allowance_percent = 0
		da_backlog = frappe.db.get_value(
			"Dearness Allowance Backlog",
			{
				"payroll_start_date": ["<=", reimbursement_date],
				"payroll_end_date": [">=", reimbursement_date]
			},
			"dearness_allowance_percent"
		)

		if da_backlog:
			dearness_allowance_percent = float(da_backlog)

		# Calculate DA: (BP + SW) * DA%
		da = (basic_pay + service_weightage) * (dearness_allowance_percent / 100)
		self.reimbursement_da = da

		# Final LOP Refund Amount: (BP + SW + HRA + DA) * No. of Days / 30
		lop_refund = (basic_pay + service_weightage + hra + da) * float(self.no_of_days or 0) / 30
		self.lop_refund_amount = round(lop_refund, 2)



	# def validate(self):
	# 	reimbursement_date = getdate(self.reimbursement_date)

	# 	frappe.msgprint(f"BP: {self.reimbursement_basic_pay}, SW: {self.reimbursement_service_weightage}, Days: {self.no_of_days}")

	# 	if not (self.reimbursement_basic_pay and self.reimbursement_service_weightage and self.no_of_days):
	# 		frappe.throw("Basic Pay, Service Weightage, and No. of Days are mandatory to calculate LOP Refund Amount.")

	# 	basic_pay = float(self.reimbursement_basic_pay or 0)
	# 	service_weightage = float(self.reimbursement_service_weightage or 0)

	# 	hra = (basic_pay + service_weightage) * 0.16
	# 	self.reimbursement_hra = hra

	# 	dearness_allowance_percent = 0
	# 	da_backlog = frappe.db.get_value(
	# 		"Dearness Allowance Backlog",
	# 		{
	# 			"payroll_start_date": ["<=", reimbursement_date],
	# 			"payroll_end_date": [">=", reimbursement_date]
	# 		},
	# 		"dearness_allowance_percent"
	# 	)

	# 	if da_backlog:
	# 		dearness_allowance_percent = float(da_backlog)
	# 		frappe.msgprint(f"DA% found: {dearness_allowance_percent}")
	# 	else:
	# 		frappe.msgprint("❌ No DA% found for given date.")

	# 	da = (basic_pay + service_weightage) * (dearness_allowance_percent / 100)
	# 	self.reimbursement_da = da

	# 	lop_refund = (basic_pay + service_weightage + hra + da) * float(self.no_of_days or 0) / 30
	# 	self.lop_refund_amount = round(lop_refund, 2)
