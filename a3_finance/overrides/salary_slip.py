import frappe

def pull_values_from_payroll_master(doc, method):
    settings = frappe.get_single("Payroll Master Settings")

    doc.custom_service_weightage                      = settings.service_weightage
    doc.custom_dearness_allowance_                    = settings.dearness_allowance_
    doc.custom_yearly_increment                       = settings.yearly_increment
    doc.custom_canteen_subsidy                        = settings.canteen_subsidy
    doc.custom_washing_allowance                      = settings.washing_allowance
    doc.custom_book_allowance                         = settings.book_allowance
    doc.custom_night_shift_allowance                  = settings.night_shift_allowance
    doc.custom_stitching_allowance                    = settings.stitching_allowance
    doc.custom_shoe_allowance                         = settings.shoe_allowance
    doc.custom_spectacle_allowance                    = settings.spectacle_allowance
    doc.custom_ex_gratia                              = settings.ex_gratia
    doc.custom_arrear                                 = settings.arrear
    doc.custom_festival_advance                       = settings.festival_advance
    doc.custom_festival_advance_recovery              = settings.festival_advance_recovery
    doc.custom_professional_tax                       = settings.professional_tax
    doc.custom_labour_welfare_fund                    = settings.labour_welfare_fund
    doc.custom_brahmos_recreation_club_contribution   = settings.brahmos_recreation_club_contribution
    doc.custom_benevolent_fund                        = settings.benevolent_fund
    doc.custom_society                                = settings.society
    doc.custom_canteen_recovery                       = settings.canteen_recovery


    # --- 🧮 Service Weightage Allowance Calculation ---
    if doc.employee:
        years = frappe.db.get_value("Employee", doc.employee, "custom_years_of_service") or 0
        rate = settings.service_weightage
        completed_blocks = (years - 5) // 5 + 1 if years > 5 else 0
        payout = completed_blocks * rate * 5

        # Update if component exists, else append
        found = False
        for e in doc.earnings:
            if e.salary_component == "Service Weightage":
                e.amount = payout
                e.default_amount = payout
                found = True
                break

        if not found and payout > 0:
            doc.append("earnings", {
                "salary_component": "Service Weightage",
                "amount": payout,
                "default_amount": payout,
            })

