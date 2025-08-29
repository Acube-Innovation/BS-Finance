// Copyright (c) 2025, Acube and contributors
// For license information, please see license.txt

frappe.query_reports["Component Wise Totals"] = {
	
 "filters": [
  {
   "fieldname": "from_date",
   "label": "From Date",
   "fieldtype": "Date",
   "reqd": 1
  },
  {
   "fieldname": "to_date",
   "label": "To Date",
   "fieldtype": "Date",
   "reqd": 1
  },
  {
   "fieldname": "salary_component",
   "label": "Salary Component",
   "fieldtype": "Link",
   "options": "Salary Component",
   "reqd": 1
  }
 ]

};
