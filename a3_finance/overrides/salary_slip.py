import frappe
from datetime import datetime
from decimal import Decimal, InvalidOperation
from frappe.utils import flt
from frappe.utils import getdate
from frappe.utils import getdate, flt
from calendar import month_name
from frappe.utils import getdate, flt, cint, nowdate
from frappe.utils import getdate, nowdate,rounded
from a3_finance.utils.math_utils import round_half_up
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
    doc.custom_ex_gratia                              = setting.ex_gratia
    doc.custom_arrear                                 = setting.arrear
    doc.custom_festival_advance                       = setting.festival_advance
    doc.custom_festival_advance_recovery              = setting.festival_advance_recovery
    doc.custom_labour_welfare_fund                    = setting.labour_welfare_fund if setting.payroll_month_number in [6, 12] else 0
    doc.custom_brahmos_recreation_club_contribution   = setting.brahmos_recreation_club_contribution if setting.brahmos_recreation_club_contribution else 20
    if not doc.custom_benevolent_fund:
        doc.custom_benevolent_fund                        = setting.benevolent_fund if setting.benevolent_fund else 50
    doc.custom_canteen_recovery                       = setting.canteen_recovery
    # doc.custom_conveyance_allowances                  = setting.conveyance_allowances
    doc.custom_overtime_wages                         = setting.overtime_wages
    doc.custom_hra                                    = setting.hra_
    doc.custom_deputation_allowance                   = setting.deputation_allowance
    doc.custom_other                                  = setting.others
    current_month = getdate(doc.start_date).month
    doc.custom_shoe_allowance_month = current_month if current_month <= 12 else 12
    if doc.custom_employment_type in ["Workers", "Officers","Canteen Employee"]:
        # Calculate days between start_date and end_date (inclusive)
        start = getdate(doc.start_date)
        end = getdate(doc.end_date)
        doc.custom_weekly_payment_days = (end - start).days + 1
    if doc.custom_payroll_days == 0:
        print("ggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg",setting.payroll_days)
        doc.custom_payroll_days = setting.payroll_days if setting.payroll_days else 30

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

import frappe
from frappe.utils import getdate

def calculate_exgratia(doc, method):
    if not doc.custom_ex_gratia:
        return  # Skip if no bonus set

    employee = doc.employee
    bonus_amount = float(doc.custom_ex_gratia)

    # Determine previous financial year
    doc_date = getdate(doc.start_date)
    if doc_date.month >= 4:
        prev_fy_start = f"{doc_date.year - 1}-04-01"
        prev_fy_end = f"{doc_date.year}-03-31"
    else:
        prev_fy_start = f"{doc_date.year - 2}-04-01"
        prev_fy_end = f"{doc_date.year - 1}-03-31"

    # Fetch total LOP days from LOP per Request within prev FY
    total_lop = frappe.db.sql("""
        SELECT SUM(no__of_days) FROM `tabLop Per Request`
        WHERE employee_id= %s
          AND start_date BETWEEN %s AND %s
    """, (employee, prev_fy_start, prev_fy_end))[0][0] or 0

    # Set total LOP days in field
    doc.custom_total_lop_previous_year = total_lop

    # Calculate Ex-Gratia
    exgratia = (bonus_amount / 360.0) * (360.0 - total_lop)
    doc.custom_ex_gratia = round(exgratia)

    print(f"[DEBUG] Bonus: {bonus_amount}, LOP: {total_lop}, ExGratia: {doc.custom_ex_gratia}")




# def set_professional_tax(doc, method):
#     print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
#     # Only apply tax in January (1) and July (7)
#     salary_month = getdate(doc.start_date).month
#     if salary_month not in [1, 7]:
#         return  # Do nothing in other months

#     if not doc.gross_pay:
#         return  # If gross pay is not available, exit
#     if doc.gross_pay ==0:
#         frappe.db.set_value("Salary Slip", doc.name, "custom_professional_tax", slab.tax_amount)
#     # Get active Profession Tax document
#     profession_tax = frappe.get_value("Profession Tax", {"is_active": 1}, "name")
#     if not profession_tax:
#         frappe.log_error("No active Profession Tax document found", "Professional Tax Calculation")
#         return

#     profession_tax_doc = frappe.get_doc("Profession Tax", profession_tax)
    
#     # Loop through tax slabs
#     for slab in profession_tax_doc.profession__tax_slab:
#         if slab.from_gross_salary <= doc.gross_pay <= slab.to_gross_salary:
#             doc.custom_professional_tax = slab.tax_amount
#             print(f"doc.gross_payyyyyyyyyyyyyyyy",{doc.gross_pay})
#             frappe.db.set_value("Salary Slip", doc.name, "custom_professional_tax", slab.tax_amount)
#             print(f"✅ [Professional Tax] Gross Pay: {doc.gross_pay} → Applied Tax: {slab.tax_amount}")
#             break  # Stop at first match
#         # else:
#         #     print(f"⚠️ [Professional Tax] No slab matched for Gross Pay: {doc.gross_pay}")
#     doc.calculate_net_pay()


from frappe.utils import getdate
from datetime import datetime

def set_professional_tax(doc, method):
    salary_month = getdate(doc.start_date).month
    salary_year = getdate(doc.start_date).year

    if salary_month not in [1, 7]:
        return  # Apply tax only in Jan or July

    if not doc.employee:
        return

    # Define financial year range for the current tax window
    if salary_month == 7:
        # July → Apr to Sep of same financial year
        start = datetime(salary_year, 4, 1)
        end = datetime(salary_year, 9, 30)
    else:  # January
        # Jan → Oct to Mar (spans two calendar years)
        if salary_month == 1:
            start = datetime(salary_year - 1, 10, 1)
            end = datetime(salary_year, 3, 31)

    # Sum gross pay for eligible months
    gross_total = frappe.db.sql("""
        SELECT SUM(gross_pay) as total
        FROM `tabSalary Slip`
        WHERE employee = %s
          AND posting_date BETWEEN %s AND %s
    """, (doc.employee, start, end), as_dict=True)[0]["total"] or 0

    # Fetch active Profession Tax
    profession_tax = frappe.get_value("Profession Tax", {"is_active": 1}, "name")
    if not profession_tax:
        frappe.log_error("No active Profession Tax document found", "Professional Tax Calculation")
        return

    profession_tax_doc = frappe.get_doc("Profession Tax", profession_tax)
    print("Grosssssssssss Payyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", gross_total)
    gross_total += flt(doc.custom_gross_actual_amount) * 2
    # Match slab based on gross total
    for slab in profession_tax_doc.profession__tax_slab:
        if slab.from_gross_salary <= gross_total <= slab.to_gross_salary:
            slab.tax_amount = 1250
            doc.custom_professional_tax = slab.tax_amount
            frappe.db.set_value("Salary Slip", doc.name, "custom_professional_tax", slab.tax_amount)
            frappe.logger().info(f"[Professional Tax] Applied ₹{slab.tax_amount} for cumulative gross ₹{gross_total}")
            break

    doc.calculate_net_pay()




def set_conveyance_allowance(slip, method):
    # Convert start_date to a datetime object
    start_date = getdate(slip.start_date)

    # Extract month name and year
    month = start_date.strftime("%B")
    year = start_date.strftime("%Y")

    # Use SQL to calculate SUM of pro_rata_charges
    result = frappe.db.sql("""
        SELECT SUM(pro_rata_charges) AS total,
        SUM(present_days) AS days
        FROM `tabEmployee Conveyance Days`
        WHERE employee = %s
        AND payroll_year = %s
        AND payroll_date = %s
    """, (slip.employee, year, month), as_dict=True)

    total = flt(result[0].total) if result and result[0].total else 0

    # Set the custom field
    slip.custom_conveyance_allowances = total
    slip.custom_conveyance_days = flt(result[0].days)

  


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
    total_overtime_hrs = frappe.db.sql("""
        SELECT SUM(overtime_hours) FROM `tabEmployee Overtime Wages`
        WHERE employee_id = %s AND payroll_year = %s AND payroll_month = %s
    """, (slip.employee, year, month))[0][0] or 0

    # Round and assign
    if total_overtime_amount:
        slip.custom_overtime_wages = round_half_up(total_overtime_amount)  # Rounded to nearest rupee
        slip.custom_ot_hrs = total_overtime_hrs



def set_employee_reimbursement_wages(slip, method):
    from frappe.utils import getdate, flt

    start_date = getdate(slip.start_date)
    month = start_date.strftime("%B")
    year = start_date.strftime("%Y")

    # Sum both reimbursement_hra and lop_refund_amount for the employee/month/year
    result = frappe.db.sql("""
        SELECT 
            SUM(reimbursement_hra) AS total_hra,
            SUM(lop_refund_amount) AS total_lop_refund,
            SUM(no_of_days) AS refund_days,
            SUM(tl_hours) AS refund_hrs
        FROM `tabEmployee Reimbursement Wages`
        WHERE employee_id = %s AND reimbursement_month = %s AND reimbursement_year = %s
    """, (slip.employee, month, year), as_dict=True)
    
    if result and result[0]:
        hra_sum = flt(result[0].total_hra or 0)
        lop_sum = flt(result[0].total_lop_refund or 0)
        total_reimbursement = hra_sum + lop_sum

        slip.custom_employee_reimbursement_wages = round_half_up(lop_sum)
        slip.custom_reimbursement_hra_amount = round_half_up(hra_sum)
        slip.custom_total_reimbursement = round_half_up(total_reimbursement)
        slip.custom_lop_refund_days = flt(result[0].refund_days or 0)
        slip.custom_lop_refund_hrs = flt(result[0].refund_hrs or 0)

        print(f"HRA Sum: {hra_sum}, LOP Refund Sum: {lop_sum}, Total: {total_reimbursement}")





def set_lop_in_hours_deduction(slip, method):
    start_date = getdate(slip.start_date)

    # Extract month name and year from start date
    month = start_date.strftime("%B")     # e.g., "June"
    year = start_date.strftime("%Y")      # e.g., "2025"

    # Get sum of time_loss_amount (will retain decimals)
    total_time_loss = frappe.db.sql("""
        SELECT SUM(time_loss_amount)
        FROM `tabEmployee Time Loss`
        WHERE employee_id = %s AND payroll_year = %s AND payroll_month = %s
    """, (slip.employee, year, month))[0][0] or 0
    time_loss_hours = frappe.db.sql("""
        SELECT SUM(time_loss_hours)
        FROM `tabEmployee Time Loss`
        WHERE employee_id = %s AND payroll_year = %s AND payroll_month = %s
    """, (slip.employee, year, month))[0][0] or 0

    slip.custom_time_loss_in_hours_deduction = round_half_up(total_time_loss)
    slip.custom_lop_hrs = time_loss_hours


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
        "Employee",
        {
            "employee": doc.employee,
        },
        "custom_service_weightage_emp",
        as_dict=True
    )

    doc.custom_actual_sw = float(sw_row.custom_service_weightage_emp or 0) if sw_row else 0
    # adjusted_sw = doc.custom_actual_sw - round( sw_loss)
    # doc.custom_service_weightage= round(adjusted_sw, 2)  #reused an unused field (custom_basic_pay)
    adjusted_sw = doc.custom_actual_sw - float(sw_loss)
    doc.custom_service_weightage = round_half_up(adjusted_sw)



import frappe
from frappe.utils import getdate, nowdate, cint, flt
from calendar import month_name

@frappe.whitelist()
def update_tax_on_salary_slip(slip, method):
    if isinstance(slip, str):
        slip = frappe.get_doc("Salary Slip", slip)

    print(f"\n--- Updating Tax for Salary Slip: {slip.name} ---")

    employee = slip.employee
    start_date = getdate(slip.start_date)
    month = start_date.strftime("%B")
    month_number = start_date.month
    year = start_date.year
    base_salary = frappe.db.sql(
        """
        SELECT base
        FROM `tabSalary Structure Assignment`
        WHERE employee = %s
        AND from_date <= %s
        AND docstatus = 1
        ORDER BY from_date DESC
        LIMIT 1
        """,
        (slip.employee, slip.start_date),
    )

    base_salary = flt(base_salary[0][0]) if base_salary else 0

    service_weightage = flt(frappe.db.get_value("Employee", employee, "custom_service_weightage_emp")) or 0
    employment_type = frappe.db.get_value("Employee", employee, "employment_type") or ""
    has_washing = frappe.db.get_value("Employee", employee, "custom_has_uniform") or "0"
    no_of_children = cint(frappe.db.get_value("Employee", employee, "custom_no_of_children_eligible_for_cea") or 0)
    vehicle_type = frappe.db.get_value("Employee", employee, "custom_vehicle_type")
    extra_taxable= flt(frappe.db.get_value("Employee", employee, "custom_additional_salary_for_tax") or 0)

    pms_name = frappe.get_value("Payroll Master Setting", {"payroll_month": month, "payroll_year": str(year)}, "name")
    if not pms_name:
        frappe.throw("Payroll Master Setting not found for the given month and year.")
    pms = frappe.get_doc("Payroll Master Setting", pms_name)

    da_amt = round((base_salary + service_weightage) * flt(pms.get("dearness_allowance_", 0)))
    hra_amt = round((base_salary + service_weightage) * flt(pms.get("hra_", 0)))
    canteen_subsidy = flt(pms.get("canteen_subsidy", 0))

    medical_allowance = 0
    for row in pms.get("medical_allowance", []):
        if flt(row.from_base_pay) <= base_salary <= flt(row.to_base_pay):
            medical_allowance = flt(row.amount)
            break

    washing_allowance = flt(pms.get("washing_allowance", 0)) if employment_type.lower() == "workers" and has_washing == 1 else 0
    book_allowance = flt(pms.get("book_allowance", 0)) if employment_type.lower() == "officers" else 0

    conveyance_allowance = 0
    for row in pms.get("conveyance_allowance", []):
        if row.type_of_vehicles == vehicle_type:
            conveyance_allowance = flt(row.amount_per_month)
            break

    children_education_allowance = 0
    for row in pms.get("children_education_allowance", []):
        if cint(row.child_details) == no_of_children:
            children_education_allowance = flt(row.amount)
            break

    monthly_earning = (
        base_salary + service_weightage + da_amt + hra_amt + medical_allowance +
        washing_allowance + book_allowance + conveyance_allowance +
        children_education_allowance + canteen_subsidy
    )
    print(f"Monthly Earning: {monthly_earning}")

    fy_start_year = year if month_number >= 4 else year - 1
    fiscal_months = list(month_name)[4:month_number] if month_number > 4 else []

    past_details = frappe.get_list(
        "Employee Payroll Details",
        filters={
            "employee": employee,
            "payroll_year": str(fy_start_year),
            "payroll_month": ["in", fiscal_months] if fiscal_months else ""
        },
        fields=["gross_pay", "lop_hrs", "tax_paid"],
        order_by="payroll_month asc"
    ) if fiscal_months else []

    total_tax_paid = sum(flt(row.tax_paid) for row in past_details)
    slip.custom_current_total_tax_paid = total_tax_paid
    total_past_taxable = sum(flt(row.gross_pay) - flt(row.lop_hrs) for row in past_details)

    current_gross = flt(slip.gross_pay)
    current_lop = round(flt(slip.custom_time_loss_in_hours_deduction))
    current_taxable = current_gross - current_lop
    

    months_left = 15 - month_number if month_number >= 4 else 3 - month_number + 1
    slab_candidates = frappe.get_all(
            "Income Tax Slab",
            filters={"disabled": 0, "docstatus": 1},
            fields=["name", "effective_from"]
        )
    slab_doc=""
    if slab_candidates:
        today = getdate(nowdate())
        valid_slabs = [doc for doc in slab_candidates if getdate(doc.effective_from) <= today]
        latest_slab_doc = max(valid_slabs, key=lambda d: getdate(d.effective_from))
        slab_doc = frappe.get_doc("Income Tax Slab", latest_slab_doc.name)
    else:
        frappe.msgprint("Plaese Set Up the income tax Slabs")
    ex_gratia= slab_doc.custom_ex_gratia if slab_doc.custom_ex_gratia else 65000
    std_exemption = slab_doc.marginal_relief_limit - slab_doc.tax_relief_limit if slab_doc.marginal_relief_limit and slab_doc.tax_relief_limit else 75000
    estimated_total_taxable_income = (
        (monthly_earning * months_left) + total_past_taxable + current_taxable + ex_gratia - std_exemption + extra_taxable
    )
    slip.custom_current_net_total_earnings = estimated_total_taxable_income + std_exemption
    
    if estimated_total_taxable_income >= slab_doc.tax_relief_limit:
        net_taxable_income = estimated_total_taxable_income
        print(f"Net Taxable Income: {net_taxable_income}")

        # slab_candidates = frappe.get_all(
        #     "Income Tax Slab",
        #     filters={"disabled": 0, "docstatus": 1},
        #     fields=["name", "effective_from"]
        # )
        # today = getdate(nowdate())

        # valid_slabs = [doc for doc in slab_candidates if getdate(doc.effective_from) <= today]
        if not valid_slabs:
            frappe.throw("No active Income Tax Slab is currently applicable.")
        # latest_slab_doc = max(valid_slabs, key=lambda d: getdate(d.effective_from))
        # slab_doc = frappe.get_doc("Income Tax Slab", latest_slab_doc.name)

        relief_threshold = flt(slab_doc.tax_relief_limit or 1200000)
        marginal_threshold = flt(slab_doc.marginal_relief_limit or 1275000)
        print(f"Using Tax Slab: {slab_doc.name}, Relief Threshold: {relief_threshold}, Marginal Threshold: {marginal_threshold}")

        slabs = []
        for row in slab_doc.slabs:
            from_amt = flt(row.from_amount or 0)
            to_amt = flt(row.to_amount or 0)
            rate = flt(row.percent_deduction or 0) / 100
            slab_range = to_amt - from_amt if to_amt else 40000000
            slabs.append((slab_range, rate))
        print(f"Defined Slabs: {slabs}")

        tax = 0
        remaining = net_taxable_income
        for slab_amt, rate in slabs:
            if remaining > slab_amt:
                tax += slab_amt * rate
                remaining -= slab_amt
            else:
                tax += remaining * rate
                remaining = 0
                break
        print(f"Tax Before Marginal Relief: {round_half_up(tax)}")

        if (
            net_taxable_income > relief_threshold and
            net_taxable_income <= marginal_threshold and
            tax > (net_taxable_income - relief_threshold)
        ):
            marginal_relief = tax - (net_taxable_income - relief_threshold)
            print(f"Marginal Relief Applied: {marginal_relief}")
            tax = round_half_up(net_taxable_income - relief_threshold)

        print(f"Tax After Marginal Relief (Before Cess): {round_half_up(tax)}")
        cess_rate = slab_doc.custom_cess_rate if slab_doc.custom_cess_rate else 4
        cess = 1+ (cess_rate/100)
        tax_with_cess = round_half_up(round_half_up(tax) * cess)
        print(f"Tax After Cess: {tax_with_cess}")

        rebate_limit = flt(slab_doc.standard_tax_exemption_amount or 60000)
        rebate_income_limit = 700000
        if net_taxable_income <= rebate_income_limit and tax_with_cess <= rebate_limit:
            print(f"Rebate Applied: {tax_with_cess}")
            tax_with_cess = 0

        final_tax = tax_with_cess - total_tax_paid
        slip.custom_deputation_allowance = tax_with_cess
        monthly_tax = round_half_up(final_tax / (months_left + 1)) if final_tax > 0 else 0
        print(f"Final Tax: {final_tax}, Monthly Tax: {monthly_tax}")

        slip.custom_income_tax = monthly_tax
        if monthly_tax !=0:
            slip.custom_std_deduction = marginal_threshold - relief_threshold

        row = next((d for d in slip.deductions if d.salary_component == "Income Tax"), None)
        if row:
            row.amount = monthly_tax
            print("Updated existing Income Tax deduction row.")
        else:
            slip.append("deductions", {
                "salary_component": "Income Tax",
                "amount": monthly_tax
            })
            print("Appended new Income Tax deduction row.")

        slip.calculate_net_pay()
        print(f"--- Completed Tax Update for {slip.name} ---\n")
    # slip.calculate_net_pay()







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
    doc.calculate_net_pay()
    total_earnings = sum([row.amount for row in doc.earnings])
    total_deductions = sum([row.amount for row in doc.deductions])
    net_salary = total_earnings - total_deductions

    for row in doc.deductions:
        if row.salary_component == "Society":
            if row.amount > 0.75 * net_salary:
                row.amount = 0
                # frappe.msgprint("Society deduction exceeds 75% of net salary and has been set to 0.")



def create_benevolent_fund_log(doc, method):
    if not doc.employee:
        return

    # Check if employee is eligible
    is_beneficiary = frappe.db.get_value('Employee', doc.employee, 'custom_has_benevolent_fund_contribution')
    if not is_beneficiary:
        return

    # Check if Benevolent Fund component is present and its amount is 0
    fund_amount = 0
    for row in doc.deductions:
        if row.salary_component == "BENEVOLENT FUND":
            fund_amount = row.amount or 0
            break

    if fund_amount == 0:
        start_date = getdate(doc.start_date)
        payroll_month = start_date.strftime("%m")
        payroll_year = start_date.strftime("%Y")

        # Avoid duplicate logs
        exists = frappe.db.exists("Benevolent Fund Log", {
            "employee": doc.employee,
            "payroll_month": payroll_month,
            "payroll_year":payroll_year,
            "amount": doc.custom_benevolent_fund
        })
        if not exists:
            frappe.get_doc({
                "doctype": "Benevolent Fund Log",
                "employee_id": doc.employee,
                "payroll_month": payroll_month,
                "payroll_year":payroll_year
            }).insert(ignore_permissions=True)



from frappe.utils import getdate

def set_pending_benevolent_fund(doc, method):
    if not doc.employee:
        return
    MONTHLY_AMOUNT = 50
    # Check eligibility
    is_beneficiary = frappe.db.get_value("Employee", doc.employee, "custom_has_benevolent_fund_contribution")
    if not is_beneficiary:
        doc.custom_benevolent_fund = 0
        return

    
    gross = doc.gross_pay or 0
    to_deduct = 0

    # Get unpaid logs in oldest-to-newest order
    unpaid_logs = frappe.get_all("Benevolent Fund Log",
        filters={"employee_id": doc.employee, "status": "Unpaid"},
        fields=["name", "amount"],
        order_by="payroll_month asc"
    )

    remaining_gross = gross
    for log in unpaid_logs:
        amt = log.amount or MONTHLY_AMOUNT
        if remaining_gross >= amt:
            to_deduct += amt
            remaining_gross -= amt
        else:
            break

    # Now check if current month can be included
    if remaining_gross >= MONTHLY_AMOUNT:
        to_deduct += MONTHLY_AMOUNT

    doc.custom_benevolent_fund = to_deduct

def mark_paid_benevolent_logs(doc, method):
    if not doc.employee or not doc.custom_benevolent_fund:
        return

    is_beneficiary = frappe.db.get_value("Employee", doc.employee, "custom_has_benevolent_fund_contribution")
    if not is_beneficiary:
        return

    remaining_amount = doc.custom_benevolent_fund

    # Fetch unpaid logs in chronological order
    unpaid_logs = frappe.get_all("Benevolent Fund Log",
        filters={"employee_id": doc.employee, "status": "Unpaid"},
        fields=["name", "amount"],
        order_by="payroll_month asc"
    )

    for log in unpaid_logs:
        amt = log.amount or 0
        if remaining_amount >= amt:
            frappe.db.set_value("Benevolent Fund Log", log.name, {
                "status": "Paid",
                "salary_slip":doc.name
            })
            remaining_amount -= amt
        else:
            break

def reset_benevolent_logs_on_cancel(doc, method):
    if not doc.employee:
        return

    # Bulk update logs where salary slip is linked to this one
    frappe.db.sql("""
        UPDATE `tabBenevolent Fund Log`
        SET status = 'Unpaid', salary_slip = NULL
        WHERE employee_id = %s AND salary_slip = %s AND status = 'Paid'
    """, (doc.employee, doc.name))


def create_pf_detailed_summary(doc, method):
    from frappe.utils import getdate

    if not doc.start_date or not doc.employee:
        return

    # Extract year and month from start_date
    start_date = getdate(doc.start_date)
    payroll_month = start_date.strftime("%m")
    payroll_year = start_date.strftime("%Y")

    # Get LOP Deduction and LOP Refund from salary components
    lop_in_hours = 0
    lop_refund = 0
    for comp in doc.deductions:
        if comp.salary_component == "LOP (in Hours) Deduction":
            lop_in_hours = comp.amount
        elif comp.salary_component == "LOP Refund":
            lop_refund = comp.amount
        elif comp.salary_component == "Employee PF":
            pf = comp.amount

    # Check if record exists
    existing = frappe.db.exists("PF Detailed Log", {
        "employee": doc.employee,
        "payroll_month": payroll_month,
        "payroll_year": payroll_year
    })

    values = {
        "employee": doc.employee,
        "payroll_month": payroll_month,
        "payroll_year": payroll_year,
        "da_percentage": doc.custom_dearness_allowence_percentage,
        "lop_in_hours": lop_in_hours,
        "lop_refund": lop_refund,
        "reimbursement_hra": doc.custom_reimbursement_hra_amount,
        "pf":pf,
        "salary_slip": doc.name
    }

    if existing:
        pf_doc = frappe.get_doc("PF Detailed Log", existing)
        pf_doc.update(values)
        pf_doc.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype": "PF Detailed Log",
            **values
        }).insert(ignore_permissions=True)

from frappe.utils import getdate

def final_calculation(doc, method):
    doc.compute_component_wise_year_to_date()

    # Determine fiscal year start (April 1 of the year of start_date)
    fiscal_year_start = getdate(doc.start_date).replace(month=4, day=1)

    for row in doc.deductions:
        if row.salary_component == "Society":
            society_ytd = frappe.db.sql(
                """
                SELECT COALESCE(SUM(sd.amount), 0)
                FROM `tabSalary Slip` ss
                JOIN `tabSalary Detail` sd ON sd.parent = ss.name
                WHERE ss.docstatus IN (0, 1)
                  AND ss.employee = %s
                  AND sd.salary_component = %s
                  AND ss.start_date >= %s
                  AND ss.end_date <= %s
                """,
                (doc.employee, "Society", fiscal_year_start, doc.end_date),
            )[0][0] or 0

            # society_ytd += row.amount
            row.year_to_date = society_ytd

    doc.calculate_net_pay()
    doc.set_net_pay()




def apprentice_working_days(doc, method):
    end_date = getdate(doc.end_date)
    start_date = getdate(doc.start_date)
    if doc.custom_employment_type == "Apprentice":
        # Get apprentice contract end date
        app_end_date = getdate(frappe.db.get_value('Employee', doc.employee, 'contract_end_date'))
        doj = getdate(frappe.db.get_value('Employee', doc.employee, 'date_of_joining'))
        

        # frappe.msgprint(f"Apprentice End Date: {app_end_date}, Salary Slip End Date: {end_date}")

        if app_end_date < end_date:
            # Calculate number of working days after apprentice contract ends
            total_working_days = (app_end_date - start_date).days + 1
            # frappe.msgprint(f"Total working days after apprentice contract end: {total_working_days}")
            doc.custom_weekly_payment_days = total_working_days
        elif doj > start_date and doj <= end_date:
            # Calculate number of working days from date of joining to end date
            total_working_days = (end_date - doj).days + 1
            frappe.msgprint(f"Total working days from date of joining: {total_working_days}")
            doc.custom_weekly_payment_days = total_working_days
        else:
            doc.custom_weekly_payment_days = 30
    elif doc.custom_employment_type in ["Worker", "Officer"]:
        doc.custom_weekly_payment_days = (end_date - start_date).days + 1


import frappe

def set_actual_amounts(doc, method):
    total = 0
    total_ytd =0
    # Fetch related values only once
    ssa = frappe.db.sql(
    """
    SELECT base
    FROM `tabSalary Structure Assignment`
    WHERE employee = %s
      AND from_date <= %s
      AND docstatus = 1
    ORDER BY from_date DESC
    LIMIT 1
    """,
    (doc.employee, doc.start_date),
    as_dict=True
)

    base_salary = flt(ssa[0].base) if ssa else 0


    emp = frappe.db.get_value(
        "Employee",
        doc.employee,
        ["custom_service_weightage_emp","custom_vehicle_type"],  # adjust the field name
        as_dict=True
    )

    for row in doc.earnings:
        if row.abbr in ["BP","B"]:
            row.custom_actual_amount = base_salary if ssa else 0
            total += row.custom_actual_amount

        elif row.abbr == "SW":
            row.custom_actual_amount = emp.custom_service_weightage_emp if emp else 0
            total += row.custom_actual_amount

        elif row.abbr == "VDA":
            row.custom_actual_amount = round_half_up((base_salary+emp.custom_service_weightage_emp) * doc.custom_dearness_allowence_percentage )if emp else 0
            total += row.custom_actual_amount
        
        elif row.abbr == "HRA":
            row.custom_actual_amount = round_half_up ((base_salary+emp.custom_service_weightage_emp) * doc.custom_hra )if emp else 0
            total += row.custom_actual_amount
        
        elif row.abbr == "Canteen Subsidy":
            row.custom_actual_amount= doc.custom_canteen_subsidy
            total += row.custom_actual_amount
        
        elif row.abbr == "Medical Allowance":
            row.custom_actual_amount= (1400 if base_salary <= 29699 else 1700 if base_salary <= 34000 else 2000)
            total += row.custom_actual_amount
        
        elif row.abbr == "Conv. Allowance":
            row.custom_actual_amount= (1400 if emp.custom_vehicle_type == "4 Wheeler" else 750 if emp.custom_vehicle_type == "2 Wheeler" else 350 if emp.custom_vehicle_type == "Others" else 0)
            total += row.custom_actual_amount

        elif row.abbr == "Children Education Allowance":
            # For other components, either copy row.amount or set to 0
            row.custom_actual_amount = row.amount
            total += row.custom_actual_amount

        elif row.abbr == "Washing Allowance":
            row.custom_actual_amount = row.amount
            total += row.custom_actual_amount
        
        elif row.abbr == "Book Allowance":
            row.custom_actual_amount = row.amount
            total += row.custom_actual_amount


    doc.custom_gross_actual_amount=total

    for row in doc.deductions:
        # Add the YTD value (if None, treat as 0)
        total_ytd += (row.year_to_date or 0)

    # Assign to your custom field
    doc.custom_gross_deduction_year_to_date = total_ytd

    # YTD of Days Section
    payment_days = frappe.db.sql("""
    SELECT SUM(ss.custom_weekly_payment_days)
    FROM `tabSalary Slip` AS ss 
    WHERE ss.employee = %s AND ss.docstatus != 2
""", (doc.employee,))

    doc.custom_payment_days_ytd = payment_days[0][0] if payment_days and payment_days[0][0] else 0
    doc.custom_conveyance_days_ytd = frappe.db.sql("""SELECT SUM(ss.custom_conveyance_days) FROM `tabSalary Slip` AS ss WHERE ss.employee = %s AND ss.docstatus != 2""", (doc.employee,))[0][0] or 0
    custom_lop_refund_days_ytd = frappe.db.sql("""SELECT SUM(ss.custom_lop_refund_days) FROM `tabSalary Slip` AS ss WHERE ss.employee = %s AND ss.docstatus !=2""",(doc.employee))

    doc.custom_lop_refund_days_ytd = custom_lop_refund_days_ytd[0][0]
    doc.custom_lop_refund_hrs_ytd = frappe.db.sql("""SELECT SUM(ss.custom_lop_refund_hrs) FROM `tabSalary Slip` AS ss WHERE ss.employee = %s AND ss.docstatus != 2""", (doc.employee,))[0][0] or 0
    doc.custom_lop_hrs_ytd = frappe.db.sql("""SELECT SUM(ss.custom_lop_hrs) FROM `tabSalary Slip` AS ss WHERE ss.employee = %s AND ss.docstatus != 2""", (doc.employee,))[0][0] or 0
    doc.custom_lop_days_ytd = frappe.db.sql("""SELECT SUM(ss.custom_uploaded_leave_without_pay) FROM `tabSalary Slip` AS ss WHERE ss.employee = %s AND ss.docstatus != 2""", (doc.employee,))[0][0] or 0
    doc.custom_ot_hrs_ytd = frappe.db.sql("""SELECT SUM(ss.custom_ot_hrs) FROM `tabSalary Slip` AS ss WHERE ss.employee = %s AND ss.docstatus != 2""", (doc.employee,))[0][0] or 0

def set_weekly_present_days_from_canteen(doc,method):
    self=doc
    """Set custom_weekly_present_days from Canteen Employee Attendace if a matching record exists"""
    if not (self.start_date and self.end_date and self.employee):
        return

    # Directly join parent and child tables to get present_days in one query
    present_days = frappe.db.sql(
        """
        SELECT child.present_days
        FROM `tabCanteen Employee Attendace` AS parent
        JOIN `tabUploaded Details` AS child
            ON child.parent = parent.name
        WHERE parent.from_date = %s
            AND parent.to_date = %s
            AND child.employee = %s
            AND child.parenttype = 'Canteen Employee Attendace'
            AND child.parentfield = 'employee_attendance'
        LIMIT 1
        """,
        (self.start_date, self.end_date, self.employee),
        as_dict=True,
    )

    if present_days:
        self.custom_weekly_present_days = present_days[0].present_days
# import frappe

def add_society_deduction(doc, method):
    """Add society deductions for this salary slip if payroll_date falls within the pay period."""
    doc.calculate_net_pay()
    if not (doc.employee and doc.start_date and doc.end_date):
        return

    # Prepare a set of (salary_component, amount) already in deductions
    # existing = {(d.salary_component, float(d.amount)) for d in doc.deductions}

    # Fetch matching society deductions directly using DB filter
    society_records = frappe.get_all(
        "Society Deduction",
        filters={
            "employee": doc.employee,
            "payroll_date": ["between", [doc.start_date, doc.end_date]],
        },
        fields=["salary_component", "amount"]
    )
    doc.custom_society_deduction = society_records[0].amount if society_records else 0
    doc.calculate_net_pay()
    

    # Append only new deductions
    # for rec in society_records:
    #     key = (rec.salary_component, float(rec.amount))
    #     if key not in existing:
    #         doc.append("deductions", {
    #             "salary_component": rec.salary_component,
    #             "amount": rec.amount
    #         })

# def apply_society_deduction_cap(doc, method):
#     """
#     Cap total deductions to 75% of earnings by adjusting Society deduction.
#     If there are multiple 'Society' rows (one from structure, one from Additional Salary),
#     the linked rows are unlinked so values don't revert.
#     """
#     # Society
#     for row in doc.deductions:
#         if row.salary_component == "Society":
#             if row.amount == 0:
#                 return
#     frappe.log_error("apply_society_deduction_cap started", "DEBUG")
#     total_earnings = sum(e.amount for e in doc.earnings)
#     max_deductions = total_earnings * 0.75
#     total_deductions = sum(d.amount for d in doc.deductions)

#     frappe.log_error("apply_society_deduction_cap started", "DEBUG")
#     print(f"Society deduction cap check: Max={max_deductions}, Current={total_deductions}")

#     if total_deductions <= max_deductions:
#         return  # No adjustment required

#     excess = total_deductions - max_deductions

#     society_main = None
#     society_linked = []

#     # Separate Society rows into structure-based and linked
#     for row in doc.deductions:
#         if row.salary_component == "Society":
#             if getattr(row, "additional_salary", None):
#                 society_linked.append(row)
#             else:
#                 society_main = row

#     # Unlink any linked Society rows so ERPNext won't refresh them
#     for row in society_linked:
#         row.additional_salary = None

#     # Choose which row to adjust: prefer structure-based
#     target = society_main or (society_linked[0] if society_linked else None)
#     frappe.logger().info("apply_society_deduction_cap triggered")

#     if not target:
#         return  # No Society row found to adjust

#     # Adjust amount to enforce the cap
#     adjusted_amount = max(target.amount - excess, 0)

#     # Round down to the nearest 1000
#     adjusted_amount = (adjusted_amount // 1000) * 1000
#     if adjusted_amount > 1000:
#         target.amount = adjusted_amount
#     else:
#         target.amount = 0

#     # Recalculate totals
#     total_current = sum(d.amount for d in doc.deductions)
#     total_ytd = sum(
#         getattr(d, "year_to_date", 0) or 0 for d in doc.deductions
#     )

#     doc.total_deduction = total_current
#     doc.net_pay = doc.gross_pay - doc.total_deduction
#     doc.custom_gross_deduction_year_to_date = total_ytd
#     doc.rounded_total = rounded(doc.net_pay)
#     doc.compute_year_to_date()
#     doc.compute_month_to_date()
#     doc.calculate_net_pay()
#     # doc.set_net_pay()


def apply_society_deduction_cap(doc, method):
    """
    Cap total deductions to 75% of earnings by adjusting Society deduction.
    Society is no longer an additional salary, so simply overwrite amount.
    """
    # Find Society row
    society_row = next((row for row in doc.deductions if row.salary_component == "Society"), None)

    if not society_row or society_row.amount == 0:
        return  # Nothing to adjust

    total_earnings = sum(e.amount for e in doc.earnings)
    max_deductions = total_earnings * 0.75
    total_deductions = sum(d.amount for d in doc.deductions)

    print(f"Society deduction cap check: Max={max_deductions}, Current={total_deductions}")

    if total_deductions <= max_deductions:
        return  # No capping needed

    excess = total_deductions - max_deductions

    # Reduce the society amount by excess, not below 0
    adjusted_amount = max(society_row.amount - excess, 0)

    # Round down to nearest 1000
    adjusted_amount = (adjusted_amount // 1000) * 1000

    society_row.amount = adjusted_amount if adjusted_amount > 1000 else 0

    # Recompute totals
    doc.total_deduction = sum(d.amount for d in doc.deductions)
    doc.net_pay = doc.gross_pay - doc.total_deduction
    doc.custom_gross_deduction_year_to_date = sum((d.year_to_date or 0) for d in doc.deductions)
    doc.rounded_total = rounded(doc.net_pay)
    doc.compute_year_to_date()
    doc.compute_month_to_date()
    # doc.calculate_net_pay()



def custom_skip_society(doc, method):
    """
    Remove Society components that came from Additional Salary
    so they don't appear as a separate deduction row.
    """
    # Filter deductions list: keep everything except linked Society
    new_deductions = []
    for d in doc.deductions:
        if (
            d.salary_component == "Society"
            and (d.additional_salary or getattr(d, "additional_salary", None))
        ):
            # Skip this row
            continue
        new_deductions.append(d)

    # doc.deductions = new_deductions
































































































# def calculate_deductions_totals(doc):
#     """
#     Calculate total deductions and total deductions YTD
#     from the Salary Slip deductions table.
#     """
#     total_current = sum(d.amount for d in doc.deductions)
#     total_ytd = sum(
#         getattr(d, "year_to_date", 0) or 0 for d in doc.deductions
#     )

#     return total_current, total_ytd

    
# import frappe
# from math import floor

# def apply_society_deduction_cap(doc, method):
#     """
#     1. Remove linked Society rows to avoid duplicates.
#     2. Fetch Society amount directly from Additional Salary if exists in period.
#     3. Adjust Society deduction so total deductions <= 75% of earnings.
#        If adjustment required, round down to nearest 1000.
#     """

#     # Remove all linked Society rows
#     doc.deductions = [
#         d for d in doc.deductions
#         if not (
#             d.salary_component == "Society"
#             and (getattr(d, "additional_salary", None))
#         )
#     ]

#     # Compute totals
#     total_earnings = sum(e.amount for e in doc.earnings)
#     max_deductions = total_earnings * 0.75
#     total_deductions = sum(d.amount for d in doc.deductions)

#     # If under the cap, no adjustment needed
#     if total_deductions <= max_deductions:
#         return

#     # Find Society Additional Salary for this period
#     additional_salary_amount = frappe.db.get_value(
#         "Additional Salary",
#         {
#             "employee": doc.employee,
#             "salary_component": "Society",
#             "payroll_date": ["between", [doc.start_date, doc.end_date]],
#             "docstatus": 1,
#         },
#         "amount",
#     ) or 0

#     # Excess amount over the 75% cap
#     excess = total_deductions + additional_salary_amount - max_deductions
#     if excess <= 0:
#         return  # No need to adjust

#     # Calculate final Society deduction
#     society_final = max(additional_salary_amount - excess, 0)

#     # Round down to nearest 1000
#     society_final = (society_final // 1000) * 1000

#     if society_final > 0:
#         # Append one clean Society row with adjusted value
#         doc.append("deductions", {
#             "salary_component": "Society",
#             "amount": society_final
#         })

#     # Refresh totals
#     doc.set_totals()


# # def calculate_current_actual_base(doc,method):
#     base= frappe.db.get_value('Employee',self.employee,'custom_basic_pay')
#     service_weightage=frappe.db.get_value('Employee',self.employee,'custom_service_weightage_emp')
#     other_payments=frappe.get_value(
#         "Payroll Master Setting",
#         {"payroll_month": month, "payroll_year": year},
#         ["dearness_allowance_", "house_rent_allowance", "stitching_allowance", "washing_allowance"],
#         as_dict=True
#     ) or {}



# def set_custom_medical_allowance(doc, method):
#     print("========== Setting Custom Medical Allowance ==========")


#     # 1. Get base salary from Salary Structure Assignment
#     base = frappe.db.get_value("Salary Structure Assignment", {
#         "employee": doc.employee,
#         "from_date": ["<=", doc.start_date],
#     }, "base")

#     if not base:
#         print("Base salary not found for employee.")
#         return

#     # 2. Fetch active Medical Allowance Slab
#     slab = frappe.get_all("Medical Allowance Slab", filters={"is_active": 1}, limit=1)
#     if not slab:
#         print("No active Medical Allowance Slab found.")
#         return

#     slab_doc = frappe.get_doc("Medical Allowance Slab", slab[0].name)

#     # 3. Get LOP days from Salary Slip or custom logic
#     lop_days = doc.custom_uploaded_leave_without_pay or 0
#     print(f"LOP Days: {lop_days}")

#     # 4. Check slab ranges in child table
#     for row in slab_doc.medical_allowance:
#         from_amt = row.get("from_base_pay") or 0
#         to_amt = row.get("to_base_pay")
#         allowance_amt = row.get("amount") or 0

#         print(f"Trying Slab: {from_amt} - {to_amt}, Amount: {allowance_amt}, Base: {base}")

#         # Handle open-ended slab
#         if to_amt in [0, None]:
#             if base >= from_amt:
#                 if lop_days > 10:
#                     proportionate = (allowance_amt / 30) * (30 - lop_days)
#                     doc.custom_medical_allowance = round(proportionate, 2)
#                     print(f"⚠️ LOP > 10: Proportionate Allowance: {doc.custom_medical_allowance}")
#                 else:
#                     doc.custom_medical_allowance = allowance_amt
#                     print(f"✅ Matched Open-Ended Slab: {from_amt} - ∞, Amount: {allowance_amt}")
#                 break

#         elif from_amt <= base <= to_amt:
#             if lop_days > 10:
#                 proportionate = (allowance_amt / 30) * (30 - lop_days)
#                 doc.custom_medical_allowance = round(proportionate, 2)
#                 print(f"⚠️ LOP > 10: Proportionate Allowance: {doc.custom_medical_allowance}")
#             else:
#                 doc.custom_medical_allowance = allowance_amt
#                 print(f"✅ Matched Slab: {from_amt} - {to_amt}, Amount: {allowance_amt}")
#             break
#     # doc.get_emp_and_working_day_details()
#     print("@@@@@@@@@@@@@salary slip core@@@@@@@@@@@@@@@@@@@@@@@")


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

# def update_tax_after_save(doc, method):
#     # This runs after the salary slip is saved
#     frappe.logger(f"Slip saved for {doc.employee} — now running tax logic.")

# def set_income_tax_from_custom_field(slip, method):
#     tax_amount = flt(slip.custom_income_tax)

#     # Update if exists, else append
#     row = next((d for d in slip.deductions if d.salary_component == "Income Tax"), None)

#     if row:
#         row.amount = tax_amount
#     else:
#         slip.append("deductions", {
#             "salary_component": "Income Tax",
#             "amount": tax_amount
#         })


# def update_tax_on_salary_slip(slip, method):
#     # if slip.docstatus != 0:
#     #     return

#     from calendar import month_name
#     from frappe.utils import getdate, flt, cint

#     employee = slip.employee
#     start_date = getdate(slip.start_date)
#     month = start_date.strftime("%B")
#     month_number = start_date.month
#     year = start_date.year

#     print(f"\n--- Processing Tax for {employee} - {month} {year} ---")

#     base_salary = flt(frappe.db.get_value("Salary Structure Assignment", {"employee":slip.employee}, "base")) or 0
#     service_weightage = flt(frappe.db.get_value("Employee", employee, "custom_service_weightage_emp")) or 0
#     employment_type = frappe.db.get_value("Employee", employee, "employment_type") or ""
#     no_of_children = cint(frappe.db.get_value("Employee", employee, "custom_no_of_children_eligible_for_cea") or 0)
#     vehicle_type = frappe.db.get_value("Employee", employee, "custom_vehicle_type") or None

#     print(f"Base Salary: {base_salary}")
#     print(f"Service Weightage: {service_weightage}")
#     print(f"Employment Type: {employment_type}")
#     print(f"No of Children: {no_of_children}")
#     print(f"Vehicle Type: {vehicle_type}")

#     # Get full Payroll Master Setting document
#     pms_name = frappe.get_value("Payroll Master Setting", {"payroll_month": month, "payroll_year": str(year)}, "name")
#     if not pms_name:
#         frappe.throw("Payroll Master Setting not found for the given month and year.")

#     pms = frappe.get_doc("Payroll Master Setting", pms_name)

#     da_amt = round((base_salary + service_weightage) * flt(pms.get("dearness_allowance_", 0)))
#     hra_amt = round((base_salary + service_weightage) * flt(pms.get("hra_", 0)))
#     canteen_subsidy = flt(pms.get("canteen_subsidy", 0))

#     print(f"DA (%): {pms.get('dearness_allowance_', 0)}, Amount: {da_amt}")
#     print(f"HRA (%): {pms.get('hra_', 0)}, Amount: {hra_amt}")
#     print(f"Canteen Subsidy: {canteen_subsidy}")

#     medical_allowance = 1400 if base_salary <= 29699 else 1700 if base_salary <= 34000 else 2000
#     washing_allowance = 125 if employment_type.lower() == "workers" else 0
#     book_allowance= 250 if employment_type.lower() == "officers" else 0

#     print(f"Medical Allowance: {medical_allowance}")
#     print(f"Washing Allowance: {washing_allowance}")

#     # ✅ Get Conveyance Allowance from PMS child table
#     conveyance_allowance = 0
#     if vehicle_type and hasattr(pms, "conveyance_allowance"):
#         for row in pms.conveyance_allowance:
#             if row.type_of_vehicles == vehicle_type:
#                 conveyance_allowance = flt(row.amount_per_month)
#                 print(f"Matched Vehicle Type in PMS: {row.type_of_vehicles} → ₹{conveyance_allowance}")
#                 break
#     else:
#         print("No conveyance match found or conveyance_allowance table missing.")

#     # children_education_allowance = sum(
#     # flt(row.amount) for row in slip.earnings
#     # print(f"Children Education Allowance: {children_education_allowance}")
#     if no_of_children == 1:
#         children_education_allowance = 400
#     elif no_of_children >=2:
#         children_education_allowance = 800
#     else:
#         children_education_allowance=0
#     print(f"Children Education Allowance: {children_education_allowance}")
#     # Monthly earning
#     monthly_earning = (
#         base_salary + service_weightage + da_amt + hra_amt +
#         medical_allowance + washing_allowance +
#         conveyance_allowance + children_education_allowance + canteen_subsidy + book_allowance
#     )
#     print(f"Monthly Earning (Estimated): {monthly_earning}")
#     # Past payroll info
#     fy_start_year = year if month_number >= 4 else year - 1
#     fiscal_months = list(month_name)[4:month_number] if month_number > 4 else []

#     print(f"Fiscal Year Start: {fy_start_year}")
#     print(f"Past Months Considered: {fiscal_months}")

#     past_details = frappe.get_list(
#         "Employee Payroll Details",
#         filters={
#             "employee": employee,
#             "payroll_year": str(fy_start_year),
#             "payroll_month": ["in", fiscal_months] if fiscal_months else ""
#         },
#         fields=["actual_earning","gross_pay", "lop_hrs", "tax_paid"],
#         order_by="payroll_month asc" if fiscal_months else None
#     ) if fiscal_months else []

#     total_tax_paid = sum(flt(row.tax_paid) for row in past_details)
#     total_past_taxable = sum(flt(row.gross_pay) - flt(row.lop_hrs) for row in past_details)

#     print(f"Total Tax Paid So Far: {total_tax_paid}")
#     print(f"Total Past Taxable Income: {total_past_taxable}")
#     # monthly_earning = flt(frappe.db.get_value("Employee", employee, "custom_actual_earnings")) or 0
#     current_gross = flt(slip.gross_pay)
#     current_lop = round(flt(slip.custom_time_loss_in_hours_deduction))
#     current_taxable = current_gross - current_lop

#     print(f"Current Gross Pay: {current_gross}")
#     print(f"Current LOP: {current_lop}")
#     print(f"Current Taxable Income: {current_taxable}")

#     if month_number >= 4:
#         months_left = 15 - month_number
#     else:
#         months_left = 3 - month_number + 1

#     print(f"Months Left in FY: {months_left}")

#     estimated_total_taxable_income = (
#         (monthly_earning * months_left) +
#         total_past_taxable + current_taxable + 65000 - 75000
#     )
#     # estimated_total_taxable_income = (
#     #     (monthly_earning * months_left) +
#     #     total_past_taxable + current_taxable + 65000 - 75000
#     # )

#     print(f"Months Left in FY: {months_left}")
#     print(f"Estimated Full-Year Taxable Income Before Tax Deduction: {estimated_total_taxable_income}")

#     # net_taxable_income = estimated_total_taxable_income - total_tax_paid
#     net_taxable_income = estimated_total_taxable_income

#     print(f"Net Taxable Income (After Deducting Tax Paid): {net_taxable_income}")

#     # Tax slab calculation
#     tax = 0
#     remaining = net_taxable_income
#     slabs = [
#     (400000, 0.00),  # First 4L: no tax
#     (400000, 0.05),  # Next 4L: 5%
#     (400000, 0.10),  # ...
#     (400000, 0.15),
#     (400000, 0.20),
#     (400000, 0.25),(40000000,0.30)]

#     if remaining > 1200000:
#         for slab_amt, rate in slabs:
#             if remaining > slab_amt:
#                 slab_tax = slab_amt * rate
#                 tax += slab_tax
#                 remaining -= slab_amt
#                 print(f"Slab: {slab_amt} @ {rate*100}% = {slab_tax}")
#             else:
#                 slab_tax = remaining * rate
#                 tax += slab_tax
#                 print(f"Slab: {remaining} @ {rate*100}% = {slab_tax}")
#                 remaining = 0
#                 break
#     else:
#         remaining = 0
#         tax=0
#     if remaining > 0:
#         slab_tax = remaining * 0.30
#         tax += slab_tax
#         print(f"Remaining: {remaining} @ 30% = {slab_tax}")

#     cess = tax * 0.04
#     tax *= 1.04
#     tax-= sum(flt(row.tax_paid) for row in past_details)
#     # ================================================================
#     # slip.custom_current_net_total_earnings=estimated_total_taxable_income
#     # slip.custom_income_tax=sum(flt(row.tax_paid) for row in past_details)
#     # slip.custom_tax_calculation_month=months_left
#     # ====================================================================
#     print(f"Cess (4%): {cess}")
#     print(f"Final Monthly Tax Payable: {round(tax, 2)}")

#     monthly_tax = round(tax)
#     slip.custom_income_tax = round(monthly_tax/(months_left+1))
#     print(f"Final Tax Payable: {round(slip.custom_income_tax, 2)}")
#     tax_amount = flt(slip.custom_income_tax)

#     # # Update if exists, else append
#     row = next((d for d in slip.deductions if d.salary_component == "Income Tax"), None)

#     if row:
#         row.amount = tax_amount
#     else:
#         slip.append("deductions", {
#             "salary_component": "Income Tax",
#             "amount": tax_amount
#         })
#     slip.calculate_net_pay()


    # if deduction_row != slip.custom_income_tax:
    #     slip.save()

