from __future__ import unicode_literals
import frappe
from frappe import _

def insert_item_price_history(self, method):
	if(self.items):
		for item in self.items:
			frappe.get_doc({
				"doctype": "Item Price History",
				"item_code": item.item_code,
				"price": item.rate,
				"ref_doctype": self.doctype,
				"ref_docname": self.name,
				"transaction_date" : self.posting_date
			}).insert()

@frappe.whitelist()
def fetch_last_four_prices(item_code):
	limit = frappe.db.get_single_value("Custom Settings", 'limit') or 4
	item_price = """
		select 
			a.item_code, a.price, a.transaction_date
		from 
			`tabItem Price History` a, `tabPurchase Receipt` b
		where 
			a.ref_doctype = 'Purchase Receipt'
			and a.ref_docname = b.name
			and b.docstatus = 1
			and a.item_code = '{0}'
		order by 
			a.transaction_date DESC 
		limit {1}
	""".format(item_code, limit)

	historic_prices = frappe.db.sql(item_price,as_dict = 1)
	return historic_prices

def create_gst_gl_entry(self, method):
	enable_tax_gross_up = frappe.db.get_single_value("Custom Settings", 'enable_tax_gross_up')

	if enable_tax_gross_up:
		expense_account = frappe.db.get_single_value("Custom Settings", 'gst_expense_account')
		income_account = frappe.db.get_single_value("Custom Settings", 'gst_income_account')

		if not expense_account or not income_account:
			frappe.throw(_("Please set default GST expense and income account in custom settings"))
		
		gst_setting_account = frappe.db.get_list('GST Account', filters={'company': self.company}, fields=['cgst_account', 'sgst_account', 'igst_account'])

		tax_amount = 0
		gl_entries = []

		for taxes in self.taxes:
			for row in gst_setting_account:
				if (row.sgst_account == taxes.account_head 
					or row.cgst_account == taxes.account_head 
					or row.igst_account == taxes.account_head):
					tax_amount += taxes.tax_amount
					#assume cost centers are same on all tax lines and pick anyone for gl entry
					if taxes.cost_center:
						cost_center = taxes.cost_center

		if tax_amount > 0:
			gl_entries = []
			from erpnext.accounts.general_ledger import make_gl_entries
			#income entry
			gl_entries.append(
				self.get_gl_dict({
					"account": income_account,
					"against": self.customer,
					"credit": tax_amount,
					"credit_in_account_currency": tax_amount,
					"cost_center": cost_center
				})
			)
			#expense entry
			gl_entries.append(
				self.get_gl_dict({
					"account": expense_account,
					"against": self.customer,
					"debit": tax_amount,
					"debit_in_account_currency": tax_amount,
					"cost_center": cost_center
				})
			)
			make_gl_entries(gl_entries)

def set_accounting_dimension_defaults(self, method):
	accounting_dimension_defaults = get_accounting_dimension_defaults(self.tfy_transaction_type)
	if accounting_dimension_defaults:
		for row in accounting_dimension_defaults:
			setattr(self, row.accounting_dimension_fieldname, row.default_value)

@frappe.whitelist()
def get_accounting_dimension_defaults(transaction_type):
	if transaction_type and frappe.db.exists("Accounting Dimension Default", transaction_type):
		return frappe.get_doc("Accounting Dimension Default", transaction_type).dimension_defaults