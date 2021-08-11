// Copyright (c) 2017, earthians and contributors
// For license information, please see license.txt

frappe.listview_settings['Fabric Ownership Transfer'] = {
	onload: function(frm){
 	    frappe.route_options = {
			"change_owner":0
		};
 	}
};
