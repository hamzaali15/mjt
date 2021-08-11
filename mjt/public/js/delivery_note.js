frappe.provide('frappe.dashboards.chart_sources');
frappe.ui.form.on('Delivery Note', {
    onload: function(frm){
		frm.trigger('set_options');
		frm.trigger('render_filters_table');		
    },
    refresh: function(frm){ 
        frm.trigger('set_options');
		frm.trigger('render_filters_table');
		frm.fields_dict.get_item_from_process_order.$input.addClass("btn-primary");
    },
	get_item_from_process_order: function(frm){
		frappe.call({
			method: "mjt.mjt.util.get_process_order_finish_item",
			args: {
				doc_name: frm.doc.name,
				filters_json: frm.doc.filters_json				
			},
			callback: function(r) {				
				if(r.message) {
					frm.clear_table('items');
					for (const d of r.message)
					{
					    if(d.quantity > 0){
                            var row = frm.add_child('items');
                            row.item_code = d.item;
                            row.item_name = d.item_name;
                            row.description = d.description;
                            row.qty = d.quantity;
                            row.rate = d.rate;
                            row.stock_uom = d.stock_uom;
                            row.uom = d.stock_uom;
                            row.warehouse = d.warehouse;
                            row.batch_no = d.lot_no;
                            row.design_no = d.design_no;
                            row.party_name = d.customer_name;
                            row.quality_name = d.quality_name;
                            row.than = d.than;
                            row.business_unit = d.business_unit;
                        }
					}
					frm.refresh_field('items');
				}					
			}
		});
	},
    customer: function(frm){
        if(frm.doc.customer){
            frappe.db.get_value("Double Ledger Parties",{'customer': frm.doc.customer}, ['supplier']).then(r => {
                let values = r.message;
                frm.set_value('party_code',values.supplier);

            });
            frm.refresh_field("party_code");
        }
    },
    set_options: function(frm) {
		let aggregate_based_on_fields = [];
		const doctype = "Process Order";

		if (doctype) {
			frappe.model.with_doctype(doctype, () => {
				frappe.get_meta(doctype).fields.map(df => {
					if (frappe.model.numeric_fieldtypes.includes(df.fieldtype)) {
						if (df.fieldtype == 'Currency') {
							if (!df.options || df.options !== 'Company:company:default_currency') {
								return;
							}
						}
						aggregate_based_on_fields.push({label: df.label, value: df.fieldname});
					}
				});

				frm.set_df_property('aggregate_function_based_on', 'options', aggregate_based_on_fields);
			});
		}
	},

	render_filters_table: function(frm) {
		let wrapper = $(frm.get_field('filters_json').wrapper).empty();
		frm.filter_table = $(`<table class="table table-bordered" style="cursor:pointer; margin:0px;">
			<thead>
				<tr>
					<th style="width: 33%">${__('Filter')}</th>
					<th style="width: 33%">${__('Condition')}</th>
					<th>${__('Value')}</th>
				</tr>
			</thead>
			<tbody></tbody>
		</table>`).appendTo(wrapper);

		frm.filters = JSON.parse(frm.doc.filters_json || '[]');

		frm.trigger('set_filters_in_table');

		frm.filter_table.on('click', () => {
			let dialog = new frappe.ui.Dialog({
				title: __('Set Filters'),
				fields: [{
					fieldtype: 'HTML',
					fieldname: 'filter_area',
				}],
				primary_action: function() {
					let values = this.get_values();
					if (values) {
						this.hide();
						frm.filters = frm.filter_group.get_filters();
						frm.set_value('filters_json', JSON.stringify(frm.filters));
						frm.trigger('set_filters_in_table');
					}
				},
				primary_action_label: "Set"
			});

			frappe.dashboards.filters_dialog = dialog;

			frm.filter_group = new frappe.ui.FilterGroup({
				parent: dialog.get_field('filter_area').$wrapper,
				doctype: "Process Order",
				on_change: () => {},
			});
			dialog.show();
			dialog.set_values(frm.filters);
		});
	},

	set_filters_in_table: function(frm) {
		if (!frm.filters.length) {
			const filter_row = $(`<tr><td colspan="3" class="text-muted text-center">
				${__("Click to Set Filters")}</td></tr>`);
			frm.filter_table.find('tbody').html(filter_row);
		} else {
			let filter_rows = '';
			frm.filters.forEach(filter => {
				filter_rows +=
					`<tr>
						<td>${filter[1]}</td>
						<td>${filter[2] || ""}</td>
						<td>${filter[3]}</td>
					</tr>`;

			});
			frm.filter_table.find('tbody').html(filter_rows);
		}
	}
});

frappe.ui.form.on('Delivery Note Item', {
    batch_no: function (frm,cdt,cdn) {
	    var child = locals[cdt][cdn];
	    if (!child.design_no){
	        frappe.db.get_value("Batch",child.batch_no, ['design_no']).then(r => {
                let values = r.message;
                frappe.model.set_value(cdt,cdn,"design_no",values.design_no);

            });
            refresh_field("design_no", cdn, "items");
	    }
	},
	item_code: function(frm, cdt, cdn) {
	    var d = locals[cdt][cdn];
	    frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item",
                filters: { "name": d.item_code },
                fields: ["has_batch_no", "has_serial_no"]
            },
            callback: function (r) {
                if(r.message){
                    if(r.message[0].has_batch_no && !r.message[0].has_serial_no){
                         erpnext.stock.select_batch(frm, d);
                    }
                }
            }
        })
	}
});

erpnext.stock.select_batch = (frm, item) => {
	frappe.require("assets/mjt/js/util.js", function() {
		new erpnext.SerialNoBatchSelector({
			frm: frm,
			item: item,
			warehouse_details: {type: "Source Warehouse", name: frm.doc.set_warehouse}
		});
	});

}
