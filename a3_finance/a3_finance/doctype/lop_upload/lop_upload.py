# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt
import frappe
from frappe.utils import nowdate
from frappe.model.document import Document
import pandas as pd
from datetime import timedelta, datetime
from frappe.utils.file_manager import get_file
from frappe.utils import getdate, add_days
from collections import defaultdict
from datetime import timedelta

class LOPUpload(Document):
    # def validate(self):
    #     if self.status == "Processed":
    #         return

    #     file_path = get_file(self.upload_file)[1]
    #     df = pd.read_excel(file_path)

    #     # Clear old child table entries if any
    #     self.set("lop_entries", [])

    #     for idx, row in df.iterrows():
    #         try:
    #             sl_no = int(row["Sl. No."])
    #             ec = str(row["EC"])
    #             name = row["NAME"]
    #             no_of_days = float(row["No. of Days"])
    #             lop_type = row["TYPE"]
    #             tl_hours = row["TL hrs."]
    #             start_date = pd.to_datetime(row["DATE"]).date()
    #         except Exception as e:
    #             frappe.throw(f"Error processing row {idx+1}: {e}")

    #         full_days = int(no_of_days)
    #         has_half_day = (no_of_days - full_days) == 0.5

    #         # Add full day entries
    #         for i in range(full_days):
    #             self.append("lop_entries", {
    #                 "sl_no": sl_no,
    #                 "ec": ec,
    #                 "employee_name": name,
    #                 "total_lop_days": no_of_days,
    #                 "lop_type": lop_type,
    #                 "lop_start_date": start_date,
    #                 "lop_split_date": start_date + timedelta(days=i),
    #                 "is_half_day": 0,
    #                 "tl_hours": tl_hours,
    #             })

    #         # Add half day entry if any
    #         if has_half_day:
    #             self.append("lop_entries", {
    #                 "sl_no": sl_no,
    #                 "ec": ec,
    #                 "employee_name": name,
    #                 "total_lop_days": no_of_days,
    #                 "lop_type": lop_type,
    #                 "lop_start_date": start_date,
    #                 "lop_split_date": start_date + timedelta(days=full_days),
    #                 "is_half_day": 1
    #             })

    #     self.status = "Processed"




    def validate(self):
        if self.status == "Processed":
            return

        file_path = get_file(self.upload_file)[1]
        df = pd.read_excel(file_path)

        # ✅ Fetch holiday list once
        holiday_dates = self.get_all_holidays()

        # Clear old entries
        self.set("lop_entries", [])

        # Dictionary to store LOP summary per employee
        lop_summary = {}

        for idx, row in df.iterrows():
            try:
                sl_no = int(row["Sl. No."])
                ec = str(row["EC"])
                name = row["NAME"]
                tl_hours = row.get("TL hrs.", 0)

                if self.process_type == "Time Loss":
                    self.append("lop_entries", {
                        "sl_no": sl_no,
                        "ec": ec,
                        "employee_name": name,
                        "tl_hours": tl_hours
                    })
                    continue

                no_of_days = float(row["No. of Days"])
                lop_type = row["TYPE"]
                start_date = pd.to_datetime(row["DATE"]).date()

            except Exception as e:
                frappe.throw(f"Error processing row {idx+1}: {e}")

            full_days = int(no_of_days)
            has_half_day = (no_of_days - full_days) == 0.5

            # ✅ Add full day entries, skipping holidays
            current_date = start_date
            added_days = 0
            while added_days < full_days:
                if current_date not in holiday_dates:
                    self.append("lop_entries", {
                        "sl_no": sl_no,
                        "ec": ec,
                        "employee_name": name,
                        "total_lop_days": no_of_days,
                        "lop_type": lop_type,
                        "lop_start_date": start_date,
                        "lop_split_date": current_date,
                        "is_half_day": 0,
                        "tl_hours": tl_hours,
                    })
                    added_days += 1
                current_date += timedelta(days=1)

            # ✅ Add half day entry, skipping holidays
            if has_half_day:
                while current_date in holiday_dates:
                    current_date += timedelta(days=1)
                self.append("lop_entries", {
                    "sl_no": sl_no,
                    "ec": ec,
                    "employee_name": name,
                    "total_lop_days": no_of_days,
                    "lop_type": lop_type,
                    "lop_start_date": start_date,
                    "lop_split_date": current_date,
                    "is_half_day": 1
                })

            # ✅ Collect for Lop Summary
            key = (ec, start_date)
            if key not in lop_summary:
                lop_summary[key] = {
                    "employee_id": ec,
                    "employee_name": name,
                    "start_date": start_date,
                    "no__of_days": 0.0
                }
            lop_summary[key]["no__of_days"] += no_of_days

        # ✅ Insert records into Lop Summary
        for (emp_id, start_date), data in lop_summary.items():
            frappe.get_doc({
                "doctype": "Lop Summary",
                "employee_id": emp_id,
                "employee_name": data["employee_name"],
                "start_date": data["start_date"],
                "no__of_days": round(data["no__of_days"], 2),
                "payroll_month": self.payroll_month,   # Assume this field exists on current DocType
                "payroll_year": self.payroll_year      # Assume this field exists on current DocType
            }).insert(ignore_permissions=True)

        self.status = "Processed"


    def get_all_holidays(self):
        # You can later enhance this to use employee-specific holiday list
        holiday_list_name = frappe.db.get_single_value("Company", "default_holiday_list")
        if not holiday_list_name:
            return set()

        holidays = frappe.get_all("Holiday", filters={"parent": holiday_list_name}, fields=["holiday_date"])
        return {h.holiday_date for h in holidays}






@frappe.whitelist()
def create_leave_applications(docname):
    doc = frappe.get_doc("LOP Upload", docname)
    created = 0

    for row in doc.lop_entries:
        employee = frappe.db.get_value("Employee", {"employee_number": row.ec}, "name")
        if not employee:
            continue

        leave_doc = frappe.get_doc({
            "doctype": "Leave Application",
            "employee": employee,
            "from_date": row.lop_split_date,
            "to_date": row.lop_split_date,
            "leave_type": row.lop_type,  # e.g., Casual Leave / Loss of Pay etc.
            "half_day": 1 if row.is_half_day else 0,
            "half_day_date": row.lop_split_date if row.is_half_day else None,
            "posting_date": nowdate(),
            "status": "Approved",
            "description": f"Auto-created from LOP Import {docname}"
        })
        leave_doc.insert(ignore_permissions=True)
        leave_doc.submit()
        created += 1
        
    return f"{created} Leave Applications Created"


# @frappe.whitelist()
# def create_additional_salary(docname):
#     doc = frappe.get_doc("LOP Upload", docname)

#     if doc.process_type != "Reimbursement":
#         frappe.throw("This action is only allowed for 'Reimbursement' process type.")

#     # Group lop_entries by EC
#     ec_map = defaultdict(list)

#     for entry in doc.lop_entries:
#         if entry.ec and entry.lop_split_date and entry.total_lop_days:
#             ec_map[entry.ec].append(entry)

#     for ec, entries in ec_map.items():
#         employee = frappe.get_value("Employee", {"employee_number": ec}, "name")
#         if not employee:
#             frappe.msgprint(f"Employee not found for EC: {ec}")
#             continue

#         refund_dates = []

#         for entry in entries:
#             total_days = float(entry.total_lop_days)
#             full_days = int(total_days)
#             has_half_day = (total_days - full_days) > 0

#             for i in range(full_days):
#                 refund_dates.append({
#                     "refund_date": add_days(entry.lop_split_date, i),
#                     "is_half_day": 0,
#                     "hours": 0
#                 })

#             if has_half_day:
#                 refund_dates.append({
#                     "refund_date": add_days(entry.lop_split_date, full_days),
#                     "is_half_day": 1,
#                     "hours": 0
#                 })

#         # Create one Additional Salary for this EC
#         additional_salary = frappe.new_doc("Additional Salary")
#         additional_salary.employee = employee
#         additional_salary.salary_component = "LOP Refund"
#         additional_salary.payroll_date = doc.payroll_date
#         additional_salary.amount = 0  # Let formula calculate it

#         additional_salary.set("custom_lop_refund_dates", refund_dates)

#         additional_salary.insert(ignore_permissions=True)
#         additional_salary.submit()
        
#     frappe.db.commit()




@frappe.whitelist()
def create_additional_salary(docname):
    doc = frappe.get_doc("LOP Upload", docname)

    if doc.process_type not in ["Reimbursement", "Time Loss"]:
        frappe.throw("This action is only allowed for 'Reimbursement' or 'Time Loss' process types.")

    # Group lop_entries by EC
    ec_map = defaultdict(list)
    for entry in doc.lop_entries:
        if entry.ec:
            ec_map[entry.ec].append(entry)

    for ec, entries in ec_map.items():
        employee = frappe.get_value("Employee", {"employee_number": ec}, "name")
        if not employee:
            frappe.msgprint(f"Employee not found for EC: {ec}")
            continue

        # For Reimbursement: date-wise breakdown (days/half-days)
        if doc.process_type == "Reimbursement":
            refund_dates = []

            for entry in entries:
                if not entry.lop_split_date or not entry.total_lop_days:
                    continue

                total_days = float(entry.total_lop_days)
                full_days = int(total_days)
                has_half_day = (total_days - full_days) > 0

                for i in range(full_days):
                    refund_dates.append({
                        "refund_date": add_days(entry.lop_split_date, i),
                        "is_half_day": 0,
                        "hours": 0
                    })

                if has_half_day:
                    refund_dates.append({
                        "refund_date": add_days(entry.lop_split_date, full_days),
                        "is_half_day": 1,
                        "hours": 0
                    })

            additional_salary = frappe.new_doc("Additional Salary")
            additional_salary.employee = employee
            additional_salary.salary_component = "LOP Refund"
            additional_salary.payroll_date = doc.payroll_date
            additional_salary.amount = 0
            additional_salary.set("custom_lop_refund_dates", refund_dates)
            additional_salary.insert(ignore_permissions=True)
            additional_salary.submit()

        # For Time Loss: only log TL hours in custom_lop_refund_dates (no dates)
        elif doc.process_type == "Time Loss":
            refund_hours_entries = []

            refund_month_date = doc.get("refund_hours_month")
            if not refund_month_date:
                frappe.throw("Please set 'Refund Hours Month' in LOP Upload before creating Additional Salary.")

            for entry in entries:
                try:
                    hours = float(entry.tl_hours or 0)
                except:
                    hours = 0

                if hours > 0:
                    refund_hours_entries.append({
                        "is_half_day": 0,
                        "hours": hours,
                        "refund_date": refund_month_date  # optional
                    })

            if not refund_hours_entries:
                continue

            additional_salary = frappe.new_doc("Additional Salary")
            additional_salary.employee = employee
            additional_salary.salary_component = "LOP (In Hours) Refund"
            additional_salary.payroll_date = doc.payroll_date
            additional_salary.amount = 0
            additional_salary.set("custom_lop_refund_dates", refund_hours_entries)
            additional_salary.insert(ignore_permissions=True)
            additional_salary.submit()

    frappe.db.commit()
    frappe.msgprint("Additional Salary records created and submitted successfully.")
