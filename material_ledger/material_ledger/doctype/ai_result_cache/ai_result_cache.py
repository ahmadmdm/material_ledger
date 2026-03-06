# Copyright (c) 2026, Ahmad
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AIResultCache(Document):
	"""AI Result Cache DocType for storing AI analysis results"""
	
	def before_save(self):
		"""Set timestamps before saving"""
		if not self.created_at:
			from frappe.utils import now
			self.created_at = now()
	
	def is_expired(self):
		"""Check if cache entry has expired"""
		from frappe.utils import now
		return now() > self.expires_at
	
	def get_result_data(self):
		"""Get parsed result data"""
		if self.is_expired():
			return None
			
		import json
		try:
			return json.loads(self.result_data)
		except:
			return None
	
	def set_result_data(self, data):
		"""Set result data as JSON"""
		import json
		self.result_data = json.dumps(data)