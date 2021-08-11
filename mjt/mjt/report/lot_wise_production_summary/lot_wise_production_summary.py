# Copyright (c) 2013, earthians and contributors
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
			"fieldname": "lot_no",
			"fieldtype": "Link",
			"label": "Lot No",
			"options": "Batch",
			"width": 150
		},
		{
			"fieldname": "department",
			"fieldtype": "Link",
			"label": "Department",
			"options": "Manufacturing Department",
			"width": 150
		},
		{
			"fieldname": "quality_name",
			"fieldtype": "Data",
			"label": "Quality Name",
			"width": 150
		},
		{
			"fieldname": "party_code",
			"fieldtype": "Link",
			"label": "Party Code",
			"options": "Supplier",
			"width": 150
		},
		{
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"label": "Party Name",
			"width": 200,
			'fetch_from': 'party_code.supplier_name'
		},
		{
			"fieldname": "design_no",
			"fieldtype": "Link",
			"label": "Design No",
			"options": "Design",
			"width": 150
		},
		{
			"fieldname": "design_name",
			"fieldtype": "Data",
			"label": "Design Name",
			"width": 150
		},
		{
			"fieldname": "in_qty",
			"fieldtype": "Float",
			"label": "In Qty",
			"width": 100
		},
		{
			"fieldname": "out_qty",
			"fieldtype": "Float",
			"label": "Out Qty",
			"width": 100
		},
		{
			"fieldname": "shortage",
			"fieldtype": "Float",
			"label": "Over / Shortage",
			"width": 120
		},
		{
			"fieldname": "shortage_per",
			"fieldtype": "Float",
			"label": "Over / Shortage (%)",
			"width": 140
		}
	]
	return columns

def get_data(filters):
	lst = []
	query = """select 
			tpi.lot_no as lot_no
			from `tabProcess Order` as tp
			inner join `tabProcess Order Item` as tpi on tp.name = tpi.parent				
			where tpi.lot_no is not null and tp.docstatus = 1"""
	if filters.get('from_date'):
		query += " and tp.date >= '{0}'".format(filters.get('from_date'))
	if filters.get('to_date'):
		query += " and tp.date <= '{0}'".format(filters.get('to_date'))
	if filters.get('company'):
		query += " and tp.company = '{0}'".format(filters.get('company'))
	if filters.get('lot'):
		query += " and tpi.lot_no like '{0}'".format(filters.get('lot'))
	if filters.get('department'):
		query += " and tp.department = '{0}'".format(filters.get('department'))
	if filters.get('quality_code'):
		query += " and tpi.quality_code = '{0}'".format(filters.get('quality_code'))
	# query += """ group by tp.department,tpi.party_name,tpi.quality_name,tpi.design_no
	# 					order by tpi.lot_no,tp.department"""
	result = frappe.db.sql(query, as_dict=True)
	lot_lst = []
	for r in result:
		if r['lot_no']:
			lot_no = str(r['lot_no'].split("-")[0])
			lot_lst.append(lot_no)
	if lot_lst:
		for r in set(lot_lst):
			lot_like = "%" + r + "%"
			query = """select 
					tpi.lot_no as lot_no,
					tp.department as department,
					tpi.party_name as party_code,
					ts.supplier_name as supplier_name,
					tpi.quality_name as quality_name,
					tpi.quality_code as quality_code,
					tp.process_name as process_name,
					tpi.design_no as design,
					d.design as design_name,
					sum(tpi.quantity) as in_qty,
					0 as out_qty
					from `tabProcess Order` as tp
					left join `tabProcess Order Item` as tpi on tp.name = tpi.parent				
					left join `tabSupplier` as ts on ts.name = tpi.party_name
					left join `tabDesign` as d on d.name = tpi.design_no
					where tpi.lot_no like '{0}' and tpi.lot_no is not null and tpi.party_name is not null and tp.docstatus = 1""".format(lot_like)

			if filters.get('from_date'):
					query += " and tp.date >= '{0}'".format(filters.get('from_date'))
			if filters.get('to_date'):
					query += " and tp.date <= '{0}'".format(filters.get('to_date'))
			if filters.get('company'):
				query += " and tp.company = '{0}'".format(filters.get('company'))
			if filters.get('lot'):
				query += " and tpi.lot_no like '{0}'".format(filters.get('lot'))
			if filters.get('department'):
				query += " and tp.department = '{0}'".format(filters.get('department'))
			if filters.get('quality_code'):
				query += " and tpi.quality_code = '{0}'".format(filters.get('quality_code'))

			query += """ group by tp.department,tpi.party_name,tpi.quality_name,tpi.design_no
					order by tpi.lot_no,tp.department"""
			result2 = frappe.db.sql(query, as_dict=True)
			for res in result2:
				query2 = """select 							
							sum(tpfi.quantity) as out_qty
							from `tabProcess Order` as tp
							left join `tabProcess Order Finish Item` as tpfi on tp.name = tpfi.parent
							where tpfi.lot_no like '{0}' 
							and tp.department = '{1}' 
							and tpfi.quality_code = '{2}'
							and tpfi.party_name = '{3}'							
							and tp.docstatus = 1""".format(lot_like, res.department, res.quality_code, res.party_code)

				if filters.get('from_date'):
					query2 += " and tp.date >= '{0}'".format(filters.get('from_date'))
				if filters.get('to_date'):
					query2 += " and tp.date <= '{0}'".format(filters.get('to_date'))
				if filters.get('company'):
					query2 += " and tp.company = '{0}'".format(filters.get('company'))
				if res.design:
					query2 += " and tpfi.design_no = '{0}' ".format(res.design)
				else:
					query2 += " and tpfi.design_no is null"

				result3 = frappe.db.sql(query2, as_dict=True)
				if result3:
					if result3[0].out_qty:
						res['out_qty'] = result3[0].out_qty
				lst.append({
					"lot_no": r,
					"department": res.department,
					"party_code": res.party_code,
					"supplier_name": res.supplier_name,
					"quality_name": res.quality_name,
					"process_name": res.process_name,
					"design_no": res.design,
					"design_name": res.design_name,
					"in_qty": res.in_qty,
					"out_qty": res.out_qty,
					"shortage": res.out_qty - res.in_qty,
					"shortage_per": ((res.out_qty - res.in_qty) * 100) / res.in_qty if res.in_qty else 0
				})
		return lst