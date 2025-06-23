


import frappe
from datetime import datetime
from decimal import Decimal, InvalidOperation
from frappe.utils import flt
from frappe.utils import getdate






def pull_values_from_payroll_master(doc, method):
    doc.get_emp_and_working_day_details()
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
    doc.custom_conveyance_allowances                  = settings.conveyance_allowances
    doc.custom_overtime_wages                         = settings.overtime_wages
    doc.custom_hra                                    = settings.hra_
 

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






def set_professional_tax(doc, method):
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    # Only apply tax in January (1) and July (7)
    salary_month = getdate(doc.start_date).month
    if salary_month not in [1, 7]:
        return  # Do nothing in other months

    if not doc.gross_pay:
        return  # If gross pay is not available, exit

    # Get active Profession Tax document
    profession_tax = frappe.get_value("Profession Tax", {"is_active": 1}, "name")
    if not profession_tax:
        frappe.log_error("No active Profession Tax document found", "Professional Tax Calculation")
        return

    profession_tax_doc = frappe.get_doc("Profession Tax", profession_tax)

    # Loop through tax slabs
    for slab in profession_tax_doc.profession__tax_slab:
        if slab.from_gross_salary <= doc.gross_pay <= slab.to_gross_salary:
            doc.custom_professional_tax = slab.tax_amount
            frappe.db.set_value("Salary Slip", doc.name, "custom_professional_tax", slab.tax_amount)
            print(f"✅ [Professional Tax] Gross Pay: {doc.gross_pay} → Applied Tax: {slab.tax_amount}")
            break  # Stop at first match
        else:
            print(f"⚠️ [Professional Tax] No slab matched for Gross Pay: {doc.gross_pay}")



def set_custom_medical_allowance(doc, method):
    print("========== Setting Custom Medical Allowance ==========")


    # 1. Get base salary from Salary Structure Assignment
    base = frappe.db.get_value("Salary Structure Assignment", {
        "employee": doc.employee,
        "from_date": ["<=", doc.start_date],
    }, "base")

    if not base:
        print("Base salary not found for employee.")
        return

    # 2. Fetch active Medical Allowance Slab
    slab = frappe.get_all("Medical Allowance Slab", filters={"is_active": 1}, limit=1)
    if not slab:
        print("No active Medical Allowance Slab found.")
        return

    slab_doc = frappe.get_doc("Medical Allowance Slab", slab[0].name)

    # 3. Get LOP days from Salary Slip or custom logic
    lop_days = doc.custom_uploaded_leave_without_pay or 0
    print(f"LOP Days: {lop_days}")

    # 4. Check slab ranges in child table
    for row in slab_doc.medical_allowance:
        from_amt = row.get("from_base_pay") or 0
        to_amt = row.get("to_base_pay")
        allowance_amt = row.get("amount") or 0

        print(f"Trying Slab: {from_amt} - {to_amt}, Amount: {allowance_amt}, Base: {base}")

        # Handle open-ended slab
        if to_amt in [0, None]:
            if base >= from_amt:
                if lop_days > 10:
                    proportionate = (allowance_amt / 30) * (30 - lop_days)
                    doc.custom_medical_allowance = round(proportionate, 2)
                    print(f"⚠️ LOP > 10: Proportionate Allowance: {doc.custom_medical_allowance}")
                else:
                    doc.custom_medical_allowance = allowance_amt
                    print(f"✅ Matched Open-Ended Slab: {from_amt} - ∞, Amount: {allowance_amt}")
                break

        elif from_amt <= base <= to_amt:
            if lop_days > 10:
                proportionate = (allowance_amt / 30) * (30 - lop_days)
                doc.custom_medical_allowance = round(proportionate, 2)
                print(f"⚠️ LOP > 10: Proportionate Allowance: {doc.custom_medical_allowance}")
            else:
                doc.custom_medical_allowance = allowance_amt
                print(f"✅ Matched Slab: {from_amt} - {to_amt}, Amount: {allowance_amt}")
            break
    # doc.get_emp_and_working_day_details()
    print("@@@@@@@@@@@@@salary slip core@@@@@@@@@@@@@@@@@@@@@@@")


# def set_custom_medical_allowance(doc, method=None):
#     # 1. Get base pay from Salary Structure Assignment
#     base = frappe.db.get_value("Salary Structure Assignment", {
#         "employee": doc.employee,
#         "from_date": ["<=", doc.start_date],
#         "docstatus": 1
#     }, "base")

#     if not base:
#         frappe.msgprint("Base salary not found in Salary Structure Assignment.")
#         return

#     # 2. Fetch medical_allowance child table from Payroll Master Settings
#     settings = frappe.get_single("Payroll Master Settings")
#     slabs = settings.get("medical_allowance") or []

#     if not slabs:
#         frappe.msgprint("No medical allowance slabs found in Payroll Master Settings.")
#         return

#     # 3. Find matching slab based on base pay
#     slab_amount = 0
#     for slab in slabs:
#         from_amt = slab.get("from_base_pay") or 0
#         to_amt = slab.get("to_base_pay") or 0
#         if from_amt <= base <= to_amt:
#             slab_amount = slab.get("amount") or 0
#             break
#         elif base > to_amt and to_amt == max(s.get("to_base_pay") or 0 for s in slabs):
#             # For open-ended final slab
#             slab_amount = slab.get("amount") or 0

#     # 4. Adjust for LOP if LOP days > 10
#     lop_days = doc.custom_uploaded_leave_without_pay or 0
#     if lop_days > 10:
#         slab_amount = round(((30 - lop_days) / 30) * slab_amount, 2)

#     # 5. Set value in custom field
#     doc.db_set("custom_medical_allowance", slab_amount)





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
  

# def set_overtime_wages(slip, method):
#     start_date = getdate(slip.start_date)
#     year = start_date.strftime("%Y")
#     month = start_date.strftime("%B")  # Example: 'April'

#     row = frappe.db.get_value(
#         "Employee Overtime Wages",
#         {
#             "employee_id": slip.employee,  # ✅ correct field name
#             "payroll_year": year,
#             "payroll_month": month
#         },
#         ["total_amount"],
#         as_dict=True
#     )

#     if row and row.get("total_amount"):
#         slip.custom_overtime_wages = row["total_amount"]
#         print(f"@@@@@@@@@@@@@@@@@@@@@@@@@@@@Overtime Total Amount from DB: {row['total_amount']}")
#         print(f"A##########################ssigned to Slip.custom_overtime_wages: {slip.custom_overtime_wages}")
#     else:
#         print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$No matching Overtime Wages entry found.")

# from frappe.utils import getdate

def set_overtime_wages(slip, method):
    start_date = getdate(slip.start_date)
    year = start_date.strftime("%Y")
    month = start_date.strftime("%B")  # e.g., "April"

    # Fetch all matching records (can be multiple)
    rows = frappe.db.get_all(
        "Employee Overtime Wages",
        filters={
            "employee_id": slip.employee,  # ✅ field should be 'employee' not 'employee_id'
            "payroll_year": year,
            "payroll_month": month
        },
        fields=["total_amount"]
    )

    # Sum all total_amount values
    total_overtime_amount = sum(float(row.total_amount or 0) for row in rows)

    if total_overtime_amount:
        slip.custom_overtime_wages = total_overtime_amount
        print(f"✅ Overtime Total Amount summed from DB: {total_overtime_amount}")
        print(f"✅ Assigned to Slip.custom_overtime_wages: {slip.custom_overtime_wages}")
    else:
        print("❌ No matching Overtime Wages entry found.")



def set_employee_reimbursement_wages(slip,method):
    start_date = getdate(slip.start_date)

    month = start_date.strftime("%B")
    year = start_date.strftime("%Y")
    
    row = frappe.db.get_value(
        "Employee Reimbursement Wages",
        {
            "employee_id": slip.employee,
            "reimbursement_month": month,
            "reimbursement_year": year,
        },
        ["lop_refund_amount"],
        as_dict=True
    )
    if row and row.get("lop_refund_amount"):
        slip.custom_employee_reimbursement_wages = row["lop_refund_amount"]







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



def set_lop_in_hours_deduction(slip, method):
    start_date = getdate(slip.start_date)

    # Extract month name and year from start date
    month = start_date.strftime("%B")     # e.g., "June"
    year = start_date.strftime("%Y")      # e.g., "2025"

    # Query for matching Employee Service Weightage
    row = frappe.db.get_value(
        "Employee Time Loss",
        {
            "employee_id": slip.employee,
            "payroll_year": year,
            "payroll_month": month
        },
        ["time_loss_amount"],
        as_dict=True
    )

    if row and row.time_loss_amount:
        slip.custom_time_loss_in_hours_deduction = row.time_loss_amount


# LOP Days Summary for taking leave
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
        FROM `tabLop Days Summary`
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
