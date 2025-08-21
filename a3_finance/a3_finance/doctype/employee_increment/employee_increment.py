# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.utils import today
from frappe.model.document import Document


class EmployeeIncrement(Document):
	def on_submit(doc):
		# Fetch latest Salary Structure Assignment
		ssa = frappe.db.get_value(
			"Salary Structure Assignment",
			{"employee": doc.employee, "docstatus": 1},
			["name", "salary_structure", "base", "income_tax_slab"],
			order_by="from_date desc",
			as_dict=True
		)

		if not ssa:
			frappe.throw("No Salary Structure Assignment found for this employee.")

		# Calculate new base salary
		new_base = ssa.base
		if doc.increment_amount:
			new_base += doc.increment_amount
		elif doc.increment_percentage:
			new_base += (ssa.base * doc.increment_percentage / 100)

		# Create new Salary Structure Assignment
		new_ssa = frappe.new_doc("Salary Structure Assignment")
		new_ssa.employee = doc.employee
		new_ssa.salary_structure = ssa.salary_structure
		new_ssa.base = new_base
		new_ssa.from_date = doc.from_date or today()
		if ssa.income_tax_slab:
			new_ssa.income_tax_slab = ssa.income_tax_slab

		new_ssa.insert(ignore_permissions=True)
		new_ssa.submit()

		# frappe.msgprint(f"New Salary Structure Assignment created: {new_ssa.name} with Base {new_base}")

