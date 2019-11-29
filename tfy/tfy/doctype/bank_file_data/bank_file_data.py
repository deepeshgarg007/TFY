# -*- coding: utf-8 -*-
# Copyright (c) 2019, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

class BankFileData(Document):
	def validate(self):
		if not frappe.db.get_value('Bank', {'name': self.bank}, ['account']):
			frappe.throw(_("Please set reconcilation bank account in Bank"))

		if not frappe.db.get_value('Store Code', {'company': self.company,'terminal_id': self.terminal_id, 'merchant_id': self.merchant_id},['store_code']):
			frappe.throw(_("Please configure store code for terminal ID {0}").format(self.terminal_id))

		if not self.status:
			self.status = "Unreconciled"

@frappe.whitelist()
def create_recon_entries():
	bank_transactions = frappe.db.sql('''
							select
								a.name, a.company, a.bank, a.terminal_id, a.credit_card_no, a.auth_code, a.amount, b.store_code
							from
								`tabBank File Data` a, `tabStore Code` b
							where
								a.company = b.company and
								a.terminal_id = b.terminal_id and
								a.merchant_id = b.merchant_id and
								a.status not in ('Reconciled')
							''', as_dict=1)

	for bank_transaction in bank_transactions:
		invoices = match_invoice(bank_transaction)
		if invoices:
			for invoice in invoices:
				if invoice['name']:
					create_entries(invoice['name'], bank_transaction)
		else:
			update_bank_tran_status(bank_transaction, "No Matching Invoice")

def create_entries(invoice_no, bank_transaction):
	invoice = frappe.get_doc('Sales Invoice', invoice_no)
	if invoice.grand_total != 0:
		gl_entries = []
		from erpnext.accounts.general_ledger import make_gl_entries
		for mop in invoice.payments:
			if mop.type == "Bank" and mop.base_amount == flt(bank_transaction["amount"]):
				#find current entry for bank
				gl_entry = frappe.db.sql('''
								select
									account, debit, party
								from
									`tabGL Entry`
								where
									company = %s and
									voucher_type = 'Sales Invoice' and voucher_no = %s
									and account = %s
								''', (bank_transaction['company'], invoice.name, mop.account), as_dict = 1)

				for gl_entry_invoice in gl_entry:
					if gl_entry_invoice["debit"] == flt(bank_transaction["amount"]):
						gl_entries.append(
							invoice.get_gl_dict({
								"account": gl_entry_invoice['account'],
								"against": gl_entry_invoice['party'],
								"voucher_type": "Sales Invoice",
								"voucher_no": invoice.name,
								"credit": gl_entry_invoice['debit'],
								"credit_in_account_currency": gl_entry_invoice['debit']
							})
						)
						gl_entries.append(
							invoice.get_gl_dict({"account": frappe.db.get_value('Bank', {'name': bank_transaction['bank']}, ['account']),
								"against": gl_entry_invoice['party'],
								"voucher_type": "Sales Invoice",
								"voucher_no": invoice.name,
								"debit": gl_entry_invoice['debit'],
								"debit_in_account_currency": gl_entry_invoice['debit']
							})
						)
						make_gl_entries(gl_entries)
						update_bank_tran_status(bank_transaction, "Reconciled", "Sales Invoice", invoice.name)
					else:
						update_bank_tran_status(bank_transaction, "Amount mismatch", "Sales Invoice", invoice.name)
			else:
				update_bank_tran_status(bank_transaction, "Payment mismatch", "Sales Invoice", invoice.name)

def match_invoice(bank_transaction):
	card_no = bank_transaction['credit_card_no']
	invoices = frappe.db.sql('''
					select
						name
					from
						`tabSales Invoice`
					where
						name not in (select ref_docname from `tabBank File Data` where ref_doctype = 'Sales Invoice'
						and ref_docname IS NOT NULL)
						and store_code = %s and auth_code = %s and RIGHT(credit_card_no, 4) = %s
						and company = %s
						and is_pos = 1 and docstatus = 1
					''', (bank_transaction['store_code'], bank_transaction['auth_code'], card_no[-4:], bank_transaction['company']), as_dict = 1)
	return invoices

def update_bank_tran_status(bank_transaction, status, ref_doctype=None, ref_docname=None):
	bank_tran = frappe.get_doc('Bank File Data', bank_transaction['name'])
	bank_tran.ref_doctype = ref_doctype
	bank_tran.ref_docname = ref_docname
	bank_tran.status = status
	bank_tran.save()
