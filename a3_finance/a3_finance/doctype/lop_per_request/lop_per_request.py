# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import calendar
from frappe.utils import getdate

class LopPerRequest(Document):
	def validate(self):
		from frappe.utils import getdate

		if not self.start_date:
			return

		start = getdate(self.start_date)
		month_number = start.month
		year = start.year

		# === 1. Get Payroll Master Setting ===
		setting = self.get_previous_payroll_master_setting(year, month_number)
		if not setting:
			frappe.throw("No applicable Payroll Master Setting found for this period.")

		payroll_days = setting.payroll_days or 30
		da_percent = float(setting.dearness_allowance_ or 0)

		self.employee_da_for_payroll_period = da_percent

		# === 2. Get Base Salary from SSA (first try from given date, else fallback to latest) ===
		base_salary = frappe.db.get_value(
			"Salary Structure Assignment",
			{
				"employee": self.employee_id,
				"from_date": ["<=", start],
				"docstatus": 1
			},
			"base",
			order_by="from_date desc"
		)

		# ❗ Fallback if not found: use latest SSA
		if not base_salary:
			base_salary = frappe.db.get_value(
				"Salary Structure Assignment",
				{
					"employee": self.employee_id,
					"docstatus": 1
				},
				"base",
				order_by="from_date desc"
			)

		if not base_salary:
			frappe.throw("No active Salary Structure Assignment found for the employee.")

		self.base_salary = base_salary

		# === 3. Get Service Weightage ===
		sw_row = frappe.db.get_value(
			"Employee Service Weightage",
			{
				"employee_id": self.employee_id,
				"payroll_month": start.strftime("%B"),
				"payroll_year": str(year)
			},
			"service_weightage",
			as_dict=True
		)

		service_weightage = float(sw_row.service_weightage or 0) if sw_row else 0
		self.employee_service_weightage = service_weightage

		# === 4. Calculate Losses ===
		try:
			lop_days = float(self.no__of_days or 0)
			self.lop_amount = (self.base_salary / payroll_days) * lop_days

			# Service Weightage Loss
			self.employee_service_weightage_loss = round((service_weightage / payroll_days) * lop_days, 2)

			# DA Loss
			lop_da_loss = ((base_salary + service_weightage) * da_percent / payroll_days) * lop_days
			self.employee_da_loss_for_payroll_period = round(lop_da_loss, 2)

		except Exception as e:
			frappe.throw(f"Invalid 'LOP Days' value for loss calculations: {e}")


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
