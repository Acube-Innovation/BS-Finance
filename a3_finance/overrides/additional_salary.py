import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
from collections import defaultdict
import calendar
from frappe.utils import getdate
from frappe.utils import flt, getdate
@frappe.whitelist()
def calculate_lop_refund(self, method=None):
    if self.salary_component != "LOP Refund":
        return
    refund_dates = self.get("custom_lop_refund_dates") or []

    if not refund_dates:
        frappe.msgprint("No LOP Refund Dates selected.")
        return

    # Group refund dates by (year, month)
    month_map = defaultdict(list)
    for row in refund_dates:
        if row.get("refund_date"):
            date_obj = row.get("refund_date")
            key = (date_obj.year, date_obj.month)
            month_map[key].append((date_obj, row.get("is_half_day")))

    total_refund_amount = 0

    for (year, month), dates in month_map.items():
        # Try to get salary slip for this month
        month_start = f"{year}-{month:02d}-01"
        salary_slip = frappe.db.get_value(
            "Salary Slip",
            {
                "employee": self.employee,
                "start_date": ["<=", month_start],
                "end_date": [">=", month_start],
                "docstatus": 1
            },
            ["name"]
        )

        if not salary_slip:
            frappe.msgprint(f"No approved Salary Slip found for {month_start}.")
            continue

        components = frappe.get_all(
            "Salary Detail",
            filters={"parent": salary_slip, "parenttype": "Salary Slip"},
            fields=["salary_component", "amount"]
        )

        # Extract BP, SW, HRA, VDA
        bp = sw = hra = vda = 0
        print("Starting component calculations...")

        for comp in components:
            comp_type = comp.salary_component.lower()
            print(f"Checking component: {comp.salary_component} with amount: {comp.amount}")

            if "basic" in comp_type:
                bp += comp.amount
                print(f"Added to BP: {comp.amount}, Total BP: {bp}")
            elif "service weightage" in comp_type or "sw" in comp_type:
                sw += comp.amount
                print(f"Added to SW: {comp.amount}, Total SW: {sw}")
            elif "House Rent Allowance" in comp_type:
                hra += comp.amount
                print(f"Added to HRA: {comp.amount}, Total HRA: {hra}")
            elif "Variable DA" in comp_type:
                vda += comp.amount
                print(f"Added to VDA: {comp.amount}, Total VDA: {vda}")

        total = bp + sw + hra + vda
        print(f"Total amount (BP + SW + HRA + VDA): {total}")

        daily_rate = total / 30
        print(f"Daily rate (Total / 30): {daily_rate}")

        refund_days = sum(0.5 if is_half else 1 for _, is_half in dates)
        refund_amount = daily_rate * refund_days

        print(f"Refund amount (Daily rate * refund days): {refund_amount}")

        total_refund_amount += refund_amount
        print(f"Total refund amount so far: {total_refund_amount}")

        # Set the calculated amount
        self.amount = round(total_refund_amount, 2)
        print(f"Final rounded refund amount set to: {self.amount}")


def custom_validate(doc, method):
    # ---------------- Night Shift Allowance ----------------
    if doc.salary_component == "Night Shift Allowance":
        if not doc.custom_night_shift_count:
            frappe.throw(_("Please enter Night Shift Count for Night Shift Allowance"))

        # Use latest salary slip to derive applicable Payroll Master Setting
        latest_slip = frappe.get_all(
            "Salary Slip",
            filters={"employee": doc.employee, "docstatus": 1},
            order_by="start_date desc",
            limit=1
        )

        if not latest_slip:
            frappe.throw(_("No submitted Salary Slip found for this employee"))

        slip_doc = frappe.get_doc("Salary Slip", latest_slip[0].name)
        start = getdate(slip_doc.start_date)
        setting = get_previous_payroll_master_setting(start.year, start.month)

        if not setting:
            frappe.throw(_("No applicable Payroll Master Setting found."))

        rate = setting.night_shift_allowance or 0
        doc.amount = doc.custom_night_shift_count * rate

    # ---------------- EL Encashment ----------------
    elif doc.salary_component == "EL Encashment":
        if not doc.custom_el_days:
            frappe.throw(_("Please enter EL Days for EL Encashment"))

        # Get Basic Pay from Salary Structure Assignment
        basic = flt(frappe.db.get_value("Salary Structure Assignment", {"employee": doc.employee}, "base")) or 0
        if not basic:
            frappe.throw(_("Basic pay not found in Salary Structure Assignment."))

        # Get Service Weightage from Employee
        sw = flt(frappe.db.get_value("Employee", doc.employee, "custom_service_weightage_emp")) or 0

        # Get current Payroll Master Setting
        today = getdate(doc.payroll_date)
        month = today.strftime("%B")
        year = str(today.year)
        setting_name = frappe.get_value("Payroll Master Setting", {
            "payroll_month": month,
            "payroll_year": year
        }, "name")

        if not setting_name:
            frappe.throw(_("Payroll Master Setting not found for this month."))

        setting = frappe.get_doc("Payroll Master Setting", setting_name)
        vda_percentage = flt(setting.get("dearness_allowance_", 0))

        # Compute DA (Dearness Allowance)
        da = round((basic + sw) * vda_percentage)

        # Compute per day and final amount
        payroll_days = setting.get("payroll_days") or 30
        per_day = (basic + sw + da) * doc.custom_el_days
        doc.amount = round(per_day / payroll_days, 2)

        # Debug log
        print(f"[DEBUG] Basic: {basic}, SW: {sw}, VDA%: {vda_percentage}, DA: {da}, Per Day: {per_day}, EL Days: {doc.custom_el_days}, Amount: {doc.amount}")


def get_previous_payroll_master_setting(year, month_number):
    years_to_consider = [year, year - 1]

    settings = frappe.get_all(
        "Payroll Master Setting",
        filters={"payroll_year": ["in", years_to_consider]},
        fields=["name", "payroll_year", "payroll_month_number", "payroll_days", "night_shift_allowance"],
        order_by="payroll_year desc, payroll_month_number desc",
        limit=20
    )

    for record in settings:
        ry, rm = int(record["payroll_year"]), int(record["payroll_month_number"])
        if ry < year or (ry == year and rm <= month_number):
            return frappe.get_doc("Payroll Master Setting", record["name"])

    return None


@frappe.whitelist()
def process_lop_hour_refund(self, method=None):
    if self.salary_component != "LOP (In Hours) Refund":
        return

    refund_entries = self.get("custom_lop_refund_dates") or []

    if not refund_entries:
        frappe.msgprint("No LOP Refund Hours selected.")
        return

    # Group refund hours by month
    month_map = defaultdict(float)
    for row in refund_entries:
        if row.get("refund_date") and row.get("hours"):
            date_obj = row.get("refund_date")
            key = (date_obj.year, date_obj.month)
            month_map[key] += float(row.get("hours"))

    total_amount = 0
    total_hours = 0

    for (year, month), hours in month_map.items():
        month_start = f"{year}-{month:02d}-01"

        salary_slip = frappe.db.get_value(
            "Salary Slip",
            {
                "employee": self.employee,
                "start_date": ["<=", month_start],
                "end_date": [">=", month_start],
                "docstatus": 1
            },
            "name"
        )

        if not salary_slip:
            frappe.msgprint(f"No approved Salary Slip found for {month_start}. Skipping.")
            continue

        components = frappe.get_all(
            "Salary Detail",
            filters={"parent": salary_slip, "parenttype": "Salary Slip"},
            fields=["salary_component", "amount"]
        )

        bp = sw = vda = 0
        for comp in components:
            comp_type = comp.salary_component.lower()
            if "basic" in comp_type:
                bp += comp.amount
            elif "service weightage" in comp_type or "sw" in comp_type:
                sw += comp.amount
            elif "variable da" in comp_type or "vda" in comp_type:
                vda += comp.amount

        base_total = bp + sw + vda
        per_hour_rate = base_total / 240
        refund_amount = round(per_hour_rate * hours, 2)

        total_amount += refund_amount
        total_hours += hours

    if total_amount > 0:
        self.amount = total_amount  # Set the amount in the current Additional Salary doc
        # frappe.msgprint(f"Calculated refund: ₹{total_amount} for {total_hours} hrs.")
    else:
        self.amount = 0
        frappe.msgprint("No valid refund amount calculated.")




from collections import defaultdict
from datetime import datetime
import frappe


def process_overtime_amount(self, method=None):
    if self.salary_component != "Overtime Wages":
        return

    ot_entries = self.get("custom_lop_refund_dates") or []
    total_hours = 0
    for row in ot_entries:
        if row.get("hours"):
            total_hours += float(row.get("hours"))

    if total_hours == 0:
        frappe.msgprint("No OT hours entered.")
        self.amount = 0
        return

    if not self.payroll_date:
        frappe.msgprint("Please select 'Payroll Date' to calculate Overtime Wages.")
        self.amount = 0
        return

    reference_date = self.payroll_date
    if isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

    # --- Get Active Salary Structure Assignment ---
    assignment = frappe.db.get_value(
        "Salary Structure Assignment",
        {
            "employee": self.employee,
            "from_date": ["<=", reference_date],
            "docstatus": 1
        },
        "salary_structure",
        order_by="from_date desc"
    )

    if not assignment:
        frappe.msgprint("No active Salary Structure Assignment found.")
        self.amount = 0
        return

    # --- Get Salary Structure Components ---
    components = frappe.get_all(
        "Salary Detail",
        filters={"parent": assignment, "parenttype": "Salary Structure"},
        fields=["salary_component", "amount"]
    )

    bp = sw = vda = 0
    for comp in components:
        comp_type = comp.salary_component.lower()
        if "basic" in comp_type:
            bp += comp.amount
        elif "service weightage" in comp_type or "sw" in comp_type:
            sw += comp.amount
        elif "variable da" in comp_type or "vda" in comp_type:
            vda += comp.amount

    base_total = bp + sw + vda

    if base_total == 0:
        frappe.msgprint("Basic + SW + VDA total is zero. Cannot calculate Overtime.")
        self.amount = 0
        return

    # --- Calculate Overtime Wages ---
    per_hour_rate = base_total / 240
    ot_amount = round(per_hour_rate * total_hours, 2)

    self.amount = ot_amount
    frappe.msgprint(f"Calculated Overtime: ₹{ot_amount} for {total_hours} hrs based on Salary Structure in {reference_date.strftime('%B %Y')}.")
