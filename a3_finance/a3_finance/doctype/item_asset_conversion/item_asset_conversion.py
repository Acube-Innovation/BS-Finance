# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ItemAssetConversion(Document):

    def before_save(self):

        if not self.convert_to_fixed_asset:
            return

        if not self.item:
            frappe.throw("Item is required")

        if not self.asset_category:
            frappe.throw("Asset Category is required")

        if not frappe.db.exists("Item", self.item):
            frappe.throw(f"Item {self.item} not found")

        try:
         
        

          
            frappe.db.set_value("Item", self.item, {
                "is_stock_item": 0,
                "is_fixed_asset": 1,
                "asset_category": self.asset_category,
                "auto_create_assets":1
            }, update_modified=False)

            frappe.msgprint(f"✅ Item {self.item} converted to Fixed Asset")

        except Exception as e:
            frappe.throw(str(e))
