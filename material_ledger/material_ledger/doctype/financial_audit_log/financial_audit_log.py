# Copyright (c) 2025, Your Company
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FinancialAuditLog(Document):
    """
    Financial Audit Log DocType
    Tracks all financial report access and actions
    """
    
    def before_insert(self):
        """Set default values before insert"""
        if not self.timestamp:
            self.timestamp = frappe.utils.now_datetime()
        if not self.user:
            self.user = frappe.session.user
    
    def validate(self):
        """Validate audit log entry"""
        # Ensure required fields
        if not self.action:
            frappe.throw("Action is required")
        if not self.report_type:
            frappe.throw("Report Type is required")
    
    @staticmethod
    def log_action(action, report_type, **kwargs):
        """
        Static method to create audit log entry
        
        Args:
            action: Action type (view, export, print, etc.)
            report_type: Report type
            **kwargs: Additional fields
        """
        try:
            doc = frappe.new_doc("Financial Audit Log")
            doc.action = action
            doc.report_type = report_type
            doc.company = kwargs.get('company')
            doc.fiscal_year = kwargs.get('year')
            doc.period = kwargs.get('period')
            doc.user = frappe.session.user
            doc.timestamp = frappe.utils.now_datetime()
            doc.success = kwargs.get('success', True)
            doc.error_message = kwargs.get('error_message')
            doc.details = kwargs.get('details')
            
            # Get IP and user agent
            if hasattr(frappe.local, 'request') and frappe.local.request:
                forwarded = frappe.local.request.headers.get('X-Forwarded-For')
                if forwarded:
                    doc.ip_address = forwarded.split(',')[0].strip()
                else:
                    doc.ip_address = frappe.local.request.remote_addr
                doc.user_agent = (frappe.local.request.headers.get('User-Agent') or '')[:500]
            
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            
            return doc.name
            
        except Exception as e:
            frappe.log_error(f"Failed to create audit log: {str(e)}", "Audit Log Error")
            return None
