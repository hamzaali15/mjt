# Copyright (c) 2021, RF and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from  datetime import datetime

class DesignReceivingandApproval(Document):
	pass

@frappe.whitelist()
def validate(self, method):
		ordered_qtyy = frappe.db.sql("""select sum(soi.qty) from `tabSales Order` as so left join `tabSales Order Item` as soi on soi.parent = %s where so.name = %s and soi.item_code = %s group by soi.item_code""", (self.sales_order, self.sales_order, self.category))
		warehousee = frappe.db.sql("""select sum(actual_qty) from `tabStock Ledger Entry` where warehouse = 'Finished Goods - MJT' and item_code = %s group by item_code, warehouse""", (self.category))
		# warehousee = frappe.db.sql("""select sum(actual_qty) from `tabStock Ledger Entry` where warehouse = 'Finished Goods - MJT' and item_code = %s and design_no = %s group by item_code, warehouse""", (self.category, self.design_no))
		production_pc = frappe.db.sql("""select sum(qty) from `tabDelivery Note Item` where against_sales_order = %s and item_code = %s group by item_code""", (self.sales_order, self.category))
		sales_returnn = frappe.db.sql("""select sum(dni.qty) from `tabDelivery Note` as dn left join `tabDelivery Note Item` as dni on dni.parent = dn.name where dn.is_return = 1 and dni.against_sales_order = %s and dni.item_code = %s group by dni.item_code""", (self.sales_order, self.category))
		if ordered_qtyy:
			self.ordered_qty = ordered_qtyy[0][0]
		else:
			self.ordered_qty = 0
		if warehousee:
			self.in_warehouse = warehousee[0][0]
		else:
			self.in_warehoue = 0
		if production_pc:
			self.production_pcs = production_pc[0][0]
		else:
			self.production_pcs = 0
		if sales_returnn:
			self.sales_return = sales_returnn[0][0]
		else:
			self.sales_return = 0
		
		if self.production_pcs and self.sales_return == 0:
			self.balance_pcs = self.ordered_qty - self.production_pcs + self.sales_return
		elif self.production_pcs and self.sales_return:
			self.balance_pcs = self.ordered_qty - self.production_pcs + self.sales_return