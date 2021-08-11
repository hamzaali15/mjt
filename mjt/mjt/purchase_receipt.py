import frappe
from frappe import _

def swap_supplied_data(doc, method):
	if doc.process_order:
		for res in doc.supplied_items1:
			doc.append('supplied_items',{
				'rm_item_code': res.rm_item_code,
					'batch_no': res.batch_no,
					'design_no': res.design_no,
					'description': res.description,
					'required_qty': res.required_qty,
					'consumed_qty': res.consumed_qty,
					'stock_uom': res.stock_uom,
					'rate': res.rate,
					'amount': res.amount
			})
		doc.db_update()

def change_process_order_status(doc, method):
	if doc.process_order:
		process_order = frappe.get_doc("Process Order",doc.process_order)
		if process_order.status == 'In Process':
			process_order.status = 'Completed'
			process_order.db_update()
		else:
			frappe.throw(_("Process Order is Completed"))

def make_raw_material_dl_entry(doc, mathod):
	pass
# 	if doc.process_order:
# 		process_order = frappe.get_doc('Process Order', doc.process_order)
# 		target_warehouse = frappe.get_doc('Warehouse', process_order.fg_warehouse)
# 		supplier_warehouse = frappe.get_doc('Warehouse', process_order.wip_warehouse)
# 		for res in doc.supplied_items:
# 			if res.amount:
# 				cost_center = frappe.db.get_values("Company", doc.company, ["cost_center"])[0]
# 				if cost_center:
# 					cost_center = cost_center[0]
# 				item_cost_center = frappe.db.get_value("Item Default",{'parent': res.rm_item_code, 'company': doc.company},["buying_cost_center"])
# 				gl_list = frappe.new_doc('GL Entry')
# 				args = {
# 					"posting_date": doc.posting_date,
# 					"account": target_warehouse.account,
# 					"against": supplier_warehouse.account,
# 					"cost_center": item_cost_center or cost_center,
# 					"remarks": "Accounting Entry for Stock",
# 					"debit": res.amount,
# 					"is_opening": "No",
# 					"company": doc.company,
# 					"voucher_type": 'Purchase Receipt',
# 					"voucher_no": doc.name,
# 					"business_unit": process_order.business_unit}
# 				gl_list.update(args)
# 				gl_list.flags.ignore_permissions = 1
# 				gl_list.validate()
# 				gl_list.db_insert()
# 				gl_list.run_method("on_update_with_args", False, 'Yes', False)
# 				gl_list.flags.ignore_validate = True
# 				gl_list.submit()
#
# 				gl_list = frappe.new_doc('GL Entry')
# 				args = {
# 					"posting_date": doc.posting_date,
# 					"account": supplier_warehouse.account,
# 					"against": target_warehouse.account,
# 					"cost_center": item_cost_center or cost_center,
# 					"remarks": "Accounting Entry for Stock",
# 					"credit": res.amount,
# 					"is_opening ": "No",
# 					"company": doc.company,
# 					"voucher_type": 'Purchase Receipt',
# 					"voucher_no": doc.name,
# 					"business_unit": process_order.business_unit}
# 				gl_list.update(args)
# 				gl_list.flags.ignore_permissions = 1
# 				gl_list.validate()
# 				gl_list.db_insert()
# 				gl_list.run_method("on_update_with_args", False, 'Yes', False)
# 				gl_list.flags.ignore_validate = True
# 				gl_list.submit()


