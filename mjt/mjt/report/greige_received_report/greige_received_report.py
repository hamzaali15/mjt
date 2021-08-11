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
			"fieldname": "receiving_form",
			"fieldtype": "Link",
			"label": "ID",
			"options": "Greige Receiving Form",
			"width": 70
		},
		{
			"fieldname": "date",
			"fieldtype": "Date",
			"label": "Date",
			"options": "Greige Receiving Form",
			"width": 90
		},
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
			"fieldname": "than",
			"fieldtype": "Float",
			"label": "Than",
			"width": 70
		},
		{
			"fieldname": "received_qty",
			"fieldtype": "Float",
			"label": "Received Meters",
			"width": 120
		},
		{
			"fieldname": "short_length",
			"fieldtype": "Float",
			"label": "Length Short",
			"width": 120
		},
		{
			"fieldname": "net_received_meter",
			"fieldtype": "Float",
			"label": "Net Received Meters",
			"width": 140
		},
		{
			"fieldname": "remarks",
			"fieldtype": "Text",
			"label": "Remarks",
			"width": 140
		}
	]
	return columns

def get_data(filters):
	if filters.get('company'):
		query = """select 
			r.name,
			r.date,
			r.batch_no,
			r.customer_name,
			r.quality_name,
			r.than,
			r.received_qty,
			r.short_length,
			r.net_received_meter,
			r.remarks
			from `tabGreige Receiving Form` as r
			where r.batch_no is not null and r.docstatus = 1 and r.company = '{0}'""".format(filters.get('company'))

		if filters.get('from_date'):
			query += " and r.date >= '{0}'".format(filters.get('from_date'))

		if filters.get('to_date'):
			query += " and r.date <= '{0}'".format(filters.get('to_date'))

		if filters.get('quality_code'):
			query += " and r.quality_code = '{0}'".format(filters.get('quality_code'))

		if filters.get('customer_code'):
			query += " and r.customer_code = '{0}'".format(filters.get('customer_code'))

		if filters.get("group_by") == _("Group by Party"):
			query += "order by customer_name, date"

		if filters.get("group_by") == _("Group by Date"):
			query += "order by date"

		if filters.get("group_by") == _("Group by Quality"):
			query += "order by quality_name"

		result = frappe.db.sql(query,as_dict=True)
		data = []

		tthan = 0
		trqty = 0
		tsleng = 0
		tnrmeters = 0
		current_value= ""
		previous_value=""
		cur_pre_val=""		
		received_meters = 0
		net_received_meters = 0
		total_than = 0
		total_short_length = 0
		i=len(result)

		def subTotal():
			total_row = {
				"receiving_form": "",
				"date": "",
				"batch_no": "",
				"customer_name": "",
				"quality_name": "<b>"+"Sub Total"+"</b>",
				"than": total_than,
				"received_qty": received_meters,
				"short_length": total_short_length,
				"net_received_meter": net_received_meters,
				"remarks": " "
			}
			data.append(total_row)

		def gTotal():
			total_row1 = {
				"receiving_form": "",
				"date": "",
				"batch_no": "",
				"customer_name": "",
				"quality_name": "<b>"+"Grand Total"+"</b>",
				"than": tthan,
				"received_qty": trqty,
				"short_length": tsleng,
				"net_received_meter": tnrmeters,
				"remarks": ""
			}
			data.append(total_row1)

		for row in result:
			i=i-1
			if filters.get("group_by") == _("Group by Party"):
				current_value = row.customer_name
				if(cur_pre_val != ""):
					if(cur_pre_val != current_value):
						previous_value = cur_pre_val
				if(previous_value == ""):
					previous_value = row.customer_name

			if filters.get("group_by") == _("Group by Date"):
				current_value = row.date
				if(cur_pre_val != ""):
					if(cur_pre_val != current_value):
						previous_value = cur_pre_val
				if(previous_value == ""):
					previous_value = row.date

			if filters.get("group_by") == _("Group by Quality"):
				current_value = row.quality_name
				if(cur_pre_val != ""):
					if(cur_pre_val != current_value):
						previous_value = cur_pre_val
				if(previous_value == ""):
					previous_value = row.quality_name	

			if(current_value == previous_value):
				received_meters += row.received_qty	
				net_received_meters += row.net_received_meter
				total_than += row.than
				total_short_length += row.short_length

			if(current_value != "" and previous_value != ""):
				if(current_value != previous_value):
					subTotal()
					previous_value = ""
					if filters.get("group_by") == _("Group by Party"):
						cur_pre_val=row.customer_name
					if filters.get("group_by") == _("Group by Date"):
						cur_pre_val=row.date
					if filters.get("group_by") == _("Group by Quality"):
						cur_pre_val=row.quality_name
					received_meters = row.received_qty
					net_received_meters = row.net_received_meter
					total_than = row.than
					total_short_length = row.short_length	

			tthan += row.than
			trqty += row.received_qty
			tsleng += row.short_length
			tnrmeters += row.net_received_meter

			row = {
				"receiving_form": row.name,
				"date": row.date,
				"batch_no": row.batch_no,
				"customer_name": row.customer_name,
				"quality_name": row.quality_name,
				"than": row.than,
				"received_qty": row.received_qty,
				"short_length": row.short_length,
				"net_received_meter": row.net_received_meter,
				"remarks": row.remarks
			}
			data.append(row)
			if(i==0):
				if filters.get("group_by"):
					subTotal()
					gTotal()
				else:
					gTotal()
		return data
	else:
		return []