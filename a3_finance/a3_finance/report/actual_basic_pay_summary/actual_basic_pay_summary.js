// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Actual Basic Pay Summary"] = {
	
  "filters": [
    {
      "fieldname": "employee",
      "label": "Employee",
      "fieldtype": "Link",
      "options": "Employee"
    },
    {
      "fieldname": "employment_type",
      "label": "Employment Type",
      "fieldtype": "Link",
      "options": "Employment Type"
    },
    {
      "fieldname": "department",
      "label": "Department",
      "fieldtype": "Link",
      "options": "Department"
    },
    {
      "fieldname": "company",
      "label": "Company",
      "fieldtype": "Link",
      "options": "Company"
    }
  ]


};
