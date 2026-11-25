# BrahMos ERPNext – Open Action Points: change log

Points from the "BrahMos ERPNext – Open Action Points" brief (13 November 2026) and the Reports & Observations
Tracker. All changes are in the `a3_finance` app. Tested on the local copy of the `batl` site (ERPNext / Frappe
15.90.1, India Compliance 15.25.6) on 18 November 2026.

To deploy: pull the app, then `bench --site <site> migrate` (runs the patch, syncs the workflow, workflow state,
property setter and report fixtures, and adds the workspace link), `bench --site <site> clear-cache`, and restart.

Tests: `bench --site <site> run-tests --module a3_finance.tests.test_finance_points` and
`--module a3_finance.tests.test_accounts_payable_ageing` (22 tests, all passing; they use the site's own data and
roll back).

## Point 3 – Ageing, Creditors (GRN Date; Excel export)

- "GRN Date" added to Ageing Based On in Accounts Payable and Accounts Payable Summary. An invoice ages from the
  posting date of its GRN (Purchase Receipt); with several GRNs, the latest; with none, the invoice posting date.
- Excel export sent as a real `.xlsx` download. Frappe's own response had a malformed Content-Disposition, so
  browsers saved a random name with no extension. Amounts are written as numbers, dates as dates, with a bold
  frozen header.
- Moved from a3_procurement to a3_finance on 18 November 2026.
- Files:
  - `overrides/accounts_payable_ageing.py`
  - `public/js/accounts_payable_ageing.js`
  - `overrides/report_export.py`
  - `hooks.py` (app_include_js, before_request, before_job, override_whitelisted_methods)
  - `tests/test_accounts_payable_ageing.py`
- Test result: 9 tests pass.

## Point 4 – Ageing, Debtors (Excel export)

- Root cause 1, permissions: Export of Accounts Receivable needs Export on Sales Invoice. Neither Accounts User nor
  Accounts Manager had it, so the Export menu was hidden.
- Root cause 2: the same download fault as point 3.
- Fix: patch `patches/v1_1/report_export_permission.py` switches Export on for:
  - Purchase Invoice and Sales Invoice: Accounts User and Accounts Manager
  - Item: Accounts User, Stock User and Stock Manager

  It only changes the Export flag on each role's existing level-0 row.
- Accounts Receivable and its Summary are laid out for Excel (`FORMATTED_REPORTS`).
- Test result: exports with and without Group by Customer pass; a real Accounts User can export.

## Point 5 – Ageing, Stock (Excel export)

- Root cause: Export needs Export on Item. Stock User, Stock Manager and Accounts User had none. The download fault
  from point 3 also applied.
- Fix: the same patch, plus the Excel layout. Every "Age (x - y)" and "Value (x - y)" bucket is written as a number.
- Stock Ageing remains a prepared report. The export reads the user's prepared result for the same filters.
- Test result: passes.

## Point 10 – Workflow, Purchase Invoice ("Illegal Document Status for Rejected")

- Root cause: the first state, "Prepared By", was marked as a submitted state, but a new invoice is a draft in it.
  "Reject" moved a draft to "Rejected", a cancelled state, and Frappe cannot cancel a draft.
  - It was marked submitted only because Frappe's Workflow form refuses a draft state that leads to a cancelled
    state ("Cannot cancel before submitting").
- Fix, in `fixtures/workflow.json` for the Purchase Invoice, Payment Entry and Journal Entry workflows:
  - "Prepared By" is now a draft state.
  - New draft state "Returned for Correction" (Accounts User may edit it); `fixtures/workflow_state.json` and hooks
    fixtures updated.
  - Reject on a draft goes to "Returned for Correction" (condition `doc.docstatus == 0`).
  - "Approve" from "Returned for Correction" submits to "Checked By".
  - Reject after approval goes to "Rejected", as before (condition `doc.docstatus == 1`).
- Legacy documents are left as they are; Reject is no longer offered on them:
  - submitted documents still in "Prepared By" (PI 146, of which 111 are opening entries; PE 5; JE 6)
  - drafts left in "Checked By" or "Verified By" (PI 53, PE 64, JE 2)
- Test result: full path tested for PI, PE and JE (reject draft → approve → reject → amend).

## Point 11 – Workflow, Payment Entry (errors after rejection and amendment)

- Root cause: Amend copied the state "Rejected" onto the new document. Frappe allows a new document only in the
  first state, hence "Workflow State transition not allowed from Prepared By to Rejected". "Rejected" is editable
  only by the Chief Finance Officer, so other users had no Save.
- Fix:
  - `overrides/workflow_amend.py` (doc_events "*" before_validate) puts a new amendment in the first state.
  - `public/js/workflow_amend.js` does the same in the form.
  - The point 10 workflow change applies to Payment Entry too.
  - Moved from a3_procurement to a3_finance.
- Test result: passes; an amended PE opens in "Prepared By" with Save.

## Point 26 – Cost Center ("Main - BATL")

- Finding: since 1 April 2026, 407 of 486 income/expense ledger lines (₹25.23 crore) carry "Main - BATL".
- Part A, `overrides/cost_center_mandatory.py`: an income or expense line entered by a user needs a Cost Center
  other than the company default.
  - Blocked: Purchase Invoice items, Sales Invoice items, Journal Entry lines, Payment Entry deductions, Stock Entry
    lines (Material Issue / Receipt), Expense Claim lines.
  - Warned only: Purchase Order and Material Request (they are created from Indents automatically).
  - Not checked: documents made by the system or by other documents (payroll, petty labour and ION journals, exchange
    gain/loss, revaluation, depreciation, imports, jobs) and returns.
- Part B: the Company default is kept. ERPNext uses it for exchange gain/loss and revaluation journals, payment
  reconciliation and advance journals, TDS rows, and a Payment Entry without a cost center; removing it would make
  those fail. The rule above removes it from user entry instead.
- Part C: new report "Cost Center Budget vs Actual"
  (`a3_finance/report/cost_center_budget_vs_actual`).
  - Cost Center → Account → Voucher tree: Annual Budget, Budget to Date (monthly distribution or twelfths, as
    ERPNext's budget check), Actual, Variance, Utilised % and Balance.
  - Each amount opens the General Ledger.
  - Linked on Accounting › Cost Center and Budgeting (`workspace_links.py`, after_migrate).
- Test result: rule and report tests pass; saving a JE on Main - BATL is refused with the row and account named.

## Point 27 – Trial Balance, group ledgers in bold

- `public/js/trial_balance_bold_groups.js` bolds every group account (a row other rows have as parent) on screen and
  in Print/PDF, by adjusting ERPNext's print row class; ledgers stay normal.
- The Excel export bolds group accounts (`Account.is_group`), the top-level heads and the total.
- Amount columns are sized to their largest number, so Excel shows no ###.
- Test result: passes; checked on screen, in the print template and in the exported file.

## Point 29 – TDS user guide

- `docs/brahmos/tds_in_erpnext.py` → "TDS in ERPNext - User Guide.pdf" (8 pages).
- Checked against ERPNext 15.90.1 / India Compliance 15.25.6. The differences found are listed in the guide; for
  example, India Compliance 15.27.1 or later carries the Income Tax Act 2025 codes and FY 2026-27 rates.

## Points 33 and 34 – MAT-STE-01139 (₹0.01 and amount vs Grand Total)

- Root cause: a 1-paisa rounding difference. Moving average 4,058.4375. 50 units left the source at
  ₹2,02,921.87 (₹4,05,843.75 − ₹2,02,921.88) and entered the target at 50 × 4,058.4375 = ₹2,02,921.875 →
  ₹2,02,921.88.
  - Both warehouses map to Stock In Hand, so the stock account moved by ₹0.01, balanced against the row's Difference
    Account. That account was Consumption of Tools & General Stores, from the Item Group default.
  - The screen showed the rate rounded to ₹4,058.44, so 50 × rate looked like ₹2,02,922.00. The stored amount and the
    Grand Total (₹2,02,921.88) are correct.
- Preventive fix:
  - `overrides/stock_entry_transfer.py` sets the Difference Account of transfer rows to the company's Stock
    Adjustment Account.
  - Stock Entry rates are shown to 4 decimals (property setters on basic_rate and valuation_rate).
- Same pattern found, not corrected (needs approval):
  - MAT-STE-00493 and MAT-STE-00902 (₹0.01 each, Repairs & Maintenance)
  - MAT-STE-01177: ₹13,580 to Stock Adjustment. This is a different cause: the target rate of ₹1,358 is half the
    source valuation of ₹2,716. It needs review.
- Test result: passes.

## Point 35 – Same item in two item groups

- `docs/brahmos/same_item_two_item_groups.py` → "Same Item in Two Item Groups - Options.pdf" (6 pages), covering:
  - Option 1: single item code
  - Option 2: Repack with Additional Costs
  - Option 3: subcontracting
  - a comparison and a decision guide

## Point 8 – Payment advice: the fix made permanent (found 18 November 2026)

- a3_finance exports its print formats as fixtures (`fixtures/print_format.json`), which are re-imported on every
  migrate after the module files are synced. The fixture still held the August 2025 copies of "Bank Payment Advice"
  and "Goods Receipt Note", so their fixes (12 November and 6 October 2026) were reverted on each migrate.
- Fix: the fixture entries were made identical to the fixed module JSON (`modified` 2026-11-18 12:00). Verified on
  batl after migrate: one line per invoice and a single Total on the payment advice.

## Also changed in a3_procurement

- `report/msme_ageing/msme_ageing.py`: MSME Ageing has its own GRN-date lookup. It used to import it from
  `a3_procurement.accounts_payable_ageing`, which moved to a3_finance.

## Shared

- `docs/brahmos/acube_pdf.py`: A4 reportlab layout for the client documents (Acube navy/teal, DejaVu Sans, cover,
  header, footer, page numbers).
- `docs/brahmos/finance_testing_guide.py` → "Finance Testing Guide.pdf" (44 pages): every tracker point (Sl 1 – 35) with
  your point, the action taken, how it was done, how to check it, and screenshots; plus an appendix of decisions.

## Payroll – EPF Wages of FTC employees follow the wage ceiling (18 November 2026)

- Raised by Finance on the November-2026 ECR. With a Statutory Wage Ceiling of 25,000, the FTC employees (schemes
  EPS-1250 ER-550 and EPS-0 ER-1800) showed EPF Wages 15,000 while their PF was worked out on 25,000 (EPS 2,083 +
  ER 917, or ER 3,000).
- `a3_finance/doctype/pf_detailed_log/pf_detailed_log.py`: the EPF Wages of these two schemes are capped at the
  month's ceiling, not at a fixed 15,000. The 1.16% additional EPS stays on the wages above 15,000.
- Tests: `tests/test_pf_wage_ceiling.py` (2 tests pass; ceilings 15,000 and 25,000).
- After deploying, re-save the November-2026 PF Detailed Logs (payroll_month "11", payroll_year "2026").
- The Payroll Guide (3 / 11 November) still says EPF Wages stay at 15,000 at most for these schemes; to be
  corrected.

## Payment Entry print formats – hard-coded text replaced by document data (25 November 2026)

- Bank Receipt
  - "Received with thanks from" is the party of the payment, with its address: the Customer Address on the
    payment, else the party's primary address. It was fixed text for BrahMos Aerospace Pvt Ltd, Hyderabad.
  - Remarks print the payment's Remarks field. They were a fixed sentence about BAPL, Hyderabad.
- Cash Payment Voucher
  - Account is the party (or, with no party, the account paid to). It was always "Labour Charges".
  - "On Account of" prints the Remarks field. It was a fixed sentence about casual labourers.
- Petty Cash Receipt Voucher
  - The ledgers are taken from the Sales Invoice the receipt is allocated to: its income account, each tax with its
    rate, and round off. Each is the receipt's share of the invoice. An advance or on-account amount is shown
    against the party.
  - Before, every receipt was split as total ÷ 1.19 into CGST 9%, SGST 9% and TCS 1%. That was wrong for
    RT/2026-2027/11/002, whose invoice has CGST 6% and SGST 6% and no TCS.
- Bank Payment Advice
  - "Ref :" at the top is the Supplier Invoice No of the Purchase Invoice paid. When several invoices are paid,
    their numbers are separated by commas. When none has a Supplier Invoice No, the payment number is shown, as
    before. The invoice table ("Your Invoice", Date) is unchanged.
  - The bank branch comes from the Bank Account's Branch Address. While that is empty, the old text is kept.
  - The closing line is the company name.
- Bank Receipt, Cash Payment Voucher and Petty Cash Receipt Voucher
  - The company address at the top is the company's primary address.
  - Before, the first address linked to the company was taken: "Jaya Springs-Billing", a supplier address
    (Coimbatore) that is linked to the company by mistake.
- NEFT (a3_procurement, `neft_print.py`): the date on the form is the day it is printed, not the posting date.
- Files:
  - `payment_entry_print.py` (Jinja methods `get_payment_party`, `get_receipt_breakup`)
  - `hooks.py` (jinja)
  - the four print formats, in both their module JSON and `fixtures/print_format.json`
- To deploy: `bench --site <site> migrate`, then clear-cache and restart.
