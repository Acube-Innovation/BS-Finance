# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt





class PhysicalCashClosing(Document):

	def validate(self):
		"""Main validation entry point"""
		self.validate_duplicate_denominations()
		self.validate_cash_account()
		self.calculate_total_from_denominations()
		self.set_system_balance()
		self.calculate_difference()
		self.validate_negative_values()

	def validate_duplicate_denominations(self):
		"""Ensure denomination is not repeated"""
		seen = set()

		for row in self.cash_denomination_detail:
			if row.denomination in seen:
				frappe.throw(
					f"Duplicate denomination found: <b>{row.denomination}</b>. "
					"Each denomination should appear only once."
				)
			seen.add(row.denomination)

	def validate_cash_account(self):
		"""Ensure selected account is a Cash account"""
		if not self.cash_account:
			frappe.throw("Cash Account is required.")

		account_type = frappe.db.get_value("Account", self.cash_account, "account_type")

		if account_type != "Cash":
			frappe.throw(f"Account <b>{self.cash_account}</b> is not a Cash account.")

	def validate_negative_values(self):
		"""Prevent negative entries"""
		if flt(self.total_cash_counted) < 0:
			frappe.throw("Total Cash Counted cannot be negative.")

		for row in self.cash_denomination_detail:
			if flt(row.count) < 0:
				frappe.throw(f"Negative count not allowed for denomination {row.denomination}")

 

	def calculate_total_from_denominations(self):
		"""Sum denomination amounts"""
		total = 0

		for row in self.cash_denomination_detail:
			row.amount = flt(row.denomination) * flt(row.count)
			total += row.amount

		self.total_cash_counted = total

	def set_system_balance(self):
		"""Fetch real-time balance from GL Entry"""
		if not self.cash_account:
			self.system_balance = 0
			return

		balance = frappe.db.sql("""
			SELECT SUM(debit) - SUM(credit)
			FROM `tabGL Entry`
			WHERE account = %s
		""", (self.cash_account,))[0][0] or 0

		self.system_balance = flt(balance)


	def calculate_difference(self):
		"""Calculate variance between counted and system balance"""
		self.difference = flt(self.total_cash_counted) - flt(self.system_balance)
