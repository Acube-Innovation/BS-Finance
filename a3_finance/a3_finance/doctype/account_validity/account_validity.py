# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AccountValidity(Document):
    def validate(self):
        if self.start_date > self.end_date:
            frappe.throw("Start Date cannot be after End Date")

