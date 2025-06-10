import frappe
from frappe.utils import getdate

def update_account_status():
    today = getdate()
    validity_records = frappe.get_all(
        "Account Validity",
        fields=["account", "start_date", "end_date"]
    )

    for record in validity_records:
        if not record.account:
            continue

        try:
            account = frappe.get_doc("Account", record.account)

            if record.start_date and record.end_date:
                if record.start_date <= today <= record.end_date:
                    if account.disabled:
                        account.disabled = 0
                        account.save(ignore_permissions=True)
                else:
                    if not account.disabled:
                        account.disabled = 1
                        account.save(ignore_permissions=True)

        except frappe.DoesNotExistError:
            frappe.logger().warning(f"Account {record.account} not found.")
