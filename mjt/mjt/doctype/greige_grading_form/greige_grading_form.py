# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime
from frappe.model.document import Document

class GreigeGradingForm(Document):

	def before_save(self):
		if self.greige_receiving_form:
			doc = frappe.get_doc("Greige Receiving Form",self.greige_receiving_form)
			if doc:
				rev_time = datetime.strptime((str(doc.date) + " " + str(doc.current_time)), '%Y-%m-%d %H:%M:%S')
				grad_time = datetime.strptime(str(self.date + " " + self.current_time), '%Y-%m-%d %H:%M:%S')
				if rev_time > grad_time:
					frappe.throw(_("Grading Date must be greater then the Receiving Date!"))

	def on_submit(self):
		query = frappe.db.sql("""select * from `tabGreige Grading Form` where name != %s and greige_receiving_form =%s and docstatus = 1""",
							(self.name, self.greige_receiving_form))
		if query:
			frappe.throw(
				_("Greige Grading already has done against this Greige Receiving  {0}").format(self.greige_receiving_form))

	@frappe.whitelist()
	def add_entry(self):
		if not self.item:
			frappe.throw(_("Select the Item!"))
		if not self.grading_meter or self.grading_meter <= 0:
			frappe.throw(_("Grading Meter should be greater then the zero!"))

		total = self.grading_meter
		if total > self.total_remaining_meter:
			frappe.throw(_("Grading meter should not exceed Total Remaining meter. left Remaining Meter quantity is <b>{0}</b>.").format(self.total_remaining_meter))
		greige_recv = frappe.get_doc("Greige Receiving Form",self.greige_receiving_form)
		process_meter = 0
		if not self.batch_no:
			check_process = frappe.db.sql("""select sum(grading_meter) as grading_meter from `tabGreige Grading Child` 
							where item =%s and parent =%s order by date desc""", (self.item,self.name), as_dict=True)
			if check_process:
				process_meter = check_process[0].grading_meter
			if not process_meter:
				process_meter = 0
			self.append('greige_grading', {
				'item': greige_recv.item,
				'received_qty': self.total_received_meter,
				'short_length': greige_recv.short_length,
				'process_meter': process_meter,
				'remaining_meter': self.total_received_meter - greige_recv.short_length - process_meter,
				'grading_meter': self.grading_meter,
				'fabric_meter': self.fabric_meter,
				'net_grading_meter': self.grading_meter - self.fabric_meter,
				'date': datetime.now()
			})
		else:
			check_process = frappe.db.sql("""select sum(grading_meter) as grading_meter from `tabGreige Grading Child` 
							where item =%s and batch_no =%s and parent =%s order by date desc""", (self.item, self.batch_no, self.name), as_dict=True)
			if check_process:
				process_meter = check_process[0].grading_meter
			if not process_meter:
				process_meter = 0
			self.append('greige_grading', {
				'item': greige_recv.item,
				'batch_no': greige_recv.batch_no,
				'received_qty': self.total_received_meter,
				'short_length': greige_recv.short_length,
				'process_meter': process_meter,
				'remaining_meter': self.total_received_meter - greige_recv.short_length- process_meter,
				'grading_meter': self.grading_meter,
				'fabric_meter': self.fabric_meter,
				'net_grading_meter': self.grading_meter - self.fabric_meter,
				'date': datetime.now()
			})

		self.save(ignore_permissions=True)

		total_received_meter = 0
		total_short_length = 0
		total_process_meter = 0
		total_grading_meter = 0
		total_fabric_meter = 0
		total_net_grading_meter = 0
		for res in self.greige_grading:
			total_received_meter += res.received_qty
			total_short_length += res.short_length
			total_process_meter += res.process_meter
			total_grading_meter += res.grading_meter
			total_fabric_meter += res.fabric_meter
			total_net_grading_meter += res.net_grading_meter

		self.total_process_meter = total_process_meter
		self.total_remaining_meter = self.net_received_meter - total_grading_meter
		self.total_grading_meter = total_grading_meter
		self.total_fabric_meter = total_fabric_meter
		self.total_net_grading_meter = total_net_grading_meter

		self.grading_meter = 0
		self.fabric_meter = 0
		self.save(ignore_permissions=True)

		query = frappe.db.sql("""SELECT name From `tabGreige Mending Form` 
						where greige_grading_form = %s and docstatus = 1 limit 1""", (self.name), as_dict=True)
		if query:
			mending_form = frappe.get_doc("Greige Mending Form", query[0].name)
			mending_form.total_grading_meter = self.total_grading_meter
			mending_form.total_fabric_meter = self.total_fabric_meter
			mending_form.total_remaining_meter = mending_form.total_grading_meter - mending_form.total_mending_meter
			mending_form.flags.ignore_validate_update_after_submit = True
			mending_form.save(ignore_permissions=True)
		return True

	@frappe.whitelist()
	def edit_entry(self):
		if not self.line_no:
			frappe.throw(_("Please enter line number!"))

		if not self.grading_meter or self.grading_meter <= 0:
			frappe.throw(_("Grading Meter should be greater then the zero!"))

		query = """select name,date from `tabGreige Grading Child` where parent = '{0}' order by date limit {1},1""".format(self.name, self.line_no-1)
		result = frappe.db.sql(query,as_list=True)
		if result:
			process_meter = 0
			check_process = frappe.db.sql("""select sum(grading_meter) as grading_meter from `tabGreige Grading Child` 
									where item ='{0}' and batch_no ='{1}' and parent ='{2}' and date < '{3}'""".format(self.item, self.batch_no, self.name, result[0][1]), as_dict=True)
			if check_process:
				process_meter = check_process[0].grading_meter
			if not process_meter:
				process_meter = 0

			child_obj = frappe.get_doc("Greige Grading Child",result[0][0])

			query = frappe.db.sql("""SELECT SUM(total_net_mending_meter) as mending_qty From `tabGreige Mending Form` 
					where greige_grading_form = %s and docstatus = 1""",(self.name), as_dict=True)
			if query[0].mending_qty:
				grade_qty = self.total_net_grading_meter + self.grading_meter - child_obj.grading_meter
				if query[0].mending_qty > grade_qty:
					frappe.throw(_("<b>{0}</b> meter mending is already done against this Grading Form.").format(query[0].mending_qty))

			child_obj.process_meter = process_meter
			child_obj.remaining_meter = child_obj.received_qty - child_obj.short_length - process_meter
			child_obj.grading_meter = self.grading_meter
			child_obj.fabric_meter = self.fabric_meter
			child_obj.net_grading_meter = self.grading_meter - self.fabric_meter
			child_obj.flags.ignore_validate_update_after_submit = True
			child_obj.db_update()
			child_obj.save(ignore_permissions=True)

			query2 = """select name,date from `tabGreige Grading Child` where parent = '{0}' and date > '{1}' order by date""".format(self.name, child_obj.date)
			result2 = frappe.db.sql(query2,as_dict=True)
			for res in result2:
				process_meter = 0
				check_process = frappe.db.sql("""select sum(grading_meter) as grading_meter from `tabGreige Grading Child` 
														where item ='{0}' and batch_no ='{1}' and parent ='{2}' and date < '{3}'""".format(
					self.item, self.batch_no, self.name, res.date), as_dict=True)
				if check_process:
					process_meter = check_process[0].grading_meter
				if not process_meter:
					process_meter = 0
				line_doc = frappe.get_doc("Greige Grading Child",res.name)
				line_doc.process_meter = process_meter
				line_doc.remaining_meter = line_doc.received_qty - line_doc.short_length - process_meter
				line_doc.flags.ignore_validate_update_after_submit = True
				line_doc.db_update()
				line_doc.save(ignore_permissions=True)
		else:
			frappe.throw(_("Please enter valid line number!"))
		return True

	@frappe.whitelist()
	def update_summery(self):
		query = frappe.db.sql("""SELECT SUM(process_meter),SUM(grading_meter),SUM(fabric_meter),SUM(net_grading_meter) FROM `tabGreige Grading Child` where parent =%s""",(self.name),as_list=True)
		if query:
			self.total_process_meter = query[0][0]
			self.total_remaining_meter = self.net_received_meter - query[0][1]
			self.total_grading_meter = query[0][1]
			self.total_fabric_meter = query[0][2]
			self.total_net_grading_meter = query[0][3]
			self.flags.ignore_validate_update_after_submit = True
			self.line_no = 0
			self.grading_meter = 0
			self.fabric_meter = 0
			self.db_update()

			mn = frappe.db.sql("""SELECT name From `tabGreige Mending Form` 
									where greige_grading_form = %s and docstatus = 1 limit 1""", (self.name),
								  as_dict=True)
			if mn:
				mending_form = frappe.get_doc("Greige Mending Form", mn[0].name)
				mending_form.total_grading_meter = query[0][1]
				mending_form.total_fabric_meter = query[0][2]
				mending_form.total_remaining_meter = mending_form.total_grading_meter - mending_form.total_mending_meter
				mending_form.flags.ignore_validate_update_after_submit = True
				mending_form.save(ignore_permissions=True)
			return True

		return True

	@frappe.whitelist()
	def add_fabric(self):
		if not self.fabric_qty or self.fabric_qty <= 0:
			frappe.throw(_("Fabric Qty should be greater then the zero!"))
		else:
			total_received_meter = self.total_received_meter
			self.total_received_meter = total_received_meter + self.fabric_qty
			self.net_received_meter = total_received_meter + self.fabric_qty - self.total_short_length
			self.total_remaining_meter = total_received_meter + self.fabric_qty - self.total_grading_meter
			self.line_no = 0
			self.grading_meter = 0
			self.fabric_meter = 0
			self.append("tracking",{
				"quantity" : self.fabric_qty,
				"date":datetime.now(),
				"user":frappe.session.user
			})
			self.fabric_qty = 0
			self.flags.ignore_validate_update_after_submit = True
			self.save(ignore_permissions=True)
