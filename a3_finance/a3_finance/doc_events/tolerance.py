

import erpnext.controllers.status_updater as status_updater

def custom_check_overflow_with_allowance(self, item, args):
    """Disable ERPNext overflow check — handled by custom tolerance."""
    return  # do nothing

def apply_override():
    status_updater.StatusUpdater.check_overflow_with_allowance = custom_check_overflow_with_allowance
