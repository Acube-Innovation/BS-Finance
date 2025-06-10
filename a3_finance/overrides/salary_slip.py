


import frappe
from datetime import datetime
from decimal import Decimal, InvalidOperation
from frappe.utils import flt



def pull_values_from_payroll_master(doc, method):
    settings = frappe.get_single("Payroll Master Settings")

    doc.custom_service_weightage                      = settings.service_weightage
    doc.custom_dearness_allowance_                    = settings.dearness_allowance_
    doc.custom_yearly_increment                       = settings.yearly_increment
    doc.custom_canteen_subsidy                        = settings.canteen_subsidy
    doc.custom_washing_allowance                      = settings.washing_allowance
    doc.custom_book_allowance                         = settings.book_allowance
    doc.custom_night_shift_allowance                  = settings.night_shift_allowance
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


    # --- 🧮 Service Weightage Allowance Calculation ---
    if doc.employee:
        years = frappe.db.get_value("Employee", doc.employee, "custom_years_of_service") or 0
        rate = settings.service_weightage
        completed_blocks = (years - 5) // 5 + 1 if years > 5 else 0
        payout = completed_blocks * rate * 5

        # Update if component exists, else append
        found = False
        for e in doc.earnings:
            if e.salary_component == "Service Weightage":
                e.amount = payout
                e.default_amount = payout
                found = True
                break

        if not found and payout > 0:
            doc.append("earnings", {
                "salary_component": "Service Weightage",
                "amount": payout,
                "default_amount": payout,
            })






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
    # Extract month and year
    month = slip.start_date.strftime("%B")
    year = slip.start_date.strftime("%Y")

    # Search for relevant record
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

    if row:
        # Create an Additional Salary Component directly
        slip.append("earnings", {
            "salary_component": "Conv. Allowance",
            "amount": row.pro_rata_charges
        })
