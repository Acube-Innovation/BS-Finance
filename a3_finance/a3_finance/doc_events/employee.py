from frappe.utils import getdate, add_years, add_days

def set_apprentice_doe(self,method):
    if self.employment_type == "Apprentice" and self.date_of_joining:
        doj = getdate(self.date_of_joining)
        self.contract_end_date = add_days(add_years(doj, 1), -1)
