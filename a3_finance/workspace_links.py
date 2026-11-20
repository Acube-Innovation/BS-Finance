"""Links of a3_finance reports on ERPNext's own workspaces (after_migrate hook).

ERPNext's standard workspaces are synced from its files when it is updated, which can drop links added to them, and
saving them in developer mode would write into ERPNext's files; so the links are added as rows, again after every
migrate when missing."""

import frappe

# (workspace, card, report)
LINKS = [
	# point 26: next to Budget Variance Report
	("Accounting", "Cost Center and Budgeting", "Cost Center Budget vs Actual"),
]


def add_links():
	for workspace, card, report in LINKS:
		add_report_link(workspace, card, report)


def add_report_link(workspace, card, report):
	if not frappe.db.exists("Workspace", workspace) or not frappe.db.exists("Report", report):
		return
	links = frappe.get_all(
		"Workspace Link",
		filters={"parent": workspace, "parenttype": "Workspace", "parentfield": "links"},
		fields=["name", "idx", "type", "label", "link_to", "link_count"],
		order_by="idx",
	)
	if any(link.type == "Link" and link.link_to == report for link in links):
		return
	card_row = next((link for link in links if link.type == "Card Break" and link.label == card), None)
	if not card_row:
		return

	# after the card's last link
	position = card_row.idx
	for link in links:
		if link.idx <= card_row.idx:
			continue
		if link.type == "Card Break":
			break
		position = link.idx
	for link in links:
		if link.idx > position:
			frappe.db.set_value("Workspace Link", link.name, "idx", link.idx + 1, update_modified=False)

	frappe.get_doc(
		{
			"doctype": "Workspace Link",
			"parent": workspace,
			"parenttype": "Workspace",
			"parentfield": "links",
			"idx": position + 1,
			"type": "Link",
			"label": report,
			"link_type": "Report",
			"link_to": report,
			"is_query_report": 1,
			"onboard": 0,
			"hidden": 0,
		}
	).db_insert()
	frappe.db.set_value(
		"Workspace Link", card_row.name, "link_count", (card_row.link_count or 0) + 1, update_modified=False
	)
	frappe.clear_cache()
