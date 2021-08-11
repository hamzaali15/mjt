from __future__ import unicode_literals
import frappe
from frappe import _
from mjt.mjt.doctype.design.design import set_design_nos
from erpnext.stock.doctype.batch.batch import get_batch_no,get_batch_qty
from frappe.utils import flt, cint, get_link_to_form

def update_design(sle, method):
    if sle.voucher_type == "Stock Entry":
        sel = frappe.get_doc("Stock Entry Detail",sle.voucher_detail_no)
        if sel.design_no:
            sle.design_no = sel.design_no
    # if sle.voucher_type == "Purchase Receipt":
    #     pass
    #     sel = frappe.get_doc("Purchase Receipt Item",sle.voucher_detail_no)
    #     # if sel.design_no:
    #     #     sle.design_no = sel.design_no
    if sle.voucher_type == "Delivery Note":
        sel = frappe.get_doc("Delivery Note Item",sle.voucher_detail_no)
        if sel.design_no:
            sle.design_no = sel.design_no

    if sle.batch_no:
        batch = frappe.get_doc("Batch", sle.batch_no)
        if batch:
            sle.party_code = batch.supplier
            if batch.supplier:
                sle.party_name = frappe.db.get_value("Supplier", batch.supplier, "supplier_name")
            sle.quality_code = batch.quality_code
            sle.quality_name = batch.quality_name
            sle.design_no = batch.design_no
    sle.db_update()


def update_finish_rate(st, method):
    if st.stock_entry_type == "Manufacture":
        total = 0
        for i in st.items:
            if i.s_warehouse and not i.t_warehouse:
                total += i.amount
        line_total_qty = 0
        for i in st.items:
            if not i.s_warehouse and i.t_warehouse:
                line_total_qty += i.qty
        for i in st.items:
            if not i.s_warehouse and i.t_warehouse:
                i.basic_rate = total/line_total_qty if total else 0

def validate_design_no(obj, method):
    for itm in obj.items:
        if frappe.db.get_value("Item", itm.item_code, "has_design") == 1 and not itm.design_no:
            frappe.throw(_("The selected item <b>{0}</b> is required the Design No!").format(itm.item_code))


def set_batch_nos(doc, warehouse_field, throw=False):
    """Automatically select `batch_no` for outgoing items in item table"""
    for d in doc.items:
        qty = d.get('stock_qty') or d.get('transfer_qty') or d.get('qty') or 0
        has_batch_no = frappe.db.get_value('Item', d.item_code, 'has_batch_no')
        warehouse = d.get(warehouse_field, None)
        if has_batch_no and warehouse and qty > 0:
            if not d.batch_no:
                d.batch_no = get_batch_no(d.item_code, warehouse, qty, throw, d.serial_no)
            else:
                batch_qty = get_batch_qty(batch_no=d.batch_no, warehouse=warehouse, posting_date=doc.posting_date, posting_time=doc.posting_time)
                if flt(batch_qty, d.precision("qty")) < flt(qty, d.precision("qty")):
                    frappe.throw(_("Row #{0}: The batch {1} has only {2} qty. Please select another batch which has {3} qty available or split the row into multiple rows, to deliver/issue from multiple batches").format(d.idx, d.batch_no, batch_qty, qty))


def validate_stock_ent_design_qty(obj,method):
    set_batch_nos(obj, 's_warehouse', True)
    set_design_nos(obj, 's_warehouse')
    if obj.stock_entry_type == "Manufacture" and obj.process_order:
        for itm in obj.items:
            if itm.allow_zero_valuation_rate:
                itm.allow_zero_valuation_rate = 0

def validate_sale_inv_design_qty(obj,method):
    if obj._action != 'submit' and obj.update_stock and not obj.is_return:
        set_batch_nos(obj, 'warehouse', True)
        set_design_nos(obj, 'warehouse', True)

def validate_delivery_note_design_qty(obj,method):
    if obj._action != 'submit' and not obj.is_return:
        set_batch_nos(obj, 'warehouse', True)
        set_design_nos(obj, 'warehouse', True)

def fill_design_no(doc, method):
    for res in doc.items:
        if res.batch_no:
            batch = frappe.get_doc("Batch", res.batch_no)
            if batch.design_no:
                res.design_no = batch.design_no