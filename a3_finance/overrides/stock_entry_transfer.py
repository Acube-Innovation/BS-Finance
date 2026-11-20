"""A Material Transfer posts its rounding difference to the company's Stock Adjustment account (BrahMos tracker
points 33 and 34).

On a transfer, the value leaving the source warehouse and the value entering the target warehouse are each rounded
to the paisa (MAT-STE-01139: 50 x ₹4,058.4375 left Consumable Store-Restricted at ₹2,02,921.87 and entered
Consumable Store-Unrestricted at ₹2,02,921.88). Both warehouses post to Stock In Hand, so the stock account moves by
the 1 paisa difference, and ERPNext balances it against the row's Difference (expense) account - which, fetched from
the Item Group defaults, was a consumption ledger (Consumption of Tools & General Stores).

For transfer rows (a source and a target warehouse) the difference account is set to the company's Stock Adjustment
Account, the ledger meant for stock value differences, so consumption ledgers carry consumption only. Nothing else
on the entry changes, and entries already submitted are not touched.
"""

import frappe

TRANSFER_PURPOSES = ("Material Transfer",)


def set_transfer_difference_account(doc, method=None):
	if doc.purpose not in TRANSFER_PURPOSES:
		return
	account = frappe.get_cached_value("Company", doc.company, "stock_adjustment_account")
	if not account:
		return
	for row in doc.items:
		if row.s_warehouse and row.t_warehouse and row.expense_account != account:
			row.expense_account = account
