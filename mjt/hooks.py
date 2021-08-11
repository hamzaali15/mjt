# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "mjt"
app_title = "MJT"
app_publisher = "RF"
app_description = "MJT"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hamza@rf.com"
app_license = "MIT"

# Includes in <head>
# ------------------

fixtures = [{"dt":"Custom Field", "filters": [["fieldname", "in", ("process_order", "department")]]}]

# include js, css files in header of desk.html
# app_include_css = "/assets/mjt/css/mjt.css"
# app_include_js = "/assets/mjt/js/mjt.js"

# include js, css files in header of web template
# web_include_css = "/assets/mjt/css/mjt.css"
# web_include_js = "/assets/mjt/js/mjt.js"

doc_events = {
    "Stock Entry": {
        "on_submit": [
                "mjt.mjt.doctype.process_order.process_order.manage_se_changes",
                "mjt.mjt.doctype.process_order_ledger.process_order_ledger.make_process_order_ledger"
            ],
        "on_cancel": "mjt.mjt.doctype.process_order.process_order.manage_se_changes",
        "before_insert": "mjt.mjt.custom_stock_ledger_entry.update_finish_rate",
        "before_save": "mjt.mjt.custom_stock_ledger_entry.update_finish_rate",
        "validate": "mjt.mjt.custom_stock_ledger_entry.validate_stock_ent_design_qty"
    },
    "Stock Ledger Entry": {
        "after_insert": "mjt.mjt.custom_stock_ledger_entry.update_design"
    },
    "Sales Invoice": {
        "before_submit": "mjt.mjt.custom_stock_ledger_entry.validate_design_no",
        "validate": "mjt.mjt.custom_stock_ledger_entry.validate_sale_inv_design_qty"
    },
    "Purchase Invoice": {
        "before_submit": "mjt.mjt.custom_stock_ledger_entry.validate_design_no"
    },
    "Delivery Note": {
        "before_submit": "mjt.mjt.custom_stock_ledger_entry.validate_design_no",
        "validate": "mjt.mjt.custom_stock_ledger_entry.validate_delivery_note_design_qty"
    },
    "Purchase Receipt": {
        "before_submit": ["mjt.mjt.custom_stock_ledger_entry.validate_design_no",
                            "mjt.mjt.purchase_receipt.swap_supplied_data"
                        ],
        "before_save": "mjt.mjt.custom_stock_ledger_entry.fill_design_no",
        "on_submit": [
                    "mjt.mjt.purchase_receipt.change_process_order_status",
                    # "mjt.mjt.purchase_receipt.make_raw_material_dl_entry",
                    "mjt.mjt.doctype.process_order_ledger.process_order_ledger.make_process_order_ledger"
                    ]
    },
    "Batch": {
        "before_save" :"mjt.mjt.custom_batch.design_name"
    },
    "Workstation": {
        "before_save": "mjt.mjt.util.set_workstation_net_rate"
    },
    "Design Receiving and Approval": {
        "validate": "mjt.mjt.doctype.design_receiving_and_approval.design_receiving_and_approval.validate"
    },
}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
        "Stock Entry": "public/js/stock_entry.js",
        #"Sales Invoice": "public/js/sales_invoice.js",
        "Purchase Invoice": "public/js/purchase_invoice.js",
        "Delivery Note": "public/js/delivery_note.js"
    }
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
# get_website_user_home_page = "mjt.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "mjt.install.before_install"
# after_install = "mjt.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mjt.notifications.get_notification_config"

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

# Scheduled Tasks
# ---------------

scheduler_events = {
    "hourly": ["mjt.mjt.doctype.process_order_ledger.process_order_ledger.make_entry_schedular"]
}

# Testing
# -------

# before_tests = "mjt.install.before_tests"

# Overriding Methods
# ------------------------------

override_whitelisted_methods = {
	"erpnext.stock.doctype.batch.batch.split_batch": "mjt.mjt.custom_batch.split_batch",
    "erpnext.stock.doctype.stock_entry.stock_entry_utils.make_stock_entry": "mjt.mjt.custom_batch.make_stock_entry"
}
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "mjt.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "mjt.task.get_dashboard_data"
# }

override_doctype_class = {
    'Purchase Receipt': 'mjt.override_purchase_receipt.OverridePurchaseReceipt',
    'Repost Item Valuation': 'mjt.override_item_repost_valuation.OverrideRepostItemValuation'
}

jenv = {
    "methods": [
        "update_print_no:mjt.mjt.custom_count_print.update_print_no",
        "get_batch_fabric_qty:mjt.mjt.custom_jinja_methods.get_batch_fabric_qty",
        "get_finish_product:mjt.mjt.custom_jinja_methods.get_finish_product"
    ]
}