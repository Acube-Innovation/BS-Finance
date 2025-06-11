


import frappe
from datetime import datetime
from decimal import Decimal, InvalidOperation
from frappe.utils import flt
from frappe.utils import getdate


def pull_values_from_payroll_master(doc, method):
    settings = frappe.get_single("Payroll Master Settings")

    doc.custom_service_weightage                      = settings.service_weightage
    doc.custom_dearness_allowance_                    = settings.dearness_allowance_
    doc.custom_yearly_increment                       = settings.yearly_increment
    doc.custom_canteen_subsidy                        = settings.canteen_subsidy
    doc.custom_washing_allowance                      = settings.washing_allowance
    doc.custom_book_allowance                         = settings.book_allowance
    doc.custom_stitching_allowance                    = settings.stitching_allowance
    doc.custom_shoe_allowance                         = settings.shoe_allowance
    doc.custom_spectacle_allowance                    = settings.spectacle_allowance
    doc.custom_ex_gratia                              = settings.ex_gratia
    doc.custom_arrear                                 = settings.arrear
    doc.custom_festival_advance                       = settings.festival_advance
    doc.custom_festival_advance_recovery              = settings.festival_advance_recovery
    doc.custom_labour_welfare_fund                    = settings.labour_welfare_fund
    doc.custom_brahmos_recreation_club_contribution   = settings.brahmos_recreation_club_contribution
    doc.custom_benevolent_fund                        = settings.benevolent_fund
    doc.custom_canteen_recovery                       = settings.canteen_recovery
    doc.custom_conveyance_allowances                = settings.conveyance_allowances
    doc.custom_overtime_wages                       =settings.overtime_wages
 

    # # --- 🧮 Service Weightage Allowance Calculation ---
    # if doc.employee:
    #     years = frappe.db.get_value("Employee", doc.employee, "custom_years_of_service") or 0
    #     rate = settings.service_weightage
    #     completed_blocks = (years - 5) // 5 + 1 if years > 5 else 0
    #     payout = completed_blocks * rate * 5

    #     # Update if component exists, else append
    #     found = False
    #     for e in doc.earnings:
    #         if e.salary_component == "Service Weightage":
    #             e.amount = payout
    #             e.default_amount = payout
    #             found = True
    #             break

    #     if not found and payout > 0:
    #         doc.append("earnings", {
    #             "salary_component": "Service Weightage",
    #             "amount": payout,
    #             "default_amount": payout,
    #         })






def set_professional_tax(doc, method=None):
    from frappe.utils import getdate

    doc.custom_professional_tax = 0

    if doc.start_date:
        try:
            start_date_obj = getdate(doc.start_date)
        except Exception as e:
            frappe.log_error(f"Error parsing start_date: {e}", "set_professional_tax")
            return

        # Change to applicable months: May & July (5, 7)
        if start_date_obj.month in [5, 7]:
            settings = frappe.get_single("Payroll Master Settings")
            slabs = settings.get("professional_tax") or []

            try:
                gross = Decimal(str(doc.gross_pay or 0))
            except InvalidOperation:
                frappe.log_error("Invalid gross pay value", "set_professional_tax")
                return

            for row in slabs:
                try:
                    from_amt = Decimal(str(row.from_gross_salary or 0))
                    to_amt = Decimal(str(row.to_gross_salary or 0))
                    tax = Decimal(str(row.tax_amount or 0))
                except InvalidOperation as e:
                    frappe.log_error(f"Invalid slab amount: {e}", "set_professional_tax")
                    continue

                if to_amt == 0 and gross >= from_amt:
                    doc.custom_professional_tax = float(tax)
                    break
                elif from_amt <= gross <= to_amt:
                    doc.custom_professional_tax = float(tax)
                    break

            # Optional debug
            frappe.logger().info(f"[PTAX] Gross: {gross}, Applied Tax: {doc.custom_professional_tax}")






def set_conveyance_allowance(slip, method):
    # Convert start_date to a datetime object
    start_date = getdate(slip.start_date)

    # Extract month name and year
    month = start_date.strftime("%B")
    year = start_date.strftime("%Y")

    # Fetch pro rata charges from Employee Conveyance Days
    row = frappe.db.get_value(
        "Employee Conveyance Days",
        {
            "employee": slip.employee,
            "payroll_year": year,
            "payroll_date": month
        },
        ["pro_rata_charges"],
        as_dict=True
    )

    if row and row.pro_rata_charges:
        # Set value in custom field on Salary Slip
        slip.custom_conveyance_allowances = row.pro_rata_charges
  

def set_overtime_wages(slip, method):
    start_date = getdate(slip.start_date)

    month = start_date.strftime("%B")
    year = start_date.strftime("%Y")

    row = frappe.db.get_value(
        "Employee Overtime Wages",
        {
            "employee_id": slip.employee,
            "payroll_year": year,
            "payroll_month": month
        },
        ["total_amount"],
        as_dict=True
    )

    if row and row.get("total_amount"):
        slip.custom_overtime_wages = row["total_amount"]




def set_custom_service_weightage(slip, method):
    start_date = getdate(slip.start_date)

    # Extract month name and year from start date
    month = start_date.strftime("%B")     # e.g., "June"
    year = start_date.strftime("%Y")      # e.g., "2025"

    # Query for matching Employee Service Weightage
    row = frappe.db.get_value(
        "Employee Service Weightage",
        {
            "employee_id": slip.employee,
            "payroll_year": year,
            "payroll_month": month
        },
        ["service_weightage"],
        as_dict=True
    )

    if row and row.service_weightage:
        slip.custom_service_weightage = row.service_weightage


def set_lop_summary(slip, method):
    from frappe.utils import getdate

    start_date = getdate(slip.start_date)

    # Extract month name and year from start date
    month = start_date.strftime("%B")     # e.g., "June"
    year = start_date.strftime("%Y")      # e.g., "2025"

    
    row = frappe.db.get_value(
        "Lop Summary",
        {
            "employee_id": slip.employee,
            "payroll_year": year,
            "payroll_month": month
        },
        ["no__of_days"],
        as_dict=True
    )

    if row and row.no__of_days:
        slip.custom_uploaded_leave_without_pay = row.no__of_days

    # ✅ Fetch total LOP days from Lop Summary
    lop_total = frappe.db.sql("""
        SELECT SUM(no__of_days) as total_days
        FROM `tabLop Summary`
        WHERE employee_id = %s AND payroll_month = %s AND payroll_year = %s
    """, (slip.employee, month, year), as_dict=True)

    if lop_total and lop_total[0].total_days:
        slip.custom_uploaded_leave_without_pay = round(lop_total[0].total_days, 2)
    else:
        slip.custom_uploaded_leave_without_pay = 0.0


def set_shoe_allowance_based_on_month(doc, method):
    if doc.start_date:
        start_month = getdate(doc.start_date).strftime("%m")  # Gets month as "01", "02", ..., "12"
        doc.custom_shoe_allowance = int(start_month)
        doc.custom_spectacle_allowances_month = int(start_month)
