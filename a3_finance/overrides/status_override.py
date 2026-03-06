import math
import frappe
from frappe.utils import flt
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt


class CustomPurchaseReceipt(PurchaseReceipt):

    def check_overflow_with_allowance(self, item, args):
        """Custom tolerance validation for Purchase Receipt"""

        # Validate only quantity overflow
        if "qty" not in args.get("target_ref_field", ""):
            return

        ref_qty = flt(item.get(args["target_ref_field"]))
        received_qty = flt(item.get(args["target_field"]))

        if not ref_qty:
            return

        # 🔹 Get Purchase Order reference
        po_name = item.get("parent")
        po_idx = item.get("idx")
        po_tolerance = None

        # 🔹 Fetch tolerance from PO Item table
        if item.get("parenttype") == "Purchase Order" and po_name and po_idx:
            po_tolerance = frappe.db.get_value(
                "Purchase Order Item",
                {"parent": po_name, "idx": po_idx},
                "custom_tolerance"
            )

        # 🔹 Purchase Receipt level tolerance
        pr_tolerance = getattr(self, "custom_tolerance", None)
        print(pr_tolerance)

        po_tolerance = flt(po_tolerance) if po_tolerance not in (None, "") else None
        pr_tolerance = flt(pr_tolerance) if pr_tolerance not in (None, "") else None

        if  po_tolerance:
            tolerance = po_tolerance
        elif pr_tolerance :
            tolerance = pr_tolerance
        else:
            tolerance = 0

        # 🔹 Calculate max allowed quantity
        max_allowed_qty = ref_qty * (1 + tolerance / 100)

        # 🔹 Validation
        if received_qty > max_allowed_qty:
            excess = received_qty - max_allowed_qty

            frappe.throw(
                f"""
                        Over Receipt Not Allowed for Item <b>{item.item_code}</b><br><br>
                        Purchase Order: <b>{po_name or "N/A"}</b><br>
                        Ordered Qty: <b>{int(ref_qty)}</b><br>
                        Received Qty: <b>{int(received_qty)}</b><br>
                        Allowed Tolerance: <b>{int(tolerance)}%</b><br>
                        Maximum Allowed Qty: <b>{int(max_allowed_qty)}</b><br>
                        Excess Qty: <b>{int(math.ceil(excess))}</b>
                """,
                title="Tolerance Exceeded",
            )
