# -*- coding: utf-8 -*-
# Copyright (c) 2018, earthians and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, time_diff_in_hours
from frappe import _
import json
from frappe.model.naming import make_autoname
from erpnext.stock.doctype.batch.batch import get_batch_qty

class ProcessOrder(Document):

	def validate(self):
		if self.is_subcontracting and not self.allow_scrap_rate:
			for res in self.get('scrap'):
				res.rate = 0

	def on_submit(self):
		if not self.wip_warehouse:
			frappe.throw(_("Work-in-Progress Warehouse is required before Submit"))
		if not self.fg_warehouse:
			frappe.throw(_("Target Warehouse is required before Submit"))
		if self.scrap and not self.scrap_warehouse:
			frappe.throw(_("Scrap Warehouse is required before submit"))
		frappe.db.set(self, 'status', 'Submitted')
		m_lst = []
		for m in self.materials:
			if m.design_no:
				m_lst.append(m.design_no)
		f_lst = []
		for f in self.finished_products:
			if f.design_no:
				f_lst.append(f.design_no)
		s_lst = []
		for s in self.scrap:
			if s.design_no:
				s_lst.append(s.design_no)
		if m_lst:
			for lst in f_lst:
				if lst not in m_lst:
					frappe.throw(_("Please select one of the material product designs only!"))
			for lst in s_lst:
				if lst not in m_lst:
					frappe.throw(_("Please select one of the material product designs only!"))

	def before_submit(self):
		for itm in self.materials:
			if frappe.db.get_value("Item", itm.item, "has_batch_no") == 1 and not itm.lot_no:
				frappe.throw(_("The selected item <b>{0}</b> is required the Lot no in Materials!").format(itm.item))

			if frappe.db.get_value("Item", itm.item, "has_design") == 1 and not itm.design_no:
				frappe.throw(_("The selected item <b>{0}</b> is required the Design No in Materials!").format(itm.item))

		for itm in self.finished_products:
			if frappe.db.get_value("Item", itm.item, "has_batch_no") == 1 and not itm.lot_no:
				frappe.throw(_("The selected item <b>{0}</b> is required the Lot no in Finish Product!").format(itm.item))

			if frappe.db.get_value("Item", itm.item, "has_design") == 1 and not itm.design_no:
				frappe.throw(_("The selected item <b>{0}</b> is required the Design No in Finish Product!").format(itm.item))

		for itm in self.scrap:
			if frappe.db.get_value("Item", itm.item, "has_batch_no") == 1 and not itm.lot_no:
				frappe.throw(_("The selected item <b>{0}</b> is required the Lot no in Scarp!").format(itm.item))

			if frappe.db.get_value("Item", itm.item, "has_design") == 1 and not itm.design_no:
				frappe.throw(_("The selected item <b>{0}</b> is required the Design No in Scarp!").format(itm.item))
		for m in self.materials:
			for f in self.finished_products:
				if m.row_no and f.row_no:
					if m.row_no == f.row_no:
						if m.design_no != f.design_no:
							frappe.throw(_("Row no {0} Design {1} Should be Same with Raw Material!").format(f.idx, f.design_no))

			for s in self.scrap:
				if m.row_no and s.row_no:
					if m.row_no == s.row_no:
						if m.design_no != s.design_no:
							frappe.throw(_("Row no {0} Design {1} Should be Same with Raw Material!").format(s.idx, s.design_no))

	def on_cancel(self):
		stock_entry = frappe.db.sql("""select name from `tabStock Entry`
			where process_order = %s and docstatus = 1""", self.name)
		if stock_entry:
			frappe.throw(_("Cannot cancel because submitted Stock Entry \
			{0} exists").format(stock_entry[0][0]))
		ledger_entries = frappe.get_list("Process Order Ledger",filters={'name': self.name}, fields=['name'])
		for res in ledger_entries:
			doc = frappe.get_doc("Process Order Ledger", res.name)
			doc.is_cancelled = 1
			doc.db_update()
		frappe.db.set(self, 'status', 'Cancelled')

	@frappe.whitelist()
	def get_process_details(self):
		#	Set costing_method
		self.costing_method = frappe.db.get_value("Process Definition", self.process_name, "costing_method")
		self.supplier_rate = frappe.db.get_value("Process Definition", self.process_name, "rate")
		#	Set Child Tables
		process = frappe.get_doc("Process Definition", self.process_name)
		if process:
			if process.materials:
				self.add_item_in_table(process.materials, "materials")
			if process.finished_products:
				self.add_item_in_table(process.finished_products, "finished_products")
			if process.scrap:
				self.add_item_in_table(process.scrap, "scrap")

	@frappe.whitelist()
	def start_finish_processing(self, status):
		if status == "In Process":
			if not self.end_dt:
				self.end_dt = get_datetime()
		self.flags.ignore_validate_update_after_submit = True
		self.save()
		if status == "In Process" and self.is_subcontracting:
			return self.make_purchase_receipt()
		else:
			return self.make_stock_entry(status)

	@frappe.whitelist()
	def add_additional_fabric(self, status):
		self.flags.ignore_validate_update_after_submit = True
		self.save()
		return self.make_add_fabric_stock_entry()

	@frappe.whitelist()
	def make_add_fabric_stock_entry(self):
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.process_order = self.name
		stock_entry.stock_entry_type = "Material Transfer for Manufacture"
		stock_entry.additional_fabric_qty = 1
		stock_entry = self.set_se_items_add_fabric(stock_entry)
		return stock_entry.as_dict()

	@frappe.whitelist()
	def set_se_items_add_fabric(self, se):
		#set source and target warehouse
		se.from_warehouse = self.src_warehouse
		se.to_warehouse = self.wip_warehouse
		for item in self.materials:
			if self.src_warehouse:
				src_wh = self.src_warehouse
			else:
				src_wh = frappe.db.get_value("Item Default", {'parent': item.item, 'company': self.company},\
					["default_warehouse"])
			#create stock entry lines
			se = self.set_additional_qty_se_items(se, item, src_wh, self.wip_warehouse, False)

		return se

	@frappe.whitelist()
	def set_se_items_start(self, se):
		#set source and target warehouse
		se.from_warehouse = self.src_warehouse
		se.to_warehouse = self.wip_warehouse
		for item in self.materials:
			if self.src_warehouse:
				src_wh = self.src_warehouse
			else:
				src_wh = frappe.db.get_value("Item Default", {'parent': item.item, 'company': self.company},\
					["default_warehouse"])
			#create stock entry lines
			se = self.set_se_items(se, item, src_wh, self.wip_warehouse, False)

		return se

	@frappe.whitelist()
	def set_se_items_finish(self, se):
		#set from and to warehouse
		se.from_warehouse = self.wip_warehouse
		se.to_warehouse = self.fg_warehouse

		se_materials = frappe.get_doc("Stock Entry",{"process_order": self.name, "docstatus": '1'})
		#get items to consume from previous stock entry or append to items
		#TODO allow multiple raw material transfer
		raw_material_cost = 0
		operating_cost = 0
		if se_materials:
			raw_material_cost = se_materials.total_incoming_value
		# 	print("--------raw_material_cost-",raw_material_cost)
		# 	se.items = se_materials.items
		# 	for item in se.items:
		# 		item.s_warehouse = se.from_warehouse
		# 		item.t_warehouse = None
		# else:
		for item in self.materials:
			basic_rate = None
			if se_materials:
				se_materials_line = frappe.get_doc("Stock Entry Detail", {"parent": se_materials.name, "item_code": item.item})
				basic_rate = se_materials_line.basic_rate
			se = self.set_se_items(se, item, se.from_warehouse, None, False, None, None, None, basic_rate)
			#TODO calc raw_material_cost

		#no timesheet entries, calculate operating cost based on workstation hourly rate and process start, end
		production_cost = 0
		if self.base_on == 'Operation Cost':
			hourly_rate = frappe.db.get_value("Workstation", self.workstation, "hour_rate")
			if hourly_rate:
				frappe.db.set(self, 'hour_rate', hourly_rate)
				if self.operation_hours:
					if self.operation_hours > 0:
						hours = self.operation_hours
					else:
						hours = time_diff_in_hours(self.end_dt, self.start_dt)
						frappe.db.set(self, 'operation_hours', hours)
				else:
					hours = time_diff_in_hours(self.end_dt, self.start_dt)
					frappe.db.set(self, 'operation_hours', hours)
				operating_cost = hours * float(hourly_rate)
			production_cost = operating_cost
			if production_cost:
				frappe.db.set(self, 'total_operation_cost', production_cost)
		
		elif self.base_on == 'Production Cost':
			hourly_rate = frappe.db.get_value("Workstation", self.workstation, "p_net_hour_rate")
			if hourly_rate:
				frappe.db.set(self, 'hour_rate', hourly_rate)
				total_pro_qty = 0
				for item in self.finished_products:
					if item.quantity:
						if item.quantity > 0:
							total_pro_qty += item.quantity
				production_cost = total_pro_qty * float(hourly_rate)
				if production_cost:
					frappe.db.set(self, 'total_additonal_production_cost', production_cost)
		
		#calc total_qty and total_sale_value
		qty_of_total_production = 0
		total_sale_value = 0
		for item in self.finished_products:
			if item.quantity:
				if item.quantity > 0:
					qty_of_total_production = float(qty_of_total_production) + item.quantity
					if self.costing_method == "Relative Sales Value":
						sale_value_of_pdt = frappe.db.get_value("Item Price", {"item_code":item.item}, "price_list_rate")
						if sale_value_of_pdt:
							total_sale_value += float(sale_value_of_pdt) * item.quantity
						else:
							frappe.throw(_("Selling price not set for item {0}").format(item.item))

		value_scrap = frappe.db.get_value("Process Definition", self.process_name, "value_scrap")
		if value_scrap:
			for item in self.scrap:
				if item.quantity:
					if item.quantity > 0:
						qty_of_total_production = float(qty_of_total_production + item.quantity)
						if self.costing_method == "Relative Sales Value":
							sale_value_of_pdt = frappe.db.get_value("Item Price", {"item_code":item.item}, "price_list_rate")
							if sale_value_of_pdt:
								total_sale_value += float(sale_value_of_pdt) * item.quantity
							else:
								frappe.throw(_("Selling price not set for item {0}").format(item.item))

		#add Stock Entry Items for produced goods and scrap
		add_total_qty = 0
		for item in self.finished_products:
			if item.quantity:
				add_total_qty += item.quantity
		for item in self.scrap:
			if item.quantity:
				add_total_qty += item.quantity

		for item in self.finished_products:
			se = self.set_se_items(se, item, None, se.to_warehouse, True, qty_of_total_production, total_sale_value, production_cost,None,add_total_qty,1)

		for item in self.scrap:
			if value_scrap:
				se = self.set_se_items(se, item, None, self.scrap_warehouse, True, qty_of_total_production, total_sale_value, production_cost,None,add_total_qty,None,1)
			else:
				se = self.set_se_items(se, item, None, self.scrap_warehouse, False, None, None, None, None,add_total_qty,None,1)
		
		self.add_additional_cost(se,production_cost)
		return se

	@frappe.whitelist()
	def add_additional_cost(self, se, production_cost):
		if production_cost:
			expenses_included_in_valuation = frappe.get_cached_value("Company", self.company,"expenses_included_in_valuation")
			se.append('additional_costs',{
				'expense_account':expenses_included_in_valuation,
				'description': 'Operation Cost',
				'amount':production_cost
			})

	@frappe.whitelist()
	def set_se_items(self, se, item, s_wh, t_wh, calc_basic_rate=False, qty_of_total_production=None, total_sale_value=None, production_cost=None, basic_rate=None,add_total_qty=0,is_finish_item=None,is_scrap_item=None):
		if item.quantity:
			if item.quantity > 0:
				expense_account, cost_center = frappe.db.get_values("Company", self.company, \
					["default_expense_account", "cost_center"])[0]
				item_name, stock_uom, description = frappe.db.get_values("Item", item.item, \
					["item_name", "stock_uom", "description"])[0]

				item_expense_account, item_cost_center = frappe.db.get_value("Item Default", {'parent': item.item, 'company': self.company},\
					["expense_account", "buying_cost_center"])

				if not expense_account and not item_expense_account:
					frappe.throw(_("Please update default Default Cost of Goods Sold Account for company {0}").format(self.company))

				if not cost_center and not item_cost_center:
					frappe.throw(_("Please update default Cost Center for company {0}").format(self.company))
				has_design = frappe.db.get_value("Item", item.item, "has_design")
				se_item = se.append("items")
				se_item.item_code = item.item
				se_item.qty = item.quantity
				se_item.s_warehouse = s_wh
				se_item.t_warehouse = t_wh
				se_item.item_name = item_name
				se_item.description = description
				se_item.uom = stock_uom
				se_item.stock_uom = stock_uom
				se_item.batch_no = item.lot_no
				se_item.design_no = item.design_no if has_design else None
				se_item.than = item.than if item.than else 0
				se_item.process_line = item.name
				if basic_rate:
					se_item.basic_rate = basic_rate
				else:
					se_item.allow_zero_valuation_rate = 1
				se_item.expense_account = item_expense_account or expense_account
				se_item.cost_center = item_cost_center or cost_center

				# in stock uom
				se_item.transfer_qty = item.quantity
				se_item.conversion_factor = 1.00

				#pass business unit
				se_item.business_unit = self.business_unit
				se_item.is_finished_item = is_finish_item
				se_item.is_scrap_item = is_scrap_item

				item_details = se.run_method( "get_item_details",args = (frappe._dict(
				{"item_code": item.item, "company": self.company, "uom": stock_uom, 's_warehouse': s_wh})), for_update=True)

				for f in ("uom", "stock_uom", "description", "item_name", "expense_account",
				"cost_center", "conversion_factor"):
					se_item.set(f, item_details.get(f))

				if calc_basic_rate:
					if add_total_qty:
						se_item.additional_cost = (production_cost / add_total_qty) * item.quantity
					
					if self.costing_method == "Physical Measurement":
						se_item.basic_rate = production_cost/qty_of_total_production

					elif self.costing_method == "Relative Sales Value":
						sale_value_of_pdt = frappe.db.get_value("Item Price", {"item_code":item.item}, "price_list_rate")
						se_item.basic_rate = (float(sale_value_of_pdt) * float(production_cost)) / float(total_sale_value)
		return se

	@frappe.whitelist()
	def set_additional_qty_se_items(self, se, item, s_wh, t_wh, calc_basic_rate=False, qty_of_total_production=None, total_sale_value=None, production_cost=None):
		if item.additional_qty:
			if item.additional_qty > 0:
				expense_account, cost_center = frappe.db.get_values("Company", self.company, \
					["default_expense_account", "cost_center"])[0]
				item_name, stock_uom, description = frappe.db.get_values("Item", item.item, \
					["item_name", "stock_uom", "description"])[0]

				item_expense_account, item_cost_center = frappe.db.get_value("Item Default", {'parent': item.item, 'company': self.company},\
					["expense_account", "buying_cost_center"])

				if not expense_account and not item_expense_account:
					frappe.throw(_("Please update default Default Cost of Goods Sold Account for company {0}").format(self.company))

				if not cost_center and not item_cost_center:
					frappe.throw(_("Please update default Cost Center for company {0}").format(self.company))
				has_design = frappe.db.get_value("Item", item.item, "has_design")
				se_item = se.append("items")
				se_item.item_code = item.item
				se_item.qty = item.additional_qty
				se_item.s_warehouse = s_wh
				se_item.t_warehouse = t_wh
				se_item.item_name = item_name
				se_item.description = description
				se_item.uom = stock_uom
				se_item.stock_uom = stock_uom
				se_item.batch_no = item.lot_no
				se_item.design_no = item.design_no if has_design else None
				se_item.than = item.than if item.than else 0
				se_item.process_line = item.name
				se_item.expense_account = item_expense_account or expense_account
				se_item.cost_center = item_cost_center or cost_center

				# in stock uom
				se_item.transfer_qty = item.additional_qty
				se_item.conversion_factor = 1.00
				
				#pass business unit
				se_item.business_unit = self.business_unit

				item_details = se.run_method( "get_item_details",args = (frappe._dict(
				{"item_code": item.item, "company": self.company, "uom": stock_uom, 's_warehouse': s_wh})), for_update=True)

				for f in ("uom", "stock_uom", "description", "item_name", "expense_account",
				"cost_center", "conversion_factor"):
					se_item.set(f, item_details.get(f))

				if calc_basic_rate:
					if self.costing_method == "Physical Measurement":
						se_item.basic_rate = production_cost/qty_of_total_production
					elif self.costing_method == "Relative Sales Value":
						sale_value_of_pdt = frappe.db.get_value("Item Price", {"item_code":item.item}, "price_list_rate")
						se_item.basic_rate = (float(sale_value_of_pdt) * float(production_cost)) / float(total_sale_value)
		return se


	@frappe.whitelist()
	def make_stock_entry(self, status):
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.process_order = self.name
		if status == "Submitted":
			stock_entry.purpose = "Material Transfer for Manufacture"
			stock_entry.stock_entry_type = "Material Transfer for Manufacture"
			stock_entry = self.set_se_items_start(stock_entry)
		if status == "In Process":
			stock_entry.purpose = "Manufacture"
			stock_entry.stock_entry_type = "Manufacture"
			stock_entry = self.set_se_items_finish(stock_entry)

		return stock_entry.as_dict()
		
	@frappe.whitelist()
	def add_item_in_table(self, table_value, table_name):
		self.set(table_name, [])
		for item in table_value:
			po_item = self.append(table_name, {})
			po_item.item = item.item
			po_item.item_name = item.item_name
			po_item.row_no = item.row_no
			po_item.rate = item.rate

	@frappe.whitelist()
	def map_lot_no(self):
		for f_line in self.finished_products:
			if f_line.row_no:
				material_line = frappe.get_list("Process Order Item",fields="*", filters={"parent": f_line.parent, "row_no": f_line.row_no, "parentfield": "materials"}, order_by="idx", limit=1)
				if material_line:
					material_line = material_line[0]
					if material_line.lot_no:
						bch = frappe.get_doc("Batch", material_line.lot_no)
						if frappe.db.get_value("Item", f_line.item, "has_batch_no") == 1:
							split_name = ''
							batch_doc = None
							if frappe.db.get_value("Item", f_line.item, "batch_suffix"):
								split_name = (material_line.lot_no).split("-")[0]+"-"+str(frappe.db.get_value("Item", f_line.item, "batch_suffix"))
								if material_line.design_no:
									split_name = split_name + "-" + str(material_line.design_no)
							else:
								name_lst = str(f_line.item).split(" ")
								itm_name = ''
								for i in name_lst:
									if i:
										itm_name += i[0]
								split_name = (material_line.lot_no).split("-")[0]+"-"+str(itm_name)
								if material_line.design_no:
									split_name = split_name + "-" + str(material_line.design_no)
							if not frappe.db.exists('Batch', split_name):
								batch = frappe.new_doc("Batch")
								batch.batch_id = split_name
								batch.item = f_line.item
								batch.supplier = bch.supplier
								batch.quality_code = bch.quality_code
								batch.quality_name = bch.quality_name
								if material_line.design_no:
									batch.design_no = material_line.design_no
								batch.insert(ignore_permissions=True)
								batch_doc = batch
							else:
								batch_doc = frappe.get_doc("Batch", split_name)
							f_line.lot_no = batch_doc.name
							f_line.party_name = batch_doc.supplier
							f_line.customer_name = batch_doc.party_name
							f_line.quality_code = batch_doc.quality_code
							f_line.quality_name = batch_doc.quality_name
							if material_line.design_no:
								f_line.design_no = material_line.design_no
				else:
					frappe.throw(_("Invalid Mapping Material Row No <b>{0}</b>").format(f_line.row_no))
		
		for s_line in self.scrap:
			if s_line.row_no:
				material_line = frappe.get_list("Process Order Item",fields="*", filters={"parent": f_line.parent, "row_no": s_line.row_no, "parentfield": "materials"}, order_by="idx", limit=1)
				if material_line:
					material_line = material_line[0]
					if material_line.lot_no:
						bch = frappe.get_doc("Batch", material_line.lot_no)
						if frappe.db.get_value("Item", s_line.item, "has_batch_no") == 1:
							split_name = ''
							batch_doc = None
							if frappe.db.get_value("Item", s_line.item, "batch_suffix"):
								split_name = (material_line.lot_no).split("-")[0]+"-"+str(frappe.db.get_value("Item", s_line.item, "batch_suffix"))
								if material_line.design_no:
									split_name = split_name + "-" + str(material_line.design_no)
							else:
								name_lst = str(s_line.item).split(" ")
								itm_name = ''
								for i in name_lst:
									if i:
										itm_name += i[0]
								split_name = (material_line.lot_no).split("-")[0]+"-"+str(itm_name)
								if material_line.design_no:
									split_name = split_name + "-" + str(material_line.design_no)
							if not frappe.db.exists('Batch', split_name):
								batch = frappe.new_doc("Batch")
								batch.batch_id = split_name
								batch.item = s_line.item
								batch.supplier = bch.supplier
								batch.quality_code = bch.quality_code
								batch.quality_name = bch.quality_name
								if material_line.design_no:
									batch.design_no = material_line.design_no
								batch.insert(ignore_permissions=True)
								batch_doc = batch
							else:
								batch_doc = frappe.get_doc("Batch", split_name)
							s_line.lot_no = batch_doc.name
							s_line.party_name = batch_doc.supplier
							s_line.customer_name = batch_doc.party_name
							s_line.quality_code = batch_doc.quality_code
							s_line.quality_name = batch_doc.quality_name
							if material_line.design_no:
								s_line.design_no = material_line.design_no
				else:
					frappe.throw(_("Invalid Mapping Material Row No <b>{0}</b>").format(s_line.row_no))

		self.flags.ignore_validate_update_after_submit = True
		self.save(ignore_permissions=True)

	@frappe.whitelist()
	def map_multi_lot_no(self):
		option_lst = []
		st = ''
		for m_line in self.materials:
			option_lst.append(m_line.lot_no)
		for number in set(option_lst):
			st += '\n' + str(number)
		fields = [{
					"label": "Lot No",
					"fieldname": "lot_no",
					"fieldtype": "Select",
					"options": st,
					"reqd": 1
				},
				{
					"label": "Design",
					"fieldname": "design",
					"fieldtype": "Link",
					"options": "Design"
				}]
		return fields

	@frappe.whitelist()
	def update_material_avl_qty(self):
		for res in self.materials:
			qty = get_batch_qty(batch_no=res.lot_no, warehouse=self.src_warehouse, item_code=res.item)
			res.available_qty = qty
			res.db_update()

	@frappe.whitelist()
	def make_purchase_receipt(self):
		department = frappe.get_doc('Manufacturing Department',self.department)
		doc = frappe.new_doc('Purchase Receipt')
		doc.supplier = department.supplier
		doc.posting_date = self.date
		doc.process_order = self.name
		doc.company = self.company
		doc.igp = self.department
		doc.is_subcontracted = 'Yes'
		doc.supplier_warehouse = self.wip_warehouse
		total_qty = 0
		total_raw_cost = 0
		for res in self.finished_products:
			total_qty += res.quantity

		for res in self.scrap:
			item = frappe.get_doc('Item',res.item)
			doc.append('items', {
				'item_code': res.item,
				'item_name': res.item_name,
				'batch_no': res.lot_no,
				'design_no': res.design_no,
				'description': item.description,
				'received_qty': res.quantity,
				'qty': res.quantity,
				'stock_uom': item.stock_uom,
				'uom': item.stock_uom,
				'price_list_rate': 0,
				'rate': res.rate,
				'warehouse': self.scrap_warehouse,
				'allow_zero_valuation_rate': res.rate,
				'business_unit': self.business_unit
			})
		
		if self.materials:
			se_query = frappe.db.sql("""select sed.item_code, sed.description, sed.batch_no, sed.design_no,
						sed.qty, sed.basic_rate, sed.stock_uom 
						from `tabStock Entry` as se
						inner join `tabStock Entry Detail` as sed on sed.parent = se.name
						and se.process_order = %s and se.docstatus = 1 
						and se.stock_entry_type = 'Material Transfer for Manufacture'""",(self.name),as_dict=True)
			for res in se_query:
				rate = 0
				amount = 0
				if res.get('basic_rate'):
					rate = round(float(res.get('basic_rate')), 3)
				if res.get('qty'):
					amount = round((float(res.get('qty')) * rate), 3)
				total_raw_cost += amount
				item = frappe.get_doc('Item', res.get('item_code'))
				doc.append('supplied_items1', {
					'rm_item_code': res.get('item_code'),
					'batch_no': res.get('batch_no'),
					'design_no': res.get('design_no'),
					'description': res.get('description'),
					'required_qty': res.get('qty'),
					'consumed_qty': res.get('qty'),
					'stock_uom': res.get('stock_uom'),
					'rate': rate,
					'amount': amount
				})

		for res in self.finished_products:
			item = frappe.get_doc('Item',res.item)
			doc.append('items', {
				'item_code': res.item,
				'item_name': res.item_name,
				'batch_no': res.lot_no,
				'design_no': res.design_no,
				'description': item.description,
				'received_qty': res.quantity,
				'qty': res.quantity,
				'stock_uom': item.stock_uom,
				'uom': item.stock_uom,
				'price_list_rate': res.rate,
				'rate': res.rate,
				'warehouse': self.fg_warehouse,
				'allow_zero_valuation_rate': 0,
				'business_unit': self.business_unit,
				'rm_supp_cost': (total_raw_cost / total_qty) * res.quantity
			})
		doc.set_missing_values()
		doc.insert(ignore_permissions=True)
		return doc.as_dict()

@frappe.whitelist()
def validate_items(se_items, po_items):
	#validate for items not in process order
	for se_item in se_items:
		if not filter(lambda x: x.item == se_item.item_code, po_items):
			frappe.throw(_("Item {0} - {1} cannot be part of this Stock Entry").format(se_item.item_code, se_item.item_name))

@frappe.whitelist()
def validate_material_qty(se, se_items, po_items):
	#TODO allow multiple raw material transfer?
	if se.additional_fabric_qty:
		for material in po_items:
			for item in se_items:
				if (material.item == item.item_code and item.process_line == material.name):
					if (item.qty != material.additional_qty):
						frappe.throw(_("Total quantity of Item {0} - {1} should be {2} in Line No. <b>{3}<b/>").format(
							material.item, material.item, material.additional_qty, item.idx))
	else:
		for material in po_items:
			for item in se_items:
				if(material.item == item.item_code  and item.process_line == material.name):
					if (item.qty != material.quantity):
						frappe.throw(_("Total quantity of Item {0} - {1} should be {2} in Line No. <b>{3}<b/>").format(
							material.item, material.item, material.quantity, item.idx))

@frappe.whitelist()
def manage_se_submit(se, po):
	if not se.additional_fabric_qty:
		if po.docstatus == 0:
			frappe.throw(_("Submit the  Process Order {0} to make Stock Entries").format(po.name))
		if po.status == "Submitted":
			po.status = "In Process"
			po.start_dt = get_datetime()
		elif po.status == "In Process":
			po.status = "Completed"
		elif po.status in ["Completed", "Cancelled"]:
			frappe.throw("You cannot make entries against Completed/Cancelled Process Orders")
	po.flags.ignore_validate_update_after_submit = True
	po.save()

@frappe.whitelist()
def manage_se_cancel(se, po):
	if not se.additional_fabric_qty:
		if po.status == "In Process":
			po.status = "Submitted"
		elif(po.status == "Completed"):
			try:
				validate_material_qty(se, se.items, po.finished_products)
				po.status = "In Process"
			except:
				frappe.throw("Please cancel the production stock entry first.")
		else:
			frappe.throw("Process order status must be In Process or Completed")
	po.flags.ignore_validate_update_after_submit = True
	po.save()

@frappe.whitelist()
def validate_se_qty(se, po):
	validate_material_qty(se, se.items, po.materials)
	if po.status == "In Process":
		validate_material_qty(se, se.items, po.finished_products)
		validate_material_qty(se, se.items, po.scrap)

@frappe.whitelist()
def manage_se_changes(doc, method):
	if doc.process_order:
		po = frappe.get_doc("Process Order", doc.process_order)
		if(method=="on_submit"):
			if po.status == "Submitted":
				validate_items(doc.items, po.materials)
			elif po.status == "In Process":
				po_items = po.materials
				po_items.extend(po.finished_products)
				po_items.extend(po.scrap)
				validate_items(doc.items, po_items)
			validate_se_qty(doc, po)
			manage_se_submit(doc, po)
		elif(method=="on_cancel"):
			manage_se_cancel(doc, po)


@frappe.whitelist()
def create_lot_no(data= None,doc_name=None):
	doc = frappe.get_doc("Process Order", doc_name)
	if data:
		d = json.loads(data)
		for res in d:
			line_obj_present = frappe.db.exists("Process Order Finish Item", res)
			if not line_obj_present:
				line_id = str(res.split("-")[0])
				line_obj = frappe.db.exists("Process Order Finish Item", line_id)
				if line_obj:
					line_obj = frappe.get_doc("Process Order Finish Item", line_id)
					line_obj.design_no = d[res]
					line_obj.flags.ignore_validate_update_after_submit = True
					line_obj.db_update()
					line_obj.save(ignore_permissions=True)

		for res in d:
			if d[res]:
				line_obj_present = frappe.db.exists("Process Order Finish Item", res)
				if line_obj_present:
					bch = frappe.get_doc("Batch", d[res])
					if bch:
						line_obj = frappe.get_doc("Process Order Finish Item", res)
						if line_obj and frappe.db.get_value("Item", line_obj.item, "has_batch_no") == 1:
							split_name = ''
							batch_doc = None
							if frappe.db.get_value("Item", line_obj.item, "batch_suffix"):
								split_name = d[res].split("-")[0]+"-"+str(frappe.db.get_value("Item", line_obj.item, "batch_suffix"))
								if line_obj.design_no:
									split_name = split_name + "-" + str(line_obj.design_no)
							else:
								name_lst = str(line_obj.item).split(" ")
								itm_name = ''
								for i in name_lst:
									if i:
										itm_name += i[0]
								split_name = d[res].split("-")[0]+"-"+str(itm_name)
								if line_obj.design_no:
									split_name = split_name + "-" + str(line_obj.design_no)

							if not frappe.db.exists('Batch', split_name):
								batch = frappe.new_doc("Batch")
								batch.batch_id = split_name
								batch.item = line_obj.item
								batch.supplier = bch.supplier
								batch.quality_code = bch.quality_code
								batch.quality_name = bch.quality_name
								batch.design_no = line_obj.design_no
								batch.insert(ignore_permissions=True)
								batch_doc = batch
							else:
								batch_doc = frappe.get_doc("Batch", split_name)
							line_obj.lot_no = batch_doc.name
							line_obj.party_name = batch_doc.supplier
							line_obj.quality_code = batch_doc.quality_code
							line_obj.quality_name = batch_doc.quality_name
							line_obj.flags.ignore_validate_update_after_submit = True
							line_obj.db_update()
							line_obj.save(ignore_permissions=True)\

		for res in d:
			line_obj_present = frappe.db.exists("Process Order Item", res)
			if not line_obj_present:
				line_id = str(res.split("-")[0])
				line_obj = frappe.db.exists("Process Order Item", line_id)
				if line_obj:
					line_obj = frappe.get_doc("Process Order Item", line_id)
					line_obj.design_no = d[res]
					line_obj.flags.ignore_validate_update_after_submit = True
					line_obj.db_update()
					line_obj.save(ignore_permissions=True)

		for res in d:
			if d[res]:
				line_obj_present = frappe.db.exists("Process Order Item", res)
				if line_obj_present:
					bch = frappe.get_doc("Batch", d[res])
					if bch:
						line_obj = frappe.get_doc("Process Order Item", res)
						if line_obj and frappe.db.get_value("Item", line_obj.item, "has_batch_no") == 1:
							split_name = ''
							batch_doc = None
							if frappe.db.get_value("Item", line_obj.item, "batch_suffix"):
								split_name = d[res].split("-")[0]+"-"+str(frappe.db.get_value("Item", line_obj.item, "batch_suffix"))
								if line_obj.design_no:
									split_name = split_name + "-" + str(line_obj.design_no)
							else:
								name_lst = str(line_obj.item).split(" ")
								itm_name = ''
								for i in name_lst:
									if i:
										itm_name += i[0]
								split_name = d[res].split("-")[0]+"-"+str(itm_name)
								if line_obj.design_no:
									split_name = split_name + "-" + str(line_obj.design_no)

							if not frappe.db.exists('Batch', split_name):
								batch = frappe.new_doc("Batch")
								batch.batch_id = split_name
								batch.item = line_obj.item
								batch.supplier = bch.supplier
								batch.quality_code = bch.quality_code
								batch.quality_name = bch.quality_name
								batch.design_no = line_obj.design_no
								batch.insert(ignore_permissions=True)
								batch_doc = batch
							else:
								batch_doc = frappe.get_doc("Batch", split_name)
							line_obj.lot_no = batch_doc.name
							line_obj.party_name = batch_doc.supplier
							line_obj.quality_code = batch_doc.quality_code
							line_obj.quality_name = batch_doc.quality_name
							line_obj.flags.ignore_validate_update_after_submit = True
							line_obj.db_update()
							line_obj.save(ignore_permissions=True)

@frappe.whitelist()
def create_multi_lot_no(data=None,doc_name=None):
	doc = frappe.get_doc("Process Order", doc_name)
	if data:
		d = json.loads(data)
		if "lot_no" in d.keys():
			bch = frappe.get_doc("Batch", d['lot_no'])
			if bch:
				for line_obj in doc.finished_products:
					if frappe.db.get_value("Item", line_obj.item, "has_batch_no") == 1:
						split_name = ''
						batch_doc = None
						if frappe.db.get_value("Item", line_obj.item, "batch_suffix"):
							split_name = d['lot_no'].split("-")[0]+"-"+str(frappe.db.get_value("Item", line_obj.item, "batch_suffix"))
							if "design" in d.keys():
								split_name = split_name + "-" + str(d['design'])
						else:
							name_lst = str(line_obj.item).split(" ")
							itm_name = ''
							for i in name_lst:
								if i:
									itm_name += i[0]
							split_name = d['lot_no'].split("-")[0]+"-"+str(itm_name)
							if "design" in d.keys():
								split_name = split_name + "-" + str(d['design'])
						if not frappe.db.exists('Batch', split_name):
							batch = frappe.new_doc("Batch")
							batch.batch_id = split_name
							batch.item = line_obj.item
							batch.supplier = bch.supplier
							batch.quality_code = bch.quality_code
							batch.quality_name = bch.quality_name
							if "design" in d.keys():
								batch.design_no = d['design']
							batch.insert(ignore_permissions=True)
							batch_doc = batch
						else:
							batch_doc = frappe.get_doc("Batch",split_name)
						line_obj.lot_no = batch_doc.name
						line_obj.party_name = batch_doc.supplier
						line_obj.quality_code = batch_doc.quality_code
						line_obj.quality_name = batch_doc.quality_name
						if "design" in d.keys():
							line_obj.design_no = d['design']
						line_obj.flags.ignore_validate_update_after_submit = True
						line_obj.db_update()
						line_obj.save(ignore_permissions=True)

				for line_obj in doc.scrap:
					if frappe.db.get_value("Item", line_obj.item, "has_batch_no") == 1:
						split_name = ''
						batch_doc = None
						if frappe.db.get_value("Item", line_obj.item, "batch_suffix"):
							split_name = d['lot_no'].split("-")[0]+"-"+str(frappe.db.get_value("Item", line_obj.item, "batch_suffix"))
							if "design" in d.keys():
								split_name = split_name + "-" + str(d['design'])
						else:
							name_lst = str(line_obj.item).split(" ")
							itm_name = ''
							for i in name_lst:
								if i:
									itm_name += i[0]
							split_name = d['lot_no'].split("-")[0]+"-"+str(itm_name)
							if "design" in d.keys():
								split_name = split_name + "-" + str(d['design'])
						if not frappe.db.exists('Batch', split_name):
							batch = frappe.new_doc("Batch")
							batch.batch_id = split_name
							batch.item = line_obj.item
							batch.supplier = bch.supplier
							batch.quality_code = bch.quality_code
							batch.quality_name = bch.quality_name
							if "design" in d.keys():
								batch.design_no = d['design']
							batch.insert(ignore_permissions=True)
							batch_doc = batch
						else:
							batch_doc = frappe.get_doc("Batch",split_name)
						line_obj.lot_no = batch_doc.name
						line_obj.party_name = batch_doc.supplier
						line_obj.quality_code = batch_doc.quality_code
						line_obj.quality_name = batch_doc.quality_name
						if "design" in d.keys():
							line_obj.design_no = d['design']
						line_obj.flags.ignore_validate_update_after_submit = True
						line_obj.db_update()
						line_obj.save(ignore_permissions=True)

@frappe.whitelist()
def get_item_available_qty(warehouse,item, batch=None):
	qty = get_batch_qty(batch_no=batch, warehouse=warehouse, item_code=item)
	return qty