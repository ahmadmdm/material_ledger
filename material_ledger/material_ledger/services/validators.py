# Copyright (c) 2025, Ahmad
# For license information, please see license.txt

"""
Validators Module for Material Ledger
Handles input validation for all API endpoints
"""

import frappe
from frappe import _
from frappe.utils import getdate, cint, flt
from datetime import datetime


class ValidationError(Exception):
    """Custom validation error"""
    pass


class InputValidator:
    """Validator class for API inputs"""
    
    @staticmethod
    def validate_company(company, required=True):
        """Validate company parameter"""
        if required and not company:
            frappe.throw(_("Company is required"))
        
        if company and not frappe.db.exists("Company", company):
            frappe.throw(_("Company '{0}' does not exist").format(company))
        
        return company
    
    @staticmethod
    def validate_date_range(from_date, to_date, required=True):
        """Validate date range parameters"""
        if required and (not from_date or not to_date):
            frappe.throw(_("Date range is required"))
        
        if from_date and to_date:
            try:
                from_dt = getdate(from_date)
                to_dt = getdate(to_date)
                
                if from_dt > to_dt:
                    frappe.throw(_("From date cannot be after To date"))
                
                # Check for reasonable date range (max 10 years)
                days_diff = (to_dt - from_dt).days
                if days_diff > 3650:  # 10 years
                    frappe.throw(_("Date range cannot exceed 10 years"))
                
            except Exception as e:
                frappe.throw(_("Invalid date format: {0}").format(str(e)))
        
        return from_date, to_date
    
    @staticmethod
    def validate_year(year, required=True):
        """Validate fiscal year parameter"""
        year = cint(year)
        
        if required and not year:
            frappe.throw(_("Year is required"))
        
        current_year = datetime.now().year
        
        if year and (year < 1900 or year > current_year + 10):
            frappe.throw(_("Year must be between 1900 and {0}").format(current_year + 10))
        
        return year
    
    @staticmethod
    def validate_period(period, period_number=None):
        """Validate period parameters"""
        valid_periods = ["annual", "quarterly", "monthly"]
        
        if period and period.lower() not in valid_periods:
            frappe.throw(_("Period must be one of: {0}").format(", ".join(valid_periods)))
        
        period = (period or "annual").lower()
        
        if period == "monthly" and period_number:
            month = cint(period_number)
            if month < 1 or month > 12:
                frappe.throw(_("Month must be between 1 and 12"))
        
        elif period == "quarterly" and period_number:
            # Handle Q1, Q2, etc. formats
            quarter_str = str(period_number).strip().upper()
            if quarter_str.startswith('Q'):
                quarter_str = quarter_str[1:]
            
            try:
                quarter = int(quarter_str)
                if quarter < 1 or quarter > 4:
                    frappe.throw(_("Quarter must be between 1 and 4"))
            except (ValueError, TypeError):
                if period_number != "ALL":
                    frappe.throw(_("Invalid quarter format"))
        
        return period, period_number
    
    @staticmethod
    def validate_account(account, company=None):
        """Validate account parameter"""
        if account:
            filters = {"name": account}
            if company:
                filters["company"] = company
            
            if not frappe.db.exists("Account", filters):
                frappe.throw(_("Account '{0}' does not exist").format(account))
        
        return account
    
    @staticmethod
    def validate_party(party_type, party):
        """Validate party parameters"""
        valid_party_types = ["Customer", "Supplier", "Employee", "Shareholder", "Student"]
        
        if party_type and party_type not in valid_party_types:
            frappe.throw(_("Invalid party type"))
        
        if party_type and party:
            if not frappe.db.exists(party_type, party):
                frappe.throw(_("{0} '{1}' does not exist").format(party_type, party))
        
        return party_type, party
    
    @staticmethod
    def validate_cost_center(cost_center, company=None):
        """Validate cost center parameter"""
        if cost_center:
            filters = {"name": cost_center}
            if company:
                filters["company"] = company
            
            if not frappe.db.exists("Cost Center", filters):
                frappe.throw(_("Cost Center '{0}' does not exist").format(cost_center))
        
        return cost_center
    
    @staticmethod
    def validate_project(project):
        """Validate project parameter"""
        if project and not frappe.db.exists("Project", project):
            frappe.throw(_("Project '{0}' does not exist").format(project))
        
        return project
    
    @staticmethod
    def validate_sections(sections):
        """Validate sections parameter for lazy loading"""
        valid_sections = {
            "dashboard", "income", "balance", "cash", 
            "equity", "dupont", "ratios", "forecast", 
            "benchmark", "ai"
        }
        
        if sections:
            if isinstance(sections, str):
                try:
                    import json
                    sections = json.loads(sections)
                except:
                    sections = [sections]
            
            if isinstance(sections, (list, tuple, set)):
                invalid = set(str(s).lower() for s in sections) - valid_sections
                if invalid:
                    frappe.msgprint(
                        _("Unknown sections: {0}").format(", ".join(invalid)),
                        indicator="orange"
                    )
        
        return sections
    
    @staticmethod
    def sanitize_html(html):
        """Sanitize HTML input to prevent XSS"""
        if not html:
            return html
        
        # Remove script tags
        import re
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'on\w+="[^"]*"', '', html, flags=re.IGNORECASE)
        html = re.sub(r"on\w+='[^']*'", '', html, flags=re.IGNORECASE)
        
        return html


class LedgerValidator:
    """Validator for Ledger API endpoints"""
    
    @staticmethod
    def validate_ledger_params(company, from_date, to_date, account=None, 
                               party_type=None, party=None, cost_center=None, project=None):
        """Validate all ledger entry parameters"""
        v = InputValidator
        
        company = v.validate_company(company)
        from_date, to_date = v.validate_date_range(from_date, to_date)
        account = v.validate_account(account, company)
        party_type, party = v.validate_party(party_type, party)
        cost_center = v.validate_cost_center(cost_center, company)
        project = v.validate_project(project)
        
        return {
            "company": company,
            "from_date": from_date,
            "to_date": to_date,
            "account": account,
            "party_type": party_type,
            "party": party,
            "cost_center": cost_center,
            "project": project
        }


class AnalysisValidator:
    """Validator for Financial Analysis API endpoints"""
    
    @staticmethod
    def validate_analysis_params(company, year, period="annual", period_number=None, sections=None):
        """Validate all financial analysis parameters"""
        v = InputValidator
        
        company = v.validate_company(company)
        year = v.validate_year(year)
        period, period_number = v.validate_period(period, period_number)
        sections = v.validate_sections(sections)
        
        return {
            "company": company,
            "year": year,
            "period": period,
            "period_number": period_number,
            "sections": sections
        }
