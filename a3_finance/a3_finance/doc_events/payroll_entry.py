import frappe
from frappe import _
from hrms.payroll.doctype.payroll_entry.payroll_entry import get_employee_list,PayrollEntry

# @frappe.whitelist()
# def get_employees_by_employment_type(payroll_entry_name, employment_types: str):
#     """Fetch employees for a payroll entry with an extra employment_type filter"""
#     doc = frappe.get_doc("Payroll Entry", payroll_entry_name)
#     filters = PayrollEntry.make_filters(self=doc)
#     print(f"Filters: {filters}")

#     # IMPORTANT: change this field name if you use custom_employment_type
#     searchstring= [e.strip() for e in employment_types.split(",")]
#     filters["employment_type"] = ["in", [e.strip() for e in employment_types.split(",")]]
#     print("filters after employment type:", filters)

#     employees = get_employee_list(filters=filters, searchfield="employment_type",search_string = "Apprentice",as_dict=True, ignore_match_conditions=True)
#     doc.set("employees", [])

#     if not employees:
#         frappe.throw(_("No employees found for employment type {0}").format(employment_types))

#     doc.set("employees", employees)
#     doc.number_of_employees = len(doc.employees)
#     doc.update_employees_with_withheld_salaries()
#     doc.save()

#     # return doc.get_employees_with_unmarked_attendance()

@frappe.whitelist()
def get_employees_by_employment_type(payroll_entry_name, employment_types: str):
    """Fetch employees for a payroll entry with an extra employment_type filter"""
    doc = frappe.get_doc("Payroll Entry", payroll_entry_name)
    filters = PayrollEntry.make_filters(self=doc)

    # Turn CSV string into a list of types
    emp_types = [e.strip() for e in employment_types.split(",") if e.strip()]

    employees = []
    if len(emp_types) == 1:
        # Single type → use searchfield + search_string (like Apprentice)
        employees = get_employee_list(
            filters=filters,
            searchfield="employment_type",
            search_string=emp_types[0],
            as_dict=True,
            ignore_match_conditions=True
        )
    else:
        # Multiple types → fetch separately and combine
        combined = []
        
        for emp_type in emp_types:
            print(f"Fetching employees for types: {emp_types}")
            emp_list = get_employee_list(
                filters=filters,
                searchfield="employment_type",
                search_string=emp_type,
                as_dict=True,
                ignore_match_conditions=True
            )
            print(f"Found {len(emp_list)} employees for type '{emp_type}'")
            combined.extend(emp_list)

        # remove duplicates (in case same employee matches twice)
        seen = set()
        employees = []
        for emp in combined:
            if emp.employee not in seen:
                employees.append(emp)
                seen.add(emp.employee)

    # Clear and set employees table
    doc.set("employees", [])

    if not employees:
        frappe.throw(_("No employees found for employment type(s): {0}").format(", ".join(emp_types)))

    doc.set("employees", employees)
    doc.number_of_employees = len(doc.employees)
    doc.update_employees_with_withheld_salaries()
    doc.save()

    return doc



import frappe
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
 
 
class CustomPayrollEntry(PayrollEntry):
 
    def get_salary_component_total(self, component_type=None, employee_wise_accounting_enabled=False):
        """
        Correctly split each employee's salary component amount 
        using custom_employee_type in Salary Component Account table.
        """
 
        salary_components = self.get_salary_components(component_type)
        if not salary_components:
            return {}
 
        component_dict = {}
 
        for item in salary_components:
 
            # Employee details
            employee = item.employee
            amount = item.amount
            component = item.salary_component
 
            emp_type = frappe.db.get_value("Employee", employee, "employment_type")
 
            # Find specific account for this employee type
            account = frappe.db.get_value(
                "Salary Component Account",
                {
                    "parent": component,
                    "parenttype": "Salary Component",
                    "parentfield": "accounts",
                    "company": self.company,
                    "custom_employment_type": emp_type,
                },
                "account",
            )
 
            # Default account (no employee type)
            if not account:
                account = frappe.db.get_value(
                    "Salary Component Account",
                    {
                        "parent": component,
                        "parenttype": "Salary Component",
                        "parentfield": "accounts",
                        "company": self.company,
                    },
                    "account",
                )
 
            if not account:
                frappe.throw(f"Account not set for Salary Component {component}")
 
            # cost center logic (unchanged)
            employee_cost_centers = self.get_payroll_cost_centers_for_employee(
                employee, item.salary_structure
            )
 
            for cost_center, percentage in employee_cost_centers.items():
                amount_cc = amount * percentage / 100
 
                key = (account, cost_center)
                component_dict[key] = component_dict.get(key, 0) + amount_cc
 
        return component_dict