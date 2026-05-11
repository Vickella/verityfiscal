from . import __version__ as app_version

app_name = "verityfiscal"
app_title = "Verity Fiscal"
app_description = "ERPNext FDMS Integration for Virtual Fiscalisation - ZIMRA Compliant"
app_icon = "octicon octicon-file-code"
app_color = "#4472C4"
app_email = "support@verityfiscal.com"
app_license = "GNU General Public License v3"
app_version = app_version

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/verityfiscal/css/verityfiscal.css"
# app_include_js = "/assets/verityfiscal/js/verityfiscal.js"

# include js, css files in header of web template
# web_include_css = "/assets/verityfiscal/css/verityfiscal-web.css"
# web_include_js = "/assets/verityfiscal/js/verityfiscal-web.js"

# include custom scss in every page
# app_include_scss = "verityfiscal/public/scss/index.scss"

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Invoice": {
		"on_submit": "verityfiscal.api.invoice.on_sales_invoice_submit",
		"on_cancel": "verityfiscal.api.invoice.on_sales_invoice_cancel",
	},
	"Purchase Invoice": {
		"on_submit": "verityfiscal.api.invoice.on_purchase_invoice_submit",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"verityfiscal.tasks.sync_fiscal_device_status",
	],
	"daily": [
		"verityfiscal.tasks.reconcile_transactions",
		"verityfiscal.tasks.generate_compliance_report",
	],
}

# Fixtures
# --------
# Sync these doctype as fixtures. Fixtures can be used to sync default values.

fixtures = [
	{"doctype": "Custom Field", "filters": [["module", "=", "Verity Fiscal"]]},
	{"doctype": "Property Setter", "filters": [["module", "=", "Verity Fiscal"]]},
]

# API
# ----
# These methods are called via API and require_admin access for certain operations

api_methods = {
	"verityfiscal.api.fdms.register_device": "verityfiscal.api.fdms.register_fiscal_device",
	"verityfiscal.api.invoice.get_invoice_status": "verityfiscal.api.invoice.get_invoice_fiscalisation_status",
	"verityfiscal.api.invoice.send_invoice": "verityfiscal.api.invoice.send_invoice_to_fdms",
}

# Permissions
# -----------

# Permissions for doctypes

permission_sets = [
	{
		"name": "Fiscal Device Manager",
		"permissions": [
			{
				"role": "System Manager",
				"read": 1,
				"write": 1,
				"submit": 1,
				"cancel": 1,
				"delete": 1,
			},
		],
	},
]

# App Settings Defaults
# ---------------------

app_settings_defaults = {
	"fdms_enabled": 0,
	"fdms_environment": "production",
	"auto_fiscalise_invoices": 0,
	"retry_failed_transmissions": 1,
	"retry_attempts": 3,
	"retry_interval": 300,  # seconds
}
