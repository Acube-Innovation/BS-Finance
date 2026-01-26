# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class PaySheet(Document):
	def before_insert(self):
	
		user = frappe.session.user
		

		if user in ("Guest", "Administrator"):
			return
		
		
		employee = frappe.db.get_value("Employee", {"user_id": user})
		
		if employee:
			self.prepared_by = employee

