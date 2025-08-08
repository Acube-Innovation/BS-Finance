# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt


# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
import calendar
from a3_finance.utils.payroll_master import get_previous_payroll_master_setting

class EmployeeReimbursementWages(Document):
    def validate(self):
        if not self.employee_id:
            frappe.throw("Employee is required to fetch salary and service weightage.")

        reimbursement_date = self.get_effective_reimbursement_date()
        if not reimbursement_date:
            frappe.throw("Either 'Reimbursement Date' or 'TL Month/Year' must be set.")

        # 1. Base Salary
        base = self.get_base_salary(reimbursement_date)
        if base is None:
            frappe.throw("Basic Pay could not be determined from Salary Structure Assignment or Actual Pay.")
        self.actual_basic_pay = float(base)

        # Apprentice logic (simplified)
        if self.employment_type == "Apprentice":
            self.set_apprentice_refund()
            return

        # 2. Payroll Master Setting (DA%, HRA%)
        month = reimbursement_date.month
        year = reimbursement_date.year
        payroll_setting = get_previous_payroll_master_setting(self,year, month)
        da_percent = float(payroll_setting.dearness_allowance_ or 0) if payroll_setting else 0
        hra_percent = float(payroll_setting.hra_ or 0.16) if payroll_setting else 0

        # 3. Service Weightage (from history or fallback)
        service_weightage = self.get_service_weightage(year, month)

        # 4. Reimbursement Calculations
        if float(self.no_of_days or 0) > 0:
            self.set_daywise_refund(service_weightage, da_percent, hra_percent)
        elif float(self.tl_hours or 0) > 0:
            self.set_hourwise_refund(service_weightage, da_percent)
        else:
            frappe.throw("Either 'No. of Days' or 'LOP Refund Hours' must be provided.")

    def get_effective_reimbursement_date(self):
        if self.reimbursement_date:
            return getdate(self.reimbursement_date)
        elif self.tl_month and self.reimbursement_year:
            try:
                month = list(calendar.month_name).index(self.tl_month)
                year = int(self.reimbursement_year)
                return getdate(f"{year}-{month:02d}-01")
            except Exception:
                frappe.throw(f"Invalid TL Month/Year: {self.tl_month} {self.reimbursement_year}")
        return None

    def get_base_salary(self, effective_date):
        # Try from Salary Structure Assignment
        ssa = frappe.db.get_value(
            "Salary Structure Assignment",
            {
                "employee": self.employee_id,
                "from_date": ["<=", effective_date],
                "docstatus": 1
            },
            "base",
            order_by="from_date desc"
        )

        if ssa is not None:
            return float(ssa)

        # Fallback to manually entered actual_basic_pay
        return float(self.actual_basic_pay or 0)

    def get_service_weightage(self, year, month):
        sw_doc = frappe.db.get_value(
            "Employee Service Weightage",
            {
                "employee_id": self.employee_id,
                "payroll_month": calendar.month_name[month],
                "payroll_year": str(year)
            },
            "service_weightage",
            as_dict=True
        )
        if sw_doc:
            return float(sw_doc["service_weightage"])
        return float(frappe.db.get_value("Employee", self.employee_id, "custom_service_weightage_emp") or 0)

    def set_daywise_refund(self, sw, da_percent, hra_percent):
        days = float(self.no_of_days)
        bp = self.actual_basic_pay
        total_base = bp + sw

        self.reimbursement_basic_pay = round((bp / 30) * days, 2)
        self.reimbursement_service_weightage = round((sw / 30) * days, 2)
        self.reimbursement_hra = round((total_base * hra_percent / 30) * days, 2)
        self.reimbursement_da = round((total_base * da_percent / 30) * days, 2)

        self.lop_refund_amount = round(
            self.reimbursement_basic_pay +
            self.reimbursement_service_weightage +
            self.reimbursement_da +
            self.reimbursement_hra,
            2
        )

    def set_hourwise_refund(self, sw, da_percent):
        hours = float(self.tl_hours)
        bp = self.actual_basic_pay
        total_base = bp + sw
        refund_days = hours / 8
        refund_ratio = refund_days / 30

        self.reimbursement_basic_pay = round((bp / 30) * refund_days, 2)
        self.reimbursement_service_weightage = round((sw / 30) * refund_days, 2)
        self.reimbursement_hra = 0  # No HRA for hour-wise
        vda = total_base * da_percent
        self.reimbursement_da = round((vda / 30) * refund_days, 2)

        self.lop_refund_amount = round(
            self.reimbursement_basic_pay +
            self.reimbursement_service_weightage +
            self.reimbursement_da,
            2
        )

        self.lop_pf_deduction = round(
            (total_base + vda) * 0.12 * (refund_days / 30), 2
        )

    def set_apprentice_refund(self):
        if float(self.no_of_days or 0) > 0:
            self.reimbursement_basic_pay = round((self.actual_basic_pay / 30) * float(self.no_of_days), 2)
            self.reimbursement_service_weightage = 0
            self.reimbursement_da = 0
            self.reimbursement_hra = 0
            self.lop_refund_amount = self.reimbursement_basic_pay
        elif float(self.tl_hours or 0) > 0:
            refund_days = float(self.tl_hours) / 8
            self.reimbursement_basic_pay = round((self.actual_basic_pay / 30) * refund_days, 2)
            self.reimbursement_service_weightage = 0
            self.reimbursement_da = 0
            self.reimbursement_hra = 0
            self.lop_refund_amount = self.reimbursement_basic_pay
            self.lop_pf_deduction = 0
        else:
            frappe.throw("Either 'No. of Days' or 'LOP Refund Hours' must be provided.")










































# import frappe
# from frappe.model.document import Document
# from frappe.utils import getdate


# class EmployeeReimbursementWages(Document):

# 	# def validate(self):
# 	# 	reimbursement_date = getdate(self.reimbursement_date)

# 	# 	if not self.employee_id:
# 	# 		frappe.throw("Employee is required to fetch salary and service weightage.")

# 	# 	# Get Salary Slip for this employee within reimbursement date
# 	# 	# salary_slip = frappe.db.get_value(
# 	# 	# 	"Salary Slip",
# 	# 	# 	{
# 	# 	# 		"employee": self.employee_id,
# 	# 	# 		"start_date": ["<=", reimbursement_date],
# 	# 	# 		"end_date": [">=", reimbursement_date],
# 	# 	# 		"docstatus": 1
# 	# 	# 	},
# 	# 	# 	["name", "custom_dearness_allowance_"],
# 	# 	# 	as_dict=True
# 	# 	# )

# 	# 	base = 0
# 	# 	da_percent = 0

# 	# 	# if salary_slip:
# 	# 	# 	slip_name = salary_slip.name
# 	# 	# 	da_percent = float(salary_slip.custom_dearness_allowance_ or 0)

# 	# 	# 	# Fetch Basic Pay from Salary Slip Earnings (Salary Detail)
# 	# 	# 	base = frappe.db.get_value("Salary Detail", {
# 	# 	# 		"parent": slip_name,
# 	# 	# 		"parenttype": "Salary Slip",
# 	# 	# 		"salary_component": "Basic"
# 	# 	# 	}, "amount")

# 	# 	# Fallback: base from Salary Structure Assignment (Basic component)
# 	# 	if not base:
# 	# 		assignment = frappe.db.sql("""
# 	# 			SELECT name, base FROM `tabSalary Structure Assignment`
# 	# 			WHERE employee = %s AND from_date <= %s AND docstatus = 1
# 	# 			ORDER BY from_date DESC LIMIT 1
# 	# 		""", (self.employee_id, reimbursement_date), as_dict=True)

# 	# 		if assignment:
# 	# 			base = assignment[0].base


# 	# 	if not base:
# 	# 		# frappe.throw("Base Salary could not be determined from Salary Slip or Salary Structure Assignment.")
# 	# 		base = self.actual_basic_pay
# 	# 		self.reimbursement_basic_pay=base/ 30 * self.no_of_days
# 	# 	else:
# 	# 		self.actual_basic_pay = base
# 	# 		self.reimbursement_basic_pay=base/ 30 * self.no_of_days
# 	# 	basic_pay = float(base)

# 	# 	# Get Service Weightage from Employee Payroll Details


# 	# 	month = getdate(reimbursement_date).strftime("%B")  # e.g., "June"
# 	# 	year = getdate(reimbursement_date).strftime("%Y")   # e.g., "2025"

# 	# 	sw_doc = frappe.db.get_value(
# 	# 		"Employee Service Weightage",
# 	# 		{
# 	# 			"employee_id": self.employee_id,
# 	# 			"payroll_month": month,
# 	# 			"payroll_year": year
# 	# 		},
# 	# 		"service_weightage",
# 	# 		as_dict=True
# 	# 	)


# 	# 	service_weightage = float(sw_doc["service_weightage"]) if sw_doc else 0
# 	# 	self.reimbursement_service_weightage = (service_weightage/30 ) * self.no_of_days


# 	# 	# ----- CONDITION 1: When LOP is in DAYS -----
# 	# 	if float(self.no_of_days or 0) > 0:
# 	# 		# Calculate HRA: (BP + SW) * 0.16
# 	# 		hra = (basic_pay + service_weightage) * 0.16
# 	# 		self.reimbursement_hra = hra / 30 * self.no_of_days

# 	# 		# DA: (BP + SW) * DA%
# 	# 		da = (basic_pay + service_weightage) * (da_percent / 100)
# 	# 		self.reimbursement_da = da/ 30 * self.no_of_days

# 	# 		# LOP Refund Amount
# 	# 		lop_refund = (basic_pay + service_weightage + hra + da) * float(self.no_of_days) / 30
# 	# 		self.lop_refund_amount = round(lop_refund, 2)

# 	# 	# ----- CONDITION 2: When LOP is in HOURS -----
# 	# 	elif float(self.tl_hours or 0) > 0:
# 	# 		refund_hours = float(self.tl_hours)

# 	# 		# Variable DA
# 	# 		vda = (basic_pay + service_weightage) * (da_percent / 100)
# 	# 		self.reimbursement_da = vda
# 	# 		self.reimbursement_hra = 0  # HRA is not considered for hours-based refund

# 	# 		# Refund Amount
# 	# 		lop_refund = (basic_pay + service_weightage + vda) * refund_hours / 240
# 	# 		self.lop_refund_amount = round(lop_refund, 2)

# 	# 		# PF Deduction
# 	# 		pf_deduction = (basic_pay + service_weightage + vda) * 0.12 * (refund_hours / 240)
# 	# 		self.lop_pf_deduction = round(pf_deduction, 2)

# 	# 	else:
# 	# 		frappe.throw("Either 'No. of Days' or 'LOP Refund Hours' must be provided.")

# 	def validate(self):
# 		from frappe.utils import getdate
# 		import calendar

# 		reimbursement_date = getdate(self.reimbursement_date)

# 		if not self.employee_id:
# 			frappe.throw("Employee is required to fetch salary and service weightage.")

# 		# Try fetching base from Salary Structure Assignment
# 		base = None
# 		assignment = frappe.db.sql("""
# 			SELECT base FROM `tabSalary Structure Assignment`
# 			WHERE employee = %s AND from_date <= %s AND docstatus = 1
# 			ORDER BY from_date DESC LIMIT 1
# 		""", (self.employee_id, reimbursement_date), as_dict=True)

# 		if assignment and assignment[0].get("base") is not None:
# 			base = assignment[0]["base"]

# 		# If base still None, fallback to reimbursement_basic_pay
# 		# if base is None and self.reimbursement_basic_pay:
# 		# 	base = self.reimbursement_basic_pay

# 		# If still None, fallback to actual_basic_pay
# 		if base is None and self.actual_basic_pay:
# 			base = self.actual_basic_pay

# 		# Final fail-safe
# 		if base is None:
# 			frappe.throw("Basic Pay not found from Salary Structure, Reimbursement, or Actual Pay fields.")

# 		basic_pay = float(base)
# 		self.actual_basic_pay = basic_pay  # assign back
# 		print(f"Basic Pay: {basic_pay}")

# 		# Payroll month/year
# 		if self.employment_type != "Apprentice":
# 			print("kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
# 			if self.reimbursement_date:
# 				month_name = reimbursement_date.strftime("%B")
# 				month = list(calendar.month_name).index(month_name)
# 				year = int(reimbursement_date.strftime("%Y"))
# 			else:
# 				try:
# 					month = list(calendar.month_name).index(self.tl_month)
# 				except:
# 					frappe.throw(f"Invalid month format: {self.tl_month}")
# 				year = int(self.reimbursement_year)

# 			# DA %
# 			da_doc = get_previous_payroll_master_setting(year, month)
# 			da_percent = float(da_doc.dearness_allowance_ or 0) if da_doc else 0
# 			hra_percent = float(da_doc.hra_ or 0.16)if da_doc else 0 

# 			# Service Weightage
# 			sw_doc = frappe.db.get_value(
# 				"Employee Service Weightage",
# 				{
# 					"employee_id": self.employee_id,
# 					"payroll_month": calendar.month_name[month],
# 					"payroll_year": str(year)
# 				},
# 				"service_weightage",
# 				as_dict=True
# 			)
# 			if sw_doc:
# 				service_weightage = float(sw_doc["service_weightage"]) 
# 			else:
# 				service_weightage = frappe.db.get_value("Employee",{'name':self.employee_id},'custom_service_weightage_emp')
# 			if not self.actual_basic_pay:
# 			# 	if self.reimbursement_date:
# 			# 		ssa = frappe.get_all(
# 			# 	"Salary Structure Assignment",
# 			# 	filters={
# 			# 		"employee": self.employee_id,
# 			# 		"from_date": ["<=", reimbursement_date],
# 			# 		"docstatus": 1
# 			# 	},
# 			# 	fields=["base"],
# 			# 	order_by="from_date desc",
# 			# 	limit=1
# 			# )
# 			# 		self.actual_basic_pay = flt(ssa[0].base) if ssa else 0
# 				self.actual_basic_pay = frappe.db.get_value('Salary Structure Assignment',{'employee':self.employee_id},'base')

# 			# Days-based refund
# 			if float(self.no_of_days or 0) > 0:
# 				self.reimbursement_service_weightage = (service_weightage / 30) * float(self.no_of_days)
# 				self.reimbursement_basic_pay = (self.actual_basic_pay /30) * float(self.no_of_days)
# 				hra = ((self.actual_basic_pay + service_weightage) * hra_percent) / 30 * self.no_of_days
# 				self.reimbursement_hra = hra

# 				da = ((self.actual_basic_pay + service_weightage) * da_percent) / 30 * self.no_of_days
# 				self.reimbursement_da = da

# 				lop_refund = (
# 					self.reimbursement_basic_pay +
# 					self.reimbursement_service_weightage +
# 					self.reimbursement_da +
# 					self.reimbursement_hra
# 				)
# 				self.lop_refund_amount = round(lop_refund, 2)

# 			# TL-based refund
# 			elif float(self.tl_hours or 0) > 0:
# 				refund_hours = float(self.tl_hours / 8)
# 				self.reimbursement_basic_pay = (self.actual_basic_pay / 30) * refund_hours
# 				self.reimbursement_service_weightage = (service_weightage / 30) * refund_hours

# 				vda = (basic_pay + service_weightage) * da_percent
# 				self.reimbursement_da = (vda / 30) * refund_hours
# 				self.reimbursement_hra = 0

# 				total_eligible = (
# 					self.reimbursement_basic_pay +
# 					self.reimbursement_service_weightage +
# 					self.reimbursement_da
# 				)
# 				self.lop_refund_amount = round(total_eligible, 2)

# 				pf_deduction = (basic_pay + service_weightage + vda) * 0.12 * (refund_hours / 240)
# 				self.lop_pf_deduction = round(pf_deduction, 2)

# 			else:
# 				frappe.throw("Either 'No. of Days' or 'LOP Refund Hours' must be provided.")

# 		# If Apprentice, skip HRA, DA, Service Weightage
# 		if self.employment_type == "Apprentice":
# 			if float(self.no_of_days or 0) > 0:
# 				self.reimbursement_basic_pay = (basic_pay / 30) * float(self.no_of_days)
# 				self.reimbursement_service_weightage = 0
# 				self.reimbursement_da = 0
# 				self.reimbursement_hra = 0
# 				self.lop_refund_amount = round(self.reimbursement_basic_pay, 2)

# 			elif float(self.tl_hours or 0) > 0:
# 				refund_hours = float(self.tl_hours) / 8
# 				self.reimbursement_basic_pay = (basic_pay / 30) * refund_hours
# 				self.reimbursement_service_weightage = 0
# 				self.reimbursement_da = 0
# 				self.reimbursement_hra = 0
# 				self.lop_refund_amount = round(self.reimbursement_basic_pay, 2)
# 				self.lop_pf_deduction = 0
# 			else:
# 				frappe.throw("Either 'No. of Days' or 'LOP Refund Hours' must be provided.")
# 			return  # Skip rest of the logic for apprentice




# def get_previous_payroll_master_setting(given_year, given_month_number):
# 	years_to_consider = [given_year, given_year - 1]
	
# 	settings = frappe.get_all(
# 		"Payroll Master Setting",
# 		filters={"payroll_year": ["in", years_to_consider]},
# 		fields=["name", "payroll_year", "payroll_month_number"],
# 		order_by="payroll_year desc, payroll_month_number desc",
# 		limit=20
# 	)

# 	for record in settings:
# 		ry = int(record["payroll_year"])
# 		rm = int(record["payroll_month_number"])
# 		if ry < given_year or (ry == given_year and rm <= given_month_number):
# 			return frappe.get_doc("Payroll Master Setting", record["name"])
	
# 	return None








	# def validate(self):
	# 	reimbursement_date = getdate(self.reimbursement_date)

	# 	frappe.msgprint(f"BP: {self.reimbursement_basic_pay}, SW: {self.reimbursement_service_weightage}, Days: {self.no_of_days}")

	# 	if not (self.reimbursement_basic_pay and self.reimbursement_service_weightage and self.no_of_days):
	# 		frappe.throw("Basic Pay, Service Weightage, and No. of Days are mandatory to calculate LOP Refund Amount.")

	# 	basic_pay = float(self.reimbursement_basic_pay or 0)
	# 	service_weightage = float(self.reimbursement_service_weightage or 0)

	# 	hra = (basic_pay + service_weightage) * 0.16
	# 	self.reimbursement_hra = hra

	# 	dearness_allowance_percent = 0
	# 	da_backlog = frappe.db.get_value(
	# 		"Dearness Allowance Backlog",
	# 		{
	# 			"payroll_start_date": ["<=", reimbursement_date],
	# 			"payroll_end_date": [">=", reimbursement_date]
	# 		},
	# 		"dearness_allowance_percent"
	# 	)

	# 	if da_backlog:
	# 		dearness_allowance_percent = float(da_backlog)
	# 		frappe.msgprint(f"DA% found: {dearness_allowance_percent}")
	# 	else:
	# 		frappe.msgprint("❌ No DA% found for given date.")

	# 	da = (basic_pay + service_weightage) * (dearness_allowance_percent / 100)
	# 	self.reimbursement_da = da

	# 	lop_refund = (basic_pay + service_weightage + hra + da) * float(self.no_of_days or 0) / 30
	# 	self.lop_refund_amount = round(lop_refund, 2)
