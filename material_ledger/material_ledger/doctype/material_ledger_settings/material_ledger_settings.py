# Copyright (c) 2025, Ahmad
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password


class MaterialLedgerSettings(Document):
    """
    Material Ledger Settings - Single DocType
    Manages all configuration for the Material Ledger application
    """
    
    def validate(self):
        """Validate settings"""
        # Validate rate limit settings
        if self.enable_rate_limiting:
            if not self.rate_limit_requests or self.rate_limit_requests < 1:
                frappe.throw(_("Rate limit requests must be at least 1"))
            if not self.rate_limit_window or self.rate_limit_window < 1:
                frappe.throw(_("Rate limit window must be at least 1 second"))
        
        # Validate cache settings
        if self.enable_caching:
            if not self.cache_timeout or self.cache_timeout < 1:
                frappe.throw(_("Cache timeout must be at least 1 second"))
        
        # Validate AI settings
        if self.enable_ai_analysis:
            if self.ai_provider == "DeepSeek" and not self.deepseek_api_key:
                frappe.msgprint(_("DeepSeek API Key is required for AI analysis"), indicator="orange")
            elif self.ai_provider == "OpenAI" and not self.openai_api_key:
                frappe.msgprint(_("OpenAI API Key is required for AI analysis"), indicator="orange")
    
    def on_update(self):
        """Clear cache when settings are updated"""
        frappe.cache().delete_keys("material_ledger*")
        frappe.cache().delete_keys("financial_analysis*")
    
    @staticmethod
    def get_settings():
        """
        Get Material Ledger Settings (cached)
        Returns dict with all settings
        """
        cache_key = "material_ledger_settings"
        settings = frappe.cache().get_value(cache_key)
        
        if not settings:
            try:
                doc = frappe.get_single("Material Ledger Settings")
                settings = {
                    "enable_ai_analysis": doc.enable_ai_analysis,
                    "ai_provider": doc.ai_provider,
                    "ai_model": doc.ai_model,
                    "enable_rate_limiting": doc.enable_rate_limiting,
                    "rate_limit_requests": doc.rate_limit_requests or 50,
                    "rate_limit_window": doc.rate_limit_window or 60,
                    "enable_audit_logging": doc.enable_audit_logging,
                    "audit_retention_days": doc.audit_retention_days or 90,
                    "enable_caching": doc.enable_caching,
                    "cache_timeout": doc.cache_timeout or 300,
                    "auto_refresh_interval": doc.auto_refresh_interval or 0,
                    "default_currency_format": doc.default_currency_format,
                    "decimal_places": doc.decimal_places or 2,
                    "date_format": doc.date_format,
                    "default_company": doc.default_company
                }
                frappe.cache().set_value(cache_key, settings, expires_in_sec=300)
            except Exception:
                # Return defaults if settings don't exist
                settings = {
                    "enable_ai_analysis": True,
                    "ai_provider": "DeepSeek",
                    "ai_model": "deepseek-reasoner",
                    "enable_rate_limiting": True,
                    "rate_limit_requests": 50,
                    "rate_limit_window": 60,
                    "enable_audit_logging": True,
                    "audit_retention_days": 90,
                    "enable_caching": True,
                    "cache_timeout": 300,
                    "auto_refresh_interval": 0,
                    "default_currency_format": "SAR",
                    "decimal_places": 2,
                    "date_format": "dd-mm-yyyy",
                    "default_company": None
                }
        
        return settings
    
    @staticmethod
    def get_api_key(provider=None):
        """
        Get decrypted API key for the specified provider
        
        Args:
            provider: 'DeepSeek' or 'OpenAI'. If None, uses configured provider.
            
        Returns:
            str: Decrypted API key or None
        """
        try:
            settings = MaterialLedgerSettings.get_settings()
            provider = provider or settings.get("ai_provider", "DeepSeek")
            
            if provider == "DeepSeek":
                return get_decrypted_password(
                    "Material Ledger Settings",
                    "Material Ledger Settings",
                    "deepseek_api_key"
                )
            elif provider == "OpenAI":
                return get_decrypted_password(
                    "Material Ledger Settings",
                    "Material Ledger Settings",
                    "openai_api_key"
                )
        except Exception as e:
            frappe.log_error(f"Error getting API key: {str(e)}", "Material Ledger")
            return None
        
        return None


@frappe.whitelist()
def get_settings():
    """API endpoint to get settings (for JS)"""
    return MaterialLedgerSettings.get_settings()


@frappe.whitelist()
def test_ai_connection():
    """Test AI provider connection"""
    import requests
    
    settings = MaterialLedgerSettings.get_settings()
    api_key = MaterialLedgerSettings.get_api_key()
    
    if not api_key:
        return {
            "success": False,
            "message": _("API key not configured")
        }
    
    provider = settings.get("ai_provider", "DeepSeek")
    
    try:
        if provider == "DeepSeek":
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.get("ai_model", "deepseek-reasoner"),
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": _("Connection successful! AI is ready.")
                }
            else:
                return {
                    "success": False,
                    "message": _("Connection failed: {0}").format(response.text)
                }
                
        elif provider == "OpenAI":
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.get("ai_model", "gpt-4"),
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": _("Connection successful! AI is ready.")
                }
            else:
                return {
                    "success": False,
                    "message": _("Connection failed: {0}").format(response.text)
                }
    
    except Exception as e:
        return {
            "success": False,
            "message": _("Connection error: {0}").format(str(e))
        }
