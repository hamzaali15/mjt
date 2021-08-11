// For license information, please see license.txt

frappe.ui.form.on('Greige Receiving Form', {
    onload:function(frm){
        if (frm.doc.__islocal) {
            frm.set_value("date", frappe.datetime.now_date());
        }
    },
	refresh: function(frm) {
        if( frm.doc.docstatus ==1){
            frm.add_custom_button(__('Return'), function () {
				frappe.call({
					doc: frm.doc,
					method: 'retrun_back_qty_to_party',
					callback: function(r) {
						var d = new frappe.ui.Dialog({
                            title: __('Add Return Quantity'),
                            fields: r.message,
                            primary_action_label: __("Return"),
                            primary_action(values) {
                                d.hide();
                                frappe.call({
                                    method: "mjt.mjt.doctype.greige_receiving_form.greige_receiving_form.update_return_qty",
                                    args: {
                                        doc_name: frm.doc.name,
                                        values: values
                                    },
                                    freeze: true,
                                    callback: function() {
                                        frm.reload_doc();
                                    }
                                });
                            }
                        });
                        d.show();
					}
				});
			}).addClass("btn-primary");
        }

	    frm.set_query('batch_no', function() {
            return {
                filters: {
                    "item":frm.doc.item
                }
            }
        });
        frm.set_query('quality_code', function() {
            return {
                filters: {
                    "is_group":0
                }
            }
        });
        frm.set_query('item', function() {
            return {
                filters: {
                    "is_griege_fabric_item":1
                }
            }
        });
        frm.set_query('purchase_order', function() {
            return {
                filters: {
                    "supplier":frm.doc.customer_code,
                    "docstatus":1
                }
            }
        });
        frm.set_query('transporter', function() {
            return {
                filters: {
                    "is_transporter":1
                }
            }
        });
        frm.set_query('driver', function() {
            return {
                filters: {
                    "transporter":frm.doc.transporter
                }
            }
        });
        if(frm.doc.purchase_order){
            frm.trigger('purchase_order');
        }
	},
    purchase_order:function(frm){
         frappe.call({
            doc: frm.doc,
            method: "get_purchase_order_item",
            callback: function(data) {
                let obj = data.message;
                if(obj){
                    frm.set_query('item', function() {
                        return {
                             "filters":{"name":["in",obj]}
                        }
                    });
                }
            }
        })
    },
    edit_date: function(frm){
        if(frm.doc.edit_date == 1){
            frm.set_df_property('date', 'read_only', 0);
            frm.set_df_property('current_time', 'read_only', 0);
        }
        else{
            frm.set_df_property('date', 'read_only', 1);
            frm.set_df_property('current_time', 'read_only', 1);
        }
    },
    driver: function(frm){
        frm.set_value("transport_receipt_date", frappe.datetime.now_date());
    }
});
