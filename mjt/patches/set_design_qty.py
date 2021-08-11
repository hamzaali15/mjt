import frappe

def execute():
	frappe.reload_doc("mjt", "doctype", "design")
	for design in frappe.get_all("Design", fields=["name"]):
		design_qty = frappe.db.get_value("Stock Ledger Entry",
			{"docstatus": 1, "design_no": design.name, "is_cancelled": 0},
			"sum(actual_qty)") or 0.0
		frappe.db.set_value("Design", design.name, "design_qty", design_qty, update_modified=False)
