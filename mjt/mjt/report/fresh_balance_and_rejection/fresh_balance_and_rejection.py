# Copyright (c) 2013, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _, _dict

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		{
			"fieldname": "batch_no",
			"fieldtype": "Link",
			"label": "Batch No",
			"options": "Batch",
			"width": 150
		},
		{
			"fieldname": "quality_name",
			"fieldtype": "Data",
			"label": "Quality Name",
			"width": 150
		},
		{
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"label": "Party Name",
			"width": 150
		},
		{
			"fieldname": "received_qty",
			"fieldtype": "Float",
			"label": "Received Qty",
			"width": 150
		},
		{
			"fieldname": "short_length",
			"fieldtype": "Float",
			"label": "Short Length",
			"width": 150
		},
		{
			"fieldname": "return_qty",
			"fieldtype": "Float",
			"label": "Return Qty",
			"width": 150
		},
		{
			"fieldname": "bal_of_greige_fab",
			"fieldtype": "Float",
			"label": "Balance of Greige Fabric",
			"width": 200
		},
		{
			"fieldname": "fresh_balance",
			"fieldtype": "Float",
			"label": "Fresh Balance",
			"width": 150
		},
		{
			"fieldname": "rejection_balance",
			"fieldtype": "Float",
			"label": "Rejection Balance",
			"width": 150
		}
	]
	return columns



def get_data(filters):
	if filters.get('company'):
		query = """select 
			r.batch_no,
			r.received_qty,
			r.short_length,
			r.return_qty,
			r.customer_name,
			g.total_grading_meter,
			s.warehouse,
			r.quality_name,
			s.posting_date,
			s.actual_qty
			from `tabGreige Receiving Form` as r
			left join `tabGreige Grading Form` as g on g.greige_receiving_form = r.name and g.docstatus = 1
			left join `tabStock Ledger Entry` as s on s.batch_no = r.batch_no
			where r.batch_no is not null and r.docstatus = 1 and r.company = '{0}'
			group by r.batch_no, s.warehouse""".format(filters.get('company'))

		if filters.get('from_date'):
			query += " and s.posting_date >= '{0}'".format(filters.get('from_date'))
		if filters.get('to_date'):
			query += " and s.posting_date <= '{0}'".format(filters.get('to_date'))
		
		if filters.get("group_by") == _("Group by Party"):
			query += "order by customer_name"

		if filters.get("group_by") == _("Group by Quality"):
			query += "order by quality_name"

		result = frappe.db.sql(query,as_dict=True)
		data = []

		received_qty1 = 0
		short_length1 = 0
		return_qty1 = 0
		bal_of_greige_fab1 = 0
		fresh_balance1 = 0
		rejection_balance1 = 0
		current_value= ""
		previous_value=""
		cur_pre_val=""		
		received_qty2 = 0
		short_length2 = 0
		return_qty2 = 0
		bal_of_greige_fab2 = 0
		fresh_balance2 = 0
		rejection_balance2 = 0
		i=len(result)

		def subTotal():
			total_row = {
				"batch_no": "",
				"quality_name": "",
				"customer_name": "<b>"+"Sub Total"+"</b>",
				"received_qty": received_qty2,
				"short_length": short_length2,
				"return_qty": return_qty2,
				"bal_of_greige_fab": bal_of_greige_fab2,
				"fresh_balance": fresh_balance2,
				"rejection_balance": rejection_balance2
			}
			data.append(total_row)

		def gTotal():
			total_row1 = {
				"batch_no": "",
				"quality_name": "",
				"customer_name": "<b>"+"Grand Total"+"</b>",
				"received_qty": received_qty1,
				"short_length": short_length1,
				"return_qty": return_qty1,
				"bal_of_greige_fab": bal_of_greige_fab1,
				"fresh_balance": fresh_balance1,
				"rejection_balance": rejection_balance1
			}
			data.append(total_row1)

		for row in result:
			received_qty = 0
			if row.received_qty:
				received_qty = row.received_qty
			short_length = 0
			if row.short_length:
				short_length = row.short_length
			total_grading_meter = 0
			if row.total_grading_meter:
				total_grading_meter = row.total_grading_meter
			total_return_qty = 0
			if row.return_qty:
				total_return_qty = row.return_qty
			bal_of_greige_fab = received_qty - total_grading_meter - short_length - total_return_qty

			batch_like = str(row['batch_no'])
			query1 = """select 
					sum(s1.actual_qty) as fresh_balance
					from `tabStock Ledger Entry` as s1
					where s1.batch_no = '{0}' and s1.warehouse = 'Greige Fresh - MF' """.format(batch_like)

			result1 = frappe.db.sql(query1, as_dict=True)
			for row1 in result1:

				fresh_balance = 0
				if row1.fresh_balance:
					fresh_balance = row1.fresh_balance

				batch_like = str(row['batch_no'])
				query2 = """select 
						sum(s2.actual_qty) as rejection_balance
						from `tabStock Ledger Entry` as s2
						where s2.batch_no = '{0}' and s2.warehouse = 'Greige Rejection - MF' """.format(batch_like)
			result2 = frappe.db.sql(query2, as_dict=True)
			
			for row2 in result2:

				rejection_balance = 0
				if row2.rejection_balance:
					rejection_balance = row2.rejection_balance

				i=i-1
				if filters.get("group_by") == _("Group by Party"):
					current_value = row.customer_name
					if(cur_pre_val != ""):
						if(cur_pre_val != current_value):
							previous_value = cur_pre_val
					if(previous_value == ""):
						previous_value = row.customer_name

				if filters.get("group_by") == _("Group by Quality"):
					current_value = row.quality_name
					if(cur_pre_val != ""):
						if(cur_pre_val != current_value):
							previous_value = cur_pre_val
					if(previous_value == ""):
						previous_value = row.quality_name	

				if(current_value == previous_value):
					received_qty2 += row.received_qty
					short_length2 += row.short_length
					return_qty2 += row.return_qty
					bal_of_greige_fab2 += bal_of_greige_fab
					fresh_balance2 += fresh_balance
					rejection_balance2 += rejection_balance
					
				if(current_value != "" and previous_value != ""):
					if(current_value != previous_value):
						subTotal()
						previous_value = ""
						if filters.get("group_by") == _("Group by Party"):
							cur_pre_val=row.customer_name
						if filters.get("group_by") == _("Group by Quality"):
							cur_pre_val=row.quality_name
						received_qty2 = row.received_qty
						short_length2 = row.short_length
						return_qty2 = row.return_qty
						bal_of_greige_fab2 = bal_of_greige_fab
						fresh_balance2 = fresh_balance
						rejection_balance2 = rejection_balance
						

				received_qty1 += row.received_qty
				short_length1 += row.short_length
				return_qty1 += row.return_qty
				bal_of_greige_fab1 += bal_of_greige_fab
				fresh_balance1 += fresh_balance
				rejection_balance1 += rejection_balance
				
				row2 = {
					"batch_no": row.batch_no,
					"quality_name": row.quality_name,
					"customer_name": row.customer_name,
					"received_qty": row.received_qty,
					"short_length": row.short_length,
					"return_qty": row.return_qty,
					"bal_of_greige_fab": bal_of_greige_fab,
					"fresh_balance": fresh_balance,
					"rejection_balance": rejection_balance
				}
				data.append(row2)
				if(i==0):
					if filters.get("group_by"):
						subTotal()
						gTotal()
					else:
						gTotal()
		return data
	else:
		return []