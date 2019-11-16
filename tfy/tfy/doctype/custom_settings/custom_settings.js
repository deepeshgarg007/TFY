// Copyright (c) 2019, hello@openetech.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Custom Settings', {
	setup: function(frm) {
		frm.set_query("gst_expense_account", function() {
			return {
				filters: { root_type: 'Expense' }
			};
		});
		frm.set_query("gst_income_account", function() {
			return {
				filters: { root_type: 'Income' }
			};
		});
	}
});