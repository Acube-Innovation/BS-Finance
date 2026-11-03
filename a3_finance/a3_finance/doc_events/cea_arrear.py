"""Children Education Allowance (CEA) arrears.

The salary structure pays CEA on the employee's current No. of Children Eligible for CEA, from the month the slip
is made. When the count is changed with an Applicable On (CEA) date in a month already paid, the difference for
those months is an arrear: it is paid in the next payroll through an Additional Salary (Children Education
Allowance, added to the month's CEA), as the payroll team did by hand.

    Arrear = for each month from the Applicable On month up to the last month with a submitted salary slip:
             CEA due on the new count (Payroll Master Setting > Children Education Allowance of that month;
             nothing in a month without Basic Pay, e.g. full LOP) less the CEA paid in that month's slip
             (arrears paid in it included)

The Additional Salary is made for the month after the last submitted salary slip. Made again when the count or
date is changed again before that payroll (the previous one, not paid yet, is cancelled). A reduction is not
recovered (no negative arrear).
"""

import frappe
from frappe import _
from frappe.utils import add_days, add_months, flt, fmt_money, get_first_day, get_link_to_form, getdate

CEA = "Children Education Allowance"
CHANGE_LOG_TYPE = "No. of Children for Eligible CEA"


def on_update(doc, method=None):
    before = doc.get_doc_before_save()
    if not before:
        return
    count_changed = cstr_(before.get("custom_no_of_children_eligible_for_cea")) != cstr_(
        doc.get("custom_no_of_children_eligible_for_cea")
    )
    date_changed = getdate_(before.get("custom_applicable_on_cea")) != getdate_(doc.get("custom_applicable_on_cea"))
    if not (count_changed or date_changed) or not doc.get("custom_applicable_on_cea"):
        return
    if date_changed and not count_changed:
        update_change_log_date(doc)
    make_cea_arrear(doc)


def cstr_(value):
    return "" if value is None else str(value)


def getdate_(value):
    return getdate(value) if value else None


def update_change_log_date(doc):
    """Only the Applicable On (CEA) was corrected: the open change log entry of the count takes the new date (and
    the entry before it ends the day before), as when the count is changed."""
    effective_from = getdate(doc.custom_applicable_on_cea)
    current = frappe.get_all(
        "Employee Details Change Log",
        filters={"employee_id": doc.name, "component_type": CHANGE_LOG_TYPE, "effective_to": ["is", "not set"]},
        fields=["name", "effective_from"],
        order_by="effective_from desc",
        limit=1,
    )
    if not current:
        return
    previous = frappe.get_all(
        "Employee Details Change Log",
        filters={
            "employee_id": doc.name,
            "component_type": CHANGE_LOG_TYPE,
            "name": ["!=", current[0].name],
            "effective_from": ["<", current[0].effective_from],
        },
        fields=["name"],
        order_by="effective_from desc",
        limit=1,
    )
    frappe.db.set_value("Employee Details Change Log", current[0].name, "effective_from", effective_from)
    if previous:
        frappe.db.set_value(
            "Employee Details Change Log", previous[0].name, "effective_to", add_days(effective_from, -1)
        )


def make_cea_arrear(doc):
    applicable_from = get_first_day(doc.custom_applicable_on_cea)
    slips = frappe.get_all(
        "Salary Slip",
        filters={"employee": doc.name, "docstatus": 1, "start_date": [">=", applicable_from]},
        fields=["name", "start_date"],
        order_by="start_date",
    )
    cancel_unpaid_arrears(doc.name)
    if not slips:
        return  # the change is from a month not paid yet: the salary structure pays it

    count = int(doc.get("custom_no_of_children_eligible_for_cea") or 0)
    arrear, months = 0, []
    for slip in slips:
        paid = frappe.db.sql(
            """select ifnull(sum(amount), 0) from `tabSalary Detail`
            where parenttype = 'Salary Slip' and parent = %s and parentfield = 'earnings' and salary_component = %s""",
            (slip.name, CEA),
        )[0][0]
        due = get_cea_rate(count, slip.start_date) if has_basic_pay(slip.name) else 0
        if flt(due) != flt(paid):
            arrear += flt(due) - flt(paid)
            months.append(getdate(slip.start_date).strftime("%b %Y"))
    arrear = flt(arrear, 2)
    if arrear <= 0:
        return

    payroll_date = get_first_day(add_months(slips[-1].start_date, 1))
    additional_salary = frappe.get_doc(
        {
            "doctype": "Additional Salary",
            "employee": doc.name,
            "company": doc.company,
            "salary_component": CEA,
            "amount": arrear,
            "payroll_date": payroll_date,
            "overwrite_salary_structure_amount": 0,
            "ref_doctype": "Employee",
            "ref_docname": doc.name,
        }
    )
    additional_salary.flags.ignore_permissions = True
    additional_salary.insert()
    additional_salary.submit()
    frappe.msgprint(
        _("CEA arrear of {0} for {1} will be paid in the {2} payroll (Additional Salary {3}).").format(
            fmt_money(arrear, currency="INR"),
            ", ".join(months),
            getdate(payroll_date).strftime("%B %Y"),
            get_link_to_form("Additional Salary", additional_salary.name),
        ),
        alert=True,
    )


def cancel_unpaid_arrears(employee):
    """Cancel the CEA arrear Additional Salaries made for this employee that are not paid yet (no submitted salary
    slip of their month), so that a new change is worked out once."""
    for row in frappe.get_all(
        "Additional Salary",
        filters={
            "employee": employee,
            "salary_component": CEA,
            "docstatus": 1,
            "ref_doctype": "Employee",
            "ref_docname": employee,
        },
        fields=["name", "payroll_date"],
    ):
        paid = frappe.db.exists(
            "Salary Slip",
            {"employee": employee, "docstatus": 1, "start_date": ["<=", row.payroll_date],
             "end_date": [">=", row.payroll_date]},
        )
        if not paid:
            additional_salary = frappe.get_doc("Additional Salary", row.name)
            additional_salary.flags.ignore_permissions = True
            additional_salary.cancel()


def has_basic_pay(slip):
    return flt(
        frappe.db.get_value(
            "Salary Detail",
            {"parenttype": "Salary Slip", "parent": slip, "parentfield": "earnings", "abbr": ["in", ["BP", "B"]]},
            "amount",
        )
    ) > 0


def get_cea_rate(count, date):
    """CEA for `count` children in the month of `date`: Payroll Master Setting > Children Education Allowance (the
    rate of the highest number of children up to `count`); 400 / 800 as in the salary structure when not set."""
    if count <= 0:
        return 0
    date = getdate(date)
    setting = frappe.get_all(
        "Payroll Master Setting",
        filters={"payroll_year": ["in", [str(date.year), str(date.year - 1)]]},
        fields=["name", "payroll_year", "payroll_month_number"],
        order_by="payroll_year desc, payroll_month_number desc",
    )
    setting = next(
        (s for s in setting if (int(s.payroll_year), int(s.payroll_month_number or 0)) <= (date.year, date.month)),
        None,
    )
    rates = (
        frappe.get_all(
            "Children Education Allowance",
            filters={"parenttype": "Payroll Master Setting", "parent": setting.name},
            fields=["child_details", "amount"],
        )
        if setting
        else []
    )
    amount = None
    for rate in sorted(rates, key=lambda r: int(r.child_details or 0)):
        if count >= int(rate.child_details or 0):
            amount = flt(rate.amount)
    if amount is not None:
        return amount
    return 800 if count > 1 else 400
