// Copyright (c) 2016, earthians and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Cost of Production"] = {
	"filters": [
        {
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date"
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "TO Date"
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Manufacturing Department",
		},
		{
			"fieldname":"lot",
			"label": __("Lot"),
			"fieldtype": "Data",
		},
		{
			"fieldname":"quality_code",
			"label": __("Quality"),
			"fieldtype": "Link",
			"options": "PM Quality",
		}
	]
};
