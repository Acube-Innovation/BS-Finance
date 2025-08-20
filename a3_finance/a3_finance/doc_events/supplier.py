import frappe
from frappe.utils import nowdate, getdate

def before_insert(doc, method):
    today = getdate(nowdate())
    if today < getdate(doc.custom_effective_from):
        doc.disabled = 1

def change_supplier_status():
    today = getdate(nowdate())
    supplier_list = frappe.db.get_all("Supplier",["name","custom_effective_from"])
    for supplier in supplier_list:
        if today >= getdate(supplier.custom_effective_from):
            frappe.db.set_value("Supplier",supplier.name,"disabled",0)