// Copyright (c) 2016, RF and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Quality Wise Warehouse Stock Balance"] = {
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
		},
		{
			"fieldname": "quality_code",
			"fieldtype": "Link",
			"label": "Quality Code",
			"mandatory": 0,
			"options": "Quality"
		},
		{
			"fieldname": "customer_code",
			"fieldtype": "Link",
			"label": "Party Code",
			"mandatory": 0,
			"options": "Customer"
		}
	]
};
