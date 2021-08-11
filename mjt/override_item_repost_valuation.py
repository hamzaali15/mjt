import frappe
from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import RepostItemValuation,repost

class OverrideRepostItemValuation(RepostItemValuation):
    def on_submit(self):
        frappe.enqueue(repost, timeout=1800, queue='long', job_name='repost_sle', now=True, doc=self)