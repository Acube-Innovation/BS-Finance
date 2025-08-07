# Copyright (c) 2025, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from contextlib import contextmanager
from erpnext.assets.doctype.asset.depreciation import scrap_asset
from erpnext.assets.doctype.asset.asset import create_asset_repair
from frappe.utils import nowdate
class AssetPhysicalVerification(Document):
	pass

def on_submit(doc, method):
    submission_date = nowdate()
    for row in doc.asset:
        if row.new_status == "Scrapped":
            with suppress_msgprint():
                scrap_asset(row.asset)  
            
        # Handle Repaired Assets 
        elif row.new_status == "Repaired":
            # Get required asset values
            asset_doc = frappe.get_doc("Asset", row.asset)            
            
            # Call ERPNext core function to create Asset Repair
            repair_doc = create_asset_repair(
                company=asset_doc.company,
                asset=asset_doc.name,
                asset_name=asset_doc.asset_name
            )
            
            repair_doc.failure_date = row.failure_date or frappe.utils.today()

            # Insert (status will auto-change to 'Out of Order')
            repair_doc.insert(ignore_permissions=True)       
        
        try:
            asset_doc = frappe.get_doc("Asset", row.asset)
            asset_doc.custom_last_inspection_date = submission_date
            asset_doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to update inspection date for asset {row.asset}: {str(e)}", "Asset Verification Error")
        

@frappe.whitelist()
def get_filtered_assets(shop=None, section=None, floor=None, location=None):
    filters = {
        "docstatus": ["!=", 0],
        "status": ["not in", ["Scrapped","Out of Order","Sold"]]
    }

    if shop:
        filters["custom_shop"] = shop
    if section:
        filters["custom_section"] = section
    if floor:
        filters["custom_floor"] = floor
    if location:
        filters["location"] = location

    # Also update the field list with correct custom fields
    assets = frappe.get_all("Asset",                            
        fields=["name", "asset_name", "asset_category","item_name", "status", "location", "custom_last_inspection_date", "custom_shop", "custom_section", "custom_floor"],
        filters=filters
    )

    return assets

# Context manager to suppress frappe.msgprint
@contextmanager
def suppress_msgprint():
    original_msgprint = frappe.msgprint
    frappe.msgprint = lambda *args, **kwargs: None
    try:
        yield
    finally:
        frappe.msgprint = original_msgprint