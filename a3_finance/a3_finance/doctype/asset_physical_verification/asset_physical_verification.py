# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from erpnext.assets.doctype.asset.depreciation import scrap_asset
from erpnext.assets.doctype.asset.asset import create_asset_repair

class AssetPhysicalVerification(Document):
	pass

import frappe

def on_submit(doc, method):
    for row in doc.asset:
        if row.new_status == "Scrapped":
            scrap_asset(row.asset)  # ✅ This triggers ERPNext's built-in scrapping process
            
        # Handle Repaired Assets (set to Out of Order)
        elif row.new_status == "Repaired":
            # Get required asset values
            asset_doc = frappe.get_doc("Asset", row.asset)

            # Call ERPNext core function to create Asset Repair
            repair_doc = create_asset_repair(
                company=asset_doc.company,
                asset=asset_doc.name,
                asset_name=asset_doc.asset_name
            )

            # Set failure date from child table
            repair_doc.failure_date = row.failure_date or frappe.utils.today()

            # Insert (status will auto-change to 'Out of Order')
            repair_doc.insert(ignore_permissions=True)

            frappe.msgprint(
                f"Asset Repair created for Asset {row.asset} (Failure Date: {repair_doc.failure_date})"
            )



@frappe.whitelist()
def get_assets_by_location(location):
    if not location:
        return []

	# Only include assets that are NOT in Draft or Scrapped status
    assets = frappe.get_all(
        "Asset",
        filters={
            "location": location,
            "docstatus": ["!=", 0],               # Exclude Draft (0)
            "status": ["not in", ["Scrapped","Out of Order"]]    # Exclude Scrapped
        },
        fields=["name", "asset_category", "item_name", "custom_last_inspection_date","status"]
    )
    # assets = frappe.get_all("Asset", filters={"location": location}, fields=["name","asset_category","item_name", "custom_last_inspection_date"])
    return assets

