# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt



class PettyLabourPayment(Document):

	def validate(self):
  
		self.validate_duplicate_labour()
		self.calculate_amounts()
		self.set_total_amount()
		


	def on_submit(self):
		self.create_journal_entry()

	def on_cancel(self):
		self.cancel_journal_entry()

	
	def create_journal_entry(self):
		settings = frappe.get_single("Petty Labour Settings")

		total_amount = 0
		emp_pf_total = 0
		empr_pf_total = 0
		emp_esi_total = 0
		empr_esi_total = 0
		pf_admin_total = 0

		for row in self.payment_details:
			amount = flt(row.amount)

			emp_pf  = amount * flt(row.employee_contribution_pf_) / 100
			empr_pf = amount * flt(row.employer_contribution_pf_) / 100
			emp_esi = amount * flt(row.employee_contribution_esi_) / 100
			empr_esi= amount * flt(row.employer_contribution_esi_) / 100
			pf_admin= amount * flt(row.pf_administrative_charges_) / 100

			total_amount += amount
			emp_pf_total += emp_pf
			empr_pf_total += empr_pf
			emp_esi_total += emp_esi
			empr_esi_total += empr_esi
			pf_admin_total += pf_admin

		total_deductions = (
			emp_pf_total + empr_pf_total +
			emp_esi_total + empr_esi_total +
			pf_admin_total
		)

		net_payable = total_amount - total_deductions

		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.posting_date = self.transaction_date
		je.user_remark = f"Petty Labour Payment - {self.name}"

		# 🔹 Debit Entry
		if self.debit_entry_type == "Supplier":
			pi = self.reference_document

			supplier_account = frappe.db.get_value(
				"Purchase Invoice", pi, "credit_to"
			)

			je.append("accounts", {
				"account": supplier_account,
				"party_type": "Supplier",
				"party": self.supplier,
				"reference_type": "Purchase Invoice",
				"reference_name": pi,
				"debit_in_account_currency": total_amount
			})
		else:
			je.append("accounts", {
				"account": self.labour_charges_account,
				"debit_in_account_currency": total_amount
			})

		# 🔹 Credits — statutory accounts

		if emp_pf_total:
			je.append("accounts", {
				"account": settings.employee_contribution_pf_account,
				"credit_in_account_currency": emp_pf_total
			})

		if empr_pf_total:
			je.append("accounts", {
				"account": settings.employer_contribution_pf_account,
				"credit_in_account_currency": empr_pf_total
			})

		if emp_esi_total:
			je.append("accounts", {
				"account": settings.employee_contribution_esi__account,
				"credit_in_account_currency": emp_esi_total
			})

		if empr_esi_total:
			je.append("accounts", {
				"account": settings.employer_contribution_esi_account,
				"credit_in_account_currency": empr_esi_total
			})

		if pf_admin_total:
			je.append("accounts", {
				"account": settings.pf_administrative_charges_account,
				"credit_in_account_currency": pf_admin_total
			})

		# 🔹 Net Payable
		if net_payable:
			if self.debit_entry_type == "Supplier":
				payable_account = supplier_account
				party_type = "Supplier"
				party = self.supplier
			else:
				payable_account = self.labour_charges_account
				party_type = None
				party = None

			je.append("accounts", {
				"account": payable_account,
				"party_type": party_type,
				"party": party,
				"credit_in_account_currency": net_payable
			})

		je.insert()
		je.submit()



		self.db_set("journal_entry", je.name)

		

	def cancel_journal_entry(self):
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				je.cancel()


	def calculate_amounts(self):
		for row in self.payment_details:
		
			if flt(row.days) <= 0:
				frappe.throw(f"Days must be greater than 0 in row {row.idx}")

			
			if flt(row.wages) < 0:
				frappe.throw(f"Wages cannot be negative in row {row.idx}")

			
			row.amount = flt(row.days) * flt(row.wages)

	
	def validate_duplicate_labour(self):
		seen = set()

		for row in self.payment_details:
			if row.petty_labour in seen:
				frappe.throw(f"Duplicate labour entry: {row.petty_labour}")
			seen.add(row.petty_labour)


	def set_total_amount(self):
		self.total_amount = sum(
			flt(row.amount) for row in self.payment_details
		)
