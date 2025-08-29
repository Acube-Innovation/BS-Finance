
import frappe
from hrms.payroll.doctype.gratuity.gratuity import get_last_salary_slip, Gratuity
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from frappe import _, bold
from frappe.query_builder.functions import Sum
from frappe.utils import cstr, flt, get_datetime, get_link_to_form

def new_get_total_component_amount(self) -> float:
    applicable_earning_components = Gratuity.get_applicable_components(self)
    salary_slip = get_last_salary_slip(self.employee)
    if not salary_slip:
        frappe.throw(_("No Salary Slip found for Employee: {0}").format(bold(self.employee)))

    # consider full payment days for calculation as last month's salary slip
    # might have less payment days as per attendance, making it non-deterministic
    salary_slip.payment_days = salary_slip.total_working_days
    salary_slip.calculate_net_pay()

    total_amount = 0
    component_found = False
    for row in salary_slip.earnings:
        if row.salary_component in applicable_earning_components:
            total_amount += flt(row.custom_actual_amount)
            component_found = True

    if not component_found:
        frappe.throw(
            _("No applicable Earning component found in last salary slip for Gratuity Rule: {0}").format(
                bold(get_link_to_form("Gratuity Rule", self.gratuity_rule))
            )
        )

    return total_amount