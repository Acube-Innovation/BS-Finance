"""Data for the Payment Entry print formats of A3 Finance; both functions are Jinja methods (hooks.py).

get_payment_party(doc)    "Received with thanks from": the party's name and address (Bank Receipt, Petty Cash Receipt)
get_receipt_breakup(doc)  the ledgers of a receipt with their amounts (Petty Cash Receipt Voucher)
"""

import frappe
from frappe.contacts.doctype.address.address import get_default_address
from frappe.utils import cstr, flt


def get_payment_party(doc):
	"""Name and address lines of the party of a Payment Entry.

	The address is the one chosen on the payment (Customer Address), else the party's primary address, else any of its
	addresses. A payment without a party shows the account the money came from (Receive) or went to (Pay)."""
	name = cstr(doc.get("party_name") or doc.get("party"))
	if not name:
		account = doc.get("paid_from") if doc.get("payment_type") == "Receive" else doc.get("paid_to")
		return frappe._dict(name=account_name(account), lines=[])

	address = doc.get("customer_address") if doc.get("party_type") == "Customer" else None
	if not address and doc.get("party_type") and doc.get("party"):
		address = get_default_address(doc.party_type, doc.party)
	return frappe._dict(name=name, lines=address_lines(address))


def address_lines(address):
	if not address or not frappe.db.exists("Address", address):
		return []
	a = frappe.get_cached_doc("Address", address)
	city = ", ".join(cstr(v).strip() for v in (a.city, a.state) if cstr(v).strip())
	if cstr(a.pincode).strip():
		city = f"{city} - {cstr(a.pincode).strip()}" if city else cstr(a.pincode).strip()
	return [line for line in (cstr(a.address_line1).strip(), cstr(a.address_line2).strip(), city) if line]


def get_receipt_breakup(doc):
	"""The ledgers credited by a receipt, as [{label, amount}], adding up to the amount received.

	For each Sales Invoice the receipt is allocated to, its share (allocated / invoice total) of the invoice's income
	(by income account) and of each of its taxes. The amount not allocated to an invoice (an advance, on account, or
	allocated to another kind of document) is against the party. Deductions on the payment are subtracted. The
	rounding of the shares and of the invoices is in Round Off."""
	lines = {}  # label -> amount, in order of first use

	def add(label, amount):
		lines[label] = flt(lines.get(label)) + flt(amount)

	party_label = cstr(doc.get("party_name") or doc.get("party")) or account_name(doc.get("paid_from"))
	for row in doc.get("references") or []:
		allocated = flt(row.allocated_amount)
		if not allocated:
			continue
		invoice = None
		if row.reference_doctype == "Sales Invoice" and frappe.db.exists("Sales Invoice", row.reference_name):
			invoice = frappe.get_doc("Sales Invoice", row.reference_name)
		total = invoice_total(invoice) if invoice else 0
		if not total:
			add(party_label, allocated)
			continue
		share = allocated / total
		for item in invoice.items:
			add(account_name(item.income_account), flt(item.base_net_amount) * share)
		for tax in invoice.taxes:
			add(tax_label(tax), flt(tax.base_tax_amount_after_discount_amount) * share)

	unallocated = flt(doc.get("unallocated_amount"))
	if unallocated:
		add(party_label, unallocated)
	for row in doc.get("deductions") or []:
		if flt(row.amount):
			add(f"Less: {account_name(row.account)}", -flt(row.amount))

	out = [
		frappe._dict(label=label, amount=flt(amount, 2)) for label, amount in lines.items() if flt(amount, 2)
	]
	if not out:
		out = [frappe._dict(label=party_label, amount=flt(doc.paid_amount, 2))]
	round_off = flt(flt(doc.paid_amount, 2) - sum(line.amount for line in out), 2)
	if round_off:
		out.append(frappe._dict(label="Round Off", amount=round_off))
	return out


def invoice_total(invoice):
	"""What the customer owes on the invoice: the rounded total, unless rounding is off."""
	if not invoice.get("disable_rounded_total") and flt(invoice.get("base_rounded_total")):
		return flt(invoice.base_rounded_total)
	return flt(invoice.base_grand_total)


def tax_label(tax):
	label = cstr(tax.description).strip() or account_name(tax.account_head)
	rate = flt(tax.rate)
	return f"{label}-{rate:g}%" if rate else label


def account_name(account):
	"""Account name without the company abbreviation ("Petty Cash - BATL" -> "Petty Cash")."""
	if not account:
		return ""
	return cstr(frappe.get_cached_value("Account", account, "account_name") or account)
