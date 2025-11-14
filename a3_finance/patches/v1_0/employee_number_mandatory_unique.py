import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter  # type: ignore

def execute():
    # 1) Unhide employee_number
    make_property_setter(
        "Employee",          # doctype
        "employee_number",   # fieldname
        "hidden",            # property
        0,                   # value
        "Check"              # property type
    )

    # 2) Make employee_number mandatory
    make_property_setter(
        "Employee",
        "employee_number",
        "reqd",
        1,
        "Check"
    )

    # 3) Ensure no duplicates before making it unique (safety check)
    duplicates = frappe.db.sql("""
        SELECT employee_number, COUNT(*) AS cnt
        FROM `tabEmployee`
        WHERE employee_number IS NOT NULL
          AND employee_number != ''
        GROUP BY employee_number
        HAVING cnt > 1
    """)

    if duplicates:
        # This will stop the patch with a clear message
        msg = ", ".join(d[0] for d in duplicates if d[0])
        frappe.throw(f"Cannot set Employee.employee_number as unique because duplicates exist: {msg}")

    # 4) Make employee_number unique
    make_property_setter(
        "Employee",
        "employee_number",
        "unique",
        1,
        "Check"
    )

    # 5) Reload Employee so new properties + index are applied
    frappe.reload_doctype("Employee")
