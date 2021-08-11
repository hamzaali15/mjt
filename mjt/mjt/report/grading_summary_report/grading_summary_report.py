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
			r.name,
			r.received_qty,
			r.short_length,
			r.return_qty,
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

		result = frappe.db.sql(query,as_dict=True)
		data = []
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
			total_return_qty = 0
			if row.return_qty:
				total_return_qty = row.return_qty

			row = {
				"batch_no": row.batch_no,
				"receiving_form": row.name,
				"received_meter": row.received_qty,
				"short_length": row.short_length,
				"return_qty": row.return_qty,
				"balance": received_qty - total_grading_meter - short_length - total_return_qty,
				"grading_meter": row.total_grading_meter,
				"fabric_meter": row.total_fabric_meter,
				"mending_meter": row.total_mending_meter,
				"rejection_meter": row.total_rejection_meter
			}
			data.append(row)
		return data
	else:
		return []
