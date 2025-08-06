from frappe.utils import getdate, add_years, add_days

def set_apprentice_doe(self,method):
    if self.employment_type == "Apprentice" and self.date_of_joining:
        doj = getdate(self.date_of_joining)
        self.contract_end_date = add_days(add_years(doj, 1), -1)

def update_total_service(self,method):
    """
    Updates custom_total_service based on date_of_joining.
    Should be called in validate().
    """
    from datetime import datetime

    if not self.date_of_joining:
        self.custom_total_service = ""
        return

    doj = getdate(self.date_of_joining)
    today = datetime.today().date()

    if doj > today:
        self.custom_total_service = "0 Years and 0 Months"
        return

    years = today.year - doj.year
    months = today.month - doj.month

    if months < 0:
        years -= 1
        months += 12

    self.custom_total_service = (
        f"{years} Year{'s' if years != 1 else ''} and "
        f"{months} Month{'s' if months != 1 else ''}"
    )
