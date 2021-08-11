from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Production"),
			"items": [
                {
					"type": "doctype",
					"name": "Process Order",
					"description": _("Process Manufacturing Order."),
				},
				{
					"type": "doctype",
					"name": "Stock Entry",
					"description": _("Record item movement."),
				},
				{
					"type": "doctype",
					"name": "Material Request",
					"description": _("Requests for items."),
				},
			]
		},
        {
			"label": _("Process Manufacturing"),
			"items": [
				{
					"type": "doctype",
					"name": "Process Definition",
					"description": _("Process Definition."),
				},
				{
					"type": "doctype",
					"name": "Process Type",
					"description": _("Process Type."),
				},
                {
					"type": "doctype",
					"name": "Manufacturing Department",
					"description": _("Manufacturing Department"),
				},
                {
					"type": "doctype",
					"name": "Item",
					"description": _("All Products or Services."),
				},
                {
					"type": "doctype",
					"name": "Batch",
					"description": _("Batch (lot) of an Item."),
				},
                {
					"type": "doctype",
					"name": "Design",
					"description": _("Design"),
				},
                {
					"type": "doctype",
					"name": "Merge Lot",
					"description": _("Merge Lot"),
					"onboard": 1,
				}
			]
		},
		{
			"label": _("Gate Pass"),
			"items": [
				{
					"type": "doctype",
					"name": "Gate Pass",
					"description": "Gate Pass",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Gate Pass Type",
					"description": "Gate Pass Type",
					"onboard": 1,
				}
			]
		},
        {
			"label": _("Reports"),
			"items": [
				{
					"doctype": "Stock Ledger Entry",
					"is_query_report": True,
					"label": "Greige Stock Ledger",
					"name": "Greige Stock Ledger",
					"onboard": 1,
					"type": "report"
				},
				{
					"doctype": "Stock Ledger Entry",
					"is_query_report": True,
					"label": "Greige Batch-Wise Balance History",
					"name": "Greige Batch-Wise Balance History",
					"onboard": 1,
					"type": "report"
				},
				{
					"doctype": "Stock Ledger Entry",
					"is_query_report": True,
					"label": "Greige Design-Wise Balance History",
					"name": "Greige Design-Wise Balance History",
					"onboard": 1,
					"type": "report"
				},
				{
					"doctype": "Process Order",
					"is_query_report": 1,
					"label": "LOT-Wise Production Summary",
					"name": "LOT-Wise Production Summary",
					"onboard": 1,
					"type": "report"
				}
			]
		}
	]
