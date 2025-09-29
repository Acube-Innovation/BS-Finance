from frappe.model.document import Document
from frappe.utils import getdate, flt
import frappe
from a3_finance.utils.math_utils import round_half_up
import calendar
import json
# from hrms.payroll.doctype.salary_structure.salary_structure import AdditionalSalary


class ArrearBreakupLog(Document):
    pass






@frappe.whitelist()
def get_employee_arrear_details(employee, effective_from):
    from frappe.utils import getdate

    effective_from_date = getdate(effective_from)

    # 1️⃣ Get latest active Salary Structure Assignment
    ssa = frappe.get_all('Salary Structure Assignment',
                         filters={
                             'employee': employee,
                             'custom_inactive': 0,
                             'from_date': ['>=', effective_from_date]
                         },
                         order_by='from_date desc',
                         limit_page_length=1,
                         fields=['name', 'salary_structure'])
    ssa = ssa[0] if ssa else None

    # 2️⃣ Get Salary Slip for the employee where effective_from is in slip range
    slip = frappe.get_all('Salary Slip',
                          filters=[
                              ['employee', '=', employee],
                              ['start_date', '<=', effective_from_date],
                              ['end_date', '>=', effective_from_date]
                          ],
                          limit_page_length=1,
                          fields=['name', 'start_date', 'end_date'])
    slip = slip[0] if slip else None

    return {
        'salary_structure_assignment': ssa,
        'salary_slip': slip
    }
