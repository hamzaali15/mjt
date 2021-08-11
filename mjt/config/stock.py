from __future__ import unicode_literals
from frappe import _

def get_data():
    return [
        {
            "label": _("Textile"),
            "items": [
                {
                    "description": "Greige Setting",
                    "label": "Greige Setting",
                    "name": "Greige Setting",
                    "type": "doctype",
                    "onboard": 1
                },
                {
                    "description": "Fabric Ownership Transfer",
                    "label": "Fabric Ownership Transfer",
                    "name": "Fabric Ownership Transfer",
                    "type": "doctype",
                    "onboard": 1
                },
                {
                    "description": "Quality",
                    "label": "Quality",
                    "name": "Quality",
                    "type": "doctype",
                    "onboard": 1
                },
                {
                    "description": "Greige Receiving Form",
                    "label": "Greige Receiving Form",
                    "name": "Greige Receiving Form",
                    "type": "doctype",
                    "onboard": 1
                },
                {
                    "description": "Greige Grading Form",
                    "label": "Greige Grading Form",
                    "name": "Greige Grading Form",
                    "type": "doctype",
                    "onboard": 1
                },
                {
                    "description": "Greige Mending Form",
                    "label": "Greige Mending Form",
                    "name": "Greige Mending Form",
                    "type": "doctype",
                    "onboard": 1
                }
            ]
        }
    ]