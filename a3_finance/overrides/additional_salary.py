import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
from collections import defaultdict

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

        settings = frappe.get_single("Payroll Master Settings")
        rate = settings.night_shift_allowance or 0
        doc.amount = doc.custom_night_shift_count * rate

    # ---------------- EL Encashment ----------------
    elif doc.salary_component == "EL Encashment":
        if not doc.custom_el_days:
            frappe.throw(_("Please enter EL Days for EL Encashment"))

        # Get latest submitted salary slip for this employee
        salary_slip = frappe.get_all(
            "Salary Slip",
            filters={
                "employee": doc.employee,
                "docstatus": 1
            },
            order_by="start_date desc",
            limit=1
        )

        if not salary_slip:
            frappe.throw(_("No submitted Salary Slip found for this employee"))

        salary_slip_doc = frappe.get_doc("Salary Slip", salary_slip[0].name)

        base = sw = vda = 0

        for comp in salary_slip_doc.earnings:
            if comp.salary_component == "Basic":
                base = comp.amount
            elif comp.salary_component == "Service Weightage":
                sw = comp.amount
            elif comp.salary_component == "VDA":
                vda = comp.amount

        per_day_rate = (base + sw + vda) / 30
        doc.amount = doc.custom_el_days * per_day_rate


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




def process_overtime_amount(self, method=None):
    if self.salary_component != "Overtime Wages":
        return

    ot_entries = self.get("custom_lop_refund_dates") or []

    if not ot_entries:
        frappe.msgprint("No OT hours entered.")
        return

    # Group OT hours by (year, month)
    month_map = defaultdict(float)
    for row in ot_entries:
        if row.get("refund_date") and row.get("hours"):
            date_obj = datetime.strptime(row.get("refund_date"), "%Y-%m-%d")
            key = (date_obj.year, date_obj.month)
            month_map[key] += float(row.get("hours"))

    total_amount = 0
    total_hours = 0

    for (year, month), hours in month_map.items():
        month_start = f"{year}-{month:02d}-01"

        # Fetch approved salary slip of the month
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
            frappe.msgprint(f"No approved Salary Slip for {month_start}. Skipping OT hours for this month.")
            continue

        # Get salary components for the slip
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
        ot_amount = round(per_hour_rate * hours, 2)

        total_amount += ot_amount
        total_hours += hours

    if total_amount > 0:
        self.amount = total_amount
        frappe.msgprint(f"Calculated Overtime: ₹{total_amount} for {total_hours} hrs.")
    else:
        self.amount = 0
        frappe.msgprint("No valid Overtime amount calculated.")
