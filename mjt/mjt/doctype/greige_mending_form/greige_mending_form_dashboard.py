from __future__ import unicode_literals
from frappe import _

def get_data():
    return {
        'fieldname': 'greige_mending_form',
        'transactions': [
            {
                'label': _('Purchase Receipt'),
                'items': ['Purchase Receipt']
            }
        ]
    }