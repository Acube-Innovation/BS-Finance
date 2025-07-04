


import frappe
from datetime import datetime
from decimal import Decimal, InvalidOperation
from frappe.utils import flt
from frappe.utils import getdate
from frappe.utils import getdate, flt
from calendar import month_name


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
    from frappe.utils import getdate
    import math

    # Extract month and year from salary slip start_date
    start_date = getdate(slip.start_date)
    year = start_date.strftime("%Y")
    month = start_date.strftime("%B")

    # Fetch and sum all matching overtime wage entries
    total_overtime_amount = frappe.db.sql("""
        SELECT SUM(total_amount) FROM `tabEmployee Overtime Wages`
        WHERE employee_id = %s AND payroll_year = %s AND payroll_month = %s
    """, (slip.employee, year, month))[0][0] or 0

    # Round and assign
    if total_overtime_amount:
        slip.custom_overtime_wages = round(total_overtime_amount)  # Rounded to nearest rupee






def set_employee_reimbursement_wages(slip, method):
    from frappe.utils import getdate, flt

    start_date = getdate(slip.start_date)
    month = start_date.strftime("%B")
    year = start_date.strftime("%Y")

    # Sum both reimbursement_hra and lop_refund_amount for the employee/month/year
    result = frappe.db.sql("""
        SELECT 
            SUM(reimbursement_hra) AS total_hra,
            SUM(lop_refund_amount) AS total_lop_refund
        FROM `tabEmployee Reimbursement Wages`
        WHERE employee_id = %s AND reimbursement_month = %s AND reimbursement_year = %s
    """, (slip.employee, month, year), as_dict=True)

    if result and result[0]:
        hra_sum = flt(result[0].total_hra or 0)
        lop_sum = flt(result[0].total_lop_refund or 0)
        total_reimbursement = hra_sum + lop_sum

        slip.custom_employee_reimbursement_wages = lop_sum
        slip.custom_reimbursement_hra_amount = hra_sum
        slip.custom_total_reimbursement = total_reimbursement

        print(f"HRA Sum: {hra_sum}, LOP Refund Sum: {lop_sum}, Total: {total_reimbursement}")








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
    doc.custom_uploaded_leave_without_pay = round(no__of_days)

    sw_loss = frappe.db.get_value(
    "Lop Per Request",
    filters={
        "employee_id": doc.employee,
        "payroll_month": start_month,
        "payroll_year": start_year
    },
    fieldname="SUM(employee_service_weightage_loss)"
) or 0
    
    print(f"ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss{sw_loss}")

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
    # adjusted_sw = doc.custom_actual_sw - round( sw_loss)
    # doc.custom_service_weightage= round(adjusted_sw, 2)  #reused an unused field (custom_basic_pay)
    adjusted_sw = doc.custom_actual_sw - float(sw_loss)
    doc.custom_service_weightage = round(adjusted_sw, 2)


# def create_payroll_summary(doc,method):
#         # Create Employee Payroll Details from Salary Slip
#     if not frappe.db.exists("Employee Payroll Details", {
#         "employee": doc.employee,
#         "payroll_month": doc.payroll_month,
#         "payroll_year": doc.payroll_year
#     }):
#         epd = frappe.new_doc("Employee Payroll Details")
#         epd.employee = doc.employee
#         epd.employee_name = doc.employee_name
#         epd.payroll_month = doc.payroll_month
#         epd.payroll_year = doc.payroll_year
#         epd.start_date = doc.start_date
#         epd.end_date = doc.end_date
#         epd.base_pay = doc.base
#         epd.da = doc.custom_dearness_allowance_  # Assuming this is the field for DA
#         epd.service_weightage = doc.custom_service_weightage
#         epd.gross_pay = doc.gross_pay
#         epd.attendance_days = doc.total_working_days
#         epd.refund_hours = doc.custom_refund_hours or 0
#         epd.society_deduction = doc.custom_society_deduction or 0
#         epd.insert()
#         frappe.msgprint("✅ Employee Payroll Details created.")


@frappe.whitelist()
def update_tax_component(doc, method):
    from frappe.utils import getdate, flt

    employee = doc.employee
    gross_pay = flt(doc.gross_pay)
    time_loss_deduction = flt(doc.custom_time_loss_in_hours_deduction)
    # actual_earnings = flt(frappe.db.get_value('Employee', employee, 'custom_actual_earnings'))

    slip_date = getdate(doc.start_date)
    current_month = slip_date.strftime("%B")  # e.g., "April"
    current_year = slip_date.year

    # Calculate fiscal month index (April = 1, May = 2, ..., March = 12)
    fiscal_month_index = (slip_date.month - 4 + 12) % 12 + 1
    months_remaining = 12 - (fiscal_month_index - 1)

    # Get past months' tracker entries for this fiscal year
    past_entries = frappe.get_all(
        "Taxable Earnings Tracker",
        filters={
            "employee": employee,
            "fiscal_year": current_year,
        },
        fields=["gross_pay", "time_loss_deduction"]
    )

    # Sum up gross - deduction from all previous months
    cumulative_total = sum(
        flt(entry["gross_pay"]) - flt(entry["time_loss_deduction"]) for entry in past_entries
    )

    # Add current month's values
    cumulative_total += gross_pay - time_loss_deduction

    # Final taxable earnings
    taxable_earnings = (actual_earnings * months_remaining) + cumulative_total

    # Insert or update the Taxable Earnings Tracker
    existing = frappe.get_all(
        "Taxable Earnings Tracker",
        filters={"employee": employee, "month": current_month, "fiscal_year": current_year},
        fields=["name"],
        limit=1
    )

    if existing:
        tracker_doc = frappe.get_doc("Taxable Earnings Tracker", existing[0]["name"])
    else:
        tracker_doc = frappe.new_doc("Taxable Earnings Tracker")

    tracker_doc.employee = employee
    tracker_doc.fiscal_year = current_year
    tracker_doc.month = current_month
    tracker_doc.gross_pay = gross_pay
    tracker_doc.time_loss_deduction = time_loss_deduction
    tracker_doc.cumulative_taxable_earnings = taxable_earnings
    tracker_doc.save()

    # ✅ Update in Employee
    # frappe.db.set_value("Employee", employee, "custom_taxable_earnings", taxable_earnings)



def update_tax_on_salary_slip(slip, method):
    # if slip.docstatus != 0:
    #     return

    from calendar import month_name
    from frappe.utils import getdate, flt, cint

    employee = slip.employee
    start_date = getdate(slip.start_date)
    month = start_date.strftime("%B")
    month_number = start_date.month
    year = start_date.year

    print(f"\n--- Processing Tax for {employee} - {month} {year} ---")

    base_salary = flt(frappe.db.get_value("Salary Structure Assignment", {"employee":slip.employee}, "base")) or 0
    service_weightage = flt(frappe.db.get_value("Employee", employee, "custom_service_weightage_emp")) or 0
    employment_type = frappe.db.get_value("Employee", employee, "employment_type") or ""
    no_of_children = cint(frappe.db.get_value("Employee", employee, "custom_no_of_children_eligible_for_cea") or 0)
    vehicle_type = frappe.db.get_value("Employee", employee, "custom_vehicle_type") or None

    print(f"Base Salary: {base_salary}")
    print(f"Service Weightage: {service_weightage}")
    print(f"Employment Type: {employment_type}")
    print(f"No of Children: {no_of_children}")
    print(f"Vehicle Type: {vehicle_type}")

    # Get full Payroll Master Setting document
    pms_name = frappe.get_value("Payroll Master Setting", {"payroll_month": month, "payroll_year": str(year)}, "name")
    if not pms_name:
        frappe.throw("Payroll Master Setting not found for the given month and year.")

    pms = frappe.get_doc("Payroll Master Setting", pms_name)

    da_amt = round((base_salary + service_weightage) * flt(pms.get("dearness_allowance_", 0)))
    hra_amt = round((base_salary + service_weightage) * flt(pms.get("hra_", 0)))
    canteen_subsidy = flt(pms.get("canteen_subsidy", 0))

    print(f"DA (%): {pms.get('dearness_allowance_', 0)}, Amount: {da_amt}")
    print(f"HRA (%): {pms.get('hra_', 0)}, Amount: {hra_amt}")
    print(f"Canteen Subsidy: {canteen_subsidy}")

    medical_allowance = 1400 if base_salary <= 29699 else 1700 if base_salary <= 34000 else 2000
    washing_allowance = 125 if employment_type.lower() == "workers" else 0
    book_allowance= 250 if employment_type.lower() == "officers" else 0

    print(f"Medical Allowance: {medical_allowance}")
    print(f"Washing Allowance: {washing_allowance}")

    # ✅ Get Conveyance Allowance from PMS child table
    conveyance_allowance = 0
    if vehicle_type and hasattr(pms, "conveyance_allowance"):
        for row in pms.conveyance_allowance:
            if row.type_of_vehicles == vehicle_type:
                conveyance_allowance = flt(row.amount_per_month)
                print(f"Matched Vehicle Type in PMS: {row.type_of_vehicles} → ₹{conveyance_allowance}")
                break
    else:
        print("No conveyance match found or conveyance_allowance table missing.")

    # children_education_allowance = sum(
    # flt(row.amount) for row in slip.earnings
    # print(f"Children Education Allowance: {children_education_allowance}")
    if no_of_children == 1:
        children_education_allowance = 400
    elif no_of_children >=2:
        children_education_allowance = 800
    else:
        children_education_allowance=0
    print(f"Children Education Allowance: {children_education_allowance}")
    # Monthly earning
    monthly_earning = (
        base_salary + service_weightage + da_amt + hra_amt +
        medical_allowance + washing_allowance +
        conveyance_allowance + children_education_allowance + canteen_subsidy + book_allowance
    )
    print(f"Monthly Earning (Estimated): {monthly_earning}")
    # Past payroll info
    fy_start_year = year if month_number >= 4 else year - 1
    fiscal_months = list(month_name)[4:month_number] if month_number > 4 else []

    print(f"Fiscal Year Start: {fy_start_year}")
    print(f"Past Months Considered: {fiscal_months}")

    past_details = frappe.get_list(
        "Employee Payroll Details",
        filters={
            "employee": employee,
            "payroll_year": str(fy_start_year),
            "payroll_month": ["in", fiscal_months] if fiscal_months else ""
        },
        fields=["actual_earning","gross_pay", "lop_hrs", "tax_paid"],
        order_by="payroll_month asc" if fiscal_months else None
    ) if fiscal_months else []

    total_tax_paid = sum(flt(row.tax_paid) for row in past_details)
    total_past_taxable = sum(flt(row.gross_pay) - flt(row.lop_hrs) for row in past_details)

    print(f"Total Tax Paid So Far: {total_tax_paid}")
    print(f"Total Past Taxable Income: {total_past_taxable}")
    # monthly_earning = flt(frappe.db.get_value("Employee", employee, "custom_actual_earnings")) or 0
    current_gross = flt(slip.gross_pay)
    current_lop = round(flt(slip.custom_time_loss_in_hours_deduction))
    current_taxable = current_gross - current_lop

    print(f"Current Gross Pay: {current_gross}")
    print(f"Current LOP: {current_lop}")
    print(f"Current Taxable Income: {current_taxable}")

    if month_number >= 4:
        months_left = 15 - month_number
    else:
        months_left = 3 - month_number + 1

    print(f"Months Left in FY: {months_left}")

    estimated_total_taxable_income = (
        (monthly_earning * months_left) +
        total_past_taxable + current_taxable + 65000 - 75000
    )
    # estimated_total_taxable_income = (
    #     (monthly_earning * months_left) +
    #     total_past_taxable + current_taxable + 65000 - 75000
    # )

    print(f"Months Left in FY: {months_left}")
    print(f"Estimated Full-Year Taxable Income Before Tax Deduction: {estimated_total_taxable_income}")

    # net_taxable_income = estimated_total_taxable_income - total_tax_paid
    net_taxable_income = estimated_total_taxable_income

    print(f"Net Taxable Income (After Deducting Tax Paid): {net_taxable_income}")

    # Tax slab calculation
    tax = 0
    remaining = net_taxable_income
    slabs = [
    (400000, 0.00),  # First 4L: no tax
    (400000, 0.05),  # Next 4L: 5%
    (400000, 0.10),  # ...
    (400000, 0.15),
    (400000, 0.20),
    (400000, 0.25),(40000000,0.30)]

    if remaining > 1200000:
        for slab_amt, rate in slabs:
            if remaining > slab_amt:
                slab_tax = slab_amt * rate
                tax += slab_tax
                remaining -= slab_amt
                print(f"Slab: {slab_amt} @ {rate*100}% = {slab_tax}")
            else:
                slab_tax = remaining * rate
                tax += slab_tax
                print(f"Slab: {remaining} @ {rate*100}% = {slab_tax}")
                remaining = 0
                break
    else:
        remaining = 0
        tax=0
    if remaining > 0:
        slab_tax = remaining * 0.30
        tax += slab_tax
        print(f"Remaining: {remaining} @ 30% = {slab_tax}")

    cess = tax * 0.04
    tax *= 1.04
    tax-= sum(flt(row.tax_paid) for row in past_details)
    # ================================================================
    # slip.custom_current_net_total_earnings=estimated_total_taxable_income
    # slip.custom_income_tax=sum(flt(row.tax_paid) for row in past_details)
    # slip.custom_tax_calculation_month=months_left
    # ====================================================================
    print(f"Cess (4%): {cess}")
    print(f"Final Monthly Tax Payable: {round(tax, 2)}")

    monthly_tax = round(tax)
    slip.custom_income_tax = round(monthly_tax/(months_left+1))
    print(f"Final Tax Payable: {round(slip.custom_income_tax, 2)}")
    tax_amount = flt(slip.custom_income_tax)

    # # Update if exists, else append
    row = next((d for d in slip.deductions if d.salary_component == "Income Tax"), None)

    if row:
        row.amount = tax_amount
    else:
        slip.append("deductions", {
            "salary_component": "Income Tax",
            "amount": tax_amount
        })


    # if deduction_row != slip.custom_income_tax:
    #     slip.save()
def update_tax_after_save(doc, method):
    # This runs after the salary slip is saved
    frappe.logger(f"Slip saved for {doc.employee} — now running tax logic.")

def set_income_tax_from_custom_field(slip, method):
    tax_amount = flt(slip.custom_income_tax)

    # Update if exists, else append
    row = next((d for d in slip.deductions if d.salary_component == "Income Tax"), None)

    if row:
        row.amount = tax_amount
    else:
        slip.append("deductions", {
            "salary_component": "Income Tax",
            "amount": tax_amount
        })



import frappe
from frappe.utils import getdate, flt

def update_employee_payroll_details(slip, method):
    from frappe.utils import getdate, flt

    employee = slip.employee
    start_date = getdate(slip.start_date)
    payroll_month = start_date.strftime("%B")
    payroll_year = start_date.strftime("%Y")
    payroll_month_number = start_date.month

    # Extract only what’s needed
    gross_pay = flt(slip.gross_pay)
    lop_hrs = flt(slip.custom_time_loss_in_hours_deduction)

    # Use next() with generator for faster lookup
    tax_paid = flt(next(
        (row.amount for row in slip.deductions if row.salary_component == "Income Tax"),
        0
    ))

    # Get or create the document
    doc = frappe.get_doc("Employee Payroll Details", frappe.db.get_value(
        "Employee Payroll Details",
        {
            "employee": employee,
            "payroll_month": payroll_month,
            "payroll_year": payroll_year
        },
        "name"
    )) if frappe.db.exists("Employee Payroll Details", {
        "employee": employee,
        "payroll_month": payroll_month,
        "payroll_year": payroll_year
    }) else frappe.new_doc("Employee Payroll Details")

    # Assign fields
    doc.update({
        "start_date":slip.start_date,
        "end_date":slip.end_date,
        "employee": employee,
        "da":slip.custom_dearness_allowence_percentage,
        "hra":slip.custom_hra,
        "payroll_month": payroll_month,
        "payroll_year": payroll_year,
        "payroll_month_number": payroll_month_number,
        "gross_pay": gross_pay,
        "lop_hrs": lop_hrs,
        "net_pay" : gross_pay - lop_hrs,
        "tax_paid": tax_paid
    })

    doc.save(ignore_permissions=True)

def enforce_society_deduction_limit(doc, method):
    total_earnings = sum([row.amount for row in doc.earnings])
    total_deductions = sum([row.amount for row in doc.deductions])
    net_salary = total_earnings - total_deductions

    for row in doc.deductions:
        if row.salary_component == "Society":
            if row.amount > 0.75 * net_salary:
                row.amount = 0
                # frappe.msgprint("Society deduction exceeds 75% of net salary and has been set to 0.")


# # def calculate_current_actual_base(doc,method):
#     base= frappe.db.get_value('Employee',self.employee,'custom_basic_pay')
#     service_weightage=frappe.db.get_value('Employee',self.employee,'custom_service_weightage_emp')
#     other_payments=frappe.get_value(
#         "Payroll Master Setting",
#         {"payroll_month": month, "payroll_year": year},
#         ["dearness_allowance_", "house_rent_allowance", "stitching_allowance", "washing_allowance"],
#         as_dict=True
#     ) or {}