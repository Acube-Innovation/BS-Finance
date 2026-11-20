"""An amendment starts at the first state of its workflow (BrahMos tracker point 11).

On Amend, Frappe copies every field of the cancelled document, its workflow state ("Rejected", "Checked By" ...)
included. On save Frappe then refuses it - "Workflow State transition not allowed from Prepared By to Rejected" (a new
document may only be in the first state) - and in the form the copied "Rejected" state, editable only by the Chief
Finance Officer, hid Save from everyone else.

reset_amended_workflow_state (doc_events "*" before_validate, which runs before Frappe's workflow check) puts a new
amendment in the first state of its doctype's workflow ("Prepared By" in the Journal Entry, Payment Entry and Purchase
Invoice workflows of fixtures/workflow.json); public/js/workflow_amend.js does the same in the form, so the state shown
before saving is right too. Documents that are not amendments are not touched.
"""

import frappe
from frappe.model.workflow import get_workflow, get_workflow_name


def reset_amended_workflow_state(doc, method=None):
	if not doc.get("amended_from") or not doc.is_new():
		return
	if not get_workflow_name(doc.doctype):
		return
	workflow = get_workflow(doc.doctype)
	if not workflow.states:
		return
	first_state = workflow.states[0].state
	if doc.get(workflow.workflow_state_field) != first_state:
		doc.set(workflow.workflow_state_field, first_state)
