// Copyright (c) 2020, earthians and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gate Pass', {
	 refresh: function(frm) {
        if (frm.doc.__islocal) {
            frm.set_value("date", frappe.datetime.now_date());
            frm.set_value("status", 'Draft');
        }
	 },
	 type: function(frm) {
        var ret_obj = setseries(frm.doc.type, frm.doc.company);
        frm.set_value("naming_series", ret_obj.series);
     },
     company: function(frm) {
        var ret_obj = setseries(frm.doc.type, frm.doc.company);
        frm.set_value("naming_series", ret_obj.series);
	 },
	 fatch_data: function(frm){
	    frappe.call({
            doc: frm.doc,
            method: "fetch_data",
            callback: function(data) {
                var array = data.message;
                var array_len = array.length;
                frm.set_value('items', []);
                for (var i=0; i< array_len; i++)
                {
                    var child = frm.add_child("items");
                    child.item_code=array[i]['item_code'];
                    child.description=array[i]['description'];
                    child.unit=array[i]['unit'];
                    child.quantity=array[i]['quantity'];
                }
                frm.refresh_field('items');
            }
        })
	 }
});

frappe.ui.form.on("Gate Pass", "onload", function (frm, cdt, cdn) {
	if(cur_frm.doc.__islocal!="undefined"){
        var ret_obj = setseries(frm.doc.type, frm.doc.company);
        frm.set_value("naming_series", ret_obj.series);
	}
});

function setseries(type, company)
{
    var ret_obj={ series: "" };
    if (type == 'Inward') {
        if(company=="MJ Textile (PVT) Ltd.")
        {
            ret_obj.series = "MJT-INW-.YYYY.-.####";
        }
    }
    else if(type == 'Outward')
    {
        if(company=="MJ Textile (PVT) Ltd.")
        {
            ret_obj.series = "MJT-OUTW-.YYYY.-.####";
        }
    }
    return ret_obj;
}