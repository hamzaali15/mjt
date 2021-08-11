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
			"fieldname": "grading_form",
			"fieldtype": "Link",
			"label": "ID",
			"options": "Greige Grading Form",
			"width": 70
		},
		{
			"fieldname": "date",
			"fieldtype": "Date",
			"label": "Date",
			"options": "Greige Grading Form",
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
			"fieldname": "grading_meter",
			"fieldtype": "Float",
			"label": "Grading Meters",
			"width": 120
		},
		{
			"fieldname": "fabric_meter",
			"fieldtype": "Float",
			"label": "Grading Shortage Meters",
			"width": 120
		},
		{
			"fieldname": "net_grading_meter",
			"fieldtype": "Float",
			"label": "Net Grading Meters",
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
			g.name,
			g.date,
			g.batch_no,
			g.customer_name,
			g.quality_name,
			gc.grading_meter,
			gc.fabric_meter,
			gc.net_grading_meter,
			g.remarks
			from `tabGreige Grading Form` as g
			INNER JOIN `tabGreige Grading Child` as gc on g.name = gc.parent
			where g.batch_no is not null and g.docstatus = 1 and g.company = '{0}'""".format(filters.get('company'))

		if filters.get('from_date'):
    			query += " and g.date >= '{0}'".format(filters.get('from_date'))

		if filters.get('to_date'):
			query += " and g.date <= '{0}'".format(filters.get('to_date'))

		if filters.get('quality_code'):
			query += " and g.quality_code = '{0}'".format(filters.get('quality_code'))

		if filters.get('customer_code'):
			query += " and g.customer_code = '{0}'".format(filters.get('customer_code'))

		if filters.get("group_by") == _("Group by Party"):
			query += "order by customer_name, date"

		if filters.get("group_by") == _("Group by Date"):
			query += "order by date"

		if filters.get("group_by") == _("Group by Quality"):
			query += "order by quality_name"

		result = frappe.db.sql(query,as_dict=True)
		data = []

		tgqty = 0
		fshort = 0
		tngmeters = 0
		current_value= ""
		previous_value=""
		cur_pre_val=""		
		grading_meters = 0
		total_fabric_meters = 0
		net_grading_meters = 0
		i=len(result)

		def subTotal():
			total_row = {
				"receiving_form": "",
				"date": "",
				"batch_no": "",
				"customer_name": "",
				"quality_name": "<b>"+"Sub Total"+"</b>",
				"grading_meter": grading_meters,
				"fabric_meter": total_fabric_meters,
				"net_grading_meter": net_grading_meters,
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
				"grading_meter": tgqty,
				"fabric_meter": fshort,
				"net_grading_meter": tngmeters,
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
				grading_meters += row.grading_meter	
				net_grading_meters += row.net_grading_meter
				total_fabric_meters += row.fabric_meter

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
					grading_meters = row.grading_meter
					net_grading_meters = row.net_grading_meter
					total_fabric_meters = row.fabric_meter	
			
			tgqty += row.grading_meter
			fshort += row.fabric_meter
			tngmeters += row.net_grading_meter

			row = {
				"grading_form": row.name,
				"date": row.date,
				"batch_no": row.batch_no,
				"customer_name": row.customer_name,
				"quality_name": row.quality_name,
				"grading_meter": row.grading_meter,
				"fabric_meter": row.fabric_meter,
				"net_grading_meter": row.net_grading_meter,
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