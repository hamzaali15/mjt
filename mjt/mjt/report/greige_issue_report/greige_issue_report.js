// Copyright (c) 2016, earthians and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Greige Issue Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"fieldtype": "Link",
			"label": "Company",
			"mandatory": 1,
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
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
       }
	]
};
