# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import calendar
from frappe.utils import getdate

class LopDaysSummary(Document):
	def validate(self):
	# Extract year and month from start_date
		if not self.start_date:
			frappe.throw("Start Date is required to determine applicable Payroll Settings.")
		
		start = getdate(self.start_date)
		month_number = start.month
		year = start.year

		# Fetch the relevant Payroll Master Setting
		setting = self.get_previous_payroll_master_setting(year, month_number)

		if not setting:
			frappe.throw("No applicable Payroll Master Setting found for this period.")

		# Use payroll_days from settings
		payroll_days = setting.payroll_days or 30

		# Fetch salary structure assignment (still based on payroll_month and year, assuming that stays unchanged)
		assignment = self.get_salary_structure_assignment(self.employee_id, self.payroll_month, self.payroll_year)
		if assignment:
			self.base_salary = assignment["base"]

			try:
				days_present = float(self.no__of_days)
				self.lop_amount = (self.base_salary / payroll_days) * (payroll_days - days_present)
			except Exception as e:
				frappe.throw(f"Invalid 'No. of Days' value: {e}")
		else:
			frappe.msgprint("No active Salary Structure Assignment found for this payroll period.")

	def get_salary_structure_assignment(self, employee, month, year):
		month_number = list(calendar.month_name).index(month)
		start_date = f"{year}-{month_number:02d}-01"
		last_day = calendar.monthrange(int(year), month_number)[1]
		end_date = f"{year}-{month_number:02d}-{last_day}"

		result = frappe.db.sql("""
			SELECT
				name,
				employee,
				salary_structure,
				base,
				from_date
			FROM `tabSalary Structure Assignment`
			WHERE
				employee = %s
				AND from_date <= %s
				AND docstatus = 1
			ORDER BY from_date DESC
			LIMIT 1
		""", (employee, end_date), as_dict=True)

		return result[0] if result else None

	def get_previous_payroll_master_setting(self, given_year, given_month_number):
		years_to_consider = [int(given_year), int(given_year) - 1]

		result = frappe.get_all(
			"Payroll Master Setting",
			filters={
				"payroll_year": ["in", years_to_consider]
			},
			fields=["name", "payroll_year", "payroll_month_number", "payroll_days"],
			order_by="payroll_year desc, payroll_month_number desc",
			limit=20
		)

		for record in result:
			year = int(record["payroll_year"])
			month = int(record["payroll_month_number"])

			if (year < given_year) or (year == given_year and month <= given_month_number):
				return frappe.get_doc("Payroll Master Setting", record["name"])

		return None
