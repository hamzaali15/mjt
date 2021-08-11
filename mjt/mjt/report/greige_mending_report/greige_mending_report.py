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
			"fieldname": "mending_form",
			"fieldtype": "Link",
			"label": "ID",
			"options": "Greige Mending Form",
			"width": 70
		},
		{
			"fieldname": "date",
			"fieldtype": "Date",
			"label": "Date",
			"options": "Greige Mending Form",
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
			"fieldname": "mending_meter",
			"fieldtype": "Float",
			"label": "Mending Meters",
			"width": 120
		},
		{
			"fieldname": "rejection_meter",
			"fieldtype": "Float",
			"label": "Rejection Meter",
			"width": 120
		},
		{
			"fieldname": "net_mending_meter",
			"fieldtype": "Float",
			"label": "Net Mending Meters",
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
			m.name,
			m.date,
			m.batch_no,
			m.customer_name,
			m.quality_name,
			mc.mending_meter,
			mc.rejection_meter,
			mc.net_mending_meter,
			m.remarks
			from `tabGreige Mending Form` as m
			INNER JOIN `tabGreige Mending Child` as mc on m.name = mc.parent
			where m.batch_no is not null and m.docstatus = 1 and m.company = '{0}'""".format(filters.get('company'))

		if filters.get('from_date'):
			query += " and m.date >= '{0}'".format(filters.get('from_date'))

		if filters.get('to_date'):
			query += " and m.date <= '{0}'".format(filters.get('to_date'))

		if filters.get('quality_code'):
			query += " and m.quality_code = '{0}'".format(filters.get('quality_code'))

		if filters.get('customer_code'):
			query += " and m.customer_code = '{0}'".format(filters.get('customer_code'))
		
		if filters.get("group_by") == _("Group by Party"):
			query += "order by customer_name, date"

		if filters.get("group_by") == _("Group by Date"):
			query += "order by date"

		if filters.get("group_by") == _("Group by Quality"):
			query += "order by quality_name"

		result = frappe.db.sql(query,as_dict=True)
		data = []

		tmqty = 0
		trejection = 0
		tnmmeters = 0
		current_value= ""
		previous_value=""
		cur_pre_val=""		
		mending_meters = 0
		rejection_meters = 0
		net_mending_meters = 0
		i=len(result)

		def subTotal():
			total_row = {
				"receiving_form": "",
				"date": "",
				"batch_no": "",
				"customer_name": "",
				"quality_name": "<b>"+"Sub Total"+"</b>",
				"mending_meter": mending_meters,
				"rejection_meter": rejection_meters,
				"net_mending_meter": net_mending_meters,
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
				"mending_meter": tmqty,
				"rejection_meter": trejection,
				"net_mending_meter": tnmmeters,
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
				mending_meters += row.mending_meter	
				net_mending_meters += row.net_mending_meter
				rejection_meters += row.rejection_meter

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
					mending_meters = row.mending_meter
					net_mending_meters = row.net_mending_meter
					rejection_meters = row.rejection_meter

			tmqty += row.mending_meter
			trejection += row.rejection_meter
			tnmmeters += row.net_mending_meter

			row = {
				"mending_form": row.name,
				"date": row.date,
				"batch_no": row.batch_no,
				"customer_name": row.customer_name,
				"quality_name": row.quality_name,
				"mending_meter": row.mending_meter,
				"rejection_meter": row.rejection_meter,
				"net_mending_meter": row.net_mending_meter,
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