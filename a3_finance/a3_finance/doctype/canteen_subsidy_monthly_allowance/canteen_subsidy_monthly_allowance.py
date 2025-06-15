# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CanteenSubsidyMonthlyAllowance(Document):


	def validate(self):
		active_employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name"])

		for emp in active_employees:
			# Check if an Additional Salary already exists to avoid duplicates
			if not frappe.db.exists(
				"Additional Salary",
				{
					"employee": emp.name,
					"salary_component": "Canteen Subsidy",
					"payroll_date": self.payroll_date,
				}
			):
				additional_salary = frappe.new_doc("Additional Salary")
				additional_salary.update({
					"employee": emp.name,
					"salary_component": "Canteen Subsidy",
					"payroll_date": self.payroll_date,
					"amount": self.canteen_subsidy_monthly_allowance,
					"overwrite_salary_structure_amount": 0
				})
				additional_salary.insert()
				additional_salary.submit()
				# frappe.msgprint(f"Created Additional Salary for employee {emp.name}")
