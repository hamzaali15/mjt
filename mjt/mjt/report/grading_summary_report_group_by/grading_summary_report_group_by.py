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
			"width": 170
		},
		{
			"fieldname": "receiving_form",
			"fieldtype": "Link",
			"label": "Greige Receiving Form",
			"options": "Greige Receiving Form",
			"width": 170
		},
		{
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"label": "Party Name",
			"width": 150
		},
		{
			"fieldname": "quality_name",
			"fieldtype": "Data",
			"label": "Quality Name",
			"width": 150
		},
		{
			"fieldname": "received_meter",
			"fieldtype": "Float",
			"label": "Received Meter",
			"width": 150
		},
		{
			"fieldname": "short_length",
			"fieldtype": "Float",
			"label": "Short Length",
			"width": 150
		},
		{
			"fieldname": "return_qty",
			"fieldtype": "Float",
			"label": "Return Qty",
			"width": 150
		},
		{
			"fieldname": "balance",
			"fieldtype": "Float",
			"label": "Balance of Greige Fabric",
			"width": 150
		},
		{
			"fieldname": "grading_meter",
			"fieldtype": "Float",
			"label": "Grading Meter",
			"width": 150
		},
		{
			"fieldname": "fabric_meter",
			"fieldtype": "Float",
			"label": "Grading Shortage Meter",
			"width": 150
		},
		{
			"fieldname": "mending_meter",
			"fieldtype": "Float",
			"label": "Mending Meter",
			"width": 150
		},
		{
			"fieldname": "rejection_meter",
			"fieldtype": "Float",
			"label": "Rejection Meter",
			"width": 150
		}
	]
	return columns

def get_data(filters):
	if filters.get('company'):
		query = """select 
			r.batch_no,
			r.customer_name,
			r.quality_name,
			r.name,
			r.received_qty,
			r.short_length,
			r.return_qty,
			r.date,
			g.total_grading_meter,
			g.total_fabric_meter,
			m.total_mending_meter,
			m.total_rejection_meter
			from `tabGreige Receiving Form` as r
			left join `tabGreige Grading Form` as g on g.greige_receiving_form = r.name
			left join `tabGreige Mending Form` as m on m.greige_grading_form = g.name
			where r.batch_no is not null and r.docstatus = 1 and r.company = '{0}'""".format(filters.get('company'))

		if filters.get('batch_no'):
			query += " and r.batch_no = '{0}'".format(filters.get('batch_no'))

		if filters.get('receiving_form'):
			query += " and r.name = '{0}'".format(filters.get('receiving_form'))

		if filters.get('from_date'):
			query += " and r.date >= '{0}'".format(filters.get('from_date'))

		if filters.get('to_date'):
			query += " and r.date <= '{0}'".format(filters.get('to_date'))

		if filters.get("group_by") == _("Group by Party"):
			query += "order by customer_name, date"

		if filters.get("group_by") == _("Group by Date"):
			query += "order by date"

		if filters.get("group_by") == _("Group by Quality"):
			query += "order by quality_name"

		result = frappe.db.sql(query,as_dict=True)
		data = []

		total_received_qty = 0
		total_short_length = 0
		total_return_qty = 0
		total_balance = 0
		total_grading_meter1 = 0
		total_fabric_meter1 = 0
		total_mending_meter1 = 0
		total_rejection_meter1 = 0
		current_value= ""
		previous_value=""
		cur_pre_val=""		
		total_received_qty1 = 0
		total_short_length1 = 0
		total_return_qty1 = 0
		total_balance1 = 0
		total_grading_meter2 = 0
		total_fabric_meter2 = 0
		total_mending_meter2 = 0
		total_rejection_meter2 = 0
		i=len(result)

		def subTotal():
			total_row = {
				"batch_no": "",
				"receiving_form": "",
				"customer_name": "",
				"quality_name": "<b>"+"Sub Total"+"</b>",
				"received_meter": total_received_qty1,
				"short_length": total_short_length1,
				"return_qty": total_return_qty1,
				"balance": total_balance1,
				"grading_meter": total_grading_meter2,
				"fabric_meter": total_fabric_meter2,
				"mending_meter": total_mending_meter2,
				"rejection_meter": total_rejection_meter2
			}
			data.append(total_row)

		def gTotal():
			total_row1 = {
				"batch_no": "",
				"receiving_form": "",
				"customer_name": "",
				"quality_name": "<b>"+"Grand Total"+"</b>",
				"received_meter": total_received_qty,
				"short_length": total_short_length,
				"return_qty": total_return_qty,
				"balance": total_balance,
				"grading_meter": total_grading_meter1,
				"fabric_meter": total_fabric_meter1,
				"mending_meter": total_mending_meter1,
				"rejection_meter": total_rejection_meter1
			}
			data.append(total_row1)

		for row in result:

			received_qty = 0
			if row.received_qty:
				received_qty = row.received_qty
			short_length = 0
			if row.short_length:
				short_length = row.short_length
			
			total_grading_meter = 0
			if row.total_grading_meter:
				total_grading_meter = row.total_grading_meter
			else:
				row.total_grading_meter = 0

			total_fabric_meter = 0
			if row.total_fabric_meter:
				total_fabric_meter = row.total_fabric_meter
			else:
				row.total_fabric_meter = 0

			total_rejection_meter = 0
			if row.total_rejection_meter:
				total_rejection_meter = row.total_rejection_meter
			else:
				row.total_rejection_meter = 0

			total_mending_meter = 0
			if row.total_mending_meter:
				total_mending_meter = row.total_mending_meter
			else:
				row.total_mending_meter = 0

			total_return_qty = 0
			if row.return_qty:
				total_return_qty = row.return_qty
			balance = 0
			balance = received_qty - total_grading_meter - short_length - total_return_qty


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
				total_received_qty1 += row.received_qty
				total_short_length1 += row.short_length
				total_return_qty1 += row.return_qty
				total_balance1 += balance
				total_grading_meter2 += row.total_grading_meter
				total_fabric_meter2 += row.total_fabric_meter
				total_mending_meter2 += row.total_mending_meter
				total_rejection_meter2 += row.total_rejection_meter
			
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
					total_received_qty1 = row.received_qty
					total_short_length1 = row.short_length
					total_return_qty1 = row.return_qty
					total_balance1 = balance
					total_grading_meter2 = row.total_grading_meter
					total_fabric_meter2 = row.total_fabric_meter
					total_mending_meter2 = row.total_mending_meter
					total_rejection_meter2 = row.total_rejection_meter
					
			total_received_qty += row.received_qty
			total_short_length += row.short_length
			total_return_qty += row.return_qty
			total_balance += balance
			total_grading_meter1 += row.total_grading_meter
			total_fabric_meter1 += row.total_fabric_meter
			total_mending_meter1 += row.total_mending_meter
			total_rejection_meter1 += row.total_rejection_meter
			
			row = {
				"batch_no": row.batch_no,
				"receiving_form": row.name,
				"customer_name": row.customer_name,
				"quality_name": row.quality_name,
				"received_meter": row.received_qty,
				"short_length": row.short_length,
				"return_qty": row.return_qty,
				"balance": balance,
				"grading_meter": row.total_grading_meter,
				"fabric_meter": row.total_fabric_meter,
				"mending_meter": row.total_mending_meter,
				"rejection_meter": row.total_rejection_meter
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
