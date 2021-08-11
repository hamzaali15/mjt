# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime
from frappe.model.document import Document

class GreigeMendingForm(Document):

	def before_save(self):
		if self.greige_grading_form:
			doc = frappe.get_doc("Greige Grading Form",self.greige_grading_form)
			if doc:
				rev_time = datetime.strptime((str(doc.date) + " " + str(doc.current_time)), '%Y-%m-%d %H:%M:%S')
				grad_time = datetime.strptime(str(self.date + " " + self.current_time), '%Y-%m-%d %H:%M:%S')
				if rev_time > grad_time:
					frappe.throw(_("Mending Date must be greater then the Grading Date!"))

	def before_submit(self):
		customer_list = frappe.get_list('Double Ledger Parties', filters={'customer': self.customer_code}, fields=['supplier'], limit=1)
		supplier = None
		if customer_list:
			supplier = frappe.get_doc("Supplier", customer_list[0].supplier)
		if not supplier:
			frappe.throw(_("Supplier not found against this customer"))

	def on_submit(self):
		query = frappe.db.sql("""select * from `tabGreige Mending Form` where name != %s and greige_grading_form =%s and docstatus = 1""",
							(self.name, self.greige_grading_form))
		if query:
			frappe.throw(
				_("Greige Mending already has done against this Greige Grading  {0}").format(
					self.greige_grading_form))

	@frappe.whitelist()
	def add_entry(self):
		if not self.item:
			frappe.throw(_("Select the Item!"))
		if not self.mending_meter or self.mending_meter <= 0:
			frappe.throw(_("Mending Meter should be greater then the zero!"))
		total = self.mending_meter
		total_net_grading_meter = self.total_grading_meter - self.total_fabric_meter
		if total > self.total_remaining_meter:
			frappe.throw(_("The Mending meter should not exceed Total Remaining meter. left Remaining Meter quantity is <b>{0}</b>.").format(self.total_remaining_meter))
		purchase_ref = self.make_purchase_receipt()
		process_meter = 0
		if not self.batch_no:
			check_process = frappe.db.sql("""select sum(mending_meter) as mending_meter from `tabGreige Mending Child` 
										where item =%s and parent =%s order by date desc""",(self.item, self.name), as_dict=True)
			if check_process:
				process_meter = check_process[0].mending_meter
			if not process_meter:
				process_meter = 0
			query = frappe.db.sql("""select item,
						sum(grading_meter) as grading_meter,
						sum(fabric_meter) as fabric_meter,
						sum(process_meter) as process_meter
						from `tabGreige Grading Child` where item = %s and parent = %s group by item limit 1""",(self.item, self.greige_grading_form), as_dict=True)
			if query:
				self.append('greige_mending', {
					'item': query[0].item,
					'grading_meter': query[0].grading_meter,
					'fabric_meter': query[0].fabric_meter,
					'process_meter': process_meter,
					'remaining_meter': (query[0].grading_meter - query[0].fabric_meter - process_meter),
					'mending_meter': self.mending_meter,
					'rejection_meter': self.rejection_meter,
					'net_mending_meter': self.mending_meter - self.rejection_meter,
					'date': datetime.now(),
					'purchase_receipt_ref': purchase_ref if purchase_ref else None
				})
		else:
			check_process = frappe.db.sql("""select sum(mending_meter) as mending_meter from `tabGreige Mending Child` 
										where item =%s and batch_no =%s and parent =%s order by date desc""",(self.item, self.batch_no, self.name), as_dict=True)
			if check_process:
				process_meter = check_process[0].mending_meter
			if not process_meter:
				process_meter = 0
			query = frappe.db.sql("""select item,batch_no,
						sum(grading_meter) as grading_meter,
						sum(fabric_meter) as fabric_meter,
						sum(process_meter) as process_meter
						from `tabGreige Grading Child` 
						where item = %s and parent = %s and batch_no = %s group by item, batch_no limit 1""", (self.item, self.greige_grading_form,self.batch_no), as_dict=True)
			if query:
				self.append('greige_mending', {
					'item': query[0].item,
					'batch_no': query[0].batch_no,
					'grading_meter': query[0].grading_meter,
					'fabric_meter': query[0].fabric_meter,
					'process_meter': process_meter,
					'remaining_meter': (query[0].grading_meter - query[0].fabric_meter - process_meter),
					'mending_meter': self.mending_meter,
					'rejection_meter': self.rejection_meter,
					'net_mending_meter': self.mending_meter - self.rejection_meter,
					'date': datetime.now(),
					'purchase_receipt_ref': purchase_ref if purchase_ref else None
				})
		self.save(ignore_permissions=True)
		total_grading_meter = 0
		total_fabric_meter = 0
		total_process_meter = 0
		total_remaining_meter = 0
		total_mending_meter = 0
		total_rejection_meter = 0
		total_net_mending_meter = 0

		for res in self.greige_mending:
			total_grading_meter += res.grading_meter
			total_fabric_meter += res.fabric_meter
			total_process_meter += res.process_meter
			total_remaining_meter += res.remaining_meter
			total_mending_meter += res.mending_meter
			total_rejection_meter += res.rejection_meter
			total_net_mending_meter += res.net_mending_meter

		self.total_process_meter = total_process_meter
		self.total_remaining_meter = total_net_grading_meter - total_mending_meter
		self.total_mending_meter = total_mending_meter
		self.total_rejection_meter = total_rejection_meter
		self.total_net_mending_meter = total_mending_meter - total_rejection_meter

		self.mending_meter = None
		self.rejection_meter = None
		self.save(ignore_permissions=True)

	@frappe.whitelist()
	def make_purchase_receipt(self):
		customer_list = frappe.get_list('Double Ledger Parties', filters={'customer': self.customer_code},
										fields=['supplier'], limit=1)
		supplier = None
		if customer_list:
			supplier = frappe.get_doc("Supplier", customer_list[0].supplier)

		purchase_order = frappe.db.sql("""select r.purchase_order from `tabGreige Mending Form` m
								inner join `tabGreige Grading Form` g on g.name = m.greige_grading_form
								inner join `tabGreige Receiving Form` r on r.name = g.greige_receiving_form
								where m.name = %s limit 1""", (self.name), as_dict=True)
		grading_labor_charges = 0
		if self.grading_labor_charges:
			grading_labor_charges = self.grading_labor_charges
		manding_labor_charges = 0
		if self.manding_labor_charges:
			manding_labor_charges = self.manding_labor_charges

		if purchase_order[0].purchase_order:
			purchase_order = purchase_order[0].purchase_order

			purchase_order_item_id = frappe.db.get_list("Purchase Order Item",
														{"parent": purchase_order, "item_code": self.item}, ["name"])
			if purchase_order_item_id:
				purchase_order_item_id = purchase_order_item_id[0].name

			if purchase_order and purchase_order_item_id:
				item = frappe.get_doc("Item", self.item)
				po_line = frappe.get_doc("Purchase Order Item", purchase_order_item_id)

				doc = frappe.new_doc('Purchase Receipt')
				doc.supplier = supplier.name
				doc.posting_date = self.date
				doc.greige_mending_form = self.name
				doc.company = self.company
				doc.igp = self.batch_no
				doc.append('items', {
					'item_code': self.item,
					'item_name': self.item_name,
					'batch_no': self.batch_no,
					'description': item.description,
					'received_qty': self.mending_meter,
					'qty': (self.mending_meter - self.rejection_meter),
					'rejected_qty': self.rejection_meter,
					'stock_uom': po_line.stock_uom,
					'uom': po_line.uom,
					'price_list_rate': 0,
					'rate': po_line.rate,
					'warehouse': self.warehouse,
					'purchase_order': purchase_order,
					'purchase_order_item': purchase_order_item_id,
					'rejected_warehouse': self.rejected_warehouse,
					'allow_zero_valuation_rate': 1,
					'business_unit': self.business_unit
				})
				tax_template = frappe.db.get_single_value('Greige Setting', 'tax_template')
				if tax_template:
					tax_doc = frappe.get_doc("Purchase Taxes and Charges Template",tax_template)
					doc.taxes_and_charges = tax_template
					for tax_line in tax_doc.taxes:
						doc.append("taxes",{
							"category": tax_line.category,
							"add_deduct_tax": tax_line.add_deduct_tax,
							"charge_type": tax_line.charge_type,
							"row_id": tax_line.row_id,
							"included_in_print_rate": tax_line.included_in_print_rate,
							"account_head": tax_line.account_head,
							"description": tax_line.description,
							"rate rate": tax_line.rate,
							"cost_center": tax_line.cost_center,
							"tax_amount": self.mending_meter * (grading_labor_charges + manding_labor_charges),
							'business_unit': self.business_unit
						})
				doc.set_missing_values()
				if not self.greige_mending:
					doc.posting_date = self.date
					doc.posting_time = self.current_time
					doc.set_posting_time = 1
				doc.insert(ignore_permissions=True)
				doc.submit()
				return doc.name
		else:
			item = frappe.get_doc("Item", self.item)
			doc = frappe.new_doc('Purchase Receipt')
			doc.supplier = supplier.name
			doc.posting_date = self.date
			doc.greige_mending_form = self.name
			doc.company = self.company
			doc.igp = self.batch_no
			doc.append('items', {
				'item_code': self.item,
				'item_name': self.item_name,
				'batch_no': self.batch_no,
				'description': item.description,
				'received_qty': self.mending_meter,
				'qty': (self.mending_meter - self.rejection_meter),
				'rejected_qty': self.rejection_meter,
				'stock_uom': item.stock_uom,
				'uom': item.stock_uom,
				'price_list_rate':0,
				'rate': 0.0,
				'warehouse': self.warehouse,
				'rejected_warehouse': self.rejected_warehouse,
				'allow_zero_valuation_rate': 1,
				'business_unit': self.business_unit
			})
			tax_template = frappe.db.get_single_value('Greige Setting', 'tax_template')
			if tax_template:
				tax_doc = frappe.get_doc("Purchase Taxes and Charges Template",tax_template)
				doc.taxes_and_charges = tax_template
				for tax_line in tax_doc.taxes:
					doc.append("taxes", {
						"category": tax_line.category,
						"add_deduct_tax": tax_line.add_deduct_tax,
						"charge_type": tax_line.charge_type,
						"row_id": tax_line.row_id,
						"included_in_print_rate": tax_line.included_in_print_rate,
						"account_head": tax_line.account_head,
						"description": tax_line.description,
						"rate": tax_line.rate,
						"cost_center": tax_line.cost_center,
						"tax_amount": (self.mending_meter * (grading_labor_charges + manding_labor_charges)),
						'business_unit': self.business_unit
					})
			doc.set_missing_values()
			if not self.greige_mending:
				doc.posting_date = self.date
				doc.posting_time = self.current_time
				doc.set_posting_time = 1
			doc.insert(ignore_permissions=True)
			doc.submit()
			return doc.name
		return False

	@frappe.whitelist()
	def edit_entry(self):
		if not self.line_no:
			frappe.throw(_("Please enter line number!"))
		if not self.mending_meter or self.mending_meter <= 0:
			frappe.throw(_("Mending Meter should be greater then the zero!"))

		query = """select name,date from `tabGreige Mending Child` where parent = '{0}' order by date limit {1},1""".format(self.name, self.line_no-1)
		result = frappe.db.sql(query,as_list=True)
		if result:
			process_meter = 0
			check_process = frappe.db.sql("""select sum(mending_meter) as mending_meter from `tabGreige Mending Child` 
									where item ='{0}' and batch_no ='{1}' and parent ='{2}' and date < '{3}'""".format(self.item, self.batch_no, self.name, result[0][1]), as_dict=True)
			if check_process:
				process_meter = check_process[0].mending_meter
			if not process_meter:
				process_meter = 0
			child_obj = frappe.get_doc("Greige Mending Child",result[0][0])

			old_total = self.total_remaining_meter + child_obj.mending_meter
			total = self.mending_meter
			if total > old_total:
				frappe.throw(_(
					"The sum of Mending meter should not exceed Net Grading meter. left grading meter quantity is <b>{0}</b>.").format(old_total))

			child_obj.process_meter = process_meter
			child_obj.remaining_meter = (child_obj.grading_meter - child_obj.fabric_meter - process_meter)
			child_obj.mending_meter = self.mending_meter
			child_obj.rejection_meter = self.rejection_meter
			child_obj.net_mending_meter = self.mending_meter - self.rejection_meter

			if child_obj.purchase_receipt_ref:
				self.cancel_purchase_receipt(child_obj.purchase_receipt_ref)

			purchase_ref = self.make_purchase_receipt()
			child_obj.purchase_receipt_ref = purchase_ref if purchase_ref else None
			child_obj.flags.ignore_validate_update_after_submit = True
			child_obj.db_update()
			child_obj.save(ignore_permissions=True)

			query2 = """select name,date from `tabGreige Mending Child` where parent = '{0}' and date > '{1}' order by date""".format(self.name, child_obj.date)
			result2 = frappe.db.sql(query2,as_dict=True)
			for res in result2:
				process_meter = 0
				check_process = frappe.db.sql("""select sum(mending_meter) as mending_meter from `tabGreige Mending Child` 
																		where item ='{0}' and batch_no ='{1}' and parent ='{2}' and date < '{3}'""".format(
					self.item, self.batch_no, self.name, res.date), as_dict=True)
				if check_process:
					process_meter = check_process[0].mending_meter
				if not process_meter:
					process_meter = 0
				line_doc = frappe.get_doc("Greige Mending Child",res.name)
				line_doc.process_meter = process_meter
				line_doc.remaining_meter = (line_doc.grading_meter - line_doc.fabric_meter - process_meter)
				line_doc.net_mending_meter = line_doc.mending_meter - line_doc.rejection_meter
				line_doc.flags.ignore_validate_update_after_submit = True
				line_doc.db_update()
				line_doc.save(ignore_permissions=True)
		else:
			frappe.throw(_("Please enter valid line number!"))
		return True

	@frappe.whitelist()
	def cancel_purchase_receipt(self,purchase_ref = None):
		if purchase_ref:
			doc = frappe.get_doc("Purchase Receipt", purchase_ref)
			if doc:
				doc.cancel()

	@frappe.whitelist()
	def update_summery(self):
		query = frappe.db.sql("""SELECT SUM(process_meter),SUM(mending_meter),SUM(rejection_meter),SUM(net_mending_meter) FROM `tabGreige Mending Child` where parent =%s""",(self.name),as_list=True)
		if query:
			total_net_grading_meter = self.total_grading_meter - self.total_fabric_meter
			self.total_process_meter = query[0][0]
			self.total_mending_meter = query[0][1]
			self.total_rejection_meter = query[0][2]
			self.total_net_mending_meter = query[0][1] - query[0][2]
			self.total_remaining_meter = total_net_grading_meter - query[0][1]
			self.line_no = None
			self.mending_meter = None
			self.rejection_meter = None
			self.db_update()
		return True