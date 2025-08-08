app_name = "a3_finance"
app_title = "A3 Finance"
app_publisher = "Acube"
app_description = "Finance System Managemnet"
app_email = "contact@acubeinnovations.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "a3_finance",
# 		"logo": "/assets/a3_finance/logo.png",
# 		"title": "A3 Finance",
# 		"route": "/a3_finance",
# 		"has_permission": "a3_finance.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/a3_finance/css/a3_finance.css"
# app_include_js = "/assets/a3_finance/js/a3_finance.js"

# include js, css files in header of web template
# web_include_css = "/assets/a3_finance/css/a3_finance.css"
# web_include_js = "/assets/a3_finance/js/a3_finance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "a3_finance/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Asset Category" : "public/js/asset_category.js",
    "Item" : "public/js/item.js",
    "Supplier" : "public/js/supplier.js",
    "Salary Slip" : "public/js/salary_slip.js",
    "Payroll Entry" : "public/js/payroll_entry.js",
    }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "a3_finance/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "a3_finance.utils.jinja_methods",
# 	"filters": "a3_finance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "a3_finance.install.before_install"
# after_install = "a3_finance.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "a3_finance.uninstall.before_uninstall"
# after_uninstall = "a3_finance.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "a3_finance.utils.before_app_install"
# after_app_install = "a3_finance.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "a3_finance.utils.before_app_uninstall"
# after_app_uninstall = "a3_finance.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "a3_finance.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }
scheduler_events = {
    "daily": [
        # "a3_finance.overrides.employee_updates.update_years_of_service_for_all_employees",
        "a3_finance.overrides.account_validity.update_account_status",
        "a3_finance.scheduler.update_employee_total_service.update_total_service_for_all_employees"
    ]
}


# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
doc_events = {
    "Salary Slip": {
        "validate": [
            "a3_finance.overrides.salary_slip.pull_values_from_payroll_master",
            "a3_finance.overrides.salary_slip.set_conveyance_allowance",
            "a3_finance.overrides.salary_slip.set_overtime_wages",
            "a3_finance.overrides.salary_slip.apprentice_working_days",
            "a3_finance.overrides.salary_slip.set_weekly_present_days_from_canteen",
            # "a3_finance.overrides.salary_slip.set_lop_summary",
            # "a3_finance.overrides.salary_slip.set_shoe_allowance_based_on_month",
            "a3_finance.overrides.salary_slip.set_employee_reimbursement_wages",
            "a3_finance.overrides.salary_slip.set_lop_in_hours_deduction",
            "a3_finance.overrides.salary_slip.set_basic_pay",
            "a3_finance.overrides.salary_slip.set_medical_allowance_from_slabs",
            "a3_finance.overrides.salary_slip.calculate_exgratia",
            "a3_finance.overrides.salary_slip.set_actual_amounts",
            "a3_finance.overrides.salary_slip.set_professional_tax",
            "a3_finance.overrides.salary_slip.set_pending_benevolent_fund",
            "a3_finance.overrides.salary_slip.final_calculation",
            "a3_finance.overrides.salary_slip.add_society_deduction",
            "a3_finance.overrides.salary_slip.apply_society_deduction_cap",
            "a3_finance.overrides.salary_slip.handle_suspension_in_employee",
            "a3_finance.overrides.salary_slip.set_actual_amounts",
            "a3_finance.overrides.salary_slip.update_tax_on_salary_slip",
            
        ],
        # "before_save":["a3_finance.overrides.salary_slip.custom_skip_society"],
        "on_submit":[
            "a3_finance.overrides.salary_slip.update_employee_payroll_details",
            "a3_finance.overrides.salary_slip.create_benevolent_fund_log",
            "a3_finance.overrides.salary_slip.mark_paid_benevolent_logs",
            "a3_finance.overrides.salary_slip.create_pf_detailed_summary",
            "a3_finance.overrides.salary_slip.update_ex_gratia_in_employee",
        ],
        "on_cancel":[
            "a3_finance.overrides.salary_slip.reset_benevolent_logs_on_cancel"
        ]
    },
    "Additional Salary": {
        "validate": [
            "a3_finance.overrides.additional_salary.calculate_lop_refund",
            "a3_finance.overrides.additional_salary.custom_validate",
            "a3_finance.overrides.additional_salary.process_lop_hour_refund",
            "a3_finance.overrides.additional_salary.process_overtime_amount",
            "a3_finance.overrides.additional_salary.society_deduction_processing"
        ],
        "on_submit": [
            "a3_finance.overrides.additional_salary.create_festival_advance"
        ],
    },
    "Employee": {
        "autoname": "a3_finance.overrides.employee_updates.autoname",
        "validate": [
            "a3_finance.a3_finance.doc_events.employee.set_apprentice_doe",
            "a3_finance.a3_finance.doc_events.employee.update_total_service"]
    },
    "Salary Structure Assignment":{
        "on_submit":[
            "a3_finance.a3_finance.doc_events.salary_structure_assignment.create_payroll_summary",
            "a3_finance.a3_finance.doc_events.salary_structure_assignment.update_in_employee"]
    },
    "Income Tax Slab":{
        "validate":"a3_finance.overrides.income_tax_slab.validate_duplicate"
    }
}



# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"a3_finance.tasks.all"
# 	],
# 	"daily": [
# 		"a3_finance.tasks.daily"
# 	],
# 	"hourly": [
# 		"a3_finance.tasks.hourly"
# 	],
# 	"weekly": [
# 		"a3_finance.tasks.weekly"
# 	],
# 	"monthly": [
# 		"a3_finance.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "a3_finance.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "a3_finance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "a3_finance.task.get_dashboard_data"
# }
override_doctype_dashboards = {
    "Employee": "a3_finance.dashboard.dashboard.get_dashboard_employee_links"
}
# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["a3_finance.utils.before_request"]
# after_request = ["a3_finance.utils.after_request"]

# Job Events
# ----------
# before_job = ["a3_finance.utils.before_job"]
# after_job = ["a3_finance.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"a3_finance.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

