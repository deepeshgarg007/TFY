# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "tfy"
app_title = "Tfy"
app_publisher = "hello@openetech.com"
app_description = "Tiffany Customizations"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hello@openetech.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tfy/css/tfy.css"
# app_include_js = "/assets/tfy/js/tfy.js"

# include js, css files in header of web template
# web_include_css = "/assets/tfy/css/tfy.css"
# web_include_js = "/assets/tfy/js/tfy.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "tfy.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "tfy.install.before_install"
# after_install = "tfy.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tfy.notifications.get_notification_config"

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

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }
doc_events = {
	"Sales Invoice": {
		"on_submit": "tfy.custom_method.create_gst_gl_entry",
		"validate": ["tfy.custom_method.set_accounting_dimension_defaults",
						"tfy.custom_method.default_distance"]
	},
	"Purchase Receipt": {
		"on_submit": "tfy.custom_method.insert_item_price_history"
	}
}
# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"tfy.tasks.all"
# 	],
# 	"daily": [
# 		"tfy.tasks.daily"
# 	],
# 	"hourly": [
# 		"tfy.tasks.hourly"
# 	],
# 	"weekly": [
# 		"tfy.tasks.weekly"
# 	]
# 	"monthly": [
# 		"tfy.tasks.monthly"
# 	]
# }
scheduler_events = {
	"hourly": [
		"tfy.tfy.doctype.bank_file.bank_file.create_recon_entries"
	]
}
# Testing
# -------

# before_tests = "tfy.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "tfy.event.get_events"
# }
fixtures = [
		{	"dt":"Custom Field",
			"filters": [["name", "in", [
				"Sales Invoice-tfy_transaction_type",
				"Sales Invoice-auth_code",
				"Sales Invoice-credit_card_no",
				"Sales Invoice-match_status",
				"Bank-account",
				"Bank-charges_account",
				"Bank-gst_clearing_account",
				"Company-inter_company_accounts",
				"Company-inter_company_income_account",
				"Company-inter_company_expense_account",
				"Mode of Payment-is_credit_card"
		]]]
		},
		{"dt":"Custom Script", "filters": [["name", "in", [
				"Sales Invoice-Client",
				"Sales Order-Client",
				"Delivery Note-Client",
				"Purchase Order-Client",
				"Purchase Receipt-Client",
				"Purchase Invoice-Client",
				"Data Import Beta-Client",
				"Bank-Client",
		]]]},
		{"dt":"Property Setter", "filters": [["name", "in", [
			"Pincode Distance-title_field",
			"Store Terminal-title_field",
			"Bank File-title_field"
		]]]}
]
