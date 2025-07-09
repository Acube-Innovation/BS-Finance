import frappe

def validate_duplicate(doc, method):
    # Get list of all active Income Tax Slabs (excluding current doc if it's already saved)
    active_slabs = frappe.get_all(
        "Income Tax Slab",
        filters={"disabled": 0,"docstatus":1},
        fields=["name"]
    )

    print(f"[DEBUG] Active Income Tax Slabs: {[row.name for row in active_slabs]}")

    # Allow only 1 active (this one OR already existing one)
    if doc.disabled == 0:
        if len(active_slabs) > 1 or (len(active_slabs) == 1 and active_slabs[0].name != doc.name):
            frappe.throw("Only one Income Tax Slab can be active at a time. Please disable the others.")
