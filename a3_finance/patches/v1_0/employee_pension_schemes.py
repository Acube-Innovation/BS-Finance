"""Employee Pension Scheme is now a list (Employee Pension Scheme doctype) instead of fixed Select options, so the
finance team can name and rename the schemes. Create the schemes under their existing names, each with the
calculation it had, so employees and PF Detailed Logs keep their values."""

import frappe

from a3_finance.a3_finance.doctype.employee_pension_scheme.employee_pension_scheme import (
    CEILING_EPS_ER,
    CEILING_EPS_FULL_ER,
    CEILING_ER_ONLY,
    EPS_9_49,
    EPS_HIGHER_WAGES,
    ER_12,
)

SCHEMES = {
    "EPS-9.49  ER-2.51": EPS_9_49,
    "EPS-0  ER-12": ER_12,
    "EPS-1250  ER-550": CEILING_EPS_ER,
    "EPS-0  ER-1800": CEILING_ER_ONLY,
    "EPS-1250  ER-12%-1250": CEILING_EPS_FULL_ER,
    "EPS-8.33  ER-3.67": EPS_HIGHER_WAGES,
}


def execute():
    frappe.reload_doc("a3_finance", "doctype", "employee_pension_scheme")
    for name, calculation in SCHEMES.items():
        if frappe.db.exists("Employee Pension Scheme", name):
            continue
        frappe.get_doc(
            {"doctype": "Employee Pension Scheme", "scheme_name": name, "calculation": calculation}
        ).insert(ignore_permissions=True)
