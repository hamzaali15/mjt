# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.party import get_party_account
from  datetime import datetime
from erpnext.stock.doctype.batch.batch import get_batch_qty

class FabricOwnershipTransfer(Document):
	pass

@frappe.whitelist()
def change_owner(doc_name=None):
	doc = frappe.get_doc("Fabric Ownership Transfer",doc_name)
	if doc:
		if not doc.new_party_code:
			frappe.throw(_("Please select New party code first!"))
		batch = frappe.get_doc("Batch", doc.batch)
		if batch:
			batch_qty = get_batch_qty(batch.name)
			total_qty = 0
			for bq in batch_qty:
				total_qty += bq.qty
			old_supplier_account_type = get_party_account('Supplier', doc.old_patry_code, doc.company)
			new_supplier_account_type = get_party_account('Supplier', doc.new_party_code, doc.company)

			jv = frappe.new_doc('Journal Entry')
			jv.voucher_type = 'Journal Entry'
			jv.naming_series = 'JV-'
			jv.posting_date = datetime.now().date()
			jv.company = doc.company
			jv.fabric_ownership_transfer = doc.name

			# Entry for Customer
			total = 0
			if doc.rate:
				total = int(total_qty) * doc.rate
			jv.append('accounts', {
				'account': old_supplier_account_type,
				'party_type': "Supplier",
				'party': doc.old_patry_code,
				'credit_in_account_currency': total,
				'is_advance': 'No',
				'business_unit': doc.business_unit
			})
			# Entry for Supplier
			jv.append('accounts', {
				'account': new_supplier_account_type,
				'party_type': 'Supplier',
				'party': doc.new_party_code,
				'debit_in_account_currency': total,
				'is_advance': 'Yes',
				'business_unit': doc.business_unit
			})
			jv.save(ignore_permissions=True)
			jv.submit()

			batch.supplier = doc.new_party_code
			batch.party_name = doc.new_party_name
			batch.save(ignore_permissions=True)
			doc.change_owner = 1
			doc.save(ignore_permissions=True)
		return True



@frappe.whitelist()
def split_batch(doc_name,batch_no, item_code, warehouse, qty, new_batch_id=None):
	"""Split the batch into a new batch"""
	doc_f = frappe.get_doc("Fabric Ownership Transfer", doc_name)
	doc = frappe.get_doc("Batch", batch_no)

	if not doc_f.new_party_code:
		frappe.throw(_("Please select New party code first!"))

	batch = frappe.get_doc(dict(doctype='Batch',
								item=item_code,
								batch_id=new_batch_id,
								supplier=doc_f.new_party_code,
								party_name=doc_f.new_party_name,
								quality_code=doc.quality_code,
								quality_name=doc.quality_name,
								)).insert()

	company = frappe.db.get_value('Stock Ledger Entry', dict(
			item_code=item_code,
			batch_no=batch_no,
			warehouse=warehouse
		), ['company'])

	stock_entry = frappe.get_doc(dict(
		doctype='Stock Entry',
		purpose='Repack',
		company=company,
		items=[
			dict(
				item_code=item_code,
				qty=float(qty or 0),
				s_warehouse=warehouse,
				batch_no=batch_no,
				business_unit=doc_f.business_unit
			),
			dict(
				item_code=item_code,
				qty=float(qty or 0),
				t_warehouse=warehouse,
				batch_no=batch.name,
				business_unit=doc_f.business_unit
			),
		]
	))
	stock_entry.set_stock_entry_type()
	stock_entry.insert()
	stock_entry.submit()

	old_supplier_account_type = get_party_account('Supplier', doc_f.old_patry_code,doc_f.company)
	new_supplier_account_type = get_party_account('Supplier', doc_f.new_party_code,doc_f.company)

	jv = frappe.new_doc('Journal Entry')
	jv.voucher_type = 'Journal Entry'
	jv.naming_series = 'JV-'
	jv.posting_date = datetime.now().date()
	jv.company = doc_f.company
	jv.fabric_ownership_transfer = doc_f.name

	# Entry for Customer
	total = 0
	if doc_f.rate:
		total = int(qty) * doc_f.rate
	jv.append('accounts', {
		'account': old_supplier_account_type,
		'party_type': "Supplier",
		'party': doc_f.old_patry_code,
		'credit_in_account_currency': total,
		'is_advance': 'No',
		'business_unit': doc_f.business_unit

	})
	# Entry for Supplier
	jv.append('accounts', {
		'account': new_supplier_account_type,
		'party_type': 'Supplier',
		'party': doc_f.new_party_code,
		'debit_in_account_currency': total,
		'is_advance': 'No',
		'business_unit': doc_f.business_unit

	})
	jv.save(ignore_permissions=True)
	jv.submit()
	return batch.name



@frappe.whitelist()
def split_existing_batch(doc_name, item_code, batch_no, s_warehouse, qty, exit_batch_id=None, t_warehouse=None):
	doc_f = frappe.get_doc("Fabric Ownership Transfer", doc_name)
	exit_batch_id = frappe.get_doc("Batch", exit_batch_id)

	if not exit_batch_id.supplier:
		frappe.throw(_("No Party found in Existing Batch!"))
	company = frappe.db.get_value('Stock Ledger Entry', dict(
		item_code=item_code,
		batch_no=batch_no,
		warehouse=s_warehouse
	), ['company'])

	stock_entry = frappe.get_doc(dict(
		doctype='Stock Entry',
		purpose='Repack',
		company=company,
		items=[
			dict(
				item_code=item_code,
				qty=float(qty or 0),
				s_warehouse=s_warehouse,
				batch_no=batch_no,
				business_unit=doc_f.business_unit
			),
			dict(
				item_code=exit_batch_id.item,
				qty=float(qty or 0),
				t_warehouse=t_warehouse,
				batch_no=exit_batch_id.name,
				business_unit=doc_f.business_unit
			),
		]
	))
	stock_entry.set_stock_entry_type()
	stock_entry.insert()
	stock_entry.submit()

	old_supplier_account_type = get_party_account('Supplier', doc_f.old_patry_code, doc_f.company)
	new_supplier_account_type = get_party_account('Supplier', exit_batch_id.supplier, doc_f.company)

	jv = frappe.new_doc('Journal Entry')
	jv.voucher_type = 'Journal Entry'
	jv.naming_series = 'JV-'
	jv.posting_date = datetime.now().date()
	jv.company = doc_f.company
	jv.fabric_ownership_transfer = doc_f.name

	# Entry for Customer
	total = 0
	if doc_f.rate:
		total = int(qty) * doc_f.rate
	jv.append('accounts', {
		'account': old_supplier_account_type,
		'party_type': "Supplier",
		'party': doc_f.old_patry_code,
		'credit_in_account_currency': total,
		'is_advance': 'No',
		'business_unit': doc_f.business_unit

	})
	# Entry for Supplier
	jv.append('accounts', {
		'account': new_supplier_account_type,
		'party_type': 'Supplier',
		'party': exit_batch_id.supplier,
		'debit_in_account_currency': total,
		'is_advance': 'No',
		'business_unit': doc_f.business_unit

	})
	jv.save(ignore_permissions=True)
	jv.submit()
	return True
