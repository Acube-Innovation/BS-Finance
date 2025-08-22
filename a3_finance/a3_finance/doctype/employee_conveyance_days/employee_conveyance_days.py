

import math
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_first_day, get_last_day, add_months
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from a3_finance.utils.math_utils import round_half_up

class EmployeeConveyanceDays(Document):
    def validate(self):
        vehicle_type = frappe.db.get_value("Employee", self.employee, "custom_vehicle_type")

        if not vehicle_type:
            return  # nothing to set
        
        # ---- Month and working days (exclude holidays) ----
        rows = list(self.get("conveyance_details") or [])
        if not rows:
            return
        prev_month=0
        if not rows[0].start_date and not rows[0].end_date:
            # Determine the anchor date - use payroll month from document
            if self.payroll_date and self.payroll_year:  # Changed payroll_date to payroll_month
                # Convert month name to number
                month_number = self.month_name_to_number(self.payroll_date)  # Changed payroll_date to payroll_month
                # Get previous month (payroll_month - 1)
                if month_number == 1:
                    # If January, previous month is December of previous year
                    prev_year = int(self.payroll_year) - 1
                    prev_month = 12
                else:
                    prev_year = int(self.payroll_year)
                    prev_month = month_number - 1
                
                # Create anchor date (using 1st day of previous month)
                anchor = getdate(f"{prev_year}-{prev_month:02d}-01")
                end_date = get_last_day(anchor)  # Fixed: pass anchor date instead of prev_month
                rows[0].start_date = anchor
                rows[0].end_date = end_date
        elif rows[0].start_date:
            # Fallback: use first row's start_date if available
            anchor = getdate(rows[0].start_date)
            # Get previous month relative to this date
            anchor = add_months(anchor, -1)
        else:
            # Fallback: use current date minus 1 month
            anchor = add_months(getdate(), -1)
        
        month_start, month_end = get_first_day(anchor), get_last_day(anchor)
        holidays = set(SalarySlip.get_holidays_for_employee(self, month_start, month_end))
        total_days = (month_end - month_start).days + 1
        working_days = max(0, total_days - len(holidays))
        self.total_working_days = working_days
        cap = math.ceil(0.75 * working_days)  # minimum required
        self.minimum_working_days = cap
        
        # Get conveyance rates from Payroll Master Settings
        conveyance_rates = self.get_conveyance_rates(anchor.year, anchor.month)
        
        for row in self.conveyance_details:
            if not row.vehicle_type:  # If not set in child row
                row.vehicle_type = vehicle_type
            
            # If no start_date is set for the row, set it to the month start
            # if not row.start_date:
            #     row.start_date = month_start
        
        print(f"rowssssssssssssssssssssssssssssssssssssssss", len(rows))
        
        if len(rows) == 1:
            days = rows[0].no_of_days
            vehicle_type = rows[0].vehicle_type
            rate = conveyance_rates.get(vehicle_type, 1400)  # Default to 1400 if not found
            
            if days >= self.minimum_working_days:
                rows[0].amount = rate
            elif days < self.minimum_working_days and days >= 10:
                rows[0].amount = rate / self.minimum_working_days * days
                rows[0].adjusted_no_of_days = days
            else:
                rows[0].amount = 0
            self.pro_rata_charges = round_half_up (rows[0].amount)
            self.conveyance_charges = rate

        else:
            total_amount = 0 
            total = 0
            for row in self.conveyance_details:
                total += row.no_of_days
            
            if total >= 10:
                min_days = self.minimum_working_days
                for row in self.conveyance_details:
                    vehicle_type = row.vehicle_type
                    rate = conveyance_rates.get(vehicle_type, 1400)  # Added default value
                    
                    if rate is None:  # Additional safety check
                        rate = 1400
                    
                    if row.no_of_days >= self.minimum_working_days:
                        row.amount = rate
                        min_days = 0
                        break
                    elif row.no_of_days < self.minimum_working_days:
                        days = min(row.no_of_days, min_days)
                        print("fffffffffffff", days)
                        row.amount = rate / self.minimum_working_days * days
                        min_days -= row.no_of_days
                    
                    total_amount += row.amount 
            self.pro_rata_charges = round_half_up (total_amount)

    def month_name_to_number(self, month_name):
        """Convert month name to month number (1-12)"""
        month_map = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        return month_map.get(month_name.lower().strip(), 1)  # Default to January if not found

    def get_conveyance_rates(self, year, month):
        """Get conveyance rates from Payroll Master Settings for the given year and month"""
        payroll_settings = self.get_previous_payroll_master_setting(year, month)
        
        conveyance_rates = {}
        
        if payroll_settings:
            # Check both possible field names for the child table
            if hasattr(payroll_settings, 'conveyance_allowance'):
                for row in payroll_settings.conveyance_allowance:
                    # Try multiple possible field names
                    vehicle_type = getattr(row, 'type_of_vehicles', None) 
                    amount = getattr(row, 'amount_per_month', None) 
                    
                    if vehicle_type and amount is not None:
                        conveyance_rates[vehicle_type] = amount
            
        
        return conveyance_rates

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







































































































# import math
# from decimal import Decimal, ROUND_HALF_UP
# from collections import defaultdict
# import frappe
# from frappe.model.document import Document
# from frappe.utils import getdate, get_first_day, get_last_day
# from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
# from a3_finance.utils.math_utils import round_half_up

# class EmployeeConveyanceDays(Document):
#     def validate(self):
#         vehicle_type = frappe.db.get_value("Employee", self.employee, "custom_vehicle_type")

#         if not vehicle_type:
#             return  # nothing to set
        
#         # ---- Month and working days (exclude holidays) ----
#         rows = list(self.get("conveyance_details") or [])
#         if not rows:
#             return
            
#         anchor = getdate(rows[0].start_date)
#         month_start, month_end = get_first_day(anchor), get_last_day(anchor)
#         holidays = set(SalarySlip.get_holidays_for_employee(self, month_start, month_end))
#         total_days = (month_end - month_start).days + 1
#         working_days = max(0, total_days - len(holidays))
#         self.total_working_days = working_days
#         cap = math.ceil(0.75 * working_days)  # minimum required
#         self.minimum_working_days = cap
        
#         # Get conveyance rates from Payroll Master Settings
#         conveyance_rates = self.get_conveyance_rates(anchor.year, anchor.month)
        
#         for row in self.conveyance_details:
#             if not row.vehicle_type:  # If not set in child row
#                 row.vehicle_type = vehicle_type
        
#         print(f"rowssssssssssssssssssssssssssssssssssssssss", len(rows))
        
#         if len(rows) == 1:
#             days = rows[0].no_of_days
#             vehicle_type = rows[0].vehicle_type
#             rate = conveyance_rates.get(vehicle_type, 1400)  # Default to 1400 if not found
            
#             if days >= self.minimum_working_days:
#                 rows[0].amount = rate
#             elif days < self.minimum_working_days and days >= 10:
#                 rows[0].amount = rate / self.minimum_working_days * days  # Fixed: use self.minimum_working_days instead of cap
#             else:
#                 rows[0].amount = 0
#             self.pro_rata_charges = round_half_up(rows[0].amount)

#         else:
#             total_amount = 0 
#             total = 0
#             for row in self.conveyance_details:
#                 total += row.no_of_days
            
#             if total >= 10:
#                 min_days = self.minimum_working_days
#                 for row in self.conveyance_details:
#                     vehicle_type = row.vehicle_type
#                     rate = conveyance_rates.get(vehicle_type, 1400)  # Added default value
                    
#                     if rate is None:  # Additional safety check
#                         rate = 1400
                    
#                     if row.no_of_days >= self.minimum_working_days:
#                         row.amount = rate
#                         row.adjusted_no_of_days = self.minimum_working_days
#                         min_days = 0
#                         break
#                     elif row.no_of_days < self.minimum_working_days:
#                         days = min(row.no_of_days, min_days)
#                         print("fffffffffffff", days)
#                         row.amount = rate / self.minimum_working_days * days  # Fixed: use self.minimum_working_days instead of cap
#                         min_days -= row.no_of_days
#                         row.adjusted_no_of_days = days
                    
#                     total_amount += row.amount 
            
#             self.pro_rata_charges = round_half_up(total_amount)

#     def get_conveyance_rates(self, year, month):
#         """Get conveyance rates from Payroll Master Settings for the given year and month"""
#         payroll_settings = self.get_previous_payroll_master_setting(year, month)
        
#         conveyance_rates = {}
        
#         if payroll_settings:
#             # Check both possible field names for the child table
#             if hasattr(payroll_settings, 'conveyance_allowance'):
#                 for row in payroll_settings.conveyance_allowance:
#                     # Try multiple possible field names
#                     vehicle_type = getattr(row, 'type_of_vehicles', None) or getattr(row, 'vehicle_type', None)
#                     amount = getattr(row, 'amount_per_month', None) or getattr(row, 'amount', None)
                    
#                     if vehicle_type and amount is not None:
#                         conveyance_rates[vehicle_type] = amount
            
#             # If no conveyance details found, try other possible child table names
#             if not conveyance_rates and hasattr(payroll_settings, 'transport_details'):
#                 for row in payroll_settings.transport_details:
#                     vehicle_type = getattr(row, 'type_of_vehicles', None) or getattr(row, 'vehicle_type', None)
#                     amount = getattr(row, 'amount_per_month', None) or getattr(row, 'amount', None)
                    
#                     if vehicle_type and amount is not None:
#                         conveyance_rates[vehicle_type] = amount
        
#         return conveyance_rates

#     @staticmethod
#     def get_previous_payroll_master_setting(year, month_number):
#         import calendar

#         year = int(year)

#         # Convert month name to number if needed
#         if isinstance(month_number, str):
#             month_number = list(calendar.month_name).index(month_number)

#         years_to_consider = [year, year - 1]

#         settings = frappe.get_all(
#             "Payroll Master Setting",
#             filters={"payroll_year": ["in", years_to_consider]},
#             fields=["name", "payroll_year", "payroll_month_number"],
#             order_by="payroll_year desc, payroll_month_number desc",
#             limit=20
#         )

#         for record in settings:
#             ry = int(record["payroll_year"])
#             rm = int(record["payroll_month_number"])
#             if ry < year or (ry == year and rm <= month_number):
#                 return frappe.get_doc("Payroll Master Setting", record["name"])

#         return None













































































# # import math
# # from decimal import Decimal, ROUND_HALF_UP
# # from collections import defaultdict
# # import frappe
# # from frappe.model.document import Document
# # from frappe.utils import getdate, get_first_day, get_last_day
# # from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

# # class EmployeeConveyanceDays(Document):
# #     def validate(self):
# #         vehicle_type = frappe.db.get_value("Employee", self.employee, "custom_vehicle_type")

# #         if not vehicle_type:
# #             return  # nothing to set
# #          # ---- Month and working days (exclude holidays) ----
# #         rows = list(self.get("conveyance_details") or [])
# #         anchor = getdate(rows[0].start_date)
# #         month_start, month_end = get_first_day(anchor), get_last_day(anchor)
# #         holidays = set(SalarySlip.get_holidays_for_employee(self, month_start, month_end))
# #         total_days = (month_end - month_start).days + 1
# #         working_days = max(0, total_days - len(holidays))
# #         self.total_working_days = working_days
# #         cap = math.ceil(0.75 * working_days)  # minimum required
# #         self.minimum_working_days = cap
# #         for row in self.conveyance_details:
# #             if not row.vehicle_type:  # If not set in child row
# #                 row.vehicle_type = vehicle_type
        
# #         print(f"rowssssssssssssssssssssssssssssssssssssssss",len(rows))
# #         if len(rows) == 1:
# #             days= rows[0].no_of_days
# #             if days >= self.minimum_working_days :
# #                 rows[0].amount = 1400
# #             elif days < self.minimum_working_days and days >= 10:
# #                 rows[0].amount = 1400 / self.minimum_working_days * days
# #             else:
# #                 rows[0].amount = 0

# #         else:
# #             total_amount =0 
# #             total=0
# #             for row in self.conveyance_details:
# #                 total +=row.no_of_days
# #             if total >= 10:
# #                 min_days= self.minimum_working_days
# #                 for row in self.conveyance_details:
# #                     if row.no_of_days >= self.minimum_working_days :
# #                         row.amount = 1400
# #                         min_days= 0
# #                         break
# #                     elif row.no_of_days < self.minimum_working_days:
# #                         days= min(row.no_of_days,min_days)
# #                         print("fffffffffffff",days)
# #                         row.amount = 1400 / self.minimum_working_days * days
# #                         min_days -= row.no_of_days
# #                     total_amount += row.amount 
# #             self.pro_rata_charges = total_amount




# #         if not self.employee or not rows:
# #             for f in ("total_working_days","minimum_working_days","present_days",
# #                       "monthly_conveyance_amount","conveyance_charges","pro_rata_charges"):
# #                 setattr(self, f, 0)
# #             for r in rows:
# #                 r.amount = 0
# #                 r.adjusted_no_of_days = 0
# #             return

       

# #         if working_days <= 0:
# #             self.present_days = 0
# #             self.monthly_conveyance_amount = 0
# #             self.conveyance_charges = 0
# #             self.pro_rata_charges = 0
# #             for r in rows:
# #                 r.amount = 0
# #                 r.adjusted_no_of_days = 0
# #             return

# #         # ---- Payroll Master Setting: monthly rate per vehicle ----
# #         setting = get_previous_payroll_master_setting(self.payroll_year, self.payroll_date)
# #         if not setting:
# #             frappe.throw("No applicable Payroll Master Setting found for this payroll period.")

# #         rate_by_vehicle = {}
# #         for row in (setting.conveyance_allowance or []):
# #             if row.type_of_vehicles:
# #                 rate_by_vehicle[row.type_of_vehicles.strip().lower()] = float(row.amount_per_month or 0)

# #         # ---- Get actual days per row (No of Days stays as actual); we'll compute Adjusted later ----
# #         def days_in_range(d1, d2):
# #             if not d1 or not d2:
# #                 return 0.0
# #             d1, d2 = getdate(d1), getdate(d2)
# #             if d2 < d1:
# #                 return 0.0
# #             span = (d2 - d1).days + 1
# #             h = sum(1 for h in holidays if d1 <= h <= d2)
# #             return float(max(0, span - h))

# #         # collect by vehicle + keep rows per vehicle in chronological order for greedy assignment
# #         vehicle_rows = defaultdict(list)   # vtype -> list[(row, actual_days)]
# #         total_present = 0.0
# #         for r in rows:
# #             vtype = (r.vehicle_type or "").strip().lower()
# #             # actual days: prefer Adjusted No of Days input? NO — per requirement, No of Days is actual presence.
# #             actual = float(r.get("no_of_days") or 0)
# #             if actual <= 0 and r.get("start_date") and r.get("end_date"):
# #                 actual = days_in_range(r.start_date, r.end_date)
# #             r.no_of_days = actual  # keep visible as actual
# #             r.adjusted_no_of_days = 0  # we will set post allocation
# #             vehicle_rows[vtype].append((r, actual))
# #             total_present += actual

# #         self.present_days = total_present

# #         # ---- Allocate CONTRIBUTING days towards cap
# #         # If present >= cap: fill cap with larger-vehicle first; else: adjusted == actual
# #         days_by_vehicle = {v: sum(d for _, d in lst) for v, lst in vehicle_rows.items()}

# #         if total_present >= cap:
# #             assigned_by_vehicle = _allocate_cap_greedy(days_by_vehicle, cap)  # dict v -> assigned (<= days_by_vehicle[v])
# #         else:
# #             assigned_by_vehicle = {v: days_by_vehicle[v] for v in days_by_vehicle}

# #         # ---- Distribute assigned_by_vehicle down to rows (greedy by Start Date), set Adjusted No of Days
# #         for v, lst in vehicle_rows.items():
# #             # sort by start date for deterministic fill
# #             lst_sorted = sorted(lst, key=lambda t: getdate(t[0].start_date) if t[0].start_date else month_start)
# #             remaining = float(assigned_by_vehicle.get(v, 0.0))
# #             for r, actual in lst_sorted:
# #                 take = min(actual, remaining) if remaining > 0 else 0.0
# #                 r.adjusted_no_of_days = take
# #                 remaining -= take

# #         # ---- Effective full rate from ADJUSTED days (not raw totals)
# #         # numerator = sum(rate(v) * adjusted_days(v)); denominator = cap
# #         num = 0.0
# #         for v, lst in vehicle_rows.items():
# #             rate = rate_by_vehicle.get(v, 0.0)
# #             adj_v = sum(r.adjusted_no_of_days for r, _ in lst)
# #             num += rate * adj_v

# #         effective_full_rate = (num / cap) if cap else 0.0  # could equal a single vehicle rate (dominant) or a blend

# #         # ---- Payable: rules
# #         if total_present < 10:
# #             payable = 0.0
# #         elif total_present >= cap:
# #             payable = effective_full_rate
# #         else:
# #             payable = effective_full_rate * (total_present / cap if cap else 0.0)

# #         # ---- Parent totals
# #         self.monthly_conveyance_amount = _rhu(effective_full_rate)
# #         self.conveyance_charges = _rhu(effective_full_rate)
# #         self.pro_rata_charges = _rhu(effective_full_rate)

# #         # ---- Split payable back into child rows (by weight = rate * adjusted_row_days)
# #         # If payable == 0 simply zero amounts.
# #         weights = []
# #         W = Decimal("0")
# #         for v, lst in vehicle_rows.items():
# #             rate = Decimal(str(rate_by_vehicle.get(v, 0.0)))
# #             for r, _ in lst:
# #                 adj = Decimal(str(r.adjusted_no_of_days or 0))
# #                 w = rate * adj
# #                 weights.append((r, w))
# #                 W += w

# #         if payable <= 0 or W <= 0:
# #             for r, _ in weights:
# #                 r.amount = 0
# #             return

# #         payable_dec = Decimal(str(payable))
# #         running = Decimal("0")
# #         for i, (r, w) in enumerate(weights, start=1):
# #             if i < len(weights):
# #                 share = (payable_dec * w / W).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
# #                 r.amount = int(share)
# #                 running += share
# #             else:
# #                 r.amount = int((payable_dec - running).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# # # ---- helpers ----

# # def _allocate_cap_greedy(days_by_vehicle: dict, cap: int) -> dict:
# #     """
# #     Given per-vehicle actual days and a cap, allocate up to 'cap' days:
# #     take from the vehicle with the largest days first, then the next, etc.
# #     Returns per-vehicle assigned days (sum == min(sum(actual), cap)).
# #     """
# #     remaining = float(cap)
# #     # sort by days desc
# #     items = sorted(days_by_vehicle.items(), key=lambda kv: kv[1], reverse=False)
# #     out = {v: 0.0 for v, _ in items}
# #     for v, d in items:
# #         if remaining <= 0:
# #             break
# #         take = min(d, remaining)
# #         out[v] = take
# #         remaining -= take
# #     return out

# # def _rhu(x):
# #     return int(Decimal(str(x)).quantize(0, rounding=ROUND_HALF_UP))







# # import math
# # from decimal import Decimal, ROUND_HALF_UP
# # import frappe
# # from frappe.model.document import Document
# # from frappe.utils import date_diff, getdate, nowdate , get_first_day , get_last_day
# # from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
# # from datetime import date 

# # class EmployeeConveyanceDays(Document):
# #     def validate(self):
# #         # Fetch vehicle type from Employee if not already set
# #         vehicle_type = frappe.db.get_value("Employee", self.employee, "custom_vehicle_type")
# #         self.vehicle_type = self.vehicle_type or vehicle_type or ""
# #         month_start= get_first_day(self.start_date)
# #         month_end = get_last_day(self.end_date)
# #         print("month_start",month_start, "month_end",month_end)
# #         # month_end 
# #         payment_days = date_diff(month_end, month_start) + 1
        
# #         payment_days -= len(SalarySlip.get_holidays_for_employee(self,month_start, month_end))
# #         self.total_working_days = payment_days if payment_days > 0 else 0
# #         if not self.employee or not self.present_days or not self.total_working_days:
# #             return
# #         if not self.vehicle_type:
# #             return

# #         # Fetch Payroll Master Setting (current or latest applicable)
# #         setting = get_previous_payroll_master_setting(self.payroll_year, self.payroll_date)
# #         if not setting:
# #             frappe.throw("No applicable Payroll Master Setting found for the given payroll period.")

# #         # Get the correct rate for the vehicle type from the setting
# #         vehicle_type_lower = self.vehicle_type.strip().lower()
# #         monthly_amount = 0
# #         for row in setting.conveyance_allowance:
# #             if row.type_of_vehicles and row.type_of_vehicles.strip().lower() == vehicle_type_lower:
# #                 monthly_amount = row.amount_per_month
# #                 break

# #         if not monthly_amount:
# #             frappe.throw(f"No conveyance rate found in Payroll Master Setting for vehicle type: {self.vehicle_type}")

# #         self.monthly_conveyance_amount = monthly_amount
# #         self.minimum_working_days = math.ceil(0.75 * self.total_working_days)

# #         # Calculate combined present days across all vehicle types for this period
# #         total_days_in_period = frappe.db.sql(
# #             """
# #             SELECT COALESCE(SUM(present_days), 0)
# #             FROM `tabEmployee Conveyance Days`
# #             WHERE employee = %s
# #               AND payroll_year = %s
# #               AND payroll_date = %s
# #               AND name != %s
# #             """,
# #             (self.employee, self.payroll_year, self.payroll_date, self.name),
# #         )[0][0]
# #         other_name = frappe.db.get_value(
# #     "Employee Conveyance Days",
# #     {
# #         "employee": self.employee,
# #         "payroll_year": self.payroll_year,
# #         "payroll_date": self.payroll_date,
# #         "name": ("!=", self.name),
# #     },
# #     "name",
# # )


# #         total_days_in_period += self.present_days

# #         # --- Apply eligibility rules based on combined attendance ---

# #         # 1. Combined days < 10 -> Not eligible at all
# #         if total_days_in_period < 10:
# #             self.conveyance_charges = 0
# #             self.pro_rata_charges = 0
# #             return

# #         # 2. Combined days >= 75% of total -> CAP at minimum_working_days
# #         if total_days_in_period >= self.minimum_working_days:
# #             print ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",{total_days_in_period})
# #             if total_days_in_period != self.present_days:
# #                 cap = self.minimum_working_days
# #                 prorated_amount = (monthly_amount * self.present_days) / cap
# #                 self.conveyance_charges = monthly_amount
# #                 self.pro_rata_charges = int(
# # 					Decimal(prorated_amount).quantize(0, rounding=ROUND_HALF_UP)
# # 				)
# #                 print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",{other_name})
# #             elif self.present_days >= self.minimum_working_days:
# #                 print ("cccccccccccccccccccccccccccccccccccccc",{self.present_days})
# #                 self.present_days = self.minimum_working_days
# #                 self.conveyance_charges = monthly_amount
# #                 self.pro_rata_charges = monthly_amount
# #             else : 
# #                 prorated_amount = (monthly_amount * self.present_days) / self.total_working_days
# #                 self.conveyance_charges = monthly_amount
# #                 self.pro_rata_charges = int(
# # 					Decimal(prorated_amount).quantize(0, rounding=ROUND_HALF_UP)
# # 				)
# #         else:
# #             # 3. Else, partial allowance (pro-rata based on actual total days)
# #             print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
# #             self.present_days = min(self.present_days, self.minimum_working_days)
# #             prorated_amount = (monthly_amount / self.minimum_working_days) * self.present_days
# #             self.conveyance_charges = monthly_amount
# #             self.pro_rata_charges = int(
# #                 Decimal(prorated_amount).quantize(0, rounding=ROUND_HALF_UP)
# #             )

# @staticmethod
# def get_previous_payroll_master_setting(year, month_number):
#     import calendar

#     year = int(year)

#     # Convert month name to number if needed
#     if isinstance(month_number, str):
#         month_number = list(calendar.month_name).index(month_number)

#     years_to_consider = [year, year - 1]

#     settings = frappe.get_all(
#         "Payroll Master Setting",
#         filters={"payroll_year": ["in", years_to_consider]},
#         fields=["name", "payroll_year", "payroll_month_number"],
#         order_by="payroll_year desc, payroll_month_number desc",
#         limit=20
#     )

#     for record in settings:
#         ry = int(record["payroll_year"])
#         rm = int(record["payroll_month_number"])
#         if ry < year or (ry == year and rm <= month_number):
#             return frappe.get_doc("Payroll Master Setting", record["name"])

#     return None
