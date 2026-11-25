app_name = "songa_multi_tenancy"
app_title = "Songa Multi Tenancy"
app_publisher = "John Karimakos Murigi"
app_description = "This app handles multi tenancy extension of the ERPNext platform which is supposed to work with SMP."
app_email = "j.murigi@songa.mobi"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "songa_multi_tenancy",
# 		"logo": "/assets/songa_multi_tenancy/logo.png",
# 		"title": "Songa Multi Tenancy",
# 		"route": "/songa_multi_tenancy",
# 		"has_permission": "songa_multi_tenancy.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/songa_multi_tenancy/css/songa_multi_tenancy.css"
# app_include_js = "/assets/songa_multi_tenancy/js/songa_multi_tenancy.js"

# include js, css files in header of web template
# web_include_css = "/assets/songa_multi_tenancy/css/songa_multi_tenancy.css"
# web_include_js = "/assets/songa_multi_tenancy/js/songa_multi_tenancy.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "songa_multi_tenancy/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "songa_multi_tenancy/public/icons.svg"

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
# 	"methods": "songa_multi_tenancy.utils.jinja_methods",
# 	"filters": "songa_multi_tenancy.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "songa_multi_tenancy.install.before_install"
# after_install = "songa_multi_tenancy.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "songa_multi_tenancy.uninstall.before_uninstall"
after_uninstall = "songa_multi_tenancy.uninstall.after_uninstall"
after_sync = "songa_multi_tenancy.install.after_sync"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "songa_multi_tenancy.utils.before_app_install"
# after_app_install = "songa_multi_tenancy.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "songa_multi_tenancy.utils.before_app_uninstall"
# after_app_uninstall = "songa_multi_tenancy.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "songa_multi_tenancy.build.after_build"

# To hook into the build process of other apps
# The list of apps being built is passed as an argument

# after_app_build = "songa_multi_tenancy.build.after_app_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "songa_multi_tenancy.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["songa_multi_tenancy.search.awesomebar_results"]

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
permission_query_conditions = {
    "Item": "songa_multi_tenancy.permissions.item_query",
    "Item Group": "songa_multi_tenancy.permissions.item_group_query",
    "Customer": "songa_multi_tenancy.permissions.customer_query",
    "Customer Group": "songa_multi_tenancy.permissions.customer_group_query",
    "Supplier": "songa_multi_tenancy.permissions.supplier_query",
    "Supplier Group": "songa_multi_tenancy.permissions.supplier_group_query",
    "Territory": "songa_multi_tenancy.permissions.territory_query",
    "Brand": "songa_multi_tenancy.permissions.brand_query",
    "Price List": "songa_multi_tenancy.permissions.price_list_query",
    "Item Price": "songa_multi_tenancy.permissions.item_price_query",
    "Pricing Rule": "songa_multi_tenancy.permissions.pricing_rule_query",
    "Holiday List": "songa_multi_tenancy.permissions.holiday_list_query",
    "Department": "songa_multi_tenancy.permissions.department_query",
    "Designation": "songa_multi_tenancy.permissions.designation_query",
    "Branch": "songa_multi_tenancy.permissions.branch_query",
    "Letter Head": "songa_multi_tenancy.permissions.letter_head_query",
    "Driver": "songa_multi_tenancy.permissions.driver_query",
    "Songa Webhook Log": "songa_multi_tenancy.permissions.songa_webhook_log_query",
    "Mpesa Express Request": "songa_multi_tenancy.permissions.mpesa_express_request_query",
    "Lead": "songa_multi_tenancy.permissions.lead_query",
    "Driver Commission Ledger": "songa_multi_tenancy.permissions.driver_commission_ledger_query",
    "Asset Type": "songa_multi_tenancy.permissions.asset_type_query",
    "Rental Days": "songa_multi_tenancy.permissions.rental_days_query",
    "Severity Type": "songa_multi_tenancy.permissions.severity_type_query",
    "Energy KWh": "songa_multi_tenancy.permissions.energy_kwh_query",
    "User": "songa_multi_tenancy.permissions.user_query",
}

has_permission = {
    "Item": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Item Group": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Customer": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Customer Group": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Supplier": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Supplier Group": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Territory": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Brand": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Price List": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Item Price": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Pricing Rule": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Holiday List": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Department": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Designation": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Branch": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Letter Head": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Driver": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Songa Webhook Log": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Mpesa Express Request": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Lead": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Driver Commission Ledger": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Asset Type": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Rental Days": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Severity Type": "songa_multi_tenancy.permissions.tenant_has_permission",
    "Energy KWh": "songa_multi_tenancy.permissions.tenant_has_permission",
    "User": "songa_multi_tenancy.permissions.user_has_permission",
}

# Automatically assign tenant/company context to scoped records and
# keep Tenant User registrations in sync.
doc_events = {
    "User": {
        "on_update": "songa_multi_tenancy.permissions.sync_tenant_user",
    },
    "Item": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Item Group": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Brand": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Customer": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Customer Group": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Supplier": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Supplier Group": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Territory": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Price List": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Item Price": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Pricing Rule": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Holiday List": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Department": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Designation": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Branch": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Letter Head": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Driver": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Songa Webhook Log": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Mpesa Express Request": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Lead": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Driver Commission Ledger": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Asset Type": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Rental Days": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Severity Type": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
    "Energy KWh": {"validate": "songa_multi_tenancy.permissions.assign_tenant_context"},
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

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

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"songa_multi_tenancy.tasks.all"
# 	],
# 	"daily": [
# 		"songa_multi_tenancy.tasks.daily"
# 	],
# 	"hourly": [
# 		"songa_multi_tenancy.tasks.hourly"
# 	],
# 	"weekly": [
# 		"songa_multi_tenancy.tasks.weekly"
# 	],
# 	"monthly": [
# 		"songa_multi_tenancy.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "songa_multi_tenancy.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "songa_multi_tenancy.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "songa_multi_tenancy.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["songa_multi_tenancy.utils.before_request"]
# after_request = ["songa_multi_tenancy.utils.after_request"]

# Job Events
# ----------
# before_job = ["songa_multi_tenancy.utils.before_job"]
# after_job = ["songa_multi_tenancy.utils.after_job"]

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
# 	"songa_multi_tenancy.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

fixtures = [
	{
        "dt": "Property Setter", 
        "filters": [
            ["module", "=", "Songa Multi Tenancy"]
        ]
    },
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "=", "Contact"]
        ],
    },
    {
        "dt": "Number Card",
        "filters": [
            ["document_type", "in", ["Tenant Provisioning", "Tenant"]]
        ]
    },
    {
        "dt": "Dashboard Chart",
        "filters": [
            ["document_type", "in", ["Tenant Provisioning", "Tenant"]]
        ]
    },
	{
        "dt": "Workspace", 
        "filters": [
            ["name", "=", "Tenants"]
        ]
    },
	{
        "dt": "Client Script",
        "filters": [
            ["name", "=", "Tenant Lifecycle Actions"]
        ]
    }
]
