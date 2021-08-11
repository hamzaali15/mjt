// Copyright (c) 2021, RF and contributors
// For license information, please see license.txt

frappe.ui.form.on('Design Receiving and Approval', {
	sales_order: function(frm){
		if(!frm.doc.sales_order){
			frm.doc.po_date = "";
			frm.doc.ordered_qty = 0.0;
			frm.doc.production_pcs = 0.0;
			frm.doc.sales_return = 0.0;
			frm.doc.in_warehouse = 0.0;
			frm.doc.balance_pcs = 0.0;
		}
	},
});