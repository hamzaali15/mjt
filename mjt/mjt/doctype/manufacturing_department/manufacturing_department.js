// Copyright (c) 2018, earthians and contributors
// For license information, please see license.txt

frappe.ui.form.on('Manufacturing Department', {
	refresh: function(frm) {
        frm.set_query('src_warehouse', function() {
            return {
                filters: {
                    "company":frm.doc.company,
                    "is_group":0
                }
            }
        });
	    frm.set_query('wip_warehouse', function() {
            return {
                filters: {
                    "company":frm.doc.company,
                    "is_group":0
                }
            }
        });
	    frm.set_query('fg_warehouse', function() {
            return {
                filters: {
                    "company":frm.doc.company,
                    "is_group":0
                }
            }
        });
	    frm.set_query('scrap_warehouse', function() {
            return {
                filters: {
                    "company":frm.doc.company,
                    "is_group":0
                }
            }
        });
        frm.trigger('is_subcontracting');
	},
    is_subcontracting : function(frm){
		frm.set_df_property('supplier', 'reqd', frm.doc.is_subcontracting ? 1 : 0);
		frm.set_df_property('wip_warehouse', 'reqd', frm.doc.is_subcontracting ? 1 : 0);
		frm.set_df_property('wip_warehouse', 'description', frm.doc.is_subcontracting ? "<b>As Supplier Warehouse</b>" : "");
        if (!frm.doc.is_subcontracting){
            frm.set_value('supplier', null);
            frm.set_value('supplier_name', null);
        }
	}
});
