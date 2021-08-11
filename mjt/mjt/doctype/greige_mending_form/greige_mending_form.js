// Copyright (c) 2020, Dexciss Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('Greige Mending Form', {
    onload:function(frm){
        if (frm.doc.__islocal) {
            frm.set_value("date", frappe.datetime.now_date());
        }
    },
    setup: function(frm) {
		frm.add_fetch("greige_grading_form", "total_net_grading_meter", "total_remaining_meter");
	},
    refresh: function(frm){
	    frm.set_query('greige_grading_form', function() {
            return {
                filters: {
//                    "customer_code":frm.doc.customer_code,
                    "docstatus":1
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
        frm.set_query('rejected_warehouse', function() {
            return {
                filters: {
                    "company":frm.doc.company,
                    "is_group":0
                }
            }
        });
        frm.set_query('warehouse', function() {
            return {
                filters: {
                    "company":frm.doc.company,
                    "is_group":0
                }
            }
        });
    },
    before_submit: function(frm) {
        frm.clear_table("greige_mending");
        frm.set_value('total_process_meter', 0);
        frm.add_fetch("greige_grading_form", "total_net_grading_meter", "total_remaining_meter");
        frm.set_value('total_mending_meter', 0);
        frm.set_value('total_rejection_meter', 0);
        frm.set_value('total_net_mending_meter', 0);
    },
    add_entry:function(frm){
        frappe.call({
            doc: frm.doc,
            method: "add_entry",
            freeze: true,
            callback: function(data) {
                frm.set_value('mending_meter', 0);
                frm.set_value('rejection_meter', 0);
                frm.refresh();
            }
        })
    },
    edit_entry:function(frm){
        frappe.call({
            doc: frm.doc,
            method: "edit_entry",
            freeze: true,
            callback: function(data) {
                 frappe.call({
                    doc: frm.doc,
                    method: "update_summery",
                    callback: function(data) {
                        frm.set_value('line_no', 0);
                        frm.set_value('mending_meter', 0);
                        frm.set_value('rejection_meter', 0);
                        frm.reload_doc();
                        frappe.msgprint(__("Data Updated"))
                    }
               })
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
    }
});
