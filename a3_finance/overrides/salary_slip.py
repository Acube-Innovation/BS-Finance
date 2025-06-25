


import frappe
from datetime import datetime
from decimal import Decimal, InvalidOperation
from frappe.utils import flt
from frappe.utils import getdate


def pull_values_from_payroll_master(doc, method):
    doc.get_emp_and_working_day_details()

    if not doc.start_date:
        frappe.throw("Start Date is required to pull Payroll Master Setting.")

    start = getdate(doc.start_date)
    month_number = start.month
    year = start.year

    # Get the best matching Payroll Master Setting
    setting = get_previous_payroll_master_setting(year, month_number)
    if not setting:
        frappe.throw("No applicable Payroll Master Setting found for the given start date.")

    # Map values from setting to Salary Slip custom fields
    doc.custom_dearness_allowence_percentage                    = setting.dearness_allowance_
    doc.custom_yearly_increment                       = setting.yearly_increment
    doc.custom_canteen_subsidy                        = setting.canteen_subsidy
    doc.custom_washing_allowance                      = setting.washing_allowance
    doc.custom_book_allowance                         = setting.book_allowance
    doc.custom_stitching_allowance                    = setting.stitching_allowance if month_number== 1 else 0
    doc.custom_shoe_allowance                         = setting.shoe_allowance if month_number== 1 else 0
    doc.custom_spectacle_allowance                    = setting.spectacle_allowance if month_number== 1 else 0
    # doc.custom_ex_gratia                              = setting.ex_gratia
    doc.custom_arrear                                 = setting.arrear
    doc.custom_festival_advance                       = setting.festival_advance
    doc.custom_festival_advance_recovery              = setting.festival_advance_recovery
    doc.custom_labour_welfare_fund                    = setting.labour_welfare_fund
    doc.custom_brahmos_recreation_club_contribution   = setting.brahmos_recreation_club_contribution
    doc.custom_benevolent_fund                        = setting.benevolent_fund
    doc.custom_canteen_recovery                       = setting.canteen_recovery
    # doc.custom_conveyance_allowances                  = setting.conveyance_allowances
    doc.custom_overtime_wages                         = setting.overtime_wages
    doc.custom_hra                                    = setting.hra_
    doc.custom_deputation_allowance                   = setting.deputation_allowance
    doc.custom_other                                  = setting.others

def get_previous_payroll_master_setting(year, month_number):
    years_to_consider = [year, year - 1]

    settings = frappe.get_all(
        "Payroll Master Setting",
        filters={"payroll_year": ["in", years_to_consider]},
        fields=["name", "payroll_year", "payroll_month_number"] + [
            "dearness_allowance_", "yearly_increment", "canteen_subsidy", "washing_allowance",
            "book_allowance", "stitching_allowance", "shoe_allowance", "spectacle_allowance",
            "ex_gratia", "arrear", "festival_advance", "festival_advance_recovery",
            "labour_welfare_fund", "brahmos_recreation_club_contribution", "benevolent_fund",
            "canteen_recovery", "conveyance_allowances", "overtime_wages", "hra_"
        ],
        order_by="payroll_year desc, payroll_month_number desc",
        limit=20
    )

    for record in settings:
        ry, rm = int(record["payroll_year"]), int(record["payroll_month_number"])
        if ry < year or (ry == year and rm <= month_number):
            return frappe._dict(record)

    return None


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







# def set_custom_service_weightage(slip, method):
#     start_date = getdate(slip.start_date)

#     # Extract month name and year from start date
#     month = start_date.strftime("%B")     # e.g., "June"
#     year = start_date.strftime("%Y")      # e.g., "2025"

#     # Query for matching Employee Service Weightage
#     row = frappe.db.get_value(
#         "Employee Service Weightage",
#         {
#             "employee_id": slip.employee,
#             "payroll_year": year,
#             "payroll_month": month
#         },
#         # ["service_weightage_after_lop"],
#         as_dict=True
#     )

    # Assign only if value exists
    # if row and row.service_weightage_after_lop:
    #     slip.custom_service_weightage = row.service_weightage_after_lop



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

    # # ✅ Fetch total LOP days from Lop Summary
    # lop_total = frappe.db.sql("""
    #     SELECT SUM(no__of_days) as total_days
    #     FROM `tabLop Days Summary`
    #     WHERE employee_id = %s AND payroll_month = %s AND payroll_year = %s
    # """, (slip.employee, month, year), as_dict=True)

    # if lop_total and lop_total[0].total_days:
    #     slip.custom_uploaded_leave_without_pay = round(lop_total[0].total_days, 2)
    # else:
    #     slip.custom_uploaded_leave_without_pay = 0.0


# def set_shoe_allowance_based_on_month(doc, method):
#     if doc.start_date:
#         start_month = getdate(doc.start_date).strftime("%m")  # Gets month as "01", "02", ..., "12"
#         doc.custom_shoe_allowance = int(start_month)
#         doc.custom_spectacle_allowances_month = int(start_month)


def set_basic_pay(doc, method):
    if not doc.start_date:
        return

    start_date = getdate(doc.start_date)
    start_month = start_date.strftime("%B")
    start_year = start_date.strftime("%Y")

    # === 1. Get LOP Values from Lop Per Request ===
    final_lop = frappe.db.get_value(
        "Lop Per Request",
        filters={
            "employee_id": doc.employee,
            "payroll_month": start_month,
            "payroll_year": start_year
        },
        fieldname="SUM(lop_amount)"
    ) or 0
    doc.custom_uploaded_lop_loss_amount = final_lop

    no__of_days = frappe.db.get_value(
        "Lop Per Request",
        filters={
            "employee_id": doc.employee,
            "payroll_month": start_month,
            "payroll_year": start_year
        },
        fieldname="SUM(no__of_days)"
    ) or 0
    doc.custom_uploaded_leave_without_pay = no__of_days

    sw_loss = frappe.db.get_value(
        "Lop Per Request",
        filters={
            "employee_id": doc.employee,
            "payroll_month": start_month,
            "payroll_year": start_year
        },
        fieldname="SUM(employee_service_weightage_loss)"
    ) or 0

    da_loss = frappe.db.get_value(
        "Lop Per Request",
        filters={
            "employee_id": doc.employee,
            "payroll_month": start_month,
            "payroll_year": start_year
        },
        fieldname="SUM(employee_da_loss_for_payroll_period)"
    ) or 0
    doc.custom_dearness_allowance_ = da_loss

    # === 2. Fetch full original service weightage for that month/year ===
    sw_row = frappe.db.get_value(
        "Employee Service Weightage",
        {
            "employee_id": doc.employee,
            "payroll_month": start_month,
            "payroll_year": start_year
        },
        "service_weightage",
        as_dict=True
    )

    doc.custom_actual_sw = float(sw_row.service_weightage or 0) if sw_row else 0
    adjusted_sw = doc.custom_actual_sw - sw_loss
    doc.custom_service_weightage= round(adjusted_sw, 2)  #reused an unused field (custom_basic_pay)
