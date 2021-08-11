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
			"width": 120
		},
		{
			"fieldname": "balance_g",
			"fieldtype": "Float",
			"label": "Balance of Greige Fabric",
			"width": 200
		},
		{
			"fieldname": "balance1",
			"fieldtype": "Float",
			"label": "Balance of Fresh Meters",
			"width": 200
		},
		{
			"fieldname": "balance2",
			"fieldtype": "Float",
			"label": "Balance of Rejection Meters",
			"width": 200
		},
		{
			"fieldname": "issue_wip",
			"fieldtype": "Float",
			"label": "Issue in WIP",
			"width": 150
		},
		{
			"fieldname": "sales_wip",
			"fieldtype": "Float",
			"label": "Out from WIP",
			"width": 150
		},
		{
			"fieldname": "wip_balance",
			"fieldtype": "Float",
			"label": "WIP Balance",
			"width": 150
		},
		{
			"fieldname": "balance_meters",
			"fieldtype": "Float",
			"label": "Balance Meters",
			"width": 150
		}
	]
	return columns

def get_data(filters):
	query = """select 
		b.name as batch_no,
		r.received_qty,
		r.short_length,
		r.return_qty,
		g.total_grading_meter,
		r.date,
		si.qty
		from `tabBatch` as b
		left join `tabGreige Receiving Form` as r on r.batch_no = b.name and r.docstatus = 1
		left join `tabGreige Grading Form` as g on g.greige_receiving_form = r.name
		left join `tabSales Invoice Item` as si on si.batch_no = b.name"""

	if filters.get('company') or filters.get('from_date') or filters.get('to_date'):
		query += " where "
	if filters.get('company'):
		query += " r.company = '{0}'".format(filters.get('company'))
		if filters.get('from_date') or filters.get('to_date'):
			query += " and "
	if filters.get('from_date'):
		query += " r.date >= '{0}'".format(filters.get('from_date'))
		if filters.get('to_date'):
			query += " and"
	if filters.get('to_date'):
		query += " r.date <= '{0}'".format(filters.get('to_date'))
	query += " group by b.name"
	
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
		balance_g = received_qty - total_grading_meter - short_length - total_return_qty
		

		batch_like = str(row['batch_no'])
		query1 = """select 
				sum(s1.actual_qty) as acqty
				from `tabStock Ledger Entry` as s1
				where s1.batch_no = '{0}' and s1.warehouse = 'Greige Fresh - MF' """.format(batch_like)

		result3 = frappe.db.sql(query1, as_dict=True)

		for row1 in result3:
			acqty = 0
			if row1.acqty:
				acqty = row1.acqty
		query2 = """select 
				sum(s2.actual_qty) as acqty1
				from `tabStock Ledger Entry` as s2
				where s2.batch_no = '{0}' and s2.warehouse = 'Greige Rejection - MF' """.format(batch_like)
		result4 = frappe.db.sql(query2, as_dict=True)
		for row2 in result4:
			acqty1 = 0
			if row2.acqty1:
				acqty1 = row2.acqty1
		query3 = """select 
				sum(sed.qty) as qty
				from `tabStock Entry` as se
				INNER JOIN `tabStock Entry Detail` as sed on se.name = sed.parent
				where sed.batch_no = '{0}' and sed.batch_no not like '%-%' and se.stock_entry_type = 'Material Transfer' and sed.s_warehouse = 'Greige Fresh - MF' """.format(batch_like)
		result5 = frappe.db.sql(query3, as_dict=True)
		for row3 in result5:
			transfer_qty = 0
			if row3.qty:
				transfer_qty = row3.qty
			qty = 0
			if row.qty:
				qty = row.qty
			wip_balance = transfer_qty - qty
			balance_meters = balance_g + acqty + acqty1 + wip_balance
			row3 = {
				"batch_no": row.batch_no,
				"balance_g": balance_g,
				"balance1": row1.acqty,
				"balance2": row2.acqty1,
				"issue_wip": row3.qty,
				"sales_wip": row.qty,
				"wip_balance": wip_balance,
				"balance_meters": balance_meters
			}
			data.append(row3)
	return data