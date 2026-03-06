import frappe
import re
from frappe.desk.reportview import get as original_get


@frappe.whitelist()
def get(*args, **kwargs):

    filters = frappe.form_dict.get("filters")

    if filters:
        filters = frappe.parse_json(filters)

        for f in filters:
            if f[0] == "Supplier" and f[1] == "name" and f[2] == "like":

                search = f[3]
                normalized = re.sub(r'[^A-Za-z0-9]', '', search).lower()

                f[3] = f"%{normalized}%"
                f[1] = "custom_search_key"

    frappe.form_dict["filters"] = filters

    return original_get(*args, **kwargs)



def update_search_key(doc, method=None):

    if doc.supplier_name:
        doc.custom_search_key = re.sub(r'[^A-Za-z0-9]', '', doc.supplier_name).lower()