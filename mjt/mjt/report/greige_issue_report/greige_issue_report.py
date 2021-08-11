# Copyright (c) 2013, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		{
			"fieldname": "name",
			"fieldtype": "Link",
			"label": "ID",
			"options": "Stock Entry",
			"width": 170
		},
		{
			"fieldname": "docstatus",
			"fieldtype": "Link",
			"label": "Status",
			"options": "Stock Entry",
			"width": 150
		},
		{
			"fieldname": "kiar_no",
			"fieldtype": "Data",
			"label": "Kiar No.",
			"width": 100
		},
		{
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Posting Date",
			"width": 150
		},
		{
			"fieldname": "batch_no",
			"fieldtype": "Link",
			"label": "Batch No.",
			"options": "Batch",
			"width": 150
		},
		{
			"fieldname": "party_name",
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
			"fieldname": "qty",
			"fieldtype": "Float",
			"label": "QTY",
			"width": 100
		},
		{
			"fieldname": "t_warehouse",
			"fieldtype": "Link",
			"label": "Item Target Warehouse",
			"options": "Warehouse",
			"width": 200
		}
	]
	return columns

def get_data(filters):
	if filters.get('company'):
		query = """select 
			se.name,
			se.docstatus,
			se.kiar_no,
			se.posting_date,
			sed.batch_no,
			sed.party_name,
			sed.quality_name,
			sed.qty,
			sed.t_warehouse
			from `tabStock Entry` as se
			INNER JOIN `tabStock Entry Detail` as sed on se.name = sed.parent
			where sed.batch_no is not null and se.kiar_no is not null and se.kiar_no > 0 and se.docstatus = 1 and se.company = '{0}'""".format(filters.get('company'))

		if filters.get('from_date'):
			query += " and se.posting_date >= '{0}'".format(filters.get('from_date'))

		if filters.get('to_date'):
			query += " and se.posting_date <= '{0}'".format(filters.get('to_date'))

		result = frappe.db.sql(query,as_dict=True)
		data = []
		for row in result:
			row = {
				"name": row.name,
				"docstatus": "Submitted",
				"kiar_no": row.kiar_no,
				"posting_date": row.posting_date,
				"batch_no": row.batch_no,
				"party_name": row.party_name,
				"quality_name": row.quality_name,
				"qty": row.qty,
				"t_warehouse": row.t_warehouse
			}
			data.append(row)
		return data
	else:
		return []