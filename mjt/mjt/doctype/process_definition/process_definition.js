// Copyright (c) 2018, earthians and contributors
// For license information, please see license.txt

frappe.ui.form.on('Process Definition', {
	refresh: function(frm) {
	},
	setup: function (frm) {
		frm.set_query("workstation", function () {
			return {
				filters: {"department": frm.doc.department}
			}
		});
	},
});

frappe.ui.form.on('Process Item', {
	item: function(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (d.parentfield == "materials" && !d.row_no)
		{	
			let row_name = "R"+d.idx
			frappe.model.set_value(cdt,cdn,"row_no",row_name);
            refresh_field("row_no", cdn, "materials");
		}
	}	
});
