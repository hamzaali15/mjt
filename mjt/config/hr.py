from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Attendance"),
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Attendance Check IN And OUT Summary",
					"doctype": "Attendance"
				},
			]
		}
	]
