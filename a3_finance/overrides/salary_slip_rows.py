"""One row per salary component on a Salary Slip.

An Additional Salary that does not overwrite the salary structure amount - the CEA arrear made by
doc_events/cea_arrear.py, for one - is put by HRMS in a row of its own, so the slip showed the component twice:
Children Education Allowance 800 (the month's, from the structure) and 4,000 (the arrear), each with its own YTD,
and the pay slip's Amount column counted the month's 800 twice.

Once the slip is worked out, the rows of a component are made one row: the first keeps its place and takes the
amounts of the others (Amount, the default / additional amounts and the YTD), and the others are removed; the
pay slip's actual amounts are then set again (set_actual_amounts). Totals do not change.

HRMS works the rows out again on each recalculation (calculate_net_pay), with the additional row on its own (so the
income tax still treats the arrear as a one-time amount), so this runs last: at the end of validate and of
before_save, as set_professional_tax recalculates the slip in both (hooks.py).
"""

from frappe.utils import flt

AMOUNT_FIELDS = ("amount", "default_amount", "additional_amount", "year_to_date")


def merge_same_component_rows(doc, method=None):
	merged = False
	for parentfield in ("earnings", "deductions"):
		rows = doc.get(parentfield) or []
		first_of, kept = {}, []
		for row in rows:
			first = first_of.get(row.salary_component)
			if first is None:
				first_of[row.salary_component] = row
				kept.append(row)
				continue
			# YTD: the first row's is the earlier slips' total plus its own amount; the other's amount is added
			for field in AMOUNT_FIELDS:
				first.set(
					field,
					flt(first.get(field)) + flt(row.get(field) if field != "year_to_date" else row.amount),
				)
			merged = True
		if len(kept) != len(rows):
			doc.set(parentfield, kept)
			for idx, row in enumerate(kept, start=1):
				row.idx = idx
	if merged:
		from a3_finance.overrides.salary_slip import set_actual_amounts

		set_actual_amounts(doc, method)
