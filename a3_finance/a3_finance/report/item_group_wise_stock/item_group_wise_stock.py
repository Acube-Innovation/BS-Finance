# Copyright (c) 2026, Acube and contributors
# For license information, please see license.txt

"""Item Group Wise Stock: opening, inward, outward and closing stock for a period, as a tree.

Store -> its Item Groups -> items -> the item's stock transactions in the period.
	Store   the stores ticked "Show in Stock Summary" on the Warehouse - Capital Store, Consumable Store, Finished
	        Goods Store, SCD Store - as in the Stock Summary report: a store's warehouses taken together ("Finished
	        Goods Store-Restricted" and "Finished Goods Store-Un-restricted" are "Finished Goods Store"). Every
	        warehouse while none is ticked; a Warehouse filter shows that warehouse (and those under it).
	Item    Opening (before the From Date), In and Out in the period, Balance as on the To Date: quantity in the
	        stock unit and stock ledger value.
	Transaction  one row per document that moved the item in or out of the store in the period, newest last, with
	        the balance after it, between an "Opening" and a "Closing" row; moves between the warehouses of one store cancel out and are not shown (a rounding
	        difference in their value still counts in the totals and balances).
	Item Group  the sum of its items; quantities only when all its items have the same unit.
	Store / Grand Total  values only.
"""

import re

import frappe
from frappe import _
from frappe.utils import flt, formatdate, getdate

SHOW_FIELD = "custom_show_in_stock_summary"
RESTRICTED = re.compile(r"[\s\-]*(un[\s\-]*restricted|restricted)$", re.IGNORECASE)
QTY_FIELDS = ("opening_qty", "in_qty", "out_qty", "balance_qty")
VALUE_FIELDS = ("opening_value", "in_value", "out_value", "balance_value")


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	columns = [{"label": _("Particulars"), "fieldname": "particulars", "fieldtype": "Data", "width": 430}]
	for label, fieldname in (
		("Opening Qty", "opening_qty"),
		("Opening Value", "opening_value"),
		("In Qty", "in_qty"),
		("In Value", "in_value"),
		("Out Qty", "out_qty"),
		("Out Value", "out_value"),
		("Balance Qty", "balance_qty"),
		("Balance Value", "balance_value"),
	):
		columns.append(
			{
				"label": _(label),
				"fieldname": fieldname,
				"fieldtype": "Float" if fieldname.endswith("_qty") else "Currency",
				"width": 130 if fieldname.endswith("_qty") else 140,
			}
		)
	return columns


def get_data(filters):
	from_date = getdate(filters.from_date)
	to_date = getdate(filters.to_date)
	warehouses = get_warehouses(filters)
	if not warehouses:
		return []
	store_of = get_store_names(warehouses)
	conditions, values = item_conditions(filters)
	values.update(warehouses=tuple(warehouses), from_date=from_date, to_date=to_date)

	# opening and closing balance of each item in each warehouse
	items_in_store = {}
	for row in frappe.db.sql(
		f"""
		select sle.item_code, sle.warehouse,
			sum(if(sle.posting_date < %(from_date)s, sle.actual_qty, 0)) as opening_qty,
			sum(if(sle.posting_date < %(from_date)s, sle.stock_value_difference, 0)) as opening_value,
			sum(sle.actual_qty) as balance_qty, sum(sle.stock_value_difference) as balance_value
		from `tabStock Ledger Entry` sle
		where sle.is_cancelled = 0 and sle.posting_date <= %(to_date)s and sle.warehouse in %(warehouses)s
			{conditions}
		group by sle.item_code, sle.warehouse
		""",
		values,
		as_dict=True,
	):
		entry = items_in_store.setdefault(
			(store_of[row.warehouse], row.item_code), frappe._dict({f: 0.0 for f in QTY_FIELDS + VALUE_FIELDS})
		)
		for field in ("opening_qty", "opening_value", "balance_qty", "balance_value"):
			entry[field] += flt(row[field])

	# the period's movements, one per document (a document's rows in the store's warehouses added together)
	moves = {}
	for row in frappe.db.sql(
		f"""
		select sle.item_code, sle.warehouse, sle.voucher_type, sle.voucher_no, sle.posting_date,
			min(timestamp(sle.posting_date, sle.posting_time)) as posted, min(sle.creation) as created,
			sum(sle.actual_qty) as qty, sum(sle.stock_value_difference) as value
		from `tabStock Ledger Entry` sle
		where sle.is_cancelled = 0 and sle.posting_date between %(from_date)s and %(to_date)s
			and sle.warehouse in %(warehouses)s {conditions}
		group by sle.item_code, sle.warehouse, sle.voucher_type, sle.voucher_no, sle.posting_date
		""",
		values,
		as_dict=True,
	):
		key = (store_of[row.warehouse], row.item_code, row.voucher_type, row.voucher_no)
		move = moves.setdefault(
			key,
			frappe._dict(
				voucher_type=row.voucher_type,
				voucher_no=row.voucher_no,
				posting_date=row.posting_date,
				posted=row.posted,
				created=row.created,
				qty=0.0,
				value=0.0,
				has_in=False,
				has_out=False,
			),
		)
		move.qty += flt(row.qty)
		move.value += flt(row.value)
		move.has_in = move.has_in or flt(row.qty) > 0
		move.has_out = move.has_out or flt(row.qty) < 0
		move.posted = min(move.posted, row.posted)

	item_moves = {}
	for (store, item_code, _vt, _vn), move in moves.items():
		if not round(move.qty, 6) and abs(move.value) < 0.005:
			continue  # nothing moved in or out of the store
		# moved between the warehouses of one store: not listed, but a rounding difference in its value still
		# counts, so that the totals and the running balance agree with the stock ledger
		move.hidden = not round(move.qty, 6) and move.has_in and move.has_out
		item_moves.setdefault((store, item_code), []).append(move)
		entry = items_in_store.setdefault(
			(store, item_code), frappe._dict({f: 0.0 for f in QTY_FIELDS + VALUE_FIELDS})
		)
		inward = move.qty > 0 or (not round(move.qty, 6) and move.value > 0)
		if inward:
			entry.in_qty += move.qty
			entry.in_value += move.value
		else:
			entry.out_qty += -move.qty
			entry.out_value += -move.value

	items_in_store = {
		key: e
		for key, e in items_in_store.items()
		if round(e.opening_qty, 6) or round(e.balance_qty, 6) or item_moves.get(key)
	}
	if not items_in_store:
		return []

	items = {
		i.name: i
		for i in frappe.get_all(
			"Item",
			filters={"name": ["in", list({item for _store, item in items_in_store})]},
			fields=["name", "item_name", "item_group", "stock_uom"],
		)
	}
	labels = get_voucher_labels([m for rows in item_moves.values() for m in rows])

	tree = {}
	for (store, item_code), entry in items_in_store.items():
		item = items.get(item_code) or frappe._dict(name=item_code, item_name=item_code, item_group="", stock_uom="")
		tree.setdefault(store, {}).setdefault(item.item_group or "", []).append((item, entry))

	data = []
	grand = {f: 0.0 for f in VALUE_FIELDS}
	for store in sorted(tree, key=lambda name: name.lower()):
		groups = tree[store]
		store_row = total_row(0, store, [row for rows in groups.values() for row in rows], with_qty=False)
		data.append(store_row)
		for field in VALUE_FIELDS:
			grand[field] += store_row[field]
		for group in sorted(groups, key=lambda name: name.lower()):
			rows = sorted(groups[group], key=lambda r: (r[0].item_name or r[0].name).lower())
			data.append(total_row(1, group or _("(No Item Group)"), rows))
			for item, entry in rows:
				data.append(
					{
						"indent": 2,
						"particulars": item.item_name or item.name,
						"item_code": item.name,
						"uom": item.stock_uom,
						**{f: entry[f] for f in QTY_FIELDS + VALUE_FIELDS},
					}
				)
				data += transaction_rows(
					item, entry, item_moves.get((store, item.name), []), labels, from_date, to_date
				)
	data.append({"indent": 0, "particulars": _("Grand Total"), "bold": 1, **grand})
	return data


def total_row(indent, label, rows, with_qty=True):
	"""A store / Item Group row: the sum of its items; quantities only when all its items have the same unit."""
	row = {"indent": indent, "particulars": label, "bold": 1}
	for field in VALUE_FIELDS:
		row[field] = sum(flt(entry[field]) for _item, entry in rows)
	uoms = {item.stock_uom for item, _entry in rows}
	if with_qty and len(uoms) == 1:
		row["uom"] = uoms.pop()
		for field in QTY_FIELDS:
			row[field] = sum(flt(entry[field]) for _item, entry in rows)
	return row


def transaction_rows(item, entry, moves, labels, from_date, to_date):
	"""The item's movements in the period, oldest first, each with the balance after it, between an Opening and a
	Closing row (the closing balance of the stock ledger)."""
	if not [m for m in moves if not m.hidden]:
		return []
	rows = []
	qty, value = flt(entry.opening_qty), flt(entry.opening_value)
	if round(qty, 6) or abs(value) >= 0.005:
		rows.append(
			{
				"indent": 3,
				"particulars": _("Opening as on {0}").format(formatdate(from_date)),
				"uom": item.stock_uom,
				"balance_qty": qty,
				"balance_value": value,
			}
		)
	for move in sorted(moves, key=lambda m: (m.posted, m.created)):
		qty += move.qty
		value += move.value
		if move.hidden:
			continue
		inward = move.qty > 0 or (not round(move.qty, 6) and move.value > 0)
		label = labels.get((move.voucher_type, move.voucher_no)) or move.voucher_type
		row = {
			"indent": 3,
			"particulars": " · ".join([move.voucher_no, formatdate(move.posting_date), label]),
			"voucher_type": move.voucher_type,
			"voucher_no": move.voucher_no,
			"uom": item.stock_uom,
			"balance_qty": qty,
			"balance_value": value,
		}
		if inward:
			row.update(in_qty=move.qty, in_value=move.value)
		else:
			row.update(out_qty=-move.qty, out_value=-move.value)
		rows.append(row)
	rows.append(
		{
			"indent": 3,
			"particulars": _("Closing as on {0}").format(formatdate(to_date)),
			"uom": item.stock_uom,
			"balance_qty": flt(entry.balance_qty),
			"balance_value": flt(entry.balance_value),
		}
	)
	return rows


def get_voucher_labels(moves):
	"""{(voucher type, voucher no): label}: the supplier of a receipt, the customer of a delivery, the type of a
	Stock Entry ("Material Transfer", "Material Receipt (Opening)" ...)."""
	labels = {}
	by_type = {}
	for m in moves:
		by_type.setdefault(m.voucher_type, set()).add(m.voucher_no)
	for doctype, field in (
		("Purchase Receipt", "supplier_name"),
		("Subcontracting Receipt", "supplier_name"),
		("Delivery Note", "customer_name"),
		("Purchase Invoice", "supplier_name"),
		("Sales Invoice", "customer_name"),
	):
		names = list(by_type.get(doctype) or [])
		if names:
			for name, party in frappe.get_all(
				doctype, filters={"name": ["in", names]}, fields=["name", field], as_list=True
			):
				labels[(doctype, name)] = f"{doctype}: {party}" if party else doctype
	names = list(by_type.get("Stock Entry") or [])
	if names:
		for e in frappe.get_all(
			"Stock Entry", filters={"name": ["in", names]}, fields=["name", "stock_entry_type", "is_opening"]
		):
			labels[("Stock Entry", e.name)] = (e.stock_entry_type or "Stock Entry") + (
				" (Opening)" if e.is_opening == "Yes" else ""
			)
	return labels


def item_conditions(filters):
	conditions, values = "", {}
	if filters.get("company"):
		conditions += " and sle.company = %(company)s"
		values["company"] = filters.company
	if filters.get("item_group"):
		lft, rgt = frappe.db.get_value("Item Group", filters.item_group, ["lft", "rgt"])
		conditions += f""" and sle.item_code in (select i.name from `tabItem` i join `tabItem Group` ig
			on ig.name = i.item_group where ig.lft >= {int(lft)} and ig.rgt <= {int(rgt)})"""
	if filters.get("item"):
		conditions += " and sle.item_code = %(item)s"
		values["item"] = filters.item
	return conditions, values


def get_warehouses(filters):
	conditions = {"is_group": 0}
	if filters.get("company"):
		conditions["company"] = filters.company
	if filters.get("warehouse"):
		lft, rgt = frappe.db.get_value("Warehouse", filters.warehouse, ["lft", "rgt"])
		conditions.update({"lft": [">=", lft], "rgt": ["<=", rgt]})
		return frappe.get_all("Warehouse", filters=conditions, pluck="name")
	shown = get_shown_warehouses()
	if shown is None:
		return frappe.get_all("Warehouse", filters=conditions, pluck="name")
	return frappe.get_all("Warehouse", filters={**conditions, "name": ["in", shown or [""]]}, pluck="name")


def get_shown_warehouses():
	"""The warehouses ticked "Show in Stock Summary" (a ticked group brings the warehouses under it); None while
	none is ticked (or the field does not exist), so that every warehouse is shown."""
	if not frappe.get_meta("Warehouse").has_field(SHOW_FIELD):
		return None
	ticked = frappe.get_all("Warehouse", filters={SHOW_FIELD: 1}, fields=["name", "lft", "rgt", "is_group"])
	if not ticked:
		return None
	names = set()
	for w in ticked:
		if w.is_group:
			names.update(
				frappe.get_all(
					"Warehouse", filters={"lft": [">=", w.lft], "rgt": ["<=", w.rgt], "is_group": 0}, pluck="name"
				)
			)
		else:
			names.add(w.name)
	return sorted(names)


def get_store_names(warehouses):
	"""{warehouse: store}: the warehouse name without the company abbreviation and Restricted / Unrestricted."""
	abbrs = frappe.get_all("Company", pluck="abbr")
	stores = {}
	for warehouse in warehouses:
		name = warehouse
		for abbr in abbrs:
			if name.endswith(f" - {abbr}"):
				name = name[: -len(f" - {abbr}")]
		stores[warehouse] = RESTRICTED.sub("", name).strip(" -") or warehouse
	return stores
