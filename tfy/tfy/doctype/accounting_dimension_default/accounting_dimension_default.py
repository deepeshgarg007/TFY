# -*- coding: utf-8 -*-
# Copyright (c) 2019, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class AccountingDimensionDefault(Document):

	def validate(self):
		dim_list = []
		for row in self.dimension_defaults:
			dim_list.append(row.accounting_dimension)

		if len(dim_list) != len(set(dim_list)):
			frappe.throw(_("Duplicate dimensions cannot exist."))