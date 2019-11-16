# -*- coding: utf-8 -*-
# Copyright (c) 2019, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe import _

class CustomSettings(Document):
	def validate(self):
		if self.enable_tax_gross_up:
			if not self.gst_expense_account or not self.gst_income_account:
				frappe.throw(_("GST Expense and Income account are mandatory since tax gross up is enabled."))