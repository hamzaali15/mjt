// Copyright (c) 2020, Dexciss Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quality', {
	refresh: function(frm) {
        frm.set_query('parent_quality', function() {
            return {
                filters: {
                    "is_group": 1
                }
            }
        });
	}
});
