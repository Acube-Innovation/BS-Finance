# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class EmployeeOvertimeWages(Document):


	def validate(self):
		try:
			# Fetch input values
			basic_pay = float(self.basic_pay or 0)
			service_weightage = float(self.service_weightage or 0)
			overtime_hours = float(self.overtime_hours or 0)

			# Ensure quarter and year are selected
			if not self.quarter_details or not self.quarter_year:
				frappe.throw("Please select both Quarter Details and Quarter Year.")

			# Convert quarter_year to integer (financial year)
			fy_year = int(self.quarter_year)

			# Define date ranges for each financial quarter
			quarter_ranges = {
				"First Quarter": (f"{fy_year}-04-01", f"{fy_year}-06-30"),
				"Second Quarter": (f"{fy_year}-07-01", f"{fy_year}-09-30"),
				"Third Quarter": (f"{fy_year}-10-01", f"{fy_year}-12-31"),
				"Fourth Quarter": (f"{fy_year}-01-01", f"{fy_year}-03-31"),
			}

			start_date_str, end_date_str = quarter_ranges.get(self.quarter_details)
			start_date = getdate(start_date_str)
			end_date = getdate(end_date_str)

			# Fetch matching Dearness Allowance Backlog entry
			backlog = frappe.get_all("Dearness Allowance Backlog",
				filters={
					"payroll_start_date": ["<=", end_date],
					"payroll_end_date": [">=", start_date]
				},
				fields=["dearness_allowance_percent"],
				limit=1
			)

			# Use percent if found, otherwise default to 0
			da_percent = float(backlog[0].dearness_allowance_percent) if backlog else 0

			# Calculate variable DA
			self.variable_da = (basic_pay + service_weightage) * (11 / 100)

			# Calculate total amount
			self.total_amount = (basic_pay + service_weightage + self.variable_da) / 240 * overtime_hours

		except Exception as e:
			frappe.throw(f"Error during calculation: {e}")
