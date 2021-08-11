from __future__ import unicode_literals
from frappe import _

def get_data():
    return {
        'fieldname': 'greige_receiving_form',
        'transactions': [
            {
                'label': _('Greige Grading Form'),
                'items': ['Greige Grading Form']
            }
        ]
    }