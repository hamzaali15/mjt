frappe.listview_settings['Gate Pass'] = {
	add_fields: ["type", "party_name", "date", "status"],
	get_indicator: function(doc) {
	    if (doc.status === "Return") {
			return [__("Return"), "darkgrey", "status,=,Return"];
		}
	    if (doc.status === "Partial Return") {
			return [__("Partial Return"), "orange", "status,=,Partial Return"];
		}
	}
};
