
from __future__ import unicode_literals
import frappe, erpnext
from frappe.utils import flt, cint, nowdate
from frappe import throw, _
import frappe.defaults
from frappe.utils import getdate
from erpnext.stock.get_item_details import get_conversion_factor
from erpnext.buying.utils import validate_for_items
from erpnext.accounts.doctype.pricing_rule.utils import (apply_pricing_rule_on_transaction)
from erpnext.controllers.sales_and_purchase_return import validate_return
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt

class OverridePurchaseReceipt(PurchaseReceipt):
    def validate(self):
        if not self.process_order:
            super(OverridePurchaseReceipt, self).validate()
        else:
            self.validate_posting_time()
            self.stock_validate()
            self.account_validate()
            if getattr(self, "supplier", None) and not self.supplier_name:
                self.supplier_name = frappe.db.get_value("Supplier", self.supplier, "supplier_name")

            self.validate_items()
            self.set_qty_as_per_stock_uom()
            self.validate_stock_or_nonstock_items()
            self.validate_warehouse()
            self.validate_from_warehouse()
            self.set_supplier_address()
            self.validate_asset_return()

            if self.doctype == "Purchase Invoice":
                self.validate_purchase_receipt_if_update_stock()

            if self.doctype == "Purchase Receipt" or (self.doctype == "Purchase Invoice" and self.update_stock):
                # self.validate_purchase_return()
                self.validate_rejected_warehouse()
                self.validate_accepted_rejected_qty()
                validate_for_items(self)

                # sub-contracting
                self.validate_for_subcontracting()
                self.create_raw_materials_supplied("supplied_items")
                self.set_landed_cost_voucher_amount()

            if self.doctype in ("Purchase Receipt", "Purchase Invoice"):
                self.update_valuation_rate()

            if self._action == "submit":
                self.make_batches('warehouse')
            else:
                self.set_status()

            self.po_required()
            self.validate_with_previous_doc()
            self.validate_uom_is_integer("uom", ["qty", "received_qty"])
            self.validate_uom_is_integer("stock_uom", "stock_qty")
            self.validate_cwip_accounts()

            self.check_on_hold_or_closed_status()

            if getdate(self.posting_date) > getdate(nowdate()):
                throw(_("Posting Date cannot be future date"))

    # update valuation rate
    def update_valuation_rate(self, reset_outgoing_rate=True):
        """
            item_tax_amount is the total tax amount applied on that item
            stored for valuation

            TODO: rename item_tax_amount to valuation_tax_amount
        """
        stock_and_asset_items = self.get_stock_items() + self.get_asset_items()

        stock_and_asset_items_qty, stock_and_asset_items_amount = 0, 0
        last_item_idx = 1
        for d in self.get("items"):
            if d.item_code and d.item_code in stock_and_asset_items:
                stock_and_asset_items_qty += flt(d.qty)
                stock_and_asset_items_amount += flt(d.base_net_amount)
                last_item_idx = d.idx

        total_valuation_amount = sum([flt(d.base_tax_amount_after_discount_amount) for d in self.get("taxes")
                                      if d.category in ["Valuation", "Valuation and Total"]])

        valuation_amount_adjustment = total_valuation_amount
        for i, item in enumerate(self.get("items")):
            if item.item_code and item.qty and item.item_code in stock_and_asset_items:
                item_proportion = flt(
                    item.base_net_amount) / stock_and_asset_items_amount if stock_and_asset_items_amount \
                    else flt(item.qty) / stock_and_asset_items_qty

                if i == (last_item_idx - 1):
                    item.item_tax_amount = flt(valuation_amount_adjustment,
                                               self.precision("item_tax_amount", item))
                else:
                    item.item_tax_amount = flt(item_proportion * total_valuation_amount,
                                               self.precision("item_tax_amount", item))
                    valuation_amount_adjustment -= item.item_tax_amount

                self.round_floats_in(item)
                if flt(item.conversion_factor) == 0.0:
                    item.conversion_factor = get_conversion_factor(item.item_code, item.uom).get(
                        "conversion_factor") or 1.0

                qty_in_stock_uom = flt(item.qty * item.conversion_factor)
                if not self.process_order:
                    item.rm_supp_cost = self.get_supplied_items_cost(item.name, reset_outgoing_rate)
                item.valuation_rate = ((item.base_net_amount + item.item_tax_amount + item.rm_supp_cost
                                        + flt(item.landed_cost_voucher_amount)) / qty_in_stock_uom)
            else:
                item.valuation_rate = 0.0

    def account_validate(self):
        if not self.get('is_return'):
            self.validate_qty_is_not_zero()

        if self.get("_action") and self._action != "update_after_submit":
            self.set_missing_values(for_validate=True)

        self.ensure_supplier_is_not_blocked()

        self.validate_date_with_fiscal_year()
        self.validate_party_accounts()

        self.validate_inter_company_reference()

        self.set_incoming_rate()

        if self.meta.get_field("currency"):
            self.calculate_taxes_and_totals()

            if not self.meta.get_field("is_return") or not self.is_return:
                self.validate_value("base_grand_total", ">=", 0)

            validate_return(self)
            self.set_total_in_words()

        self.validate_all_documents_schedule()

        if self.meta.get_field("taxes_and_charges"):
            self.validate_enabled_taxes_and_charges()
            self.validate_tax_account_company()

        self.validate_party()
        self.validate_currency()

        if self.doctype == 'Purchase Invoice':
            self.calculate_paid_amount()

        if self.doctype in ['Purchase Invoice', 'Sales Invoice']:
            pos_check_field = "is_pos" if self.doctype == "Sales Invoice" else "is_paid"
            if cint(self.allocate_advances_automatically) and not cint(self.get(pos_check_field)):
                self.set_advances()

            if self.is_return:
                self.validate_qty()
            else:
                self.validate_deferred_start_and_end_date()

            self.set_inter_company_account()

        validate_regional(self)

        validate_einvoice_fields(self)

        if self.doctype != 'Material Request':
            apply_pricing_rule_on_transaction(self)

    def stock_validate(self):
        if not self.get('is_return'):
            self.validate_inspection()
        self.validate_serialized_batch()
        self.validate_customer_provided_item()
        self.set_rate_of_stock_uom()
        self.validate_internal_transfer()
        self.validate_putaway_capacity()

@erpnext.allow_regional
def validate_regional(doc):
    pass

@erpnext.allow_regional
def validate_einvoice_fields(doc):
    pass
