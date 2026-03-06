# Copyright (c) 2026, Ahmad
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AIJobQueue(Document):
	"""AI Job Queue DocType for managing background AI processing"""
	
	def before_save(self):
		"""Validate job before saving"""
		if not self.job_id:
			import uuid
			self.job_id = str(uuid.uuid4())
			
		if not self.created_at:
			from frappe.utils import now
			self.created_at = now()
	
	def cancel_job(self):
		"""Cancel a queued or processing job"""
		if self.status in ["queued", "processing"]:
			self.status = "cancelled"
			self.save()
			return True
		return False
	
	def is_expired(self):
		"""Check if job result has expired"""
		if self.expires_at:
			from frappe.utils import now
			return now() > self.expires_at
		return False