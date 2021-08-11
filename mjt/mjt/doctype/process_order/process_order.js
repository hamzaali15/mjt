// Copyright (c) 2018, earthians and contributors
// For license information, please see license.txt

frappe.ui.form.on('Process Order', {
	setup: function (frm) {
		frm.set_query("workstation", function () {
			return {
				filters: {"department": frm.doc.department}
			}
		});
		frm.set_query("process_name", function () {
			return {
				filters: {"department": frm.doc.department, "process_type": frm.doc.process_type}
			}
		});
		frm.set_query("sale_order", function () {
			return {
				filters: {"docstatus": 1}
			}
		});
		apply_filter(frm)
	},
	refresh: function(frm){
		if(!frm.doc.__islocal && frm.doc.status == 'Submitted'){
			var start_btn = frm.add_custom_button(__('Start'), function(){
				prompt_for_qty(frm, "materials", "Enter Raw Material Quantity", true, function () {
					process_production(frm, "Submitted");
				});
			});
			start_btn.addClass('btn-primary');
		}
		if(!frm.doc.__islocal && frm.doc.status == 'In Process'){
		    var start_btn = frm.add_custom_button(__('Add Additional Fabric'), function(){
				add_fabric_qty(frm, "materials", "Enter Raw Material Quantity", true, function () {
					add_fabric(frm, "Submitted");
				});
			});
			start_btn.addClass('btn-primary');

			var finish_btn = frm.add_custom_button(__('Complete'), function(){
				finish_prompt_for_qty(frm, "finished_products", "Enter Produced Quantity", true, function () {
					if(frm.doc.scrap){
						prompt_for_qty(frm, "scrap", "Enter Scrap Quantity", false, function() {
							prompt_for_hours(frm, function() {
								process_production(frm, "In Process");
							});
						});
					}
					else {
						prompt_for_hours(frm, function() {
							process_production(frm, "In Process");
						});
					}
				});
			});
			finish_btn.addClass('btn-primary')
		}
		if(!frm.doc.__islocal){
			frappe.call({
				doc: frm.doc,
				method: "update_material_avl_qty",
				callback: function (data) {
					refresh_field("materials");
				}
			});
		}
		frm.trigger('required_rate')
		frm.trigger('required_overhead_costing')
		//erpnext.bom.calculate_op_cost(frm.doc);
	},
	workstation: function(frm){
		frappe.db.get_value("Workstation", {"name": frm.doc.workstation}, "base_on", (r) => {
			frm.set_value("base_on", r.base_on);
		});
		frm.trigger('required_overhead_costing')
		frm.refresh_field('base_on')
	},
	required_overhead_costing :function(frm){
		frm.set_df_property('base_on', 'reqd', frm.doc.workstation ? 1 : 0);	
	},
	department: function(frm){
		if(frm.doc.department){
			frappe.call({
				"method": "frappe.client.get",
				args: {
					doctype: "Manufacturing Department",
					name: frm.doc.department
				},
				callback: function (data) {
					frappe.model.set_value(frm.doctype,frm.docname, "wip_warehouse", data.message.wip_warehouse);
					frappe.model.set_value(frm.doctype,frm.docname, "fg_warehouse", data.message.fg_warehouse);
					frappe.model.set_value(frm.doctype,frm.docname, "scrap_warehouse", data.message.scrap_warehouse);
					frappe.model.set_value(frm.doctype,frm.docname, "src_warehouse", data.message.src_warehouse);
					frm.set_df_property('wip_warehouse', 'description', data.message.is_subcontracting ? "<b>As Supplier Warehouse</b>" : "");

				}
			});
		}
		frm.trigger('required_rate')
	},
	required_rate: function(frm){
		frm.get_field("finished_products").grid.toggle_reqd("rate", frm.doc.is_subcontracting ? 1 : 0);
		frm.set_df_property('wip_warehouse', 'description', frm.doc.is_subcontracting ? "<b>As Supplier Warehouse</b>" : "");
		refresh_field("finished_products");
	},
	process_name: function(frm) {
		if(frm.doc.process_name){
			frappe.call({
				doc: frm.doc,
				method: "get_process_details",
				callback: function(r) {
					refresh_field("costing_method");
					refresh_field("supplier_rate");
					refresh_field("finished_products");
					refresh_field("scrap");
					refresh_field("materials");
				}
			});
		}
		;
	},
	map_lot_no: function(frm){
	    frappe.call({
            doc: frm.doc,
            method: "map_lot_no",
            callback: function(r) {
				refresh_field('finished_products');
				refresh_field('scrap');
            }
        })
	},
	map_mutli_lot: function(frm){
	    frappe.call({
            doc: frm.doc,
            method: "map_multi_lot_no",
            callback: function(r) {
                var d = new frappe.ui.Dialog({
                    title: __('Map Lot No'),
                    fields: r.message,
                    primary_action_label: __("Map Lot"),
                    primary_action(values) {
                        d.hide();
                        frappe.call({
                            method: "mjt.mjt.doctype.process_order.process_order.create_multi_lot_no",
                            args: {
                                data: values,
                                doc_name: frm.doc.name
                            },
                            freeze: true,
                            callback: function() {
                                frm.reload_doc();
                            }
                        });
                    }
                });
                d.show();
            }
        })
	}
});

function apply_filter(frm){
    frm.fields_dict['materials'].grid.get_field("lot_no").get_query = function(doc, cdt, cdn) {
        var child = locals[cdt][cdn];
        return {
            filters:[
                   ['item', '=', child.item]
                ]
        }
    }
    frm.fields_dict['finished_products'].grid.get_field("lot_no").get_query = function(doc, cdt, cdn) {
        var child = locals[cdt][cdn];
        return {
            filters:[
                   ['item', '=', child.item]
                ]
        }
    }
    frm.fields_dict['scrap'].grid.get_field("lot_no").get_query = function(doc, cdt, cdn) {
        var child = locals[cdt][cdn];
        return {
            filters:[
               ['item', '=', child.item]
            ]
        }
    }
}

//function set_warehouse(frm) {
//	erpnext.utils.copy_value_in_all_rows(frm.doc, frm.doc.doctype, frm.doc.name, "materials", "src_warehouse");
//}

var prompt_for_qty = function (frm, table, title, qty_required, callback) {
	// if(table && !qty_required){
	// 	callback();
	// }
	let fields = []
	$.each(frm.doc[table] || [], function(i, row) {
		var feild_lable = row.item_name;
		if (row.customer_name){ feild_lable = feild_lable +' - '+row.customer_name}
		if (row.quality_name){ feild_lable = feild_lable +' - '+row.quality_name}
		if (row.lot_no){ feild_lable = feild_lable +' - '+row.lot_no}
		if (row.design_name){ feild_lable = feild_lable +' - '+row.design_name}
		fields.push({
			fieldtype: "Float",
			label: __("{0} (<b>{1} : {2} Avl. Qty</b>)", [feild_lable,frm.doc.src_warehouse,row.available_qty]),
			fieldname: row.name,
			'default': row.quantity
			//value: row.quantity //value is ignored
		});
	})
	frappe.prompt(
		fields,
		function(data) {
			let item_qty = false;
			let t_supplier_qty = 0
			let finish_qty = 0
			frm.doc[table].forEach(function(line) {
				if(data[line.name] > 0){item_qty = true;}
				frappe.model.set_value(line.doctype, line.name, "quantity", data[line.name]);
				if (frm.doc.is_subcontracting && !frm.doc.allow_scrap_rate){
                    t_supplier_qty = t_supplier_qty + data[line.name]
                }
			});
			if (qty_required && !item_qty){
				frappe.throw("Cannot start/finish Process Order with zero quantity");
			}
			if (table == 'scrap'){
                frm.doc['finished_products'].forEach(function(line) {
                    if (frm.doc.is_subcontracting && !frm.doc.allow_scrap_rate){
                        t_supplier_qty = t_supplier_qty + line.quantity
                        finish_qty = finish_qty + line.quantity
                    }
                });
                let add_fin_rate = t_supplier_qty * frm.doc.supplier_rate
                let add_rate = add_fin_rate / finish_qty
                frm.set_value("t_supplier_amt", add_fin_rate);
                frm.doc['finished_products'].forEach(function(line) {
                    frappe.model.set_value(line.doctype, line.name, "rate",add_rate );
                });
            }
			callback();
		},
		__(title),
		__("Confirm")
	);
}

var add_fabric_qty = function (frm, table, title, qty_required, callback) {
	// if(table && !qty_required){
	// 	callback();
	// }
	let fields = []
	$.each(frm.doc[table] || [], function(i, row) {
		var feild_lable = row.item_name;
		if (row.customer_name){ feild_lable = feild_lable +' - '+row.customer_name}
		if (row.quality_name){ feild_lable = feild_lable +' - '+row.quality_name}
		if (row.lot_no){ feild_lable = feild_lable +' - '+row.lot_no}
		if (row.design_name){ feild_lable = feild_lable +' - '+row.design_name}
		fields.push({
			fieldtype: "Float",
			label: __("{0} - (<b>{1} : {2} Avl. Qty</b>)", [feild_lable,frm.doc.src_warehouse,row.available_qty]),
			fieldname: row.name,
			'default': 0
			//value: row.quantity //value is ignored
		});
	})
	frappe.prompt(
		fields,
		function(data) {
			let item_qty = false;
			frm.doc[table].forEach(function(line) {
				if(data[line.name] > 0){item_qty = true;}
				frappe.model.set_value(line.doctype, line.name, "additional_qty", data[line.name]);

                let old_quantity = frappe.model.get_value(line.doctype, line.name, "quantity");
                let total_qty = data[line.name] + old_quantity

				frappe.model.set_value(line.doctype, line.name, "quantity", total_qty);
			});
			if (qty_required && !item_qty){
				frappe.throw("Cannot add zero Additional Quantity");
			}
			callback();
		},
		__(title),
		__("Confirm")
	);
}


var finish_prompt_for_qty = function (frm, table, title, qty_required, callback) {
	// if(table && !qty_required){
	// 	callback();
	// }
	let fields = []
	$.each(frm.doc[table] || [], function(i, row) {
		var feild_lable = row.item_name;
		if (row.customer_name){ feild_lable = feild_lable +' - '+row.customer_name}
		if (row.quality_name){ feild_lable = feild_lable +' - '+row.quality_name}
		if (row.lot_no){ feild_lable = feild_lable +' - '+row.lot_no}
		if (row.design_name){ feild_lable = feild_lable +' - '+row.design_name}
		fields.push({
			fieldtype: "Float",
			label: __("{0}", [feild_lable]),
			fieldname: row.name,
			'default': row.quantity
			//value: row.quantity //value is ignored
		},
		{
            "fieldtype": "Column Break"
        },
		{
			fieldtype: "Float",
			label: __("Than"),
			fieldname: __("{0}-than", [row.name]),
			'default': 0
		},
		{
            "fieldtype": "Section Break"
        });
	})
	frappe.prompt(
		fields,
		function(data) {
			let item_qty = false;
			let t_supplier_amt = 0
			frm.doc[table].forEach(function(line) {
				if(data[line.name] > 0){item_qty = true;}
				let than = line.name+"-than";
				let t = 0;
				if(data[than])
				{
				    t = data[than];
				}
				frappe.model.set_value(line.doctype, line.name, "quantity", data[line.name]);
				frappe.model.set_value(line.doctype, line.name, "than", t);
			});
			if (qty_required && !item_qty){
				frappe.throw("Cannot start/finish Process Order with zero quantity");
			}
			callback();
		},
		__(title),
		__("Confirm")
	);
}

var prompt_for_hours = function(frm, callback){
	//TODO datetime diff returns 0 for minutes
	let hours = frappe.datetime.get_hour_diff(frappe.datetime.now_datetime(), frm.doc.start_dt)
	frappe.prompt(
		[{fieldtype: "Float",
			label: __("Hours"),
			fieldname: "hours",
			description: __("Hours as per start of process is {0}", [hours]),
		}],
		function(data) {
			let item_qty = false;
			frappe.model.set_value(frm.doctype, frm.doc.name, "operation_hours", data.hours);
			callback();
		},
		__("Update hours of operation"),
		__("Confirm")
	);
}

var process_production = function (frm, status) {
	frappe.call({
		doc: frm.doc,
		method: "start_finish_processing",
		args:{
			"status": status
		},
		callback: function(r) {
			if (r.message){
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		}
	});
}


var add_fabric = function (frm, status) {
	frappe.call({
		doc: frm.doc,
		method: "add_additional_fabric",
		args:{
			"status": status
		},
		callback: function(r) {
			if (r.message){
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		}
	});
}


frappe.ui.form.on("Process Order Item", {
	item: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
	},
	lot_no: function(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.call({
			method: "mjt.mjt.doctype.process_order.process_order.get_item_available_qty",
			args: {
				warehouse: frm.doc.src_warehouse,
				item: d.item,
				batch: d.lot_no
			},
			callback: function(r) {
				frappe.model.set_value(cdt,cdn,"available_qty",r.message);
				refresh_field("available_qty", cdn, "materials");
			}
		});
		if(d.lot_no){
		    frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Batch",
                    filters: { 'name': d.lot_no },
                    fields: ['design_no', 'design_name']
                },
                callback: function (r) {
				    frappe.model.set_value(cdt,cdn,"design_no",r.message[0].design_no);
				    frappe.model.set_value(cdt,cdn,"design_name",r.message[0].design_name);
                }
            })
		}
	}
});
frappe.ui.form.on("Process Order Finish Item", {
	item: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
	}	
});

frappe.ui.form.on("Process Order Operation", "operation", function(frm, cdt, cdn) {
	var d = locals[cdt][cdn];

	if(!d.operation) return;

	frappe.call({
		"method": "frappe.client.get",
		args: {
			doctype: "Operation",
			name: d.operation
		},
		callback: function (data) {
			if(data.message.description) {
				frappe.model.set_value(d.doctype, d.name, "description", data.message.description);
			}
			if(data.message.workstation) {
				frappe.model.set_value(d.doctype, d.name, "workstation", data.message.workstation);
			}
		}
	});
});

frappe.ui.form.on("Process Order Operation", "workstation", function(frm, cdt, cdn) {
	var d = locals[cdt][cdn];

	frappe.call({
		"method": "frappe.client.get",
		args: {
			doctype: "Workstation",
			name: d.workstation
		},
		callback: function (data) {
			frappe.model.set_value(d.doctype, d.name, "base_hour_rate", data.message.hour_rate);
			frappe.model.set_value(d.doctype, d.name, "hour_rate",
				flt(flt(data.message.hour_rate) / flt(frm.doc.conversion_rate)), 2);

			erpnext.bom.calculate_op_cost(frm.doc);
			erpnext.bom.calculate_total(frm.doc);
		}
	});
});
