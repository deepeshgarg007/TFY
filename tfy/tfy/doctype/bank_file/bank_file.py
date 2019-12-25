# -*- coding: utf-8 -*-
# Copyright (c) 2019, hello@openetech.com and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

class BankFile(Document):
	def validate(self):
		bank_accounts = frappe.db.sql('''
							select
								charges_account, gst_clearing_account, account
							from
								`tabBank`
							where
								name = %s
							''', (self.bank), as_dict=1)

		for bank_account in bank_accounts:
			if not bank_account['account'] or not bank_account['charges_account'] or not bank_account['gst_clearing_account']:
				frappe.throw(_("Please set appropriate bank accounts for clearing for bank {0}".format(self.bank)))

		for data in self.bank_file_data:
			if not frappe.db.get_value('Store Terminal', {'company': self.company,'terminal_id': data.terminal_id, 'merchant_id': data.merchant_id},['store_code']):
				frappe.throw(_("Please configure store code for terminal ID {0}").format(data.terminal_id))

		batches = frappe.db.sql('''
					select
						name
					from
						`tabBank File`
					where
						bank = %s and name != %s
						and batch_no = %s and batch_date = %s
					''', (self.bank, self.name, self.batch_no, self.batch_date))

		if batches:
			frappe.throw(_("Batch ID {0} already exists for bank {1}").format(self.batch_no, self.bank))

@frappe.whitelist()
def create_recon_entries():
	bank_transactions = frappe.db.sql('''
							select
								a.bank, a.batch_no, a.batch_date, 
								(select 
									ifnull(c.store_code, '') 
								from 
									`tabStore Terminal` c
								where 
									a.company = c.company and
									b.terminal_id = c.terminal_id and
									b.merchant_id = c.merchant_id) as store_code,
								a.posting_date, a.company,
								sum(b.gross_amount) as gross_amount, sum(b.charges_amount) as charges, 
								sum(b.cgst_amount + b.sgst_amount + b.igst_amount) as gst_amount, 
								sum(b.net_amount) as net_amount
							from
								`tabBank File` a, `tabBank File Data` b
							where
								a.name = b.parent and
								a.journal_entry IS NULL
							group by
								a.bank, a.batch_no, a.batch_date, store_code, a.posting_date, a.company
							order by a.bank, a.batch_no, a.batch_date, store_code
							''', as_dict=1)

	create_entries(bank_transactions)

@frappe.whitelist()
def match_entries():
	bank_transactions = frappe.db.sql('''
							select
								b.name, a.company, a.bank, b.terminal_id, b.credit_card_no,
								b.auth_code, b.gross_amount, 
								(select 
									ifnull(c.store_code, '') 
								from 
									`tabStore Terminal` c
								where 
									a.company = c.company and
									b.terminal_id = c.terminal_id and
									b.merchant_id = c.merchant_id) as store_code,
								a.batch_no, a.batch_date
							from
								`tabBank File` a, `tabBank File Data` b
							where
								a.name = b.parent and
								b.status in ('Unreconciled')
							''', as_dict=1)

	for bank_transaction in bank_transactions:
		invoices = match_invoice(bank_transaction)
		if invoices:
			for invoice in invoices:
				invoice = frappe.get_doc('Sales Invoice', invoice['name'])
				if invoice.grand_total != 0:
					update_bank_tran_status(bank_transaction, "Matched Invoice", "Sales Invoice", invoice.name)
					invoice.match_status = "Matched Invoice"
					invoice.save()

def create_entries(bank_transactions):
	bank, batch_no, batch_date = ['', '', '']
	def_wh = frappe.db.get_single_value("Custom Settings", 'warehouse')
	cc_acc = frappe.db.get_single_value("Custom Settings", 'cc_account')

	transaction = []
	for bank_transaction in bank_transactions:
		bank_accounts = frappe.db.get_list('Bank', filters= {'name': bank_transaction['bank']}, fields=['account', 'charges_account', 'gst_clearing_account'])
		for bank_account in bank_accounts:
			clearing_acc = bank_account['gst_clearing_account']
			bank_acc = bank_account['account']
			charges_acc = bank_account['charges_account']

		if bank_transaction['net_amount'] > 0:
			transaction.append({'account': bank_acc, 'debit': bank_transaction['net_amount'], 'credit': 0, 'store_code': def_wh, 
				'posting_date': bank_transaction['posting_date'], 'company': bank_transaction['company']})
		if bank_transaction['gst_amount'] > 0:
			transaction.append({'account': clearing_acc, 'debit': bank_transaction['gst_amount'], 'credit': 0, 'store_code': def_wh, 
				'posting_date': bank_transaction['posting_date'], 'company': bank_transaction['company']})
		if bank_transaction['charges'] > 0:
			transaction.append({'account': charges_acc, 'debit': bank_transaction['charges'], 'credit': 0, 'store_code': bank_transaction['store_code'], 
				'posting_date': bank_transaction['posting_date'], 'company': bank_transaction['company']})
		if bank_transaction['gross_amount'] > 0:
			transaction.append({'account': cc_acc, 'credit': bank_transaction['gross_amount'], 'debit': 0, 'store_code': bank_transaction['store_code'], 
				'posting_date': bank_transaction['posting_date'], 'company': bank_transaction['company']})

	if transaction:
		jv_name = create_jv(transaction)
		for tran in bank_transactions:
			update_jv_bank_file(bank_transaction, jv_name)

def match_invoice(bank_transaction):
	card_no = bank_transaction['credit_card_no']
	invoices = frappe.db.sql('''
					select
						name
					from
						`tabSales Invoice`
					where
						name not in 
						(select
							ref_docname 
						from 
							`tabBank File Data` 
						where 
							ref_doctype = 'Sales Invoice' and ref_docname IS NOT NULL)
						and warehouse = %s and auth_code = %s and RIGHT(credit_card_no, 4) = %s
						and company = %s
						and is_pos = 1 and docstatus = 1
					''', (bank_transaction['store_code'], bank_transaction['auth_code'], card_no[-4:], bank_transaction['company']), as_dict = 1)
	return invoices

def create_jv(transaction):
	je_doc = frappe.new_doc("Journal Entry")
	for tran in transaction:
		if je_doc.posting_date != tran['posting_date']:
			je_doc.company = tran['company']
			je_doc.voucher_type = "Journal Entry"
			je_doc.posting_date = tran['posting_date']
		#debit lines
		if tran['debit'] > 0:
			je_doc.append("accounts", {
				"account": tran['account'],
				"warehouse": tran['store_code'],
				"debit_in_account_currency": tran['debit'],
				"debit": tran['debit'],
				"credit_in_account_currency": 0,
				"credit": 0
			})
		#credit lines
		elif tran['credit'] > 0:
			je_doc.append("accounts", {
				"account": tran['account'],
				"warehouse": tran['store_code'],
				"debit_in_account_currency": 0,
				"debit": 0,
				"credit_in_account_currency": tran['credit'],
				"credit": tran['credit']
			})

	try:
		if je_doc:
			je_doc.insert(ignore_permissions=True)
			je_doc.submit()
			return je_doc.name
	except Exception as e:
		frappe.log_error(message=e, title="Clearing JV Error")

def update_bank_tran_status(bank_transaction, status, ref_doctype=None, ref_docname=None):
	bank_tran = frappe.get_doc('Bank File Data', bank_transaction['name'])
	bank_tran.ref_doctype = ref_doctype
	bank_tran.ref_docname = ref_docname
	bank_tran.status = status
	bank_tran.save()

def update_jv_bank_file(bank_transaction, journal_entry=None):
	bank_file_name = frappe.db.get_list('Bank File', filters= {'bank': bank_transaction['bank'], 'batch_no': bank_transaction['batch_no'],
		 				'batch_date': bank_transaction['batch_date']}, fields=['name'])

	if bank_file_name:
		bank_file = frappe.get_doc('Bank File', bank_file_name[0])
		bank_file.journal_entry = journal_entry
		bank_file.save()