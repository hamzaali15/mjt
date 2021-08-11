from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'fabric_ownership_transfer',
		'transactions': [
			{
				'label': _('Journal Entry'),
				'items': ['Journal Entry']
			}
		]
	}
