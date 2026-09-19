# Copyright (c) 2025, Safdar Ali and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FbrSaleType(Document):
	def validate(self):
		if self.tax_exempted:
			self.descriptive_tax = None
		if self.furthertax and self.fedpayable:
			self.fedpayable = 0
