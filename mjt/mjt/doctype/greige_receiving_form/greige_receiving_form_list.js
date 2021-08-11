frappe.listview_settings['Greige Receiving Form'] = {
	add_fields: ["batch_no", "customer_code", "quality_code", "status"],
	get_indicator: function(doc) {
	    if (doc.status === "Return") {
			return [__("Return"), "darkgrey", "status,=,Return"];
		}
	}
};
