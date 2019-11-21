# -*- coding: utf-8 -*-
# Copyright (c) 2019, hello@openetech.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class PincodeDistance(Document):
	def validate(self):
		pincode_distance = frappe.db.get_value('Pincode Distance', 
								{'from_pincode': self.from_pincode, 'to_pincode': self.to_pincode}, 
								['name'], as_dict=1)

		if pincode_distance and pincode_distance.name and pincode_distance.name != self.name:
			frappe.throw(_("Pincode combination for distance already exists."))