# Copyright (c) 2013, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import frappe, erpnext
from erpnext import get_company_currency, get_default_company
from erpnext.accounts.report.utils import get_currency, convert_to_presentation_currency
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.report.financial_statements import get_cost_centers_with_children
from six import iteritems
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions, get_dimension_with_children
from collections import OrderedDict

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		{
			"fieldname": "batch_no",
			"fieldtype": "Link",
			"label": "Batch No",
			"options": "Batch",
			"width": 90
		},
		{
			"fieldname": "customer_name",
			"fieldtype": "Read Only",
			"label": "Party Name",
			"width": 200
		},
		{
			"fieldname": "quality_name",
			"fieldtype": "Read Only",
			"label": "Quality Name",
			"width": 200
		},
		{
			"fieldname": "total_mending_meter",
			"fieldtype": "Float",
			"label": "Mending Meters",
			"width": 120
		},
		{
			"fieldname": "total_rejection_meter",
			"fieldtype": "Float",
			"label": "Rejection Meter",
			"width": 120
		},
		{
			"fieldname": "total_net_mending_meter",
			"fieldtype": "Float",
			"label": "Net Mending Meters",
			"width": 140
		}
	]
	return columns

def get_data(filters):
	if filters.get('company'):
		query = """select 
			m.batch_no,
			m.customer_name,
			m.quality_name,
			m.total_mending_meter,
			m.total_rejection_meter,
			m.total_net_mending_meter
			from `tabGreige Mending Form` as m
			where m.batch_no is not null and m.docstatus = 1 and m.company = '{0}'""".format(filters.get('company'))

		if filters.get('from_date'):
			query += " and m.date >= '{0}'".format(filters.get('from_date'))

		if filters.get('to_date'):
			query += " and m.date <= '{0}'".format(filters.get('to_date'))

		if filters.get('quality_code'):
			query += " and m.quality_code = '{0}'".format(filters.get('quality_code'))

		if filters.get('customer_code'):
			query += " and m.customer_code = '{0}'".format(filters.get('customer_code'))

		result = frappe.db.sql(query,as_dict=True)
		data = []

		for row in result:
			row = {
				"batch_no": row.batch_no,
				"customer_name": row.customer_name,
				"quality_name": row.quality_name,
				"total_mending_meter": row.total_mending_meter,
				"total_rejection_meter": row.total_rejection_meter,
				"total_net_mending_meter": row.total_net_mending_meter
			}
			data.append(row)
		return data
	else:
		return []