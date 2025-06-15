# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeServiceWeightage(Document):


    def validate(self):
        if self.employee_id and self.service_weightage:
            # Update the custom field in Employee
            frappe.db.set_value(
                "Employee",
                self.employee_id,
                "custom_service_weightage",
                self.service_weightage
            )
