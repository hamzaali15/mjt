# -*- coding: utf-8 -*-
# Copyright (c) 2021, earthians and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class MergeLot(Document):
	@frappe.whitelist()
	def get_lots(self):
		supplier = None
		if self.party_code:
			supplier = frappe.get_list('Double Ledger Parties', filters={'customer': self.party_code}, fields=['supplier'], limit=1)
		if not supplier:
			frappe.throw(_("Customer and Supplier not linked!"))
		
		if not self.quality:
			frappe.throw(_("Select Quality First!"))

		if not self.warehouse:
			frappe.throw(_("Select Warehouse First!"))

		if not self.item_code:
			frappe.throw(_("Select Item First!"))

		query = """select sle.batch_no as lot_no, b.party_name, b.quality_name,  sum(sle.actual_qty) as avl_qty
					from `tabStock Ledger Entry` as sle
					inner join `tabBatch` as b on b.name = sle.batch_no
					where sle.batch_no is not null"""
		if self.item_code:
			query += " and b.item = '{0}'".format(self.item_code)
		if self.warehouse:
			query += " and sle.warehouse = '{0}'".format(self.warehouse)
		if supplier:
			query += " and b.supplier = '{0}'".format(supplier[0].supplier)
		if self.quality:
			query += " and b.quality_code = '{0}'".format(self.quality)

		query += """ group by batch_no, b.party_name,b.quality_name
					having sum(sle.actual_qty) > 0"""
		result = frappe.db.sql(query,as_dict=True)
		return result

	def before_submit(self):
		self.merge_lot_no()
	
	@frappe.whitelist()
	def merge_lot_no(self):
		batch_no = None
		if not self.merge_qty_in_existing_lot:
			batch_name = make_autoname("Q.###")
			supplier = None
			if self.party_code:
				sup = frappe.get_list('Double Ledger Parties', filters={'customer': self.party_code}, fields=['supplier'], limit=1)
				if sup:
					supplier = sup[0].supplier

			batch_no = frappe.get_doc(dict(
				doctype='Batch',
				batch_id=batch_name,
				item=self.item_code,
				supplier=supplier,
				quality_code=self.quality,
				business_unit=self.business_unit,
				reference_doctype=self.doctype,
				reference_name=self.name)).insert().name
		else:
			batch_no = self.lot_no
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.merge_lot = self.name
		stock_entry.company = self.company
		stock_entry.set_posting_time = 1
		stock_entry.posting_date = self.date
		stock_entry.posting_time = self.current_time
		stock_entry.stock_entry_type = "Repack"
		expense_account, cost_center = frappe.db.get_values("Company", self.company, ["default_expense_account", "cost_center"])[0]
		item_name, stock_uom, description =frappe.db.get_values("Item", self.item_code, ["item_name", "stock_uom", "description"])[0]
		item_expense_account, item_cost_center = frappe.db.get_value("Item Default",{'parent': self.item_code, 'company': self.company},["expense_account", "buying_cost_center"])
		total_merge_qty = 0
		for res in self.lots:
			if res.merge_qty:
				se_item = stock_entry.append("items")
				se_item.item_code = self.item_code
				se_item.qty = res.merge_qty
				se_item.s_warehouse = self.warehouse
				se_item.item_name = item_name
				se_item.description = description
				se_item.uom = stock_uom
				se_item.stock_uom = stock_uom
				se_item.batch_no = res.lot_no
				se_item.expense_account = item_expense_account or expense_account
				se_item.cost_center = item_cost_center or cost_center
				se_item.conversion_factor = 1.00
				se_item.business_unit = self.business_unit
				total_merge_qty += res.merge_qty

		se_item = stock_entry.append("items")
		se_item.item_code = self.item_code
		se_item.qty = total_merge_qty
		se_item.t_warehouse = self.warehouse
		se_item.item_name = item_name
		se_item.description = description
		se_item.uom = stock_uom
		se_item.stock_uom = stock_uom
		se_item.batch_no = batch_no
		se_item.business_unit = self.business_unit
		se_item.expense_account = item_expense_account or expense_account
		se_item.cost_center = item_cost_center or cost_center
		se_item.conversion_factor = 1.00
		stock_entry.set_missing_values()
		stock_entry.insert(ignore_permissions=True)
		stock_entry.validate()
		stock_entry.flags.ignore_validate_update_after_submit = True
		stock_entry.submit()
		batch = frappe.get_doc("Batch",batch_no)

		text = "<b>{0}</b> Qty Merged from <b>{1}</b> in Warehouse <b>{2}</b>".format(total_merge_qty,self.name,self.warehouse)
		self.append("merged_lot",{
			'lot_no': batch_no,
			'party_name': batch.party_name,
			'quality_name': batch.quality_name,
			'merged_qty': total_merge_qty
		})
		batch.add_comment(comment_type='Info', text=text, link_doctype=self.doctype, link_name=self.name)
		self.db_update()