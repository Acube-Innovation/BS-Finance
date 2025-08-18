import frappe
from datetime import date,timedelta
from frappe.utils import getdate, nowdate

def create_sal_str_assignment(doc, method=None):
    # Only proceed if basic pay actually changes
    if frappe.utils.flt(doc.custom_existing_basic_pay) == frappe.utils.flt(doc.custom_new_basic_pay):
        return

    # ---- latest active SSA for employee ----
    rows = frappe.get_all(
        "Salary Structure Assignment",
        filters={"employee": doc.employee, "docstatus": 1},
        fields=["name", "salary_structure", "income_tax_slab"],
        order_by="from_date desc",
        limit=1,
    )
    if not rows:
        frappe.throw("No Salary Structure Assignment found for this employee.")

    current_ssa = frappe.get_doc("Salary Structure Assignment", rows[0]["name"])

    # ---- compute from_date = 1st of the upcoming requested month ----
    # doc.custom_process_arrear_on may be "September", "Sep", or "9"
    month_val = (doc.custom_process_arrear_on or "").strip()
    if not month_val:
        frappe.throw("Please set the month in 'Process Arrear On'.")

    month_num = _month_to_int(month_val)  # 1..12
    ref_date = getdate(nowdate())         # today (server date)

    candidate = date(ref_date.year, month_num, 2)
    if candidate <= ref_date:
        candidate = date(ref_date.year + 1, month_num, 2)

    # ---- create new SSA with updated base pay ----
    ssa = frappe.new_doc("Salary Structure Assignment")
    ssa.employee = doc.employee
    ssa.salary_structure = current_ssa.salary_structure
    ssa.income_tax_slab = getattr(current_ssa, "income_tax_slab", None)
    ssa.custom_effective_from = doc.promotion_date
    ssa.custom_process_arrear_on = doc.custom_process_arrear_on
    ssa.base = doc.custom_new_basic_pay
    ssa.from_date = getdate(doc.promotion_date) + timedelta(days=1)
    ssa.insert(ignore_permissions=True)
    ssa.submit()

    # Optionally mark old SSA as inactive (custom field)
    if hasattr(current_ssa, "custom_inactive"):
        current_ssa.custom_inactive = 1
        current_ssa.save()


# ---- helpers ----

def _month_to_int(value: str) -> int:
    """Parse month from 'September' / 'Sep' / '9' into 1..12."""
    from datetime import datetime
    s = value.strip()
    # numeric
    if s.isdigit():
        m = int(s)
        if 1 <= m <= 12:
            return m
        frappe.throw(f"Month number out of range: {m}")
    # text (full / abbr)
    for fmt in ("%B", "%b"):
        try:
            return datetime.strptime(s, fmt).month
        except ValueError:
            pass
    frappe.throw(f"Invalid month name: {value!r}")
