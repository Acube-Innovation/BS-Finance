import frappe

@frappe.whitelist()
def get_asset_category_children(parent=None):
    """Fetch children for Asset Category tree view."""
    if not parent or parent == "Asset Categories":
        filters = {"custom_parent_asset_category": ["=", None]}
    else:
        filters = {"custom_parent_asset_category": parent}

    categories = frappe.get_all(
        "Asset Category",
        filters=filters,
        fields=[
            "name as value",
            "asset_category_name as title",
            "custom_is_group",
            "custom_parent_asset_category"
        ],
        order_by="asset_category_name asc"
    )

    for cat in categories:
        cat["expandable"] = 1 if cat.get("custom_is_group") else 0

    return categories