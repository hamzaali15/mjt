// Copyright (c) 2021, earthians and contributors
// For license information, please see license.txt

frappe.ui.form.on('Process Order Ledger', {
	 refresh: function(frm) {
        frm.disable_save();
	 },
	 onload: function(frm) {
        frm.disable_save();
	 }
});
