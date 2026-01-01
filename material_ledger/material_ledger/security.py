"""
Security Module for Financial Analysis
Rate limiting, audit logging, and security utilities
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, get_datetime
from functools import wraps
import hashlib
import time
import json


# ============================================
# Rate Limiting Implementation
# ============================================

class RateLimiter:
    """
    Rate limiter using Redis cache
    Implements sliding window algorithm
    """
    
    def __init__(self, key_prefix="rate_limit", default_limit=100, default_window=60):
        """
        Initialize rate limiter
        
        Args:
            key_prefix: Redis key prefix
            default_limit: Default requests per window
            default_window: Default time window in seconds
        """
        self.key_prefix = key_prefix
        self.default_limit = default_limit
        self.default_window = default_window
    
    def get_key(self, identifier):
        """Generate rate limit key"""
        return f"{self.key_prefix}:{identifier}"
    
    def is_allowed(self, identifier, limit=None, window=None):
        """
        Check if request is allowed
        
        Args:
            identifier: Unique identifier (user, IP, etc.)
            limit: Max requests per window
            window: Time window in seconds
            
        Returns:
            tuple: (allowed: bool, remaining: int, reset_time: int)
        """
        limit = limit or self.default_limit
        window = window or self.default_window
        key = self.get_key(identifier)
        
        now = time.time()
        window_start = now - window
        
        try:
            # Get current count from cache
            cache_key = f"{key}:{int(now // window)}"
            current_count = cint(frappe.cache().get(cache_key) or 0)
            
            if current_count >= limit:
                reset_time = int((int(now // window) + 1) * window)
                return False, 0, reset_time
            
            # Increment counter
            frappe.cache().set(cache_key, current_count + 1, expires_in_sec=window)
            
            remaining = limit - current_count - 1
            reset_time = int((int(now // window) + 1) * window)
            
            return True, remaining, reset_time
            
        except Exception as e:
            # If cache fails, allow request but log error
            frappe.log_error(f"Rate limiter error: {str(e)}", "Rate Limiter")
            return True, limit, int(now + window)
    
    def get_remaining(self, identifier, limit=None, window=None):
        """Get remaining requests for identifier"""
        limit = limit or self.default_limit
        window = window or self.default_window
        key = self.get_key(identifier)
        
        now = time.time()
        cache_key = f"{key}:{int(now // window)}"
        current_count = cint(frappe.cache().get(cache_key) or 0)
        
        return max(0, limit - current_count)
    
    def reset(self, identifier):
        """Reset rate limit for identifier"""
        key = self.get_key(identifier)
        now = time.time()
        window = self.default_window
        cache_key = f"{key}:{int(now // window)}"
        frappe.cache().delete(cache_key)


# Default rate limiter instance
rate_limiter = RateLimiter(
    key_prefix="financial_api",
    default_limit=100,  # 100 requests
    default_window=60   # per minute
)


def rate_limited(limit=None, window=None, by="user"):
    """
    Rate limiting decorator
    
    Args:
        limit: Max requests per window
        window: Time window in seconds
        by: Rate limit by 'user', 'ip', or 'session'
    
    Usage:
        @frappe.whitelist()
        @rate_limited(limit=10, window=60)
        def my_api():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get identifier
            if by == "ip":
                identifier = frappe.local.request.remote_addr
            elif by == "session":
                identifier = frappe.session.sid
            else:
                identifier = frappe.session.user
            
            # Add function name to identifier
            identifier = f"{identifier}:{func.__name__}"
            
            # Check rate limit
            allowed, remaining, reset_time = rate_limiter.is_allowed(
                identifier, 
                limit=limit, 
                window=window
            )
            
            # Add rate limit headers (if in request context)
            if hasattr(frappe.local, 'response'):
                frappe.local.response.headers = frappe.local.response.headers or {}
                frappe.local.response.headers['X-RateLimit-Limit'] = str(limit or rate_limiter.default_limit)
                frappe.local.response.headers['X-RateLimit-Remaining'] = str(remaining)
                frappe.local.response.headers['X-RateLimit-Reset'] = str(reset_time)
            
            if not allowed:
                frappe.throw(
                    _("Rate limit exceeded. Please try again in {0} seconds.").format(
                        reset_time - int(time.time())
                    ),
                    title=_("Too Many Requests")
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================
# Audit Logging Implementation
# ============================================

class AuditLogger:
    """
    Audit logger for tracking financial report access and actions
    """
    
    # Action types
    ACTION_VIEW = "view"
    ACTION_EXPORT = "export"
    ACTION_PRINT = "print"
    ACTION_GENERATE = "generate"
    ACTION_COMPARE = "compare"
    ACTION_SHARE = "share"
    
    def __init__(self):
        self.doctype = "Financial Audit Log"
    
    def log(self, action, report_type, details=None, company=None, 
            year=None, period=None, success=True, error_message=None):
        """
        Log an audit event
        
        Args:
            action: Type of action (view, export, print, etc.)
            report_type: Type of report (financial_analysis, ledger, balance_sheet, etc.)
            details: Additional details dict
            company: Company name
            year: Fiscal year
            period: Period (Q1, annual, etc.)
            success: Whether action was successful
            error_message: Error message if failed
        """
        try:
            # Check if doctype exists
            if not frappe.db.exists("DocType", self.doctype):
                # Create log entry in database directly
                self._log_to_table(
                    action, report_type, details, company, 
                    year, period, success, error_message
                )
            else:
                # Use doctype
                doc = frappe.new_doc(self.doctype)
                doc.update({
                    "action": action,
                    "report_type": report_type,
                    "company": company,
                    "fiscal_year": year,
                    "period": period,
                    "user": frappe.session.user,
                    "timestamp": now_datetime(),
                    "ip_address": self._get_client_ip(),
                    "user_agent": self._get_user_agent(),
                    "success": success,
                    "error_message": error_message,
                    "details": json.dumps(details or {})
                })
                doc.insert(ignore_permissions=True)
                frappe.db.commit()
                
        except Exception as e:
            # Log to error log if audit logging fails
            frappe.log_error(
                f"Audit logging failed: {str(e)}\n"
                f"Action: {action}, Report: {report_type}, User: {frappe.session.user}",
                "Audit Log Error"
            )
    
    def _log_to_table(self, action, report_type, details, company, 
                       year, period, success, error_message):
        """Log directly to a simple table if doctype doesn't exist"""
        try:
            frappe.db.sql("""
                INSERT INTO `tabCustom Log` 
                (name, creation, modified, modified_by, owner, log_type, message, reference_type, reference_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                frappe.generate_hash(length=10),
                now_datetime(),
                now_datetime(),
                frappe.session.user,
                frappe.session.user,
                "Financial Audit",
                json.dumps({
                    "action": action,
                    "report_type": report_type,
                    "company": company,
                    "year": year,
                    "period": period,
                    "success": success,
                    "error_message": error_message,
                    "details": details,
                    "ip_address": self._get_client_ip(),
                    "user_agent": self._get_user_agent()
                }),
                report_type,
                company
            ))
            frappe.db.commit()
        except Exception:
            # Silently fail if table doesn't exist
            pass
    
    def _get_client_ip(self):
        """Get client IP address"""
        try:
            if hasattr(frappe.local, 'request'):
                # Check for forwarded IP
                forwarded = frappe.local.request.headers.get('X-Forwarded-For')
                if forwarded:
                    return forwarded.split(',')[0].strip()
                return frappe.local.request.remote_addr
        except Exception:
            pass
        return "unknown"
    
    def _get_user_agent(self):
        """Get user agent string"""
        try:
            if hasattr(frappe.local, 'request'):
                return frappe.local.request.headers.get('User-Agent', 'unknown')[:500]
        except Exception:
            pass
        return "unknown"
    
    def get_logs(self, filters=None, limit=100, order_by="creation desc"):
        """
        Get audit logs with filters
        
        Args:
            filters: Dict of filters
            limit: Max records to return
            order_by: Order by clause
            
        Returns:
            list: Audit log entries
        """
        filters = filters or {}
        
        if frappe.db.exists("DocType", self.doctype):
            return frappe.get_all(
                self.doctype,
                filters=filters,
                fields=["*"],
                order_by=order_by,
                limit_page_length=limit
            )
        return []
    
    def get_user_activity(self, user=None, days=30):
        """
        Get user activity summary
        
        Args:
            user: User to get activity for (default: current user)
            days: Number of days to look back
            
        Returns:
            dict: Activity summary
        """
        user = user or frappe.session.user
        from_date = get_datetime(now_datetime()) - frappe.utils.datetime.timedelta(days=days)
        
        if frappe.db.exists("DocType", self.doctype):
            logs = frappe.get_all(
                self.doctype,
                filters={
                    "user": user,
                    "timestamp": [">=", from_date]
                },
                fields=["action", "report_type", "timestamp", "success"]
            )
            
            summary = {
                "total_actions": len(logs),
                "views": len([l for l in logs if l.action == self.ACTION_VIEW]),
                "exports": len([l for l in logs if l.action == self.ACTION_EXPORT]),
                "prints": len([l for l in logs if l.action == self.ACTION_PRINT]),
                "failed_actions": len([l for l in logs if not l.success]),
                "reports_accessed": list(set([l.report_type for l in logs]))
            }
            
            return summary
        
        return {
            "total_actions": 0,
            "views": 0,
            "exports": 0,
            "prints": 0,
            "failed_actions": 0,
            "reports_accessed": []
        }


# Default audit logger instance
audit_logger = AuditLogger()


def audit_logged(action, report_type):
    """
    Audit logging decorator
    
    Args:
        action: Action type
        report_type: Report type
    
    Usage:
        @frappe.whitelist()
        @audit_logged("view", "financial_analysis")
        def get_financial_data():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract company and year from kwargs if available
            company = kwargs.get('company')
            year = kwargs.get('year')
            period = kwargs.get('period')
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful action
                audit_logger.log(
                    action=action,
                    report_type=report_type,
                    company=company,
                    year=year,
                    period=period,
                    success=True,
                    details={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                
                return result
                
            except Exception as e:
                # Log failed action
                audit_logger.log(
                    action=action,
                    report_type=report_type,
                    company=company,
                    year=year,
                    period=period,
                    success=False,
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator


# ============================================
# Security Utilities
# ============================================

def generate_secure_token(data, expiry_hours=24):
    """
    Generate a secure token for temporary access
    
    Args:
        data: Data to encode in token
        expiry_hours: Token validity in hours
        
    Returns:
        str: Secure token
    """
    import base64
    
    expiry = get_datetime(now_datetime()) + frappe.utils.datetime.timedelta(hours=expiry_hours)
    
    payload = {
        "data": data,
        "expiry": str(expiry),
        "user": frappe.session.user
    }
    
    # Create signature
    secret = frappe.utils.get_site_config().get("encryption_key", "default_key")
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hashlib.sha256(f"{payload_str}{secret}".encode()).hexdigest()
    
    token_data = {
        "payload": payload,
        "signature": signature
    }
    
    return base64.urlsafe_b64encode(json.dumps(token_data).encode()).decode()


def verify_secure_token(token):
    """
    Verify a secure token
    
    Args:
        token: Token to verify
        
    Returns:
        dict: Token data if valid, None otherwise
    """
    import base64
    
    try:
        token_data = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        payload = token_data["payload"]
        signature = token_data["signature"]
        
        # Verify signature
        secret = frappe.utils.get_site_config().get("encryption_key", "default_key")
        payload_str = json.dumps(payload, sort_keys=True)
        expected_signature = hashlib.sha256(f"{payload_str}{secret}".encode()).hexdigest()
        
        if signature != expected_signature:
            return None
        
        # Check expiry
        if get_datetime(payload["expiry"]) < get_datetime(now_datetime()):
            return None
        
        return payload["data"]
        
    except Exception:
        return None


def sanitize_html(html):
    """
    Sanitize HTML content to prevent XSS
    
    Args:
        html: HTML string to sanitize
        
    Returns:
        str: Sanitized HTML
    """
    import re
    
    # Remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove event handlers
    html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
    
    # Remove javascript: URLs
    html = re.sub(r'javascript\s*:', '', html, flags=re.IGNORECASE)
    
    # Remove data: URLs (except images)
    html = re.sub(r'data\s*:[^,]*(?!image)', '', html, flags=re.IGNORECASE)
    
    return html


def check_report_permission(company, report_type="financial_analysis"):
    """
    Check if user has permission to access financial reports
    
    Args:
        company: Company to check permission for
        report_type: Type of report
        
    Returns:
        bool: True if user has permission
    """
    # System Manager always has access
    if "System Manager" in frappe.get_roles():
        return True
    
    # Check if user has access to company
    if not frappe.has_permission("Company", doc=company, ptype="read"):
        return False
    
    # Check specific report permissions
    report_permissions = {
        "financial_analysis": ["Accounts Manager", "Accounts User"],
        "ledger": ["Accounts Manager", "Accounts User"],
        "balance_sheet": ["Accounts Manager"],
        "income_statement": ["Accounts Manager"],
        "cash_flow": ["Accounts Manager"]
    }
    
    required_roles = report_permissions.get(report_type, ["Accounts Manager"])
    user_roles = frappe.get_roles()
    
    return any(role in user_roles for role in required_roles)


# ============================================
# API Endpoints
# ============================================

@frappe.whitelist()
def get_rate_limit_status():
    """Get current rate limit status for user"""
    identifier = f"{frappe.session.user}:get_financial_analysis"
    remaining = rate_limiter.get_remaining(identifier)
    
    return {
        "remaining": remaining,
        "limit": rate_limiter.default_limit,
        "window_seconds": rate_limiter.default_window
    }


@frappe.whitelist()
def get_my_audit_logs(days=30, limit=50):
    """Get audit logs for current user"""
    days = cint(days)
    limit = min(cint(limit), 200)  # Cap at 200
    
    from_date = get_datetime(now_datetime()) - frappe.utils.datetime.timedelta(days=days)
    
    return audit_logger.get_logs(
        filters={
            "user": frappe.session.user,
            "timestamp": [">=", from_date]
        },
        limit=limit
    )


@frappe.whitelist()
def get_user_activity_summary(days=30):
    """Get activity summary for current user"""
    return audit_logger.get_user_activity(
        user=frappe.session.user,
        days=cint(days)
    )
