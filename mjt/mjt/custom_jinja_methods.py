
from __future__ import unicode_literals
import frappe
from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def get_batch_fabric_qty(batch):
    batch_qty = float(frappe.db.sql("""select sum(actual_qty)
            from `tabStock Ledger Entry`
            where warehouse = 'Greige Fresh - MJT' and batch_no='{0}' and actual_qty > 0""".format(batch.name))[0][0] or 0)
    qty = "{:,}".format(batch_qty)
    return qty

@frappe.whitelist()
def get_finish_product(batch):
    lot_like = str((batch.name).split("-")[0]) + "%"
    batch_qty = float(frappe.db.sql("""select sum(actual_qty)
                from `tabStock Ledger Entry`
                where warehouse = 'Greige Fresh - MJT' and batch_no='{0}' and actual_qty > 0""".format(batch.name))[0][
                          0] or 0)
    data_list = []
    lst = []
    data_dict = {}
    total_fresh_product = 0
    total_finish_product = 0
    result = frappe.db.sql("""select distinct ti.item_group from `tabProcess Order` as tp 
                           inner join`tabProcess Order Finish Item` as tpfi on tp.name = tpfi.parent
                           inner join `tabItem` as ti on ti.name = tpfi.item
                           where tp.department = 'Cutting & Packing' and tpfi.lot_no like %s""", (lot_like),
                           as_dict=True)
    for res in result:
        item_group = "<b>" + str(res.item_group) + " Production</b>"
        lst.append(dict({"item": item_group, "qty": ""}))
        total_qty = 0.0
        result1 = frappe.db.sql("""select tpfi.item,ti.item_name,ti.item_group,sum(tpfi.quantity) as qty from `tabProcess Order` as tp 
                     inner join`tabProcess Order Finish Item` as tpfi on tp.name = tpfi.parent
                     inner join `tabItem` as ti on ti.name = tpfi.item
                     where tp.department = 'Cutting & Packing' and tpfi.lot_no like %s and ti.item_group = %s
                     group by tpfi.item,ti.item_name,ti.item_group""", (lot_like, res.item_group), as_dict=True)
        for r in result1:
            total_qty += r.qty
            total_finish_product += r.qty
            lst.append(dict({"item": r.item_name, "qty": r.qty}))
            if r.item_group == 'Fresh':
                total_fresh_product += r.qty

        f_name = "<b>Total " + str(res.item_group) + " Production</b><br/>"
        f_qty = "<b>" + str(total_qty) + "</b><br/>"
        lst.append(dict({"item": f_name, "qty": f_qty}))
    data_list.append(lst)

    data_dict["party_name"] = batch.party_name
    data_dict["total_gray"] = batch_qty
    data_dict["factory_shortage"] = batch_qty - total_fresh_product
    data_dict["total_finish_product"] = total_finish_product
    data_dict["age"] = "0%" if not batch_qty else str((total_finish_product * 100) / batch_qty) + "%"
    data_dict["actual_shortage"] = batch_qty - total_finish_product
    data_dict["age_short"] = "0%" if not batch_qty else str(((batch_qty - total_finish_product) * 100) / batch_qty) + "%"
    data_list.append(data_dict)
    return data_list
