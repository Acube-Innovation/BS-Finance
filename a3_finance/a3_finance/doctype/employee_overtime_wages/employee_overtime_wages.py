# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class EmployeeOvertimeWages(Document):


	# def validate(self):
	# 	try:
	# 		# Fetch input values
	# 		basic_pay = float(self.basic_pay or 0)
	# 		service_weightage = float(self.service_weightage or 0)
	# 		overtime_hours = float(self.overtime_hours or 0)

	# 		# Ensure quarter and year are selected
	# 		if not self.quarter_details or not self.quarter_year:
	# 			frappe.throw("Please select both Quarter Details and Quarter Year.")

	# 		# Convert quarter_year to integer (financial year)
	# 		fy_year = int(self.quarter_year)

	# 		# Define date ranges for each financial quarter
	# 		quarter_ranges = {
	# 			"First Quarter": (f"{fy_year}-04-01", f"{fy_year}-06-30"),
	# 			"Second Quarter": (f"{fy_year}-07-01", f"{fy_year}-09-30"),
	# 			"Third Quarter": (f"{fy_year}-10-01", f"{fy_year}-12-31"),
	# 			"Fourth Quarter": (f"{fy_year}-01-01", f"{fy_year}-03-31"),
	# 		}

	# 		start_date_str, end_date_str = quarter_ranges.get(self.quarter_details)
	# 		start_date = getdate(start_date_str)
	# 		end_date = getdate(end_date_str)

	# 		# Fetch matching Dearness Allowance Backlog entry
	# 		backlog = frappe.get_all("Dearness Allowance Backlog",
	# 			filters={
	# 				"payroll_start_date": ["<=", end_date],
	# 				"payroll_end_date": [">=", start_date]
	# 			},
	# 			fields=["dearness_allowance_percent"],
	# 			limit=1
	# 		)

	# 		# Use percent if found, otherwise default to 0
	# 		da_percent = float(backlog[0].dearness_allowance_percent) if backlog else 0

	# 		# Calculate variable DA
	# 		self.variable_da = (basic_pay + service_weightage) * (da_percent / 100)

	# 		# Calculate total amount
	# 		self.total_amount = (basic_pay + service_weightage + self.variable_da) / 240 * overtime_hours

	# 	except Exception as e:
	# 		frappe.throw(f"Error during calculation: {e}")

	def validate(self):
		import calendar
		from frappe.utils import getdate, flt

		try:
			# Validate input
			if not self.employee_id:
				frappe.throw("Employee is required.")
			if not self.quarter_details or not self.quarter_year:
				frappe.throw("Please select both Quarter Details and Quarter Year.")
			if self.overtime_hours is None:
				frappe.throw("Overtime Hours must be provided.")

			# Convert hours from HH.MM to decimal
			def convert_overtime_hours(time_value):
				hours = int(time_value)
				minutes = round((time_value - hours) * 100)
				if minutes not in [0, 15, 30, 45]:
					frappe.throw("Overtime minutes must be one of: .00, .15, .30, or .45")
				return hours + (minutes / 60)

			overtime_hours = convert_overtime_hours(float(self.overtime_hours or 0))

			fy_year = int(self.quarter_year)
			quarter = self.quarter_details.upper()

			# Quarter Date Range Mapping
			quarter_ranges = {
				"Q1": (f"{fy_year}-04-01", f"{fy_year}-06-30"),
				"Q2": (f"{fy_year}-07-01", f"{fy_year}-09-30"),
				"Q3": (f"{fy_year}-10-01", f"{fy_year}-12-31"),
				"Q4": (f"{fy_year + 1}-01-01", f"{fy_year + 1}-03-31"),
			}

			if quarter not in quarter_ranges:
				frappe.throw("Invalid Quarter selected.")

			start_date_str, end_date_str = quarter_ranges[quarter]
			ssa_date = getdate(start_date_str)
			end_date = getdate(end_date_str)

			# Get base pay from SSA
			ssa = frappe.get_all(
				"Salary Structure Assignment",
				filters={
					"employee": self.employee_id,
					"from_date": ["<=", ssa_date],
					"docstatus": 1
				},
				fields=["base"],
				order_by="from_date desc",
				limit=1
			)
			base = flt(ssa[0].base) if ssa else 0

			# Fallback to latest SSA
			if not base:
				alt_ssa = frappe.get_all(
					"Salary Structure Assignment",
					filters={"employee": self.employee_id, "docstatus": 1},
					fields=["base"],
					order_by="from_date desc",
					limit=1
				)
				base = flt(alt_ssa[0].base) if alt_ssa else 0

			self.basic_pay = base

			# Get Service Weightage
			sw_month = "April" if quarter == "Q1" else "March"
			sw_year = self.quarter_year

			s_weightage = frappe.get_value(
				"Employee Service Weightage",
				{
					"employee_id": self.employee_id,
					"payroll_month": sw_month,
					"payroll_year": str(sw_year)
				},
				"service_weightage"
			)
			if s_weightage:
				self.service_weightage = flt(s_weightage)
			else:
				self.service_weightage = frappe.db.get_value("Employee",{'name':self.employee_id},'custom_service_weightage_emp')

			# Get DA from Payroll Master Setting
			if quarter == "Q1":
				month_number = 4
				year_number = fy_year
			elif quarter == "Q4":
				month_number = 1
				year_number = self.quarter_year
			else:
				# Default: fallback to last month of quarter
				month_number = ssa_date.month
				print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm",month_number)
				year_number = ssa_date.year

			da_setting = frappe.get_all(
				"Payroll Master Setting",
				filters={
					"payroll_month_number": month_number,
					"payroll_year": year_number
				},
				fields=["dearness_allowance_"],
				limit=1
			)
			da_percent = flt(da_setting[0].dearness_allowance_) if da_setting else 0

			self.variable_da = (base + self.service_weightage) * da_percent

			# Final overtime amount
			self.total_amount = (base + self.service_weightage + self.variable_da) * overtime_hours / 240

		except Exception as e:
			frappe.throw(f"Error during calculation: {e}")
