# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt

"""Employee Pension Scheme: the EPF / EPS scheme of an employee (Employee > Employee Pension Scheme).

The name is free and can be renamed; the Calculation says how the PF Detailed Log works out EPS and ER (see
pf_detailed_log.py). Schemes on the wage ceiling use the Statutory Wage Ceiling of the Payroll Master Setting.
"""

from frappe.model.document import Document

# Calculation options (the value stored on the scheme); the PF Detailed Log works by these, not by the name
EPS_9_49 = "EPS 9.49% / ER 2.51% of EPF Wages"
ER_12 = "EPS 0 / ER 12% of EPF Wages"
CEILING_EPS_ER = "EPS 8.33% / ER 3.67% on Wages up to the Wage Ceiling"
CEILING_ER_ONLY = "EPS 0 / ER 12% on Wages up to the Wage Ceiling"
CEILING_EPS_FULL_ER = "EPS 8.33% on Wages up to the Wage Ceiling / ER 12% of EPF Wages less EPS"
EPS_HIGHER_WAGES = "EPS 8.33% (+1.16% above the Wage Ceiling) / ER 12% less EPS"


class EmployeePensionScheme(Document):
	pass
