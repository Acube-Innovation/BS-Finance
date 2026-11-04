"""Remove all of BATL's assets (782 existing assets, added 27 Feb - 6 Apr 2026) with what was made for them: their
depreciation schedules, asset movements, asset activity, the draft depreciation journal entries and the draft value
adjustment. None of these was posted to the ledger, so no balance changes. Asset categories, locations and the
depreciation settings are kept, so assets added later work as usual."""

import re

import frappe

COMPANY = "BrahMos Aerospace Thiruvananthapuram Limited"


def execute():
    assets = frappe.get_all("Asset", filters={"company": COMPANY}, pluck="name")
    if not assets:
        return

    journal_entries = get_referencing_journal_entries(assets)
    value_adjustments = frappe.get_all(
        "Asset Value Adjustment", filters={"asset": ("in", assets)}, fields=["name", "docstatus"]
    )
    check_not_posted(assets, journal_entries + value_adjustments)

    movements = frappe.get_all(
        "Asset Movement Item", filters={"asset": ("in", assets)}, pluck="parent", distinct=True
    )
    schedules = frappe.get_all("Asset Depreciation Schedule", filters={"asset": ("in", assets)}, pluck="name")

    # cancelled entries are left: their (cancelled) ledger rows still point to them
    delete("Journal Entry", [d.name for d in journal_entries if d.docstatus == 0])
    delete("Asset Value Adjustment", [d.name for d in value_adjustments if d.docstatus == 0])
    delete("Asset Movement", movements)
    delete("Asset Depreciation Schedule", schedules)
    delete("Asset Activity", frappe.get_all("Asset Activity", filters={"asset": ("in", assets)}, pluck="name"))
    delete("Asset", assets)
    reset_series(assets)


def get_referencing_journal_entries(assets):
    names = frappe.get_all(
        "Journal Entry Account",
        filters={"reference_type": "Asset", "reference_name": ("in", assets)},
        pluck="parent",
        distinct=True,
    )
    if not names:
        return []
    return frappe.get_all("Journal Entry", filters={"name": ("in", names)}, fields=["name", "docstatus"])


def check_not_posted(assets, entries):
    """Deleting a posted entry would leave its ledger rows behind: stop, so that it is cancelled first."""
    posted = [d.name for d in entries if d.docstatus == 1]
    posted += frappe.get_all(
        "GL Entry",
        filters={"voucher_type": "Asset", "voucher_no": ("in", assets), "is_cancelled": 0},
        pluck="voucher_no",
        distinct=True,
    )
    if posted:
        frappe.throw(
            "These entries are posted to the ledger. Cancel them, then migrate again to remove the assets: "
            + ", ".join(posted)
        )


def delete(doctype, names):
    """Delete the documents with their child rows, versions, comments, assignments, shares and tags."""
    if not names:
        return
    for df in frappe.get_meta(doctype).get_table_fields():
        frappe.db.delete(df.options, {"parenttype": doctype, "parent": ("in", names)})
    frappe.db.delete(doctype, {"name": ("in", names)})
    frappe.db.delete("Version", {"ref_doctype": doctype, "docname": ("in", names)})
    frappe.db.delete("Comment", {"reference_doctype": doctype, "reference_name": ("in", names)})
    frappe.db.delete("ToDo", {"reference_type": doctype, "reference_name": ("in", names)})
    frappe.db.delete("DocShare", {"share_doctype": doctype, "share_name": ("in", names)})
    frappe.db.delete("Tag Link", {"document_type": doctype, "document_name": ("in", names)})


def reset_series(assets):
    """Number the assets added later from 1 again: reset the counters of the naming series the removed assets used."""
    for prefix in {re.sub(r"\d+$", "", name) for name in assets}:
        if not frappe.db.exists("Asset", {"name": ("like", f"{prefix}%")}):
            frappe.db.sql("update `tabSeries` set `current` = 0 where `name` = %s", prefix)
