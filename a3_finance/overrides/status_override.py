import math
import frappe
from frappe.utils import flt
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt


def get_po_tolerance(po_item, po):
    """Current tolerance % of a PO row: the item's own value if set, else the PO header's.

    Read from the PO every time, since tolerance can be revised on a submitted PO.
    """
    tolerance = flt(frappe.db.get_value("Purchase Order Item", po_item, "custom_tolerance")) if po_item else 0
    if not tolerance and po:
        tolerance = flt(frappe.db.get_value("Purchase Order", po, "custom_tolerance"))
    return tolerance


class CustomPurchaseReceipt(PurchaseReceipt):

    def validate(self):
        super().validate()
        self.set_tolerance_from_purchase_order()

    def set_tolerance_from_purchase_order(self):
        """Refresh the displayed tolerance from the PO, in case it was revised after this PR was made."""
        first_po = None
        for row in self.get("items"):
            if row.get("purchase_order"):
                row.custom_tolerance = get_po_tolerance(row.get("purchase_order_item"), row.purchase_order)
                first_po = first_po or row.purchase_order
        if first_po:
            self.custom_tolerance = flt(frappe.db.get_value("Purchase Order", first_po, "custom_tolerance"))

    def check_overflow_with_allowance(self, item, args):
        """Custom tolerance validation for Purchase Receipt"""

        # Validate only quantity overflow
        if "qty" not in args.get("target_ref_field", ""):
            return

        ref_qty = flt(item.get(args["target_ref_field"]))
        received_qty = flt(item.get(args["target_field"]))

        if not ref_qty:
            return

        po_name = item.get("parent")

        # item["idx"] is the idx of the Purchase Receipt row being checked (not of the PO row);
        # use that row's PO so Material Request / Purchase Invoice checks get the same tolerance
        pr_row = next((d for d in self.get("items") if d.idx == item.get("idx")), None)
        tolerance = (
            get_po_tolerance(pr_row.get("purchase_order_item"), pr_row.get("purchase_order"))
            if pr_row
            else 0
        )

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
