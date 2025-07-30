# # Copyright (c) 2025, Acube and contributors
# # For license information, please see license.txt

# import frappe
# import math
# from frappe.model.document import Document
# from decimal import Decimal, ROUND_HALF_UP
# # from frappe.custom.doctype.customize_form.customize_form import set_df_property
# class EmployeeConveyanceDays(Document):
# 	# def validate(self):
# 	# 	# print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
# 	# 	if not self.vehicle_type:
# 	# 		vehicle_type = frappe.db.get_value("Employee", self.employee, "custom_vehicle_type")	
# 	# 		self.vehicle_type = vehicle_type if vehicle_type else ""
# 	# 	if not self.employee or not self.present_days or not self.total_working_days:
# 	# 		return

# 	# 	# Fetch vehicle type from Employee
# 	# 	# self.vehicle_type = frappe.db.get_value("Employee", self.employee, "custom_vehicle_type")

# 	# 	if not self.vehicle_type:
# 	# 		return

# 	# 	# Get payroll month/year from a date field (e.g., self.start_date)
# 	# 	# if not self.start_date:
# 	# 	# 	frappe.throw("Start Date is required to determine Payroll Master Setting.")

# 	# 	# start = getdate(self.start_date)
# 	# 	# month_number = start.month
# 	# 	# year = start.year

# 	# 	# Fetch the applicable Payroll Master Setting
# 	# 	setting = get_previous_payroll_master_setting(self.payroll_year, self.payroll_date)
# 	# 	no__of_days = frappe.db.get_value(
#     #     "Lop Per Request",
#     #     filters={
#     #         "employee_id": self.employee,
#     #         "payroll_month": self.payroll_date,
#     #         "payroll_year": self.payroll_year
#     #     },
#     #     fieldname="SUM(no__of_days)"
#     # ) or 0
# 	# 	if not setting:
# 	# 		frappe.throw("No applicable Payroll Master Setting found for the given start date.")

# 	# 	# Match vehicle type (case-insensitive) in the child table
# 	# 	monthly_amount = 0
# 	# 	for row in setting.conveyance_allowance:
# 	# 		if row.type_of_vehicles.strip().lower() == self.vehicle_type.strip().lower():
# 	# 			monthly_amount = row.amount_per_month
# 	# 			break

# 	# 	self.monthly_conveyance_amount = monthly_amount  # Or however you're storing this field
# 	# 	# Calculate minimum working days (75% of total), rounded up
# 	# 	self.minimum_working_days = math.ceil(0.75 * self.total_working_days)
# 	# 	attendance_days = self.total_working_days - no__of_days

# 	# 	# Apply rules
# 	# 	if attendance_days < 10 and self.present_days<10:
# 	# 		self.conveyance_charges = 0
# 	# 		self.pro_rata_charges = 0

# 	# 	elif self.present_days >= self.minimum_working_days:
# 	# 		self.present_days = self.minimum_working_days
# 	# 		self.conveyance_charges = monthly_amount
# 	# 		self.pro_rata_charges = monthly_amount

# 	# 	else:
# 	# 		prorated_amount = (monthly_amount / self.minimum_working_days) * self.present_days
# 	# 		self.conveyance_charges = monthly_amount
# 	# 		self.pro_rata_charges = int(Decimal(prorated_amount).quantize(0, rounding=ROUND_HALF_UP))

#     def validate(self):
#         # Fetch vehicle type from Employee if not already set
#         vehicle_type = frappe.db.get_value("Employee", self.employee, "custom_vehicle_type")
#         self.vehicle_type = self.vehicle_type or vehicle_type or ""

#         if not self.employee or not self.present_days or not self.total_working_days:
#             return
#         if not self.vehicle_type:
#             return

#         # Fetch Payroll Master Setting
#         setting = get_previous_payroll_master_setting(self.payroll_year, self.payroll_date)

#         no__of_days = frappe.db.get_value(
#             "Lop Per Request",
#             filters={
#                 "employee_id": self.employee,
#                 "payroll_month": self.payroll_date,
#                 "payroll_year": self.payroll_year,
#             },
#             fieldname="SUM(no__of_days)",
#         ) or 0

#         if not setting:
#             frappe.throw("No applicable Payroll Master Setting found for the given payroll period.")

#         # Find monthly amount for this vehicle type
#         monthly_amount = 0
#         for row in setting.conveyance_allowance:
#             if row.type_of_vehicles.strip().lower() == self.vehicle_type.strip().lower():
#                 monthly_amount = row.amount_per_month
#                 break

#         self.monthly_conveyance_amount = monthly_amount
#         self.minimum_working_days = math.ceil(0.75 * self.total_working_days)

#         # Calculate combined present days across all vehicle types for this period
#         total_days_in_period = frappe.db.sql(
#             """
#             SELECT COALESCE(SUM(present_days), 0)
#             FROM `tabEmployee Conveyance Days`
#             WHERE employee = %s
#               AND payroll_year = %s
#               AND payroll_date = %s
#               AND name != %s
#             """,
#             (self.employee, self.payroll_year, self.payroll_date, self.name),
#         )[0][0]

#         total_days_in_period += self.present_days

#         # --- Apply eligibility rules based on combined attendance ---

#         # 1. Combined days < 10 -> Not eligible at all
#         if total_days_in_period < 10:
#             self.conveyance_charges = 0
#             self.pro_rata_charges = 0
#             return

#         # 2. Combined days >= 75% of total -> full allowance for the whole month
#         if total_days_in_period >= self.minimum_working_days:
#             # Full month allowed, but split proportionally per record
#             prorated_amount = (monthly_amount / self.total_working_days) * self.present_days
#             self.conveyance_charges = monthly_amount
#             self.pro_rata_charges = int(Decimal(prorated_amount).quantize(0, rounding=ROUND_HALF_UP))
#             return

#         # 3. Else, partial allowance (pro-rata based on this record’s present days)
#         prorated_amount = (monthly_amount / self.total_working_days) * self.present_days
#         self.conveyance_charges = monthly_amount
#         self.pro_rata_charges = int(Decimal(prorated_amount).quantize(0, rounding=ROUND_HALF_UP))
import math
from decimal import Decimal, ROUND_HALF_UP
import frappe
from frappe.model.document import Document

class EmployeeConveyanceDays(Document):
    def validate(self):
        # Fetch vehicle type from Employee if not already set
        vehicle_type = frappe.db.get_value("Employee", self.employee, "custom_vehicle_type")
        self.vehicle_type = self.vehicle_type or vehicle_type or ""

        if not self.employee or not self.present_days or not self.total_working_days:
            return
        if not self.vehicle_type:
            return

        # Fetch Payroll Master Setting (current or latest applicable)
        setting = get_previous_payroll_master_setting(self.payroll_year, self.payroll_date)
        if not setting:
            frappe.throw("No applicable Payroll Master Setting found for the given payroll period.")

        # Get the correct rate for the vehicle type from the setting
        vehicle_type_lower = self.vehicle_type.strip().lower()
        monthly_amount = 0
        for row in setting.conveyance_allowance:
            if row.type_of_vehicles and row.type_of_vehicles.strip().lower() == vehicle_type_lower:
                monthly_amount = row.amount_per_month
                break

        if not monthly_amount:
            frappe.throw(f"No conveyance rate found in Payroll Master Setting for vehicle type: {self.vehicle_type}")

        self.monthly_conveyance_amount = monthly_amount
        self.minimum_working_days = math.ceil(0.75 * self.total_working_days)

        # Calculate combined present days across all vehicle types for this period
        total_days_in_period = frappe.db.sql(
            """
            SELECT COALESCE(SUM(present_days), 0)
            FROM `tabEmployee Conveyance Days`
            WHERE employee = %s
              AND payroll_year = %s
              AND payroll_date = %s
              AND name != %s
            """,
            (self.employee, self.payroll_year, self.payroll_date, self.name),
        )[0][0]

        total_days_in_period += self.present_days

        # --- Apply eligibility rules based on combined attendance ---

        # 1. Combined days < 10 -> Not eligible at all
        if total_days_in_period < 10:
            self.conveyance_charges = 0
            self.pro_rata_charges = 0
            return

        # 2. Combined days >= 75% of total -> CAP at minimum_working_days
        if total_days_in_period >= self.minimum_working_days:
            print ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",{total_days_in_period})
            if total_days_in_period != self.present_days:
                cap = self.minimum_working_days
                prorated_amount = (monthly_amount * self.present_days) / cap
                self.conveyance_charges = monthly_amount
                self.pro_rata_charges = int(
					Decimal(prorated_amount).quantize(0, rounding=ROUND_HALF_UP)
				)
            elif self.present_days >= self.minimum_working_days:
                print ("cccccccccccccccccccccccccccccccccccccc",{self.present_days})
                self.present_days = self.minimum_working_days
                self.conveyance_charges = monthly_amount
                self.pro_rata_charges = monthly_amount
            else : 
                prorated_amount = (monthly_amount * self.present_days) / self.total_working_days
                self.conveyance_charges = monthly_amount
                self.pro_rata_charges = int(
					Decimal(prorated_amount).quantize(0, rounding=ROUND_HALF_UP)
				)
        else:
            # 3. Else, partial allowance (pro-rata based on actual total days)
            print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
            prorated_amount = (monthly_amount / self.minimum_working_days) * self.present_days
            self.conveyance_charges = monthly_amount
            self.pro_rata_charges = int(
                Decimal(prorated_amount).quantize(0, rounding=ROUND_HALF_UP)
            )

@staticmethod
def get_previous_payroll_master_setting(year, month_number):
    import calendar

    year = int(year)

    # Convert month name to number if needed
    if isinstance(month_number, str):
        month_number = list(calendar.month_name).index(month_number)

    years_to_consider = [year, year - 1]

    settings = frappe.get_all(
        "Payroll Master Setting",
        filters={"payroll_year": ["in", years_to_consider]},
        fields=["name", "payroll_year", "payroll_month_number"],
        order_by="payroll_year desc, payroll_month_number desc",
        limit=20
    )

    for record in settings:
        ry = int(record["payroll_year"])
        rm = int(record["payroll_month_number"])
        if ry < year or (ry == year and rm <= month_number):
            return frappe.get_doc("Payroll Master Setting", record["name"])

    return None
