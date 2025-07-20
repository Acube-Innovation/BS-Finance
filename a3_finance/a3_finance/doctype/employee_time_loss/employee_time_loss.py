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








	# def validate(self):
	# 	# ✅ Ensure required fields are not None (0 is allowed)
	# 	if self.basic_pay is None or self.service_weightage is None or self.time_loss_hours is None:
	# 		frappe.throw("Basic Pay, Service Weightage, and Time Loss Hours must not be empty.")
	# 	if not self.time_loss_month or not self.time_loss_year:
	# 		frappe.throw("Please select both Time Loss Month and Time Loss Year.")

	# 	# ✅ Convert to float
	# 	basic_pay = float(self.basic_pay)
	# 	service_weightage = float(self.service_weightage)
	# 	time_loss_hours = float(self.time_loss_hours)

	# 	# ✅ Convert selected month and year into a date (e.g., 2025-April → 2025-04-01)
	# 	try:
	# 		month_number = list(calendar.month_name).index(self.time_loss_month)  # Converts 'April' → 4
	# 	except ValueError:
	# 		frappe.throw("Invalid Time Loss Month")

	# 	target_date_str = f"{self.time_loss_year}-{month_number:02d}-01"
	# 	target_date = getdate(target_date_str)

	# 	# ✅ Fetch DA % from backlog where target_date falls in start and end range
	# 	backlog = frappe.get_all(
	# 		"Dearness Allowance Backlog",
	# 		filters={
	# 			"payroll_start_date": ["<=", target_date],
	# 			"payroll_end_date": [">=", target_date]
	# 		},
	# 		fields=["dearness_allowance_percent"],
	# 		limit=1
	# 	)

	# 	# ✅ Use found % or default to 0
	# 	variable_percent = float(backlog[0].dearness_allowance_percent) if backlog else 0

	# 	# ✅ Compute Variable DA
	# 	variable_da = (basic_pay + service_weightage) * (variable_percent / 100)
	# 	self.variable_da = variable_da

	# 	# ✅ Final Time Loss Amount calculation
	# 	self.time_loss_amount = (basic_pay + service_weightage + variable_da) * time_loss_hours / 240
	def validate(self):
		import calendar
		from frappe.utils import getdate, flt

		if not self.employee_id:
			frappe.throw("Employee ID is required.")

		if self.time_loss_hours is None:
			frappe.throw("Time Loss Hours must not be empty.")

		if not self.time_loss_month or not self.time_loss_year:
			frappe.throw("Please select both Time Loss Month and Year.")

		# Convert month name to number
		try:
			tl_month_number = list(calendar.month_name).index(self.time_loss_month)
		except ValueError:
			frappe.throw("Invalid Time Loss Month")

		tl_date = getdate(f"{self.time_loss_year}-{tl_month_number:02d}-01")

		# 1️⃣ Get base from SSA valid for Time Loss Month
		base_assignment = frappe.db.sql("""
			SELECT base FROM `tabSalary Structure Assignment`
			WHERE employee = %s AND from_date <= %s AND docstatus = 1
			ORDER BY from_date DESC LIMIT 1
		""", (self.employee_id, tl_date), as_dict=True)

		# 2️⃣ If not found, fallback to Payroll Month
		if not base_assignment or not base_assignment[0].get("base"):
			if not self.payroll_month or not self.payroll_year:
				frappe.throw("Fallback failed: Provide Payroll Month and Year for base calculation.")
			
			try:
				payroll_month_number = list(calendar.month_name).index(self.payroll_month)
			except ValueError:
				frappe.throw("Invalid Payroll Month")

			payroll_date = getdate(f"{self.payroll_year}-{payroll_month_number:02d}-01")

			base_assignment = frappe.db.sql("""
				SELECT base FROM `tabSalary Structure Assignment`
				WHERE employee = %s AND from_date <= %s AND docstatus = 1
				ORDER BY from_date DESC LIMIT 1
			""", (self.employee_id, payroll_date), as_dict=True)

			if not base_assignment or not base_assignment[0].get("base"):
				frappe.throw("No valid Salary Structure Assignment found.")

		self.basic_pay = flt(base_assignment[0].base)

		if self.employment_type != "Apprentice":

			# ✅ Get Service Weightage
			s_weightage = frappe.get_value(
				"Employee Service Weightage",
				{
					"employee_id": self.employee_id,
					"payroll_month": self.time_loss_month,
					"payroll_year": self.time_loss_year
				},
				"service_weightage"
			)

			if s_weightage is None:
				# frappe.throw("No Service Weightage found for selected Time Loss Month and Year.")
				s_weightage= frappe.db.get_value("Employee",{'name':self.employee_id},'custom_service_weightage_emp')

			self.service_weightage = flt(s_weightage)

			# ✅ Map Time Loss Month to DA quarter start month
			def get_da_reference_month(month_num):
				if month_num in [4, 5, 6]:
					return 4  # April → Q1
				elif month_num in [7, 8, 9]:
					return 7  # July → Q2
				elif month_num in [10, 11, 12]:
					return 10  # October → Q3
				else:
					return 1  # Jan, Feb, Mar → Q4

			da_month_number = get_da_reference_month(tl_month_number)
			da_month = calendar.month_name[da_month_number]
			da_year = self.time_loss_year
			if da_month_number == 1:  # Q4 starts Jan, which may belong to next financial year
				da_year = int(self.time_loss_year) + 1 if tl_month_number in [1, 2, 3] else self.time_loss_year

			# ✅ Get DA from Payroll Master Setting for quarter-start month
			da_percent = frappe.db.get_value(
				"Payroll Master Setting",
				{
					"payroll_month_number": da_month_number,
					"payroll_year": self.time_loss_year
				},
				"dearness_allowance_"
			) or 0

			# ✅ Calculate Variable DA and Time Loss Amount
			variable_da = (self.basic_pay + self.service_weightage) * (flt(da_percent))
			self.variable_da = round(variable_da, 2)

			self.time_loss_amount = round(
				(self.basic_pay + self.service_weightage + self.variable_da) * flt(self.time_loss_hours) / 240,
				2
			)
		else:
			self.time_loss_amount = round(
				(self.basic_pay) * flt(self.time_loss_hours) / 240,
				2
			)





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
