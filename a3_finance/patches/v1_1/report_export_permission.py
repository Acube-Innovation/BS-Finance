"""Export permission for the Accounts and Stock roles on the doctypes behind the ageing reports (BrahMos Reports &
Observations Tracker points 3, 4 and 5).

A report's Export (⋯ menu > Export) is offered, and allowed, only to roles with Export on the report's reference
doctype: Accounts Payable (and Summary) → Purchase Invoice, Accounts Receivable (and Summary) → Sales Invoice, Stock
Ageing → Item. The Accounts User and Accounts Manager roles had no Export on Sales Invoice, Accounts User none on
Purchase Invoice, and the Stock and Accounts User roles none on Item, so those users had no Export in the reports.

Only the Export flag of a role's existing level-0 permission row (as set in Role Permission Manager) is switched on:
no permission row is added, and nothing else changes. Roles without a row are left out (logged).
"""

import frappe
from frappe.permissions import update_permission_property

EXPORT = {
	"Purchase Invoice": ("Accounts User", "Accounts Manager"),
	"Sales Invoice": ("Accounts User", "Accounts Manager"),
	"Item": ("Accounts User", "Stock User", "Stock Manager"),
}


def execute():
	skipped = []
	for doctype, roles in EXPORT.items():
		changed = False
		for role in roles:
			row = frappe.db.get_value(
				"Custom DocPerm",
				{"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
				["name", "read", "export"],
				as_dict=True,
			) or frappe.db.get_value(
				"DocPerm",
				{"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
				["name", "read", "export"],
				as_dict=True,
			)
			if not row or not row.read:
				skipped.append(f"{doctype}: {role}")
				continue
			if row.export:
				continue
			update_permission_property(doctype, role, 0, "export", 1, validate=False)
			changed = True
		if changed:
			frappe.clear_cache(doctype=doctype)
	if skipped:
		print("Export not set (role has no read permission row):", ", ".join(skipped))
