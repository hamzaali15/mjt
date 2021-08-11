frappe.ui.form.on("Stock Entry", "validate", function (frm, cdt, cdn) {
    var total_quantity=0
    $.each(frm.doc.items,  function(i,  d) {
        total_quantity += d.qty  
    });
    frm.doc.total_qty = total_quantity;
});

frappe.ui.form.on('Stock Entry Detail', {
    batch_no: function (frm,cdt,cdn) {
	    var child = locals[cdt][cdn];
	    if (!child.design_no){
	        frappe.db.get_value("Batch",child.batch_no, ['design_no']).then(r => {
                let values = r.message;
                frappe.model.set_value(cdt,cdn,"design_no",values.design_no);

            });
            refresh_field("design_no", cdn, "items");
	    }
	}
});