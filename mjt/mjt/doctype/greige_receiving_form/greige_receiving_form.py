# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.model.document import Document
import json
from datetime import datetime

class GreigeReceivingForm(Document):
	def on_submit(self):
		if self.purchase_order:
			query = frappe.db.sql("select * from `tabGreige Receiving Form` where name != %s and purchase_order =%s",(self.name, self.purchase_order))
			if query:
				frappe.throw(_("Greige Receiving already has done against this Purchase Order {0}").format(self.purchase_order))
		self.status = "Submitted"

	def get_purchase_order_item(self):
		lst = []
		query = frappe.db.sql("""select i.item_code from `tabPurchase Order Item` i 
							inner join `tabPurchase Order` p on p.name = i.parent
							where p.name =%s""",(self.purchase_order),as_list=True)
		for res in query:
			lst.append(res[0])
		return lst

	def before_submit(self):
		customer_list = frappe.get_list('Double Ledger Parties',filters={'customer': self.customer_code}, fields=['supplier'], limit=1)
		supplier = None
		if customer_list:
			supplier = frappe.get_doc("Supplier", customer_list[0].supplier)
		if not supplier:
			frappe.throw(_("Supplier not found against this customer"))

		if not self.batch_no:
			itm = frappe.get_doc("Item",self.item)
			if itm and itm.has_batch_no and itm.create_new_batch:
				batch = frappe.new_doc("Batch")
				if itm.batch_number_series:
					batch.batch_id = make_autoname(itm.batch_number_series)
				else:
					batch.batch_id = make_autoname('GRF.####.')
				batch.batch_qty = self.received_qty
				batch.item = self.item
				batch.supplier = supplier.name
				batch.quality_code = self.quality_code
				batch.quality_name = self.quality_name
				batch.insert(ignore_permissions=True)
				self.batch_no = batch.name
				self.net_received_meter = self.received_qty - self.short_length
				self.db_update()
			else:
				frappe.throw(_("Please set Batch no before submit!"))

	def before_save(self):
		received_qty = 0
		if self.received_qty:
			received_qty = self.received_qty

		short_length = 0
		if self.short_length:
			short_length = self.short_length
		self.net_received_meter = received_qty - short_length

	def on_cancel(self):
		self.status = "Cancelled"
		self.db_update()

	def retrun_back_qty_to_party(self):
		query = frappe.db.sql("""SELECT SUM(total_net_grading_meter) as grade_qty From `tabGreige Grading Form` where greige_receiving_form = %s""",(self.name),as_dict=True)
		return_qty = 0
		if query[0].grade_qty:
				return_qty = self.net_received_meter - query[0].grade_qty - self.return_qty
		else:
			return_qty = self.net_received_meter - self.return_qty
		qty = 'Available Return Qty ' + str(return_qty)
		fields = [
			{
				"label": qty,
				"fieldname": "heading",
				"fieldtype": "Heading"
			},
			{
				"label": "Return Qty",
				"fieldname": "return_qty",
				"fieldtype": "Float",
				"Default": 0,
			},
			{
				"label": "Reason",
				"fieldname": "reason",
				"fieldtype": "Small Text"
			}]
		return fields

@frappe.whitelist()
def update_return_qty(doc_name, values):
	doc = frappe.get_doc("Greige Receiving Form",doc_name)
	if values:
		d = json.loads(values)
		if d['return_qty'] > 0:
			query = frappe.db.sql(
				"""SELECT SUM(total_net_grading_meter) as grade_qty From `tabGreige Grading Form` where greige_receiving_form = %s""",
				(doc.name), as_dict=True)
			available_qty = 0
			history_dict = {}
			if query[0].grade_qty:
				available_qty = doc.net_received_meter - query[0].grade_qty - doc.return_qty
			else:
				available_qty = doc.net_received_meter - doc.return_qty
			if d['return_qty'] > available_qty:
				frappe.throw(_("Grading is already done against this Greige Receiving Form."))
			else:
				doc.return_qty += d['return_qty']
				history_dict = {
					'date': datetime.now(),
					'return_qty': d['return_qty']
				}
				query = frappe.db.sql("""SELECT name From `tabGreige Grading Form` 
										where greige_receiving_form = %s and docstatus = 1 limit 1""", (doc.name),
									  as_dict=True)
				if query:
					grading = frappe.get_doc("Greige Grading Form",query[0].name)
					grading.total_received_meter -= d['return_qty']
					grading.net_received_meter = grading.total_received_meter - doc.short_length
					grading.total_remaining_meter = grading.total_received_meter - grading.total_grading_meter
					grading.flags.ignore_validate_update_after_submit = True
					grading.save(ignore_permissions=True)

			if 'reason' in d.keys():
				history_dict['reason'] = d['reason']
				doc.reason = d['reason']
			if history_dict:
				doc.append("return_summary", history_dict)
			doc.status = "Return"
			doc.flags.ignore_validate_update_after_submit = True
			doc.save(ignore_permissions=True)