// Copyright (c) 2020, Dexciss Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('Greige Setting', {
	 refresh: function(frm) {
        frm.set_query('tax_template', function() {
            return {
                filters: {
                    "company":frm.doc.company
                }
            }
        });
	 }
});
