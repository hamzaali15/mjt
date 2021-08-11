// Copyright (c) 2020, Dexciss Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fabric Ownership Transfer', {
    refresh: function(frm){
        frm.set_query("batch", function () {
			return {
				filters: {'disabled':0
				}
			}
		});
        if(frm.doc.docstatus == 1 && frm.doc.change_owner == 0)
        {

            frm.add_custom_button(__('Change Owner'),function() {
                return frappe.call({
                    method: "mjt.mjt.doctype.fabric_ownership_transfer.fabric_ownership_transfer.change_owner",
                    args: {
                        doc_name: frm.doc.name
                    },
                    callback: function(r) {
                        frappe.msgprint(__("Fabric Ownership Changed"));
                        frm.reload_doc();
                    }
                });
			});
        }
        frm.trigger('make_dashboard');
    },
	make_dashboard: (frm) => {
		if(!frm.is_new()) {
			frappe.call({
				method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
				args: {batch_no: frm.doc.batch},
				callback: (r) => {
					if(!r.message) {
						return;
					}

					var section = frm.dashboard.add_section(`<h5 style="margin-top: 0px;">
						${ __("Stock Levels") }</a></h5>`);

					// sort by qty
					r.message.sort(function(a, b) { a.qty > b.qty ? 1 : -1 });

					var rows = $('<div></div>').appendTo(section);

					// show
					(r.message || []).forEach(function(d) {
						if(d.qty > 0) {
						    if(frm.doc.change_owner == 0 && frm.doc.docstatus == 1){
						        $(`<div class='row' style='margin-bottom: 10px;'>
								<div class='col-sm-3 small' style='padding-top: 3px;'>${d.warehouse}</div>
								<div class='col-sm-3 small text-right' style='padding-top: 3px;'>${d.qty}</div>
								<div class='col-sm-6'>
									<button class='btn btn-default btn-xs btn-move' style='margin-right: 7px;'
										data-qty = "${d.qty}"
										data-warehouse = "${d.warehouse}">
										${__('Move')}</button>
									<button class='btn btn-default btn-xs btn-split'
										data-qty = "${d.qty}"
										data-warehouse = "${d.warehouse}">
										${__('Split New Batch')}</button>
									<button class='btn btn-default btn-xs btn-split_exit'
										data-qty = "${d.qty}"
										data-warehouse = "${d.warehouse}">
										${__('Split Existing Batch')}</button>
								</div>
							</div>`).appendTo(rows);
						    }
//						    else{
//                                $(`<div class='row' style='margin-bottom: 10px;'>
//                                <div class='col-sm-3 small' style='padding-top: 3px;'>${d.warehouse}</div>
//                                <div class='col-sm-3 small text-right' style='padding-top: 3px;'>${d.qty}</div>
//                                <div class='col-sm-6'>
//                                    <button class='btn btn-default btn-xs btn-move' style='margin-right: 7px;'
//                                        data-qty = "${d.qty}"
//                                        data-warehouse = "${d.warehouse}">
//                                        ${__('Move')}</button>
//                                </div>
//                            </div>`).appendTo(rows);
//						    }
						}
					});

					// move - ask for target warehouse and make stock entry
					rows.find('.btn-move').on('click', function() {
						var $btn = $(this);
						const fields = [
							{
								fieldname: 'to_warehouse',
								label: __('To Warehouse'),
								fieldtype: 'Link',
								options: 'Warehouse'
							}
						];

						frappe.prompt(
							fields,
							(data) => {
								frappe.call({
									method: 'erpnext.stock.doctype.stock_entry.stock_entry_utils.make_stock_entry',
									args: {
										item_code: frm.doc.item,
										batch_no: frm.doc.batch,
										qty: $btn.attr('data-qty'),
										from_warehouse: $btn.attr('data-warehouse'),
										to_warehouse: data.to_warehouse,
										source_document: frm.doc.reference_name,
										reference_doctype: frm.doc.reference_doctype
									},
									callback: (r) => {
										frappe.show_alert(__('Stock Entry {0} created',
											['<a href="#Form/Stock Entry/'+r.message.name+'">' + r.message.name+ '</a>']));
										frm.refresh();
									},
								});
							},
							__('Select Target Warehouse'),
							__('Move')
						);
					});

					// split - ask for new qty and batch ID (optional)
					// and make stock entry via batch.batch_split
					rows.find('.btn-split').on('click', function() {
						var $btn = $(this);
						frappe.prompt([{
							fieldname: 'qty',
							label: __('New Batch Qty'),
							fieldtype: 'Float',
							'default': $btn.attr('data-qty')
						},
						{
							fieldname: 'new_batch_id',
							label: __('New Batch ID (Optional)'),
							fieldtype: 'Data'
						}],
						(data) => {
							frappe.call({
								method: 'mjt.mjt.doctype.fabric_ownership_transfer.fabric_ownership_transfer.split_batch',
								args: {
								    doc_name : frm.doc.name,
									item_code: frm.doc.item,
									batch_no: frm.doc.batch,
									qty: data.qty,
									warehouse: $btn.attr('data-warehouse'),
									new_batch_id: data.new_batch_id
								},
								freeze: true,
								callback: (r) => {
									frm.refresh();
								},
							});
						},
						__('Split New Batch'),
						__('Split')
						);
					})

					//split existing Batch

					rows.find('.btn-split_exit').on('click', function() {
					    var filter = { "item": frm.doc.item,
                                    "supplier":['=', frm.doc.new_party_code],
                                }
                        if(frm.doc.quality_code){
                            filter['quality_code'] = ['=', frm.doc.quality_code]
                        }
						var $btn = $(this);
						frappe.prompt([{
							fieldname: 'qty',
							label: __('New Batch Qty'),
							fieldtype: 'Float',
							'default': $btn.attr('data-qty')
						},
						{
							fieldname: 'exit_batch_id',
							label: __('Batch'),
							fieldtype: 'Link',
							options: 'Batch',
							reqd: 1,
                            "get_query": () =>{
                                return {
                                    filters : filter
                                }
                            }
						},
						{
							fieldname: 't_warehouse',
							label: __('To Warehouse'),
							fieldtype: 'Link',
							options: 'Warehouse',
							reqd: 1,
                            "get_query": () =>{
                                return {
                                    filters: { "is_group": 0}
                                }
                            }
						}],
						(data) => {
							frappe.call({
								method: 'mjt.mjt.doctype.fabric_ownership_transfer.fabric_ownership_transfer.split_existing_batch',
								args: {
								    doc_name : frm.doc.name,
									item_code: frm.doc.item,
									batch_no: frm.doc.batch,
									qty: data.qty,
									s_warehouse: $btn.attr('data-warehouse'),
									exit_batch_id: data.exit_batch_id,
									t_warehouse: data.t_warehouse
								},
								freeze: true,
								callback: (r) => {
									frm.refresh();
								},
							});
						},
						__('Split Existing Batch'),
						__('Split')
						);
					})

					frm.dashboard.show();
				}
			});
		}
	}
});
