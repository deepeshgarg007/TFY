# -*- coding: utf-8 -*-
# Copyright (c) 2019, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class StoreTerminal(Document):
	def validate(self):
		store_terminal = frappe.db.sql('''
							select
								name
							from
								`tabStore Terminal`
							where
								company = %s and merchant_id = %s and terminal_id =%s
								and name != %s
							''', (self.company, self.merchant_id, self.terminal_id, self.name))
		if store_terminal:
			frappe.throw(_("Merchant ID {0} and Terminal ID {1} already mapped for company {2}".
				format(self.merchant_id, self.terminal_id, self.company)))
