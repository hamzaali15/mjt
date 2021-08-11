# -*- coding: utf-8 -*-
# Copyright (c) 2021, earthians and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class ProcessOrderLedger(Document):
	pass

def delete_all_process_order_ledger():
	frappe.db.sql("""delete from `tabProcess Order Ledger`""")

def make_entry_schedular():
	process_orders = frappe.get_all('Process Order', filters={'status': "Completed"}, fields=['name'])
	for order in process_orders:
		if not frappe.db.exists("Process Order Ledger", {"process_order": order.name}):
			make_entry(order.name)

def make_process_order_ledger(obj, method):
	if obj.doctype == 'Stock Entry':
		if obj.process_order and obj.stock_entry_type == 'Manufacture':
			make_entry(obj.process_order)
	else:
		if obj.process_order:
			make_entry(obj.process_order)

def make_entry(process_order):
	if process_order:
		order_id = frappe.get_doc("Process Order", process_order)
		query = """select 
					tpi.lot_no as lot_no
					from `tabProcess Order` as tp
					inner join `tabProcess Order Item` as tpi on tp.name = tpi.parent				
					where tpi.lot_no is not null and tp.docstatus = 1 and tpi.parent = '{0}'""".format(process_order)
		result = frappe.db.sql(query, as_dict=True)
		lot_lst = []
		for r in result:
			if r['lot_no']:
				lot_no = str(r['lot_no'].split("-")[0])
				lot_lst.append(lot_no)
		total_m_cost = 0.0
		if not order_id.is_subcontracting:
			total_m_cost = frappe.db.sql("""select ifnull(sum(sed.basic_amount),0) as total_m_cost from `tabStock Entry Detail` sed
								inner join `tabStock Entry` as se on se.name = sed.parent
								where se.stock_entry_type = 'Manufacture' and se.process_order = %s
								and sed.batch_no is null 
								and sed.t_warehouse is null""",(order_id.name))[0][0]
		if lot_lst:
			for r in set(lot_lst):
				lot_like = "%" + r + "%"
				query = """select 
						tpi.lot_no as lot_no,
						tp.department as department,
						tpi.party_name as party_code,
						ts.supplier_name as supplier_name,
						tpi.quality_code as quality_code,
						tpi.quality_name as quality_name,
						tp.process_name as process_name,
						tpi.design_no as design,
						d.design as design_name,
						sum(tpi.quantity) as in_qty,
						0 as out_qty
						from `tabProcess Order` as tp
						left join `tabProcess Order Item` as tpi on tp.name = tpi.parent				
						left join `tabSupplier` as ts on ts.name = tpi.party_name
						left join `tabDesign` as d on d.name = tpi.design_no
						where tpi.lot_no like '{0}' and tpi.lot_no is not null and tpi.party_name is not null 
						and tp.docstatus = 1 and tp.name = '{1}' 
						group by tp.department,tpi.party_name,
						tpi.quality_name,tpi.design_no
						order by tpi.lot_no,tp.department
						""".format(lot_like, process_order)
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
						and tp.name = '{4}'						
						and tp.docstatus = 1""".format(lot_like, res.department, res.quality_code, res.party_code, process_order)
					if res.design:
						query2 += " and tpfi.design_no = '{0}' ".format(res.design)
					else:
						query2 += " and tpfi.design_no is null"

					result3 = frappe.db.sql(query2, as_dict=True)
					if result3:
						if result3[0].out_qty:
							res['out_qty'] = result3[0].out_qty

					ledger_entry = frappe.new_doc("Process Order Ledger")
					ledger_entry.process_order = process_order
					ledger_entry.department = res.department
					ledger_entry.lot_no = r
					ledger_entry.posting_date = order_id.date
					ledger_entry.business_unit = order_id.business_unit
					ledger_entry.company = order_id.company
					ledger_entry.quality_code = res.quality_code
					ledger_entry.quality_name = res.quality_name
					ledger_entry.party_code = res.party_code
					ledger_entry.party_name = res.supplier_name
					ledger_entry.design_no = res.design
					ledger_entry.design_name = res.design_name
					ledger_entry.in_qty = res.in_qty
					ledger_entry.out_qty = res.out_qty
					ledger_entry.shortage = res.out_qty - res.in_qty

					total_material_cost = foh_applied = labor_cost = 0
					total_finish_qty = frappe.db.sql(
						"""select ifnull(sum(quantity),0) as qty from `tabProcess Order Finish Item` where parent = '{0}'""".format(
							process_order))[0][0]
					if order_id.workstation:
						if order_id.base_on == 'Operation Cost':
							hourly_rate = frappe.db.get_value("Workstation", order_id.workstation, "hour_rate")
							electricity_cost = frappe.db.get_value("Workstation", order_id.workstation, "hour_rate_electricity")
							consumable_cost = frappe.db.get_value("Workstation", order_id.workstation, "hour_rate_consumable")
							rent_cost = frappe.db.get_value("Workstation", order_id.workstation, "hour_rate_rent")
							wages = frappe.db.get_value("Workstation", order_id.workstation, "hour_rate_labour")

							foh_sum = electricity_cost + consumable_cost + rent_cost
							foh = foh_sum * order_id.operation_hours
							foh_applied = float(foh / total_finish_qty) * res.out_qty
							labor_cost = float(wages / total_finish_qty) * res.out_qty

						if order_id.base_on == 'Production Cost':
							hourly_rate = frappe.db.get_value("Workstation", order_id.workstation, "p_net_hour_rate")
							electricity_cost = frappe.db.get_value("Workstation", order_id.workstation, "p_electricity_cost")
							consumable_cost = frappe.db.get_value("Workstation", order_id.workstation, "p_consumable_cost")
							rent_cost = frappe.db.get_value("Workstation", order_id.workstation, "p_rent_cost")
							wages = frappe.db.get_value("Workstation", order_id.workstation, "p_wages")

							foh = electricity_cost + consumable_cost + rent_cost
							foh_applied = foh * res.out_qty
							labor_cost = wages * res.out_qty

						ledger_entry.foh_applied = foh_applied
						ledger_entry.direct_labor_cost = labor_cost
					total_material_cost = float(total_m_cost / total_finish_qty) * res.out_qty
					ledger_entry.direct_material_cost = total_material_cost
					ledger_entry.insert(ignore_permissions=True)