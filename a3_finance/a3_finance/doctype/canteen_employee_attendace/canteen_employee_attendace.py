# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
import pandas as pd
from frappe.utils.file_manager import get_file_path
from frappe.model.document import Document


class CanteenEmployeeAttendace(Document):
    def validate(self):
        """
        On Save: Read the uploaded Excel file and fill the child table.
        """
        if not self.upload_file:
            # No file attached; nothing to process
            return

        # Get the file path of the uploaded file
        file_path = get_file_path(self.upload_file)

        # Detect file type (Excel/CSV)
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Normalize column names
        df.columns = [c.strip() for c in df.columns]

        # Required columns
        required_cols = ["Employee", "Present Days"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            frappe.throw(f"Missing required columns in file: {', '.join(missing)}")

        # Clear the existing child table
        self.employee_attendance = []
        self.status = "Processed"
        # Loop through each row and add to child table
        for _, row in df.iterrows():
            self.append("employee_attendance", {
                "employee": str(row["Employee"]).strip(),
                "present_days": float(row["Present Days"]) if row["Present Days"] else 0,
            })
