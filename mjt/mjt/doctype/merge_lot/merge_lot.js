// Copyright (c) 2021, earthians and contributors
// For license information, please see license.txt

frappe.ui.form.on('Merge Lot', {
        refresh: function(frm) {
            if (frm.doc.__islocal) {
                frm.set_value("date", frappe.datetime.now_date());
            }
            frm.set_query('warehouse', function() {
                return {
                    filters: {
                        "company":frm.doc.company,
                        "is_group":0
                    }
                }
            });
            frm.set_query('item_code', function() {
                return {
                    filters: {
                       "has_batch_no":1
                    }
                }
            });
            frm.set_query('lot_no', function() {
                return {
                    filters: {
                       'item': frm.doc.item_code || undefined,
                       'quality_code': frm.doc.quality || undefined 
                    }
                }
            });
            frm.trigger('merge_qty_in_existing_lot')
            frm.fields_dict.get_lots.$input.addClass("btn-primary");
        },
        merge_qty_in_existing_lot: function(frm){
            frm.set_df_property('lot_no', 'reqd', frm.doc.merge_qty_in_existing_lot ? 1 : 0);
        },
        edit_date_and_time: function(frm){
            if(frm.doc.edit_date_and_time == 1){
                frm.set_df_property('date', 'read_only', 0);
                frm.set_df_property('current_time', 'read_only', 0);
            }
            else{
                frm.set_df_property('date', 'read_only', 1);
                frm.set_df_property('current_time', 'read_only', 1);
            }
        },
        party_code : function(frm){
            frm.clear_table('lots');
            frm.refresh_field('lots');
        },
        quality : function(frm){
            frm.clear_table('lots');
            frm.refresh_field('lots');
        },
        warehouse : function(frm){
            frm.clear_table('lots');
            frm.refresh_field('lots');
        },
        item_code : function(frm){
            frm.clear_table('lots');
            frm.refresh_field('lots');
        },
        get_lots: function(frm){
            frappe.call({
                doc: frm.doc,
                method: "get_lots",
                freeze: true,
                callback: function(r) {
                    if(r.message){
                        frm.clear_table('lots');
                        for (const d of r.message){
                            var row = frm.add_child('lots');
                            row.lot_no = d.lot_no;
                            row.party_name = d.party_name;
                            row.quality_name = d.quality_name;
                            row.avl_qty = d.avl_qty;
                            row.merge_qty = 0;
                        }
                        frm.refresh_field('lots');
                    }
                    else{
                        frappe.throw(__("No Data Found!"))
                    }
                }
            });
        }
    });
    