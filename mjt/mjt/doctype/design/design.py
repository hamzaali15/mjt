# -*- coding: utf-8 -*-
# Copyright (c) 2020, earthians and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, get_link_to_form

class UnableToSelectBatchError(frappe.ValidationError):
	pass

class Design(Document):
	pass

@frappe.whitelist()
def get_design_qty(design_no=None, warehouse=None, item_code=None, posting_date=None, posting_time=None):
	"""Returns batch actual qty if warehouse is passed,
		or returns dict of qty by warehouse if warehouse is None
	The user must pass either batch_no or batch_no + warehouse or item_code + warehouse
	:param batch_no: Optional - give qty for this batch no
	:param warehouse: Optional - give qty for this warehouse
	:param item_code: Optional - give qty for this item"""
	out = 0
	if design_no and warehouse:
		cond = ""

		out = float(frappe.db.sql("""select sum(actual_qty)
			from `tabStock Ledger Entry`
			where warehouse=%s and design_no=%s {0}""".format(cond),
			(warehouse, design_no))[0][0] or 0)

	if design_no and not warehouse:
		out = frappe.db.sql('''select warehouse, sum(actual_qty) as qty
			from `tabStock Ledger Entry`
			where design_no=%s
			group by warehouse''', design_no, as_dict=1)

	if not design_no and warehouse:
		out = frappe.db.sql('''select design_no, sum(actual_qty) as qty
			from `tabStock Ledger Entry`
			where warehouse=%s
			group by design_no''', (warehouse), as_dict=1)

	return out

def set_design_nos(doc, warehouse_field, throw=False):
	"""Automatically select `batch_no` for outgoing items in item table"""
	for d in doc.items:
		qty = d.get('stock_qty') or d.get('transfer_qty') or d.get('qty') or 0
		has_design = frappe.db.get_value('Item', d.item_code, 'has_design')
		warehouse = d.get(warehouse_field, None)
		if has_design and warehouse and qty > 0:
			if not d.design_no:
				frappe.throw(_("The selected item <b>{0}</b> is required the Design No!").format(d.item_code))
			else:
				design_qty = get_design_qty(design_no=d.design_no, warehouse=warehouse)
				if flt(design_qty, d.precision("qty")) < flt(qty, d.precision("qty")):
					frappe.throw(_("Row #{0}: The Design {1} has only {2} qty. Please select another design which has {3} qty available").format(d.idx, d.design_no, design_qty, qty))
