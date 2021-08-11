// Copyright (c) 2016, Dexciss Technology and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Greige Graded Report"] = {
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
        "options": "PM Quality"
    },
    {
        "fieldname": "customer_code",
        "fieldtype": "Link",
        "label": "Party Code",
        "mandatory": 0,
        "options": "Customer"
    },
    {
        "fieldname":"group_by",
        "label": __("Group by"),
        "fieldtype": "Select",
        "options": ["", __("Group by Date"), __("Group by Party"), __("Group by Quality")]
    }
	]
};