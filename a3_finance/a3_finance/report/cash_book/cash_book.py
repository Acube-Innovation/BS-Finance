import frappe
from frappe.utils import flt


def execute(filters=None):


    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Particulars", "fieldname": "particulars", "fieldtype": "Data", "width": 350},
        {"label": "Inflow", "fieldname": "inflow", "fieldtype": "Currency", "width": 180},
        {"label": "Outflow", "fieldname": "outflow", "fieldtype": "Currency", "width": 180},
        {"fieldname": "account", "fieldtype": "Link", "options": "Account", "hidden": 1},

    ]


def get_data(filters):

    company = filters.get("company")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    bank_accounts = filters.get("bank_accounts")

    if not company or not from_date or not to_date:
        return []

    # -------------------------
    # STEP 1: Resolve Bank Accounts
    # -------------------------

    if not bank_accounts:
        bank_accounts = frappe.get_all(
            "Account",
            filters={
                "company": company,
                "account_type": ["in", ["Bank", "Cash"]]
            },
            pluck="name"
        )

    if isinstance(bank_accounts, str):
        bank_accounts = [x.strip() for x in bank_accounts.split(",")]

    if not bank_accounts:
        return []

    # -------------------------
    # STEP 2: Fetch Bank GL Entries (SAFE PLACEHOLDER BUILDING)
    # -------------------------

    placeholders = ", ".join(["%s"] * len(bank_accounts))

    bank_gl = frappe.db.sql(f"""
        SELECT name, voucher_no, debit, credit
        FROM `tabGL Entry`
        WHERE company = %s
        AND posting_date BETWEEN %s AND %s
        AND account IN ({placeholders})
        AND is_cancelled = 0
    """,
        [company, from_date, to_date] + bank_accounts,
        as_dict=True
    )

    if not bank_gl:
        return []

    voucher_list = list({d.voucher_no for d in bank_gl})

    if not voucher_list:
        return []

    # -------------------------
    # STEP 3: Fetch Opposite Entries
    # -------------------------

    voucher_placeholders = ", ".join(["%s"] * len(voucher_list))
    bank_placeholders = ", ".join(["%s"] * len(bank_accounts))

    opposite_entries = frappe.db.sql(f"""
        SELECT
            gl.voucher_no,
            gl.account,
            gl.debit,
            gl.credit,
            acc.root_type,
            acc.account_name
        FROM `tabGL Entry` gl
        INNER JOIN `tabAccount` acc ON acc.name = gl.account
        WHERE gl.voucher_no IN ({voucher_placeholders})
        AND gl.company = %s
        AND gl.account NOT IN ({bank_placeholders})
        AND gl.is_cancelled = 0
    """,
        voucher_list + [company] + bank_accounts,
        as_dict=True
    )

    # -------------------------
    # STEP 4: Determine Direction (Bank Side)
    # -------------------------

    voucher_direction = {}
    for row in bank_gl:
        if row.debit > 0:
            voucher_direction[row.voucher_no] = "in"
        elif row.credit > 0:
            voucher_direction[row.voucher_no] = "out"

    # -------------------------
    # STEP 5: Build Tree
    # -------------------------

    tree = {}
    total_in = 0
    total_out = 0

    for entry in opposite_entries:

        direction = voucher_direction.get(entry.voucher_no)
        if not direction:
            continue

        root = entry.root_type or "Others"
        # ledger = entry.account_name
        ledger = entry.account
        ledger_label = entry.account_name

        amount = flt(entry.debit) + flt(entry.credit)

        if root not in tree:
            tree[root] = {}

        if ledger not in tree[root]:
            tree[root][ledger] = {
                "label": ledger_label,
                "inflow": 0,
                "outflow": 0
            }


        if direction == "in":
            tree[root][ledger]["inflow"] += amount
            total_in += amount
        else:
            tree[root][ledger]["outflow"] += amount
            total_out += amount

    # -------------------------
    # STEP 6: Convert to Tree Data
    # -------------------------

    data = []

    for root, ledgers in tree.items():

        root_in = sum(v["inflow"] for v in ledgers.values())
        root_out = sum(v["outflow"] for v in ledgers.values())

        data.append({
            "particulars": root,
            "inflow": root_in,
            "outflow": root_out,
            "indent": 0
        })

        for ledger, values in ledgers.items():
            data.append({
                "particulars": values["label"],
                "account": ledger,
                "inflow": values["inflow"],
                "outflow": values["outflow"],
                "indent": 1,
                "parent": root
            })



    # Totals
    data.append({
        "particulars": "Total",
        "inflow": total_in,
        "outflow": total_out,
        "indent": 0
    })

    data.append({
        "particulars": "Net Inflow",
        "inflow": total_in - total_out,
        "outflow": 0,
        "indent": 0
    })

    return data
