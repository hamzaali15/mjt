# -*- coding: utf-8 -*-
# Copyright (c) 2020, earthians and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class GatePass(Document):

	def before_save(self):
		self.update_status()

	def on_submit(self):
		self.status = "Submitted"
		self.update_status()
		self.db_update()

	def on_cancel(self):
		self.status = "Cancelled"
		self.db_update()

	def on_update_after_submit(self):
		self.update_status()
		self.db_update()

	def update_status(self):
		total_packing = total_qty = total_r_qty = 0
		for res in self.items:
			if res.quantity:
				total_qty += res.quantity
			if res.return_qty:
				total_r_qty += res.return_qty
			if res.pack:
				total_packing += res.pack
		self.total_quantity = total_qty
		self.total_retrun_quantity = total_r_qty
		self.total_pack = total_packing
		if self.is_retrun:
			if 0 < total_r_qty < total_qty:
				self.status = "Partial Return"
			if total_r_qty >= total_qty:
				self.status = "Return"
		# self.db_update()

	def fetch_data(self):
		if not self.type:
			frappe.throw(_("Please select Gate Pass Type!"))
		if self.type == 'Inward' and not self.purchase_invoice:
			frappe.throw(_("Please select Purchase Invoice!"))
		if self.type == 'Outward' and not self.delivery_note:
			frappe.throw(_("Please select Delivery Note!"))

		if self.type == 'Inward':
			doc = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
			lst = []
			if doc:
				for line in doc.items:
					d = {
						'item_code': line.item_code,
						'description': line.description,
						'unit': line.uom,
						'quantity': line.qty,
					}
					lst.append(d)
			return lst
		if self.type == 'Outward':
			doc = frappe.get_doc("Delivery Note",self.delivery_note)
			lst = []
			if doc:
				for line in doc.items:
					d = {
						'item_code': line.item_code,
						'description': line.description,
						'unit': line.uom,
						'quantity': line.qty,
					}
					lst.append(d)
			return lst