# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class EmployeeReimbursementWages(Document):

	def validate(self):
		reimbursement_date = getdate(self.reimbursement_date)

		if not self.employee_id:
			frappe.throw("Employee is required to fetch salary and service weightage.")

		# Get Salary Slip for this employee within reimbursement date
		# salary_slip = frappe.db.get_value(
		# 	"Salary Slip",
		# 	{
		# 		"employee": self.employee_id,
		# 		"start_date": ["<=", reimbursement_date],
		# 		"end_date": [">=", reimbursement_date],
		# 		"docstatus": 1
		# 	},
		# 	["name", "custom_dearness_allowance_"],
		# 	as_dict=True
		# )

		base = 0
		da_percent = 0

		# if salary_slip:
		# 	slip_name = salary_slip.name
		# 	da_percent = float(salary_slip.custom_dearness_allowance_ or 0)

		# 	# Fetch Basic Pay from Salary Slip Earnings (Salary Detail)
		# 	base = frappe.db.get_value("Salary Detail", {
		# 		"parent": slip_name,
		# 		"parenttype": "Salary Slip",
		# 		"salary_component": "Basic"
		# 	}, "amount")

		# Fallback: base from Salary Structure Assignment (Basic component)
		if not base:
			assignment = frappe.db.sql("""
				SELECT name, base FROM `tabSalary Structure Assignment`
				WHERE employee = %s AND from_date <= %s AND docstatus = 1
				ORDER BY from_date DESC LIMIT 1
			""", (self.employee_id, reimbursement_date), as_dict=True)

			if assignment:
				base = assignment[0].base


		if not base:
			frappe.throw("Base Salary could not be determined from Salary Slip or Salary Structure Assignment.")

		self.reimbursement_basic_pay = base
		basic_pay = float(base)

		# Get Service Weightage from Employee Payroll Details
		sw_doc = frappe.db.sql("""
			SELECT service_weightage FROM `tabEmployee Payroll Details`
			WHERE employee = %s AND start_date <= %s AND end_date >= %s
			ORDER BY start_date DESC LIMIT 1
		""", (self.employee_id, reimbursement_date, reimbursement_date), as_dict=True)

		service_weightage = float(sw_doc[0].service_weightage) if sw_doc else 0
		self.reimbursement_service_weightage = service_weightage

		# ----- CONDITION 1: When LOP is in DAYS -----
		if float(self.no_of_days or 0) > 0:
			# Calculate HRA: (BP + SW) * 0.16
			hra = (basic_pay + service_weightage) * 0.16
			self.reimbursement_hra = hra

			# DA: (BP + SW) * DA%
			da = (basic_pay + service_weightage) * (da_percent / 100)
			self.reimbursement_da = da

			# LOP Refund Amount
			lop_refund = (basic_pay + service_weightage + hra + da) * float(self.no_of_days) / 30
			self.lop_refund_amount = round(lop_refund, 2)

		# ----- CONDITION 2: When LOP is in HOURS -----
		elif float(self.tl_hours or 0) > 0:
			refund_hours = float(self.tl_hours)

			# Variable DA
			vda = (basic_pay + service_weightage) * (da_percent / 100)
			self.reimbursement_da = vda
			self.reimbursement_hra = 0  # HRA is not considered for hours-based refund

			# Refund Amount
			lop_refund = (basic_pay + service_weightage + vda) * refund_hours / 240
			self.lop_refund_amount = round(lop_refund, 2)

			# PF Deduction
			pf_deduction = (basic_pay + service_weightage + vda) * 0.12 * (refund_hours / 240)
			self.lop_pf_deduction = round(pf_deduction, 2)

		else:
			frappe.throw("Either 'No. of Days' or 'LOP Refund Hours' must be provided.")









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
