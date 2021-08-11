
import frappe
from frappe import _
from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.model.mapper import get_mapped_doc
import json
from frappe import _

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_batch_no(doctype, txt, searchfield, start, page_len, filters):
    cond = ""
    if filters.get("posting_date"):
        cond = "and (batch.expiry_date is null or batch.expiry_date >= %(posting_date)s)"

    batch_nos = None
    if filters.get("customer"):
        supplier = frappe.get_list('Double Ledger Parties', filters={'customer': filters.get("customer")}, fields=['supplier'], limit=1)
        if supplier:
            cond = " and batch.supplier = '{0}'".format(supplier[0].supplier)

    args = {
        'item_code': filters.get("item_code"),
        'warehouse': filters.get("warehouse"),
        'posting_date': filters.get('posting_date'),
        'txt': "%{0}%".format(txt),
        "start": start,
        "page_len": page_len
    }

    having_clause = "having sum(sle.actual_qty) > 0"
    if filters.get("is_return"):
        having_clause = ""

    if args.get('warehouse'):
        batch_nos = frappe.db.sql("""select sle.batch_no, round(sum(sle.actual_qty),2), sle.stock_uom,
                concat('MFG-',batch.manufacturing_date), concat('EXP-',batch.expiry_date)
            from `tabStock Ledger Entry` sle
                INNER JOIN `tabBatch` batch on sle.batch_no = batch.name
            where
                batch.disabled = 0
                and sle.item_code = %(item_code)s
                and sle.warehouse = %(warehouse)s
                and (sle.batch_no like %(txt)s
                or batch.expiry_date like %(txt)s
                or batch.manufacturing_date like %(txt)s)
                and batch.docstatus < 2
                {cond}
                {match_conditions}
            group by batch_no {having_clause}
            order by batch.expiry_date, sle.batch_no desc
            limit %(start)s, %(page_len)s""".format(
                cond=cond,
                match_conditions=get_match_cond(doctype),
                having_clause = having_clause
            ), args)
        return batch_nos
    else:
        return frappe.db.sql("""select name, concat('MFG-', manufacturing_date), concat('EXP-',expiry_date) from `tabBatch` batch
            where batch.disabled = 0
            and item = %(item_code)s
            and (name like %(txt)s
            or expiry_date like %(txt)s
            or manufacturing_date like %(txt)s)
            and docstatus < 2
            {0}
            {match_conditions}
            order by expiry_date, name desc
            limit %(start)s, %(page_len)s""".format(cond, match_conditions=get_match_cond(doctype)), args)


@frappe.whitelist()
def get_batch_list(customer,item_code,warehouse=None):
    if warehouse:
        batch_nos = None
        if customer:
            supplier = frappe.get_list('Double Ledger Parties', filters={'customer': customer}, fields=['supplier'], limit=1)
            if supplier:
                cond = " and batch.supplier = '{0}'".format(supplier[0].supplier)

        args = {
            'item_code': item_code,
            'warehouse': warehouse
            # "page_len": 100
        }

        having_clause = "having sum(sle.actual_qty) > 0"

        if args.get('warehouse'):
            batch_nos = frappe.db.sql("""select sle.batch_no,batch.design_no, round(sum(sle.actual_qty),2)
                from `tabStock Ledger Entry` sle
                    INNER JOIN `tabBatch` batch on sle.batch_no = batch.name
                where
                    batch.disabled = 0
                    and sle.item_code = %(item_code)s
                    and sle.warehouse = %(warehouse)s
                    and batch.docstatus < 2
                    {cond}
                    {match_conditions}
                group by batch_no {having_clause}
                order by batch.expiry_date, sle.batch_no desc""".format(
                    cond=cond,
                    match_conditions=get_match_cond('Batch'),
                    having_clause = having_clause
                ), args)
            return batch_nos
        else:
            return frappe.db.sql("""select name, design_no from `tabBatch` batch
                where batch.disabled = 0
                and item = %(item_code)s
                and docstatus < 2
                {0}
                {match_conditions}
                order by expiry_date, name desc
                """.format(cond, match_conditions=get_match_cond('Batch')), args)
                # limit %(page_len)s
    else:
       return False


@frappe.whitelist()
def get_process_order_finish_item(doc_name,filters_json=None):
    if filters_json:
        raw_dict = {}
        finish_dict = {}
        process_dict = {}
        filters= json.loads(filters_json)
        for res in filters:
            if res[0] == 'Process Order':
                process_dict[res[1]] = [res[2],res[3]]
            
            if res[0] == 'Process Order Item':
                raw_dict[res[1]] = [res[2],res[3]]
            
            if res[0] == 'Process Order Finish Item':
                finish_dict[res[1]] = [res[2],res[3]]
        
        process_order_lst = []
        if process_dict:
            process_orders = frappe.get_list('Process Order', filters=process_dict, fields=('name'))
            for p in process_orders:
                process_order_lst.append(p.get('name'))
        
        if raw_dict:
            if process_order_lst:
                raw_dict['parent'] = ['in',process_order_lst] 

            process_orders_item = frappe.get_list('Process Order Item', filters=raw_dict, fields=('parent'))
            for p in process_orders_item:
                if p.get('parent') not in process_order_lst:
                    process_order_lst.append(p.get('parent'))

        if process_order_lst:
            finish_dict['parent'] = ['in',process_order_lst]

        if finish_dict:
            finish_items = frappe.get_list('Process Order Finish Item', filters=finish_dict, fields='*')
            if finish_items:
                for res in finish_items:
                    if res.quantity > 0:
                        item = frappe.get_doc('Item', res.item)
                        p_order = frappe.get_doc('Process Order', res.parent)
                        res['description'] = item.description
                        res['stock_uom'] = item.stock_uom
                        res['uom'] = item.stock_uom
                        res['warehouse'] = p_order.fg_warehouse
                        res['business_unit'] = p_order.business_unit
                return finish_items
            else:
                frappe.throw(_("No Data Found."))
    else:
        frappe.throw(_("Please set the filter."))
    return False


def set_workstation_net_rate(doc,method):
    total = 0 
    total +=  doc.p_electricity_cost if doc.p_electricity_cost else 0
    total +=  doc.p_consumable_cost if doc.p_consumable_cost else 0
    total +=  doc.p_rent_cost if doc.p_rent_cost else 0
    total +=  doc.p_wages if doc.p_wages else 0
    doc.p_net_hour_rate = total