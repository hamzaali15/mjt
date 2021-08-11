# Copyright (c) 2013, earthians and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

sec_lst = ['Pre Printing', 'Dyeing', 'Printing', 'Post Printing']
def get_columns():
	columns = [
		{
			"fieldname": "department",
			"fieldtype": "Link",
			"label": "Department",
			"options": "Manufacturing Department",
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
			"fieldname": "quality_code",
			"fieldtype": "Link",
			"label": "Quality Code",
			"options": "Quality",
			"width": 150
		},
		{
			"fieldname": "quality_name",
			"fieldtype": "Data",
			"label": "Quality Name",
			"width": 150
		},
		{
			"fieldname": "lot_no",
			"fieldtype": "Link",
			"label": "Lot No",
			"options": "Batch",
			"width": 150
		},
		# {
		# 	"fieldname": "design_no",
		# 	"fieldtype": "Data",
		# 	"label": "Design No",
		# 	"width": 150
		# },
		# {
		# 	"fieldname": "design_name",
		# 	"fieldtype": "Data",
		# 	"label": "Design Name",
		# 	"width": 150
		# },
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
		},
		{
			"fieldname": "material_cost",
			"fieldtype": "Float",
			"label": "Direct Material Cost",
			"width": 140
		},
		{
			"fieldname": "material_cost_unit",
			"fieldtype": "Float",
			"label": "Direct Material Cost Per Unit",
			"width": 140
		},
		{
			"fieldname": "labor_cost",
			"fieldtype": "Float",
			"label": "Direct Labor Cost",
			"width": 140
		},
		{
			"fieldname": "labor_cost_unit",
			"fieldtype": "Float",
			"label": "Direct Labor Cost Per Unit",
			"width": 140
		},
		{
			"fieldname": "foh_applied",
			"fieldtype": "Float",
			"label": "FOH Applied",
			"width": 140
		},
		{
			"fieldname": "foh_applied_unit",
			"fieldtype": "Float",
			"label": "FOH Applied Per Unit",
			"width": 140
		}
	]
	return columns

def get_data(filters):
	lst = []
	query = """select department, quality_code, quality_name,
			lot_no,
			party_code,party_name,
			sum(in_qty) as in_qty,
			sum(out_qty) as out_qty,
			sum(shortage) as shortage,
			sum(direct_material_cost) as direct_material_cost,
			sum(direct_labor_cost) as direct_labor_cost,
			sum(foh_applied) as foh_applied
			from `tabProcess Order Ledger`
			where is_cancelled = 0 """

	if filters.get('from_date'):
		query += " and posting_date >= '{0}'".format(filters.get('from_date'))
	if filters.get('to_date'):
		query += " and posting_date <= '{0}'".format(filters.get('to_date'))
	if filters.get('company'):
		query += " and company = '{0}'".format(filters.get('company'))
	if filters.get('lot'):
		query += " and lot_no like '{0}'".format(filters.get('lot'))
	if filters.get('department'):
		query += " and department = '{0}'".format(filters.get('department'))
	if filters.get('quality_code'):
		query += " and quality_code = '{0}'".format(filters.get('quality_code'))

	query += """ group by department,quality_name,lot_no,
				party_code,party_name"""
	result2 = frappe.db.sql(query, as_dict=True)
	for res in result2:
		lst.append({
			"lot_no": res.lot_no,
			"department": res.department,
			"party_code": res.party_code,
			"supplier_name": res.party_name,
			"quality_code": res.quality_code,
			"quality_name": res.quality_name,
			"process_name": res.process_name,
			# "design_no": res.design_no,
			# "design_name": res.design_name,
			"in_qty": res.in_qty,
			"out_qty": res.out_qty,
			"shortage": res.shortage,
			"shortage_per": ((res.shortage) * 100) / res.in_qty if res.in_qty else 0,
			"material_cost": res.direct_material_cost,
			"material_cost_unit": res.direct_material_cost / res.out_qty if res.out_qty else 0,
			"labor_cost": res.direct_labor_cost,
			"labor_cost_unit": res.direct_labor_cost / res.out_qty if res.out_qty else 0,
			"foh_applied": res.foh_applied,
			"foh_applied_unit": res.foh_applied / res.out_qty if res.out_qty else 0
		})
	return lst