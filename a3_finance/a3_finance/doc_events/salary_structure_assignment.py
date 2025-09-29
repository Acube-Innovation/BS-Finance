import frappe
from frappe.utils import flt
from frappe.utils import getdate,nowdate
from datetime import date, timedelta

def create_payroll_summary(doc, method):

    # Check for existing Employee Payroll Details with same employee and start_date
    existing_epd = frappe.get_all(
        "Employee Payroll Details",
        filters={
            "employee": doc.employee,
            "start_date": doc.from_date,
            "docstatus": ["<", 2],  # Draft or Submitted
            "active": 1
        },
        fields=["name", "base_pay"],
        limit=1
    )

    if existing_epd:
        existing_name = existing_epd[0]["name"]
        existing_base = flt(existing_epd[0]["base_pay"])

        if flt(doc.base) != existing_base:
            # Disable the old doc
            epd_doc = frappe.get_doc("Employee Payroll Details", existing_name)
            epd_doc.active = 0
            epd_doc.save()

            # Create new doc
            new_epd = frappe.new_doc("Employee Payroll Details")
            new_epd.start_date = doc.from_date
            new_epd.employee = doc.employee
            new_epd.base_pay = doc.base
            new_epd.insert()
    else:
        # No existing record, just create
        new_epd = frappe.new_doc("Employee Payroll Details")
        new_epd.start_date = doc.from_date
        new_epd.employee = doc.employee
        new_epd.base_pay = doc.base
        new_epd.insert()

def update_in_employee(doc,method):
    frappe.db.set_value('Employee',doc.employee,'custom_basic_pay',doc.base)

# def create_arrear_details_log(doc, method):
#     """
#     Create a log entry for arrear details when Salary Slip is submitted.
#     """
#     if doc.custom_effective_from and doc.custom_process_arrear_on:
#         month_val = (doc.custom_process_arrear_on or "").strip()
#         if not month_val:
#             frappe.throw("Please set the month in 'Process Arrear On'.")

#         month_num = _month_to_int(month_val)  # 1..12
#         ref_date = getdate(nowdate())         # today (server date)

#         candidate = date(ref_date.year, month_num, 1)
#         if candidate <= ref_date:
#             candidate = date(ref_date.year + 1, month_num, 1)

#         abl= frappe.get_doc({
#             "doctype": "Arrear Breakup Log",
#             "employee": doc.employee,
#             "from_date": candidate,
#             "current_base": doc.base,
#             "effective_from": doc.custom_effective_from,
#             "payroll_month": doc.custom_process_arrear_on,
#             "payroll_year": getdate(doc.custom_process_arrear_on).year})
#         abl.insert(ignore_permissions=True)

# def _month_to_int(value: str) -> int:
#     """Parse month from 'September' / 'Sep' / '9' into 1..12."""
#     from datetime import datetime
#     s = value.strip()
#     # numeric
#     if s.isdigit():
#         m = int(s)
#         if 1 <= m <= 12:
#             return m
#         frappe.throw(f"Month number out of range: {m}")
#     # text (full / abbr)
#     for fmt in ("%B", "%b"):
#         try:
#             return datetime.strptime(s, fmt).month
#         except ValueError:
#             pass
#     frappe.throw(f"Invalid month name: {value!r}")

import frappe
from frappe.utils import getdate, flt
from datetime import date, datetime

def create_arrear_details_log(doc, method):
    """
    Create Arrear Breakup Log entries for each month between promotion date (effective_from)
    and the month before payroll month (custom_process_arrear_on).
    """
    if not (doc.custom_effective_from and doc.custom_process_arrear_on):
        return

    # Convert promotion date
    effective_from = getdate(doc.custom_effective_from)

    # Convert process arrear month to number
    payroll_month_num = _month_to_int(doc.custom_process_arrear_on)
    payroll_year = effective_from.year
    if payroll_month_num <= effective_from.month:
        # If payroll month is before or same as promotion month, it belongs to next year
        payroll_year += 1

    VALID_MONTHS = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]



    # Loop through months from effective_from to month before payroll month
    arrear_months = []
    month_iter = effective_from.month
    year_iter = effective_from.year

    while True:
        # Stop before the payroll month
        if year_iter == payroll_year and month_iter == payroll_month_num:
            break

        arrear_months.append((year_iter, month_iter))

        month_iter += 1
        if month_iter > 12:
            month_iter = 1
            year_iter += 1

    # Create Arrear Breakup Log for each month
    for y, m in arrear_months:
        month_name = VALID_MONTHS[m - 1]     
        abl = frappe.get_doc({
            "doctype": "Arrear Breakup Log",
            "employee": doc.employee,
            "from_date": getdate(nowdate()),        # Today’s date
            "current_base": doc.base,
            "effective_from": doc.custom_effective_from,  # 1st day of arrear month
            "arrear_month": month_name,
            "payroll_month": doc.custom_process_arrear_on,
            "payroll_year": getdate(doc.custom_process_arrear_on).year
        })
        abl.insert(ignore_permissions=True)


def _month_to_int(value: str) -> int:
    """Parse month from 'September' / 'Sep' / '9' into 1..12."""
    s = value.strip()
    if s.isdigit():
        m = int(s)
        if 1 <= m <= 12:
            return m
        frappe.throw(f"Month number out of range: {m}")
    for fmt in ("%B", "%b"):
        try:
            return datetime.strptime(s, fmt).month
        except ValueError:
            continue
    frappe.throw(f"Invalid month name: {value!r}")
