// Copyright (c) 2016, Dexciss Technology and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Grading Summary Report"] = {
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
           "fieldname": "batch_no",
           "fieldtype": "Link",
           "label": "Batch No",
           "mandatory": 0,
           "options": "Batch"
       },
       {
           "fieldname": "receiving_form",
           "fieldtype": "Link",
           "label": "Greige Receiving Form",
           "mandatory": 0,
           "options": "Greige Receiving Form"
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
