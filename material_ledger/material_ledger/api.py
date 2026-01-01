import frappe
from frappe import _
from frappe.utils import flt, getdate, cint
import requests
import json
import time
import hashlib
from functools import wraps

# Import services
from material_ledger.material_ledger.services.validators import InputValidator, LedgerValidator, AnalysisValidator
from material_ledger.material_ledger.services.financial_calculator import FinancialCalculator
from material_ledger.material_ledger.services.ai_service import get_ai_service, generate_ai_report as ai_generate_report

# Import security module
try:
    from material_ledger.material_ledger.security import rate_limited, audit_logged, audit_logger
    SECURITY_ENABLED = True
except ImportError:
    SECURITY_ENABLED = False
    # Fallback decorators if security module not available
    def rate_limited(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def audit_logged(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


def get_settings():
    """Get Material Ledger Settings"""
    try:
        from material_ledger.material_ledger.doctype.material_ledger_settings.material_ledger_settings import MaterialLedgerSettings
        return MaterialLedgerSettings.get_settings()
    except Exception:
        return {
            "enable_rate_limiting": True,
            "rate_limit_requests": 50,
            "rate_limit_window": 60,
            "enable_caching": True,
            "cache_timeout": 300
        }


def apply_rate_limit(func):
    """Apply rate limiting if enabled in settings"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        settings = get_settings()
        if settings.get("enable_rate_limiting") and SECURITY_ENABLED:
            limit = settings.get("rate_limit_requests", 50)
            window = settings.get("rate_limit_window", 60)
            decorated = rate_limited(limit=limit, window=window, by="user")(func)
            return decorated(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper


@frappe.whitelist()
@apply_rate_limit
def get_ledger_entries(company, from_date, to_date, account=None, party_type=None, party=None, cost_center=None, project=None):
    """
    Get General Ledger entries with filters
    Professional implementation with proper error handling and validation
    """
    # Validation
    if not company:
        frappe.throw(_("Company is required"))
    
    if not from_date or not to_date:
        frappe.throw(_("Date range is required"))

    # Build filters
    filters = {
        "company": company,
        "posting_date": ["between", [from_date, to_date]],
        "is_cancelled": 0
    }

    if account: 
        filters["account"] = account
    if party_type and party:
        filters["party_type"] = party_type
        filters["party"] = party
    if cost_center: 
        filters["cost_center"] = cost_center
    if project: 
        filters["project"] = project

    # Get opening balance
    opening_balance = 0.0
    if account:
        opening_balance = get_opening_balance(company, account, from_date, party_type, party, cost_center, project)

    # Fetch GL Entries
    gl_entries = frappe.get_all(
        "GL Entry",
        fields=[
            "name", "posting_date", "account", "party_type", "party", 
            "debit", "credit", "voucher_type", "voucher_no", "remarks", 
            "cost_center", "project", "against", "is_opening", 
            "transaction_date", "due_date"
        ],
        filters=filters,
        order_by="posting_date asc, creation asc",
        limit_page_length=None
    )

    # Process entries
    data = []
    balance = opening_balance

    # Add opening balance entry if account is selected
    if account and opening_balance != 0:
        data.append({
            "posting_date": from_date,
            "account": account,
            "remarks": _("Opening Balance"),
            "debit": 0, 
            "credit": 0,
            "balance": balance,
            "is_opening": True,
            "voucher_type": "",
            "voucher_no": ""
        })

    # Add all entries with running balance
    for entry in gl_entries:
        balance += flt(entry.debit) - flt(entry.credit)
        entry["balance"] = balance
        data.append(entry)

    return data


@frappe.whitelist()
def generate_ledger_pdf(html):
    """
    Generate PDF from HTML content - Whitelisted for API access
    """
    from frappe.utils.pdf import get_pdf
    import base64
    
    try:
        pdf_content = get_pdf(html, {"orientation": "Landscape"})
        return {
            "success": True,
            "pdf_base64": base64.b64encode(pdf_content).decode('utf-8')
        }
    except Exception as e:
        frappe.log_error(f"PDF Generation Error: {str(e)}", "Material Ledger PDF")
        return {
            "success": False,
            "error": str(e)
        }


def get_opening_balance(company, account, from_date, party_type=None, party=None, cost_center=None, project=None):
    """
    Calculate opening balance for an account before the from_date
    """
    conditions = []
    values = {
        "company": company, 
        "account": account, 
        "from_date": from_date
    }
    
    if party_type and party:
        conditions.append("AND party_type = %(party_type)s AND party = %(party)s")
        values["party_type"] = party_type
        values["party"] = party
    
    if cost_center: 
        conditions.append("AND cost_center = %(cost_center)s")
        values["cost_center"] = cost_center
        
    if project: 
        conditions.append("AND project = %(project)s")
        values["project"] = project

    query = """
        SELECT SUM(debit) - SUM(credit)
        FROM `tabGL Entry`
        WHERE company = %(company)s 
        AND account = %(account)s
        AND posting_date < %(from_date)s 
        AND is_cancelled = 0
        {conditions}
    """.format(conditions=" ".join(conditions))
    
    result = frappe.db.sql(query, values)
    return flt(result[0][0]) if result and result[0][0] else 0.0


def get_current_assets(company, end_date):
    """Get actual current assets (Cash, Bank, Receivables, Stock)"""
    res = frappe.db.sql("""
        SELECT SUM(gle.debit) - SUM(gle.credit) as balance
        FROM `tabGL Entry` gle
        JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.company = %s 
        AND gle.posting_date <= %s
        AND acc.root_type = 'Asset'
        AND (acc.account_type IN ('Cash', 'Bank', 'Receivable', 'Stock')
             OR acc.name LIKE '%%Current%%')
        AND gle.is_cancelled = 0
    """, (company, end_date))
    return flt(res[0][0]) if res and res[0][0] else 0.0


def get_current_liabilities(company, end_date):
    """Get actual current liabilities (Payables, Short-term loans)"""
    res = frappe.db.sql("""
        SELECT SUM(gle.credit) - SUM(gle.debit) as balance
        FROM `tabGL Entry` gle
        JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.company = %s 
        AND gle.posting_date <= %s
        AND acc.root_type = 'Liability'
        AND (acc.account_type IN ('Payable')
             OR acc.name LIKE '%%Current%%'
             OR acc.name LIKE '%%Short%%')
        AND gle.is_cancelled = 0
    """, (company, end_date))
    return flt(res[0][0]) if res and res[0][0] else 0.0


def get_actual_cash_flows(company, start_date, end_date, net_profit):
    """Calculate actual cash flow from GL entries - OPTIMIZED single query"""
    result = frappe.db.sql("""
        SELECT 
            -- Operating: Cash accounts change
            SUM(CASE WHEN acc.root_type = 'Asset' AND acc.account_type IN ('Cash', 'Bank') 
                THEN gle.debit - gle.credit ELSE 0 END) as cash_change,
            -- Operating: AR change
            SUM(CASE WHEN acc.root_type = 'Asset' AND acc.account_type = 'Receivable' 
                THEN gle.debit - gle.credit ELSE 0 END) as ar_change,
            -- Operating: AP change
            SUM(CASE WHEN acc.root_type = 'Liability' AND acc.account_type = 'Payable' 
                THEN gle.credit - gle.debit ELSE 0 END) as ap_change,
            -- Investing: Fixed assets
            SUM(CASE WHEN acc.root_type = 'Asset' AND acc.account_type IN ('Fixed Asset', 'Accumulated Depreciation')
                THEN gle.credit - gle.debit ELSE 0 END) as investing_flow,
            -- Financing: Equity and Loans
            SUM(CASE WHEN acc.account_type = 'Equity' OR (acc.root_type = 'Liability' AND acc.name LIKE '%%Loan%%')
                THEN gle.credit - gle.debit ELSE 0 END) as financing_flow
        FROM `tabGL Entry` gle
        STRAIGHT_JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.company = %s 
        AND gle.posting_date BETWEEN %s AND %s
        AND gle.is_cancelled = 0
    """, (company, start_date, end_date), as_dict=True)[0]
    
    ar_change = flt(result.get('ar_change', 0))
    ap_change = flt(result.get('ap_change', 0))
    investing_flow = flt(result.get('investing_flow', 0))
    financing_flow = flt(result.get('financing_flow', 0))
    operating_flow = net_profit - ar_change + ap_change  # Simplified indirect method
    
    return {
        "operating": flt(operating_flow, 2),
        "investing": flt(investing_flow, 2),
        "financing": flt(financing_flow, 2),
        "net": flt(operating_flow + investing_flow + financing_flow, 2),
        "method": "actual"
    }


# Cache for financial analysis results
_analysis_cache = {}

def get_cache_key(company, year, period, period_number, sections):
    """Generate cache key for analysis results"""
    import hashlib
    key_str = f"{company}:{year}:{period}:{period_number}:{sorted(sections) if sections else 'all'}"
    return hashlib.md5(key_str.encode()).hexdigest()


@frappe.whitelist()
@apply_rate_limit
def get_financial_analysis(company, year, period="annual", period_number=None, sections=None):
    """
    Advanced Financial Analysis - CFO Level with AI Insights
    Comprehensive metrics for expert accountants
    Supports: monthly, quarterly, and annual periods

    sections: optional list/JSON/string of tabs to return for lazy loading
    """
    import time
    start_time = time.time()
    
    if not company:
        frappe.throw(_("Company is required"))
    
    year = cint(year)
    if not year:
        frappe.throw(_("Valid year is required"))

    # Server-side caching for 5 minutes
    cache_key = f"financial_analysis:{company}:{year}:{period}:{period_number}"
    cached_data = frappe.cache().get_value(cache_key)
    if cached_data and not sections:  # Return cached if full data and not specific sections
        cached_data['_cached'] = True
        cached_data['_cache_time'] = time.time() - start_time
        return cached_data

    requested_sections = set()
    if sections:
        if isinstance(sections, str):
            try:
                parsed = json.loads(sections)
                sections = parsed
            except Exception:
                sections = [sections]
        if isinstance(sections, (list, tuple, set)):
            requested_sections = {str(s) for s in sections if s}
    fetch_all = len(requested_sections) == 0

    def need(section_name):
        return fetch_all or section_name in requested_sections

    # Helper to extract quarter number from various formats (Q1, 1, "Q1", etc.)
    def parse_quarter(val):
        if not val:
            return None
        val_str = str(val).strip().upper()
        if val_str.startswith('Q'):
            val_str = val_str[1:]
        try:
            q = int(val_str)
            return q if 1 <= q <= 4 else None
        except (ValueError, TypeError):
            return None

    # Determine date range based on period
    if period == "monthly" and period_number:
        month = cint(period_number)
        if month < 1 or month > 12:
            month = 1  # Default to January if invalid
        start_date = f"{year}-{month:02d}-01"
        end_date = frappe.utils.get_last_day(start_date)
        period_label = frappe.utils.formatdate(start_date, "MMM YYYY")
    elif period == "quarterly" and period_number:
        quarter = parse_quarter(period_number)
        if not quarter:
            quarter = 1  # Default to Q1 if invalid
        start_month = (quarter - 1) * 3 + 1
        start_date = f"{year}-{start_month:02d}-01"
        end_month = start_month + 2
        end_date = frappe.utils.get_last_day(f"{year}-{end_month:02d}-01")
        period_label = f"Q{quarter} {year}"
    else:  # annual
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        period_label = str(year)
    
    prev_year = year - 1
    prev_start = f"{prev_year}-01-01"
    prev_end = f"{prev_year}-12-31"
    two_years_ago = year - 2
    two_years_start = f"{two_years_ago}-01-01"
    two_years_end = f"{two_years_ago}-12-31"
    
    # Earliest date we need to query
    earliest_date = two_years_start

    # SUPER OPTIMIZED: Single query to get all balances for all periods at once
    def get_all_periods_balances():
        """Get all account balances for all periods in a SINGLE query"""
        res = frappe.db.sql("""
            SELECT /*+ STRAIGHT_JOIN */
                acc.root_type,
                -- Current period
                SUM(CASE WHEN gle.posting_date BETWEEN %s AND %s THEN gle.debit - gle.credit ELSE 0 END) as current_balance,
                -- Cumulative until end date
                SUM(CASE WHEN gle.posting_date <= %s THEN gle.debit - gle.credit ELSE 0 END) as cumulative_balance,
                -- Previous year
                SUM(CASE WHEN gle.posting_date BETWEEN %s AND %s THEN gle.debit - gle.credit ELSE 0 END) as prev_balance,
                -- Previous year cumulative
                SUM(CASE WHEN gle.posting_date <= %s THEN gle.debit - gle.credit ELSE 0 END) as prev_cumulative,
                -- Two years ago
                SUM(CASE WHEN gle.posting_date BETWEEN %s AND %s THEN gle.debit - gle.credit ELSE 0 END) as two_years_balance,
                -- Opening balance
                SUM(CASE WHEN gle.posting_date < %s THEN gle.debit - gle.credit ELSE 0 END) as opening_balance
            FROM `tabGL Entry` gle
            STRAIGHT_JOIN `tabAccount` acc ON gle.account = acc.name
            WHERE gle.company = %s 
            AND gle.is_cancelled = 0
            AND gle.posting_date <= %s
            GROUP BY acc.root_type
        """, (
            start_date, end_date,  # current
            end_date,              # cumulative
            prev_start, prev_end,  # prev year
            prev_end,              # prev cumulative
            two_years_start, two_years_end,  # two years
            start_date,            # opening
            company,
            end_date               # max date filter
        ), as_dict=True)
        
        # Organize results
        result = {
            'current': {},
            'cumulative': {},
            'prev': {},
            'prev_cumulative': {},
            'two_years': {},
            'opening': {}
        }
        
        for r in res:
            root_type = r['root_type']
            result['current'][root_type] = abs(flt(r['current_balance']))
            result['cumulative'][root_type] = abs(flt(r['cumulative_balance']))
            result['prev'][root_type] = abs(flt(r['prev_balance']))
            result['prev_cumulative'][root_type] = abs(flt(r['prev_cumulative']))
            result['two_years'][root_type] = abs(flt(r['two_years_balance']))
            result['opening'][root_type] = abs(flt(r['opening_balance']))
        
        return result

    # Get all balances in ONE query instead of 6 separate queries
    all_balances = get_all_periods_balances()
    current_balances = all_balances['current']
    cumulative_balances = all_balances['cumulative']
    prev_balances = all_balances['prev']
    prev_cumulative = all_balances['prev_cumulative']
    two_years_balances = all_balances['two_years']
    opening_cumulative = all_balances['opening']
    
    # Current year data
    income = current_balances.get("Income", 0.0)
    expense = current_balances.get("Expense", 0.0)
    assets = cumulative_balances.get("Asset", 0.0)
    liabilities = cumulative_balances.get("Liability", 0.0)
    equity = assets - liabilities
    net_profit = income - expense
    
    # Previous year data for comparison
    prev_income = prev_balances.get("Income", 0.0)
    prev_expense = prev_balances.get("Expense", 0.0)
    prev_assets = prev_cumulative.get("Asset", 0.0)
    prev_liabilities = prev_cumulative.get("Liability", 0.0)
    prev_equity = prev_assets - prev_liabilities
    prev_profit = prev_income - prev_expense
    
    # Two years ago data
    two_years_income = two_years_balances.get("Income", 0.0)
    two_years_expense = two_years_balances.get("Expense", 0.0)
    two_years_profit = two_years_income - two_years_expense

    # Working Capital Calculation - IMPROVED: Get actual current assets/liabilities
    current_assets_data = get_current_assets(company, end_date)
    current_liabilities_data = get_current_liabilities(company, end_date)
    current_assets = current_assets_data if current_assets_data > 0 else assets * 0.4
    current_liabilities = current_liabilities_data if current_liabilities_data > 0 else liabilities * 0.3
    working_capital = current_assets - current_liabilities
    
    # Statement of Changes in Equity
    opening_assets = opening_cumulative.get("Asset", 0.0)
    opening_liabilities = opening_cumulative.get("Liability", 0.0)
    opening_equity = opening_assets - opening_liabilities
    equity_changes = calculate_equity_changes(company, start_date, end_date, opening_equity, net_profit, equity)

    # Financial Ratios (Complete Suite)
    ratios = {
        "roe": flt((net_profit / equity * 100), 2) if equity > 0 else 0,
        "roa": flt((net_profit / assets * 100), 2) if assets > 0 else 0,
        "net_margin": flt((net_profit / income * 100), 2) if income > 0 else 0,
        "asset_turnover": flt(income / assets, 2) if assets > 0 else 0,
        "leverage": flt(assets / equity, 2) if equity > 0 else 0,
        "current_ratio": flt(current_assets / current_liabilities, 2) if current_liabilities > 0 else 0,
        "quick_ratio": flt((current_assets * 0.7) / current_liabilities, 2) if current_liabilities > 0 else 0,
        "debt_ratio": flt((liabilities / assets * 100), 2) if assets > 0 else 0,
        "z_score": 0,
        "income_growth": flt(((income - prev_income) / prev_income * 100), 2) if prev_income else 0,
        "profit_growth": flt(((net_profit - prev_profit) / abs(prev_profit) * 100), 2) if prev_profit != 0 else 0,
        "working_capital": working_capital,
        "operating_margin": flt((net_profit / income * 100), 2) if income > 0 else 0,
        "dupont_roe": 0
    }

    # Altman Z-Score
    if assets > 0 and liabilities > 0:
        a = (working_capital / assets) * 1.2
        b = (equity / assets) * 1.4
        c = (net_profit / assets) * 3.3
        d = (equity / liabilities) * 0.6
        e = (income / assets) * 1.0
        ratios["z_score"] = flt(a + b + c + d + e, 2)

    # DuPont Analysis (ROE breakdown)
    if equity > 0 and assets > 0 and income > 0:
        profit_margin = net_profit / income
        asset_turnover = income / assets
        equity_multiplier = assets / equity
        ratios["dupont_roe"] = flt(profit_margin * asset_turnover * equity_multiplier * 100, 2)

    # Health Score (0-100)
    health_score = calculate_health_score(ratios, prev_income, prev_profit)

    # Risk Indicators
    risk_flags = detect_risk_flags(ratios, net_profit, income, assets, liabilities)

    # Trend Data (3 years)
    trend = {
        "current_year": {"profit": net_profit, "income": income, "assets": assets},
        "prev_year": {"profit": prev_profit, "income": prev_income, "assets": prev_assets},
        "two_years_ago": {"profit": two_years_profit, "income": two_years_income}
    }

    quarterly = []
    monthly = []
    if need("income") or need("ai"):
        quarterly = frappe.db.sql("""
            SELECT 
                QUARTER(posting_date) as q,
                SUM(CASE WHEN acc.root_type = 'Income' THEN (credit - debit) ELSE 0 END) as inc,
                SUM(CASE WHEN acc.root_type = 'Expense' THEN (debit - credit) ELSE 0 END) as exp
            FROM `tabGL Entry` gle 
            JOIN `tabAccount` acc ON gle.account = acc.name
            WHERE gle.company = %s 
            AND posting_date BETWEEN %s AND %s 
            AND is_cancelled = 0
            GROUP BY q 
            ORDER BY q
        """, (company, start_date, end_date), as_dict=True)
        
        monthly = frappe.db.sql("""
            SELECT 
                MONTH(posting_date) as month,
                MONTHNAME(posting_date) as month_name,
                SUM(CASE WHEN acc.root_type = 'Income' THEN (credit - debit) ELSE 0 END) as inc,
                SUM(CASE WHEN acc.root_type = 'Expense' THEN (debit - credit) ELSE 0 END) as exp
            FROM `tabGL Entry` gle 
            JOIN `tabAccount` acc ON gle.account = acc.name
            WHERE gle.company = %s 
            AND posting_date BETWEEN %s AND %s 
            AND is_cancelled = 0
            GROUP BY month, month_name
            ORDER BY month
        """, (company, start_date, end_date), as_dict=True)
        
        for q in quarterly:
            q['profit'] = q['inc'] - q['exp']
        for m in monthly:
            m['profit'] = m['inc'] - m['exp']

    cash_flow = {}
    cashflow_analysis = {}
    if need("cash") or need("ai"):
        # IMPROVED: Use actual cash flow calculations instead of estimates
        cash_flow = get_actual_cash_flows(company, start_date, end_date, net_profit)
        cashflow_analysis = analyze_cashflow(cash_flow, net_profit)

    # AI Report - Run in background for faster response
    ai_report = None
    ai_job_id = None
    if need("ai"):
        # Generate a unique job ID for this request
        ai_job_id = generate_ai_job_id(company, year, period, period_number)
        
        # Check if AI report is already cached
        cached_ai = frappe.cache().get_value(f"ai_report_{ai_job_id}")
        if cached_ai:
            ai_report = cached_ai
        else:
            # Prepare data for background job
            ai_data = {
                "period": period_label,
                "net_profit": net_profit,
                "income": income,
                "expense": expense,
                "assets": assets,
                "liabilities": liabilities,
                "equity": equity,
                "ratios": ratios,
                "risk_flags": risk_flags,
                "health_score": health_score,
                "quarterly": quarterly,
                "monthly": monthly,
                "equity_changes": equity_changes,
                "cash_flow": cash_flow
            }
            # Enqueue background job for AI generation
            frappe.enqueue(
                "material_ledger.material_ledger.api.generate_ai_report_background",
                queue="long",
                timeout=300,
                job_id=ai_job_id,
                company=company,
                year=year,
                data=ai_data,
                job_id_key=ai_job_id
            )

    response = {
        "period": period_label,
        "period_type": period,
        "summary": {
            "income": income,
            "expense": expense,
            "profit": net_profit,
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "health_score": health_score
        }
    }

    if need("ratios") or need("dupont") or need("dashboard") or need("ai"):
        response["ratios"] = ratios

    if need("dashboard") or need("ai"):
        response["trend"] = trend
        response["risk_flags"] = risk_flags

    if need("income") or need("ai"):
        response["quarterly"] = quarterly
        response["monthly"] = monthly
        response["income_statement_analysis"] = analyze_income_statement(income, expense, net_profit, prev_income, prev_profit)

    if need("balance") or need("ai"):
        response["balance_sheet_analysis"] = analyze_balance_sheet(assets, liabilities, equity, prev_assets, prev_liabilities)

    if need("cash") or need("ai"):
        response["cash_flow"] = cash_flow
        response["cashflow_analysis"] = cashflow_analysis

    if need("equity") or need("ai"):
        response["equity_changes"] = equity_changes

    if need("ai"):
        if ai_report:
            response["ai_report"] = ai_report
            response["ai_status"] = "ready"
        else:
            response["ai_report"] = None
            response["ai_status"] = "loading"
            response["ai_job_id"] = ai_job_id

    # Cache the full response for 5 minutes
    if fetch_all:
        frappe.cache().set_value(cache_key, response, expires_in_sec=300)
    
    response['_load_time'] = time.time() - start_time
    return response


def calculate_equity_changes(company, start_date, end_date, opening_equity, net_profit, closing_equity):
    """Calculate Statement of Changes in Equity"""
    
    # Get capital contributions and withdrawals (estimated from Owner Equity account movements)
    capital_changes = frappe.db.sql("""
        SELECT 
            SUM(CASE WHEN debit > credit THEN debit - credit ELSE 0 END) as withdrawals,
            SUM(CASE WHEN credit > debit THEN credit - debit ELSE 0 END) as contributions
        FROM `tabGL Entry` gle
        JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.company = %s 
        AND gle.posting_date BETWEEN %s AND %s
        AND acc.account_type = 'Equity'
        AND acc.root_type = 'Equity'
        AND is_cancelled = 0
    """, (company, start_date, end_date), as_dict=True)
    
    contributions = flt(capital_changes[0].get('contributions', 0) if capital_changes else 0)
    withdrawals = flt(capital_changes[0].get('withdrawals', 0) if capital_changes else 0)
    
    # Calculate dividends (estimated)
    dividends = 0
    if net_profit > 0:
        dividends = net_profit * 0.3  # Assume 30% dividend payout ratio
    
    return {
        "opening_balance": opening_equity,
        "net_profit": net_profit,
        "contributions": contributions,
        "withdrawals": withdrawals,
        "dividends": dividends,
        "closing_balance": closing_equity,
        "total_changes": closing_equity - opening_equity
    }


def analyze_income_statement(income, expense, profit, prev_income, prev_profit):
    """Detailed Income Statement Analysis"""
    
    margin = (profit / income * 100) if income > 0 else 0
    prev_margin = (prev_profit / prev_income * 100) if prev_income > 0 else 0
    revenue_growth = ((income - prev_income) / prev_income * 100) if prev_income > 0 else 0
    profit_growth = ((profit - prev_profit) / abs(prev_profit) * 100) if prev_profit != 0 else 0
    
    analysis = {
        "gross_margin": margin,
        "margin_change": margin - prev_margin,
        "revenue_growth": revenue_growth,
        "profit_growth": profit_growth,
        "expense_ratio": (expense / income * 100) if income > 0 else 0,
        "insights": []
    }
    
    # Generate insights
    if revenue_growth > 10:
        analysis["insights"].append("نمو قوي في الإيرادات - استمرار التوسع في السوق")
    elif revenue_growth < -5:
        analysis["insights"].append("⚠️ انخفاض الإيرادات - يتطلب مراجعة استراتيجية المبيعات")
    
    if margin > 20:
        analysis["insights"].append("هامش ربح ممتاز - كفاءة تشغيلية عالية")
    elif margin < 5:
        analysis["insights"].append("⚠️ هامش ربح منخفض - ضغوط على التكاليف")
    
    if profit_growth > 15:
        analysis["insights"].append("نمو استثنائي في الأرباح")
    
    return analysis


def analyze_balance_sheet(assets, liabilities, equity, prev_assets, prev_liabilities):
    """Detailed Balance Sheet Analysis"""
    
    debt_to_equity = (liabilities / equity) if equity > 0 else 0
    debt_to_assets = (liabilities / assets * 100) if assets > 0 else 0
    asset_growth = ((assets - prev_assets) / prev_assets * 100) if prev_assets > 0 else 0
    
    analysis = {
        "debt_to_equity": debt_to_equity,
        "debt_to_assets": debt_to_assets,
        "asset_growth": asset_growth,
        "equity_ratio": (equity / assets * 100) if assets > 0 else 0,
        "insights": []
    }
    
    if debt_to_equity < 0.5:
        analysis["insights"].append("هيكل تمويل محافظ - اعتماد قليل على الديون")
    elif debt_to_equity > 2:
        analysis["insights"].append("⚠️ ديون مرتفعة مقارنة بحقوق الملكية")
    
    if asset_growth > 20:
        analysis["insights"].append("نمو كبير في الأصول - توسع في الاستثمارات")
    elif asset_growth < 0:
        analysis["insights"].append("⚠️ انكماش في قاعدة الأصول")
    
    if debt_to_assets > 70:
        analysis["insights"].append("⚠️ نسبة مديونية عالية جداً")
    elif debt_to_assets < 30:
        analysis["insights"].append("وضع مالي قوي - ديون منخفضة")
    
    return analysis


def analyze_cashflow(cash_flow, net_profit):
    """Detailed Cash Flow Analysis"""
    
    operating_margin = (cash_flow["operating"] / net_profit * 100) if net_profit > 0 else 0
    free_cash_flow = cash_flow["operating"] + cash_flow["investing"]
    
    analysis = {
        "operating_margin": operating_margin,
        "free_cash_flow": free_cash_flow,
        "cash_conversion": operating_margin,
        "insights": []
    }
    
    if cash_flow["operating"] > net_profit:
        analysis["insights"].append("تدفق نقدي تشغيلي قوي - أفضل من الأرباح المحاسبية")
    elif cash_flow["operating"] < 0:
        analysis["insights"].append("⚠️ تدفق نقدي سالب من العمليات")
    
    if free_cash_flow > 0:
        analysis["insights"].append("توليد تدفق نقدي حر إيجابي")
    else:
        analysis["insights"].append("⚠️ التدفق النقدي الحر سالب - استثمارات تفوق التشغيل")
    
    if cash_flow["net"] < 0:
        analysis["insights"].append("⚠️ صافي تدفق نقدي سالب - مراقبة السيولة")
    
    return analysis


def calculate_health_score(ratios, prev_income, prev_profit):
    """Calculate overall financial health score (0-100)"""
    score = 50  # Base score
    
    # ROE Impact
    roe = ratios.get('roe', 0)
    if roe > 15:
        score += 15
    elif roe > 10:
        score += 10
    elif roe > 5:
        score += 5
    elif roe < 0:
        score -= 15
    
    # Profitability
    net_margin = ratios.get('net_margin', 0)
    if net_margin > 15:
        score += 10
    elif net_margin > 10:
        score += 7
    elif net_margin < 0:
        score -= 15
    
    # Liquidity
    current_ratio = ratios.get('current_ratio', 0)
    if 1.5 <= current_ratio <= 3:
        score += 10
    elif current_ratio > 3:
        score += 5
    elif current_ratio < 1:
        score -= 15
    
    # Leverage
    leverage = ratios.get('leverage', 0)
    if leverage < 2:
        score += 10
    elif leverage > 3:
        score -= 10
    
    # Growth
    growth = ratios.get('income_growth', 0)
    if growth > 10:
        score += 10
    elif growth > 5:
        score += 5
    elif growth < -10:
        score -= 10
    
    # Z-Score
    z_score = ratios.get('z_score', 0)
    if z_score > 2.9:
        score += 10
    elif z_score < 1.8:
        score -= 20
    
    return min(max(score, 0), 100)


def detect_risk_flags(ratios, profit, income, assets, liabilities):
    """Detect financial risk flags"""
    flags = []
    
    # Profitability Risk
    if profit < 0:
        flags.append({
            "level": "critical",
            "title": "إنهيار الربحية",
            "message": "الشركة تحقق خسائر مالية - يتطلب تدخل فوري",
            "code": "LOSS"
        })
    elif ratios.get('net_margin', 0) < 2:
        flags.append({
            "level": "warning",
            "title": "هامش ربح منخفض",
            "message": "هامش الربح أقل من 2% - يحتاج تحسين العمليات",
            "code": "LOW_MARGIN"
        })
    
    # Growth Risk
    if ratios.get('income_growth', 0) < -5:
        flags.append({
            "level": "warning",
            "title": "انخفاض الإيرادات",
            "message": "انخفاض الإيرادات بنسبة تزيد عن 5% مقارنة بالسنة السابقة",
            "code": "REVENUE_DECLINE"
        })
    
    # Liquidity Risk
    if ratios.get('current_ratio', 0) < 1:
        flags.append({
            "level": "critical",
            "title": "مشكلة سيولة حرجة",
            "message": "الالتزامات قصيرة الأجل تتجاوز الأصول المتداولة",
            "code": "LIQUIDITY_CRISIS"
        })
    
    # Leverage Risk
    if ratios.get('leverage', 0) > 3:
        flags.append({
            "level": "warning",
            "title": "ديون مرتفعة جداً",
            "message": "نسبة الديون إلى حقوق الملكية مرتفعة - مخاطر إعادة هيكلة",
            "code": "HIGH_DEBT"
        })
    elif ratios.get('debt_ratio', 0) > 70:
        flags.append({
            "level": "warning",
            "title": "نسبة مديونية مرتفعة",
            "message": "أكثر من 70% من الأصول ممولة بالديون",
            "code": "HIGH_DEBT_RATIO"
        })
    
    # Z-Score Risk
    z_score = ratios.get('z_score', 0)
    if z_score < 1.8:
        flags.append({
            "level": "critical",
            "title": "خطر إفلاس وشيك",
            "message": "Z-Score أقل من 1.8 - احتمالية إفلاس عالية",
            "code": "BANKRUPTCY_RISK"
        })
    elif z_score < 2.9:
        flags.append({
            "level": "warning",
            "title": "منطقة رمادية",
            "message": "Z-Score في منطقة خطر - يتطلب مراقبة دقيقة",
            "code": "GREY_ZONE"
        })
    
    # ROA Risk
    if ratios.get('roa', 0) < 0:
        flags.append({
            "level": "critical",
            "title": "عدم كفاءة استخدام الأصول",
            "message": "ROA سالب - الأصول لا تحقق أرباح",
            "code": "LOW_ROA"
        })
    
    return flags


def generate_ai_job_id(company, year, period, period_number):
    """Generate unique job ID for AI background task"""
    key = f"{company}_{year}_{period}_{period_number}"
    return f"ai_report_{hashlib.md5(key.encode()).hexdigest()[:16]}"


def generate_ai_report_background(company, year, data, job_id_key):
    """
    Background job to generate AI report
    Stores result in cache when complete
    """
    try:
        frappe.logger().info(f"Starting AI report generation for {company} - Job: {job_id_key}")
        
        # Generate the AI report
        ai_report = ai_generate_report(company, year, data)
        
        if ai_report:
            # Cache the result for 30 minutes
            frappe.cache().set_value(f"ai_report_{job_id_key}", ai_report, expires_in_sec=1800)
            frappe.cache().set_value(f"ai_status_{job_id_key}", "ready", expires_in_sec=1800)
            frappe.logger().info(f"AI report completed for {company} - Job: {job_id_key}")
        else:
            frappe.cache().set_value(f"ai_status_{job_id_key}", "error", expires_in_sec=300)
            frappe.cache().set_value(f"ai_error_{job_id_key}", "Failed to generate AI report", expires_in_sec=300)
            
    except Exception as e:
        frappe.log_error(f"AI Background Job Error: {str(e)}", "Material Ledger AI")
        frappe.cache().set_value(f"ai_status_{job_id_key}", "error", expires_in_sec=300)
        frappe.cache().set_value(f"ai_error_{job_id_key}", str(e), expires_in_sec=300)


@frappe.whitelist()
def get_ai_report_status(job_id):
    """
    Check status of AI report generation and return report if ready
    
    Returns:
        dict with status ('loading', 'ready', 'error') and ai_report if ready
    """
    if not job_id:
        return {"status": "error", "message": "No job ID provided"}
    
    # Check cache for status
    status = frappe.cache().get_value(f"ai_status_{job_id}")
    
    if status == "ready":
        ai_report = frappe.cache().get_value(f"ai_report_{job_id}")
        return {
            "status": "ready",
            "ai_report": ai_report
        }
    elif status == "error":
        error_msg = frappe.cache().get_value(f"ai_error_{job_id}") or "Unknown error"
        return {
            "status": "error",
            "message": error_msg
        }
    else:
        # Still loading or not started
        return {
            "status": "loading"
        }


@frappe.whitelist()
def generate_ai_report(company, year, data):
    """
    Generate AI-powered strategic financial report
    Uses the AI service with settings-based configuration
    """
    # Use the new AI service
    return ai_generate_report(company, year, data)


@frappe.whitelist()
def generate_ifrs_report(company, year, period="annual", period_number=None):
    """
    Generate a comprehensive IFRS-compliant professional financial report
    Ready for PDF export following IAS 1 and IAS 7 standards
    """
    from datetime import datetime
    
    # Get financial data
    data = get_financial_analysis(company, year, period, period_number)
    
    if not data:
        frappe.throw(_("Unable to retrieve financial data"))
    
    summary = data.get('summary', {})
    ratios = data.get('ratios', {})
    cash_flow = data.get('cash_flow', {})
    equity_changes = data.get('equity_changes', {})
    risk_flags = data.get('risk_flags', [])
    
    income = summary.get('income', 0)
    expense = summary.get('expense', 0)
    net_profit = summary.get('profit', 0)
    assets = summary.get('assets', 0)
    liabilities = summary.get('liabilities', 0)
    equity = summary.get('equity', 0)
    health_score = summary.get('health_score', 0)
    
    report_date = datetime.now().strftime("%B %d, %Y")
    period_label = data.get('period', str(year))
    
    # Determine financial health status
    if health_score >= 80:
        health_status = "Excellent"
        health_color = "#10b981"
    elif health_score >= 60:
        health_status = "Good"
        health_color = "#3b82f6"
    elif health_score >= 40:
        health_status = "Fair"
        health_color = "#f59e0b"
    else:
        health_status = "Needs Attention"
        health_color = "#ef4444"
    
    # Build professional IFRS report
    report = {
        "metadata": {
            "company": company,
            "period": period_label,
            "report_date": report_date,
            "prepared_by": "Financial Analysis System",
            "standards": "IFRS (IAS 1, IAS 7)"
        },
        
        "executive_summary": {
            "title": "Executive Summary",
            "health_score": health_score,
            "health_status": health_status,
            "overview": f"""
This report presents a comprehensive financial analysis of {company} for the period {period_label}. 
The analysis has been prepared in accordance with International Financial Reporting Standards (IFRS), 
specifically IAS 1 (Presentation of Financial Statements) and IAS 7 (Statement of Cash Flows).

**Key Highlights:**
- Total Revenue: {frappe.format(income, {'fieldtype': 'Currency'})}
- Net {'Profit' if net_profit >= 0 else 'Loss'}: {frappe.format(abs(net_profit), {'fieldtype': 'Currency'})}
- Total Assets: {frappe.format(assets, {'fieldtype': 'Currency'})}
- Return on Equity (ROE): {ratios.get('roe', 0):.2f}%
- Financial Health Score: {health_score}/100 ({health_status})

The company's overall financial position is assessed as **{health_status}** based on comprehensive ratio analysis 
and risk assessment metrics including the Altman Z-Score of {ratios.get('z_score', 0):.2f}.
""",
            "key_metrics": [
                {"label": "Revenue", "value": income, "formatted": frappe.format(income, {'fieldtype': 'Currency'})},
                {"label": "Net Income", "value": net_profit, "formatted": frappe.format(net_profit, {'fieldtype': 'Currency'})},
                {"label": "Total Assets", "value": assets, "formatted": frappe.format(assets, {'fieldtype': 'Currency'})},
                {"label": "ROE", "value": ratios.get('roe', 0), "formatted": f"{ratios.get('roe', 0):.2f}%"},
                {"label": "Health Score", "value": health_score, "formatted": f"{health_score}/100"}
            ]
        },
        
        "financial_statements": {
            "balance_sheet": {
                "title": "Statement of Financial Position (Balance Sheet)",
                "standard": "IAS 1",
                "as_of": period_label,
                "assets": {
                    "total": assets,
                    "formatted": frappe.format(assets, {'fieldtype': 'Currency'}),
                    "current_assets_estimated": assets * 0.4,
                    "non_current_assets_estimated": assets * 0.6
                },
                "liabilities": {
                    "total": liabilities,
                    "formatted": frappe.format(liabilities, {'fieldtype': 'Currency'}),
                    "current_liabilities_estimated": liabilities * 0.3,
                    "non_current_liabilities_estimated": liabilities * 0.7
                },
                "equity": {
                    "total": equity,
                    "formatted": frappe.format(equity, {'fieldtype': 'Currency'}),
                    "components": equity_changes
                },
                "validation": "Assets = Liabilities + Equity" if abs(assets - (liabilities + equity)) < 1 else "Balance check required"
            },
            
            "income_statement": {
                "title": "Statement of Profit or Loss (Income Statement)",
                "standard": "IAS 1",
                "period": period_label,
                "revenue": {
                    "total": income,
                    "formatted": frappe.format(income, {'fieldtype': 'Currency'})
                },
                "expenses": {
                    "total": expense,
                    "formatted": frappe.format(expense, {'fieldtype': 'Currency'})
                },
                "gross_profit": {
                    "amount": income - expense,
                    "formatted": frappe.format(income - expense, {'fieldtype': 'Currency'}),
                    "margin": f"{((income - expense) / income * 100) if income > 0 else 0:.2f}%"
                },
                "net_income": {
                    "amount": net_profit,
                    "formatted": frappe.format(net_profit, {'fieldtype': 'Currency'}),
                    "margin": f"{ratios.get('net_margin', 0):.2f}%"
                }
            },
            
            "cash_flow_statement": {
                "title": "Statement of Cash Flows",
                "standard": "IAS 7",
                "method": cash_flow.get('method', 'indirect'),
                "period": period_label,
                "operating_activities": {
                    "amount": cash_flow.get('operating', 0),
                    "formatted": frappe.format(cash_flow.get('operating', 0), {'fieldtype': 'Currency'}),
                    "quality": "Strong" if cash_flow.get('operating', 0) > net_profit else "Needs Review"
                },
                "investing_activities": {
                    "amount": cash_flow.get('investing', 0),
                    "formatted": frappe.format(cash_flow.get('investing', 0), {'fieldtype': 'Currency'}),
                    "interpretation": "Investment in growth" if cash_flow.get('investing', 0) < 0 else "Asset liquidation"
                },
                "financing_activities": {
                    "amount": cash_flow.get('financing', 0),
                    "formatted": frappe.format(cash_flow.get('financing', 0), {'fieldtype': 'Currency'}),
                    "interpretation": "Capital raising" if cash_flow.get('financing', 0) > 0 else "Debt repayment/Dividends"
                },
                "net_change": {
                    "amount": cash_flow.get('net', 0),
                    "formatted": frappe.format(cash_flow.get('net', 0), {'fieldtype': 'Currency'})
                }
            }
        },
        
        "financial_analysis": {
            "liquidity_ratios": {
                "title": "Liquidity Analysis",
                "description": "Measures the company's ability to meet short-term obligations",
                "ratios": [
                    {
                        "name": "Current Ratio",
                        "value": ratios.get('current_ratio', 0),
                        "formatted": f"{ratios.get('current_ratio', 0):.2f}",
                        "benchmark": "1.5 - 3.0",
                        "status": "Good" if 1.5 <= ratios.get('current_ratio', 0) <= 3.0 else "Review Required",
                        "interpretation": "Adequate liquidity" if ratios.get('current_ratio', 0) >= 1.5 else "Potential liquidity concerns"
                    },
                    {
                        "name": "Quick Ratio",
                        "value": ratios.get('quick_ratio', 0),
                        "formatted": f"{ratios.get('quick_ratio', 0):.2f}",
                        "benchmark": "> 1.0",
                        "status": "Good" if ratios.get('quick_ratio', 0) >= 1.0 else "Review Required",
                        "interpretation": "Strong quick liquidity" if ratios.get('quick_ratio', 0) >= 1.0 else "May struggle with immediate obligations"
                    },
                    {
                        "name": "Working Capital",
                        "value": ratios.get('working_capital', 0),
                        "formatted": frappe.format(ratios.get('working_capital', 0), {'fieldtype': 'Currency'}),
                        "benchmark": "Positive",
                        "status": "Good" if ratios.get('working_capital', 0) > 0 else "Critical",
                        "interpretation": "Positive working capital" if ratios.get('working_capital', 0) > 0 else "Negative working capital - urgent attention required"
                    }
                ]
            },
            
            "profitability_ratios": {
                "title": "Profitability Analysis",
                "description": "Measures the company's ability to generate profits",
                "ratios": [
                    {
                        "name": "Return on Equity (ROE)",
                        "value": ratios.get('roe', 0),
                        "formatted": f"{ratios.get('roe', 0):.2f}%",
                        "benchmark": "> 15%",
                        "status": "Excellent" if ratios.get('roe', 0) > 15 else "Good" if ratios.get('roe', 0) > 10 else "Below Average",
                        "interpretation": "Strong shareholder returns" if ratios.get('roe', 0) > 15 else "Moderate returns"
                    },
                    {
                        "name": "Return on Assets (ROA)",
                        "value": ratios.get('roa', 0),
                        "formatted": f"{ratios.get('roa', 0):.2f}%",
                        "benchmark": "> 5%",
                        "status": "Good" if ratios.get('roa', 0) > 5 else "Review Required",
                        "interpretation": "Efficient asset utilization" if ratios.get('roa', 0) > 5 else "Assets underperforming"
                    },
                    {
                        "name": "Net Profit Margin",
                        "value": ratios.get('net_margin', 0),
                        "formatted": f"{ratios.get('net_margin', 0):.2f}%",
                        "benchmark": "> 10%",
                        "status": "Good" if ratios.get('net_margin', 0) > 10 else "Average" if ratios.get('net_margin', 0) > 5 else "Low",
                        "interpretation": "Healthy profit margins" if ratios.get('net_margin', 0) > 10 else "Margins need improvement"
                    },
                    {
                        "name": "Asset Turnover",
                        "value": ratios.get('asset_turnover', 0),
                        "formatted": f"{ratios.get('asset_turnover', 0):.2f}x",
                        "benchmark": "> 1.0x",
                        "status": "Good" if ratios.get('asset_turnover', 0) > 1.0 else "Review Required",
                        "interpretation": "Efficient revenue generation from assets"
                    }
                ]
            },
            
            "solvency_ratios": {
                "title": "Solvency & Leverage Analysis",
                "description": "Measures the company's long-term financial stability",
                "ratios": [
                    {
                        "name": "Debt Ratio",
                        "value": ratios.get('debt_ratio', 0),
                        "formatted": f"{ratios.get('debt_ratio', 0):.2f}%",
                        "benchmark": "< 60%",
                        "status": "Good" if ratios.get('debt_ratio', 0) < 60 else "High Leverage",
                        "interpretation": "Conservative leverage" if ratios.get('debt_ratio', 0) < 50 else "Elevated debt levels"
                    },
                    {
                        "name": "Equity Multiplier",
                        "value": ratios.get('leverage', 0),
                        "formatted": f"{ratios.get('leverage', 0):.2f}x",
                        "benchmark": "< 2.5x",
                        "status": "Good" if ratios.get('leverage', 0) < 2.5 else "High",
                        "interpretation": "Moderate financial leverage"
                    },
                    {
                        "name": "Altman Z-Score",
                        "value": ratios.get('z_score', 0),
                        "formatted": f"{ratios.get('z_score', 0):.2f}",
                        "benchmark": "> 2.99 (Safe)",
                        "status": "Safe" if ratios.get('z_score', 0) > 2.99 else "Grey Zone" if ratios.get('z_score', 0) > 1.81 else "Distress",
                        "interpretation": "Low bankruptcy risk" if ratios.get('z_score', 0) > 2.99 else "Moderate risk - monitor closely" if ratios.get('z_score', 0) > 1.81 else "High bankruptcy risk - immediate action required"
                    }
                ]
            },
            
            "dupont_analysis": {
                "title": "DuPont Analysis",
                "description": "Decomposes ROE into its fundamental components",
                "components": [
                    {"name": "Net Profit Margin", "value": f"{ratios.get('net_margin', 0):.2f}%", "formula": "Net Income / Revenue"},
                    {"name": "Asset Turnover", "value": f"{ratios.get('asset_turnover', 0):.2f}x", "formula": "Revenue / Total Assets"},
                    {"name": "Equity Multiplier", "value": f"{ratios.get('leverage', 0):.2f}x", "formula": "Total Assets / Equity"},
                    {"name": "DuPont ROE", "value": f"{ratios.get('dupont_roe', 0):.2f}%", "formula": "Margin × Turnover × Leverage"}
                ]
            }
        },
        
        "compliance_note": {
            "title": "IFRS Compliance Statement",
            "content": f"""
**Compliance Declaration**

This financial report has been prepared in accordance with International Financial Reporting Standards (IFRS) 
as issued by the International Accounting Standards Board (IASB).

**Applicable Standards:**
- **IAS 1 - Presentation of Financial Statements**: The financial statements presented herein comply with the 
  requirements of IAS 1, including the presentation of a complete set of financial statements comprising:
  • Statement of Financial Position (Balance Sheet)
  • Statement of Profit or Loss (Income Statement)
  • Statement of Changes in Equity
  • Statement of Cash Flows

- **IAS 7 - Statement of Cash Flows**: The cash flow statement has been prepared using the {'direct' if cash_flow.get('method') == 'direct' else 'indirect'} method, 
  classifying cash flows into operating, investing, and financing activities as required by IAS 7.

**Measurement Basis:**
Financial statements are prepared on the historical cost basis unless otherwise stated.

**Reporting Period:**
This report covers the period: {period_label}

**Report Generated:** {report_date}

*Note: This automated analysis should be reviewed by qualified financial professionals before making 
investment or business decisions.*
"""
        },
        
        "risk_assessment": {
            "title": "Risk Assessment",
            "flags": risk_flags,
            "summary": f"Identified {len(risk_flags)} risk factor(s) requiring attention" if risk_flags else "No critical risks identified"
        },
        
        "recommendations": {
            "title": "Conclusions & Strategic Recommendations",
            "conclusions": [],
            "recommendations": []
        }
    }
    
    # Generate conclusions based on analysis
    conclusions = []
    recommendations = []
    
    # Profitability conclusions
    if net_profit > 0:
        conclusions.append(f"The company achieved a net profit of {frappe.format(net_profit, {'fieldtype': 'Currency'})} demonstrating operational viability.")
    else:
        conclusions.append(f"The company reported a net loss of {frappe.format(abs(net_profit), {'fieldtype': 'Currency'})} requiring immediate attention.")
        recommendations.append("Conduct comprehensive cost analysis to identify and eliminate non-essential expenses.")
    
    # Liquidity conclusions
    if ratios.get('current_ratio', 0) >= 1.5:
        conclusions.append(f"Strong liquidity position with current ratio of {ratios.get('current_ratio', 0):.2f}")
    else:
        conclusions.append(f"Liquidity concerns with current ratio of {ratios.get('current_ratio', 0):.2f}")
        recommendations.append("Improve working capital management through better receivables collection and inventory optimization.")
    
    # Leverage conclusions
    if ratios.get('debt_ratio', 0) < 50:
        conclusions.append("Conservative capital structure provides financial flexibility.")
    else:
        conclusions.append(f"Elevated leverage at {ratios.get('debt_ratio', 0):.2f}% debt ratio may limit future borrowing capacity.")
        recommendations.append("Consider debt restructuring or equity financing to reduce leverage.")
    
    # ROE conclusions
    if ratios.get('roe', 0) > 15:
        conclusions.append(f"Excellent return on equity of {ratios.get('roe', 0):.2f}% indicates strong shareholder value creation.")
    elif ratios.get('roe', 0) > 0:
        recommendations.append("Focus on improving operational efficiency to enhance ROE.")
    
    # Cash flow conclusions
    if cash_flow.get('operating', 0) > net_profit:
        conclusions.append("Operating cash flow exceeds net income, indicating strong cash generation quality.")
    elif cash_flow.get('operating', 0) > 0:
        conclusions.append("Positive operating cash flow supports ongoing operations.")
    else:
        recommendations.append("Urgent focus on improving cash flow from operations through better working capital management.")
    
    # Z-Score conclusions
    z_score = ratios.get('z_score', 0)
    if z_score > 2.99:
        conclusions.append(f"Altman Z-Score of {z_score:.2f} indicates low bankruptcy risk.")
    elif z_score > 1.81:
        recommendations.append("Monitor financial ratios closely - Z-Score indicates grey zone status.")
    else:
        recommendations.append("Implement immediate financial restructuring - Z-Score indicates distress zone.")
    
    # Add general recommendations
    if len(recommendations) < 5:
        general_recs = [
            "Implement regular financial monitoring and reporting dashboards.",
            "Diversify revenue streams to reduce concentration risk.",
            "Establish or strengthen cash reserves for unforeseen circumstances.",
            "Review pricing strategy to improve profit margins.",
            "Invest in operational efficiency and process automation."
        ]
        for rec in general_recs:
            if rec not in recommendations and len(recommendations) < 7:
                recommendations.append(rec)
    
    report["recommendations"]["conclusions"] = conclusions
    report["recommendations"]["recommendations"] = recommendations
    
    return report


@frappe.whitelist()
def export_ifrs_report_to_pdf(company, year, period="annual", period_number=None):
    """
    Export IFRS-compliant report to PDF format
    """
    from frappe.utils.pdf import get_pdf
    
    report = generate_ifrs_report(company, year, period, period_number)
    
    if not report:
        frappe.throw(_("Unable to generate report"))
    
    # Build professional HTML for PDF
    html = build_ifrs_pdf_html(report)
    
    # Generate PDF
    pdf = get_pdf(html, {"orientation": "Portrait", "page-size": "A4"})
    
    return {
        "filename": f"IFRS_Financial_Report_{company}_{report['metadata']['period']}.pdf",
        "content": pdf
    }


def build_ifrs_pdf_html(report):
    """Build professional HTML for IFRS PDF report"""
    
    metadata = report['metadata']
    exec_summary = report['executive_summary']
    statements = report['financial_statements']
    analysis = report['financial_analysis']
    compliance = report['compliance_note']
    recommendations = report['recommendations']
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ margin: 1in; }}
            body {{ 
                font-family: 'Times New Roman', serif; 
                font-size: 11pt; 
                line-height: 1.6;
                color: #333;
            }}
            .header {{ 
                text-align: center; 
                border-bottom: 3px solid #1a365d;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{ 
                color: #1a365d; 
                font-size: 24pt;
                margin: 0;
                font-weight: bold;
            }}
            .header .subtitle {{ 
                color: #4a5568; 
                font-size: 14pt;
                margin-top: 5px;
            }}
            .header .meta {{ 
                font-size: 10pt; 
                color: #718096;
                margin-top: 10px;
            }}
            h2 {{ 
                color: #1a365d; 
                font-size: 16pt;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 8px;
                margin-top: 25px;
            }}
            h3 {{ 
                color: #2d3748; 
                font-size: 13pt;
                margin-top: 20px;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin: 15px 0;
                font-size: 10pt;
            }}
            th {{ 
                background: #1a365d; 
                color: white; 
                padding: 10px;
                text-align: left;
                font-weight: bold;
            }}
            td {{ 
                padding: 8px 10px; 
                border-bottom: 1px solid #e2e8f0;
            }}
            tr:nth-child(even) {{ background: #f7fafc; }}
            .highlight-box {{ 
                background: #ebf8ff; 
                border-left: 4px solid #3182ce;
                padding: 15px;
                margin: 15px 0;
            }}
            .metric-grid {{
                display: table;
                width: 100%;
                margin: 15px 0;
            }}
            .metric-item {{
                display: table-cell;
                width: 20%;
                text-align: center;
                padding: 10px;
                border: 1px solid #e2e8f0;
            }}
            .metric-value {{ 
                font-size: 18pt; 
                font-weight: bold; 
                color: #1a365d;
            }}
            .metric-label {{ 
                font-size: 9pt; 
                color: #718096;
            }}
            .status-good {{ color: #38a169; }}
            .status-warning {{ color: #d69e2e; }}
            .status-critical {{ color: #e53e3e; }}
            .compliance-box {{
                background: #f0fff4;
                border: 1px solid #9ae6b4;
                padding: 15px;
                margin: 20px 0;
            }}
            .recommendation {{
                padding: 8px 0;
                padding-left: 20px;
                position: relative;
            }}
            .recommendation:before {{
                content: "→";
                position: absolute;
                left: 0;
                color: #3182ce;
            }}
            .page-break {{ page-break-before: always; }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                font-size: 9pt;
                color: #718096;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Financial Analysis Report</h1>
            <div class="subtitle">{metadata['company']}</div>
            <div class="meta">
                Period: {metadata['period']} | Prepared: {metadata['report_date']} | Standards: {metadata['standards']}
            </div>
        </div>
        
        <h2>1. Executive Summary</h2>
        <div class="highlight-box">
            <strong>Financial Health Assessment: </strong>
            <span style="font-size: 14pt; font-weight: bold;">{exec_summary['health_status']}</span>
            (Score: {exec_summary['health_score']}/100)
        </div>
        
        <div class="metric-grid">
    """
    
    # Add key metrics
    for metric in exec_summary['key_metrics']:
        html += f"""
            <div class="metric-item">
                <div class="metric-value">{metric['formatted']}</div>
                <div class="metric-label">{metric['label']}</div>
            </div>
        """
    
    html += f"""
        </div>
        
        <h2>2. Financial Statements</h2>
        
        <h3>2.1 Statement of Financial Position (Balance Sheet) - IAS 1</h3>
        <table>
            <tr><th colspan="2">ASSETS</th></tr>
            <tr><td>Total Assets</td><td style="text-align: right;">{statements['balance_sheet']['assets']['formatted']}</td></tr>
            <tr><th colspan="2">LIABILITIES</th></tr>
            <tr><td>Total Liabilities</td><td style="text-align: right;">{statements['balance_sheet']['liabilities']['formatted']}</td></tr>
            <tr><th colspan="2">EQUITY</th></tr>
            <tr><td>Total Equity</td><td style="text-align: right;">{statements['balance_sheet']['equity']['formatted']}</td></tr>
            <tr style="background: #1a365d; color: white;">
                <td><strong>Total Liabilities & Equity</strong></td>
                <td style="text-align: right;"><strong>{statements['balance_sheet']['assets']['formatted']}</strong></td>
            </tr>
        </table>
        
        <h3>2.2 Statement of Profit or Loss (Income Statement) - IAS 1</h3>
        <table>
            <tr><td>Total Revenue</td><td style="text-align: right;">{statements['income_statement']['revenue']['formatted']}</td></tr>
            <tr><td>Total Expenses</td><td style="text-align: right;">({statements['income_statement']['expenses']['formatted']})</td></tr>
            <tr style="background: #1a365d; color: white;">
                <td><strong>Net Income</strong></td>
                <td style="text-align: right;"><strong>{statements['income_statement']['net_income']['formatted']}</strong></td>
            </tr>
            <tr><td>Net Profit Margin</td><td style="text-align: right;">{statements['income_statement']['net_income']['margin']}</td></tr>
        </table>
        
        <h3>2.3 Statement of Cash Flows - IAS 7</h3>
        <table>
            <tr><td>Cash from Operating Activities</td><td style="text-align: right;">{statements['cash_flow_statement']['operating_activities']['formatted']}</td></tr>
            <tr><td>Cash from Investing Activities</td><td style="text-align: right;">{statements['cash_flow_statement']['investing_activities']['formatted']}</td></tr>
            <tr><td>Cash from Financing Activities</td><td style="text-align: right;">{statements['cash_flow_statement']['financing_activities']['formatted']}</td></tr>
            <tr style="background: #1a365d; color: white;">
                <td><strong>Net Change in Cash</strong></td>
                <td style="text-align: right;"><strong>{statements['cash_flow_statement']['net_change']['formatted']}</strong></td>
            </tr>
        </table>
        
        <div class="page-break"></div>
        
        <h2>3. Financial Analysis</h2>
        
        <h3>3.1 Liquidity Ratios</h3>
        <table>
            <tr><th>Ratio</th><th>Value</th><th>Benchmark</th><th>Status</th></tr>
    """
    
    for ratio in analysis['liquidity_ratios']['ratios']:
        status_class = 'status-good' if ratio['status'] == 'Good' else 'status-warning' if ratio['status'] == 'Review Required' else 'status-critical'
        html += f"""
            <tr>
                <td>{ratio['name']}</td>
                <td>{ratio['formatted']}</td>
                <td>{ratio['benchmark']}</td>
                <td class="{status_class}">{ratio['status']}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h3>3.2 Profitability Ratios</h3>
        <table>
            <tr><th>Ratio</th><th>Value</th><th>Benchmark</th><th>Status</th></tr>
    """
    
    for ratio in analysis['profitability_ratios']['ratios']:
        status_class = 'status-good' if 'Good' in ratio['status'] or 'Excellent' in ratio['status'] else 'status-warning'
        html += f"""
            <tr>
                <td>{ratio['name']}</td>
                <td>{ratio['formatted']}</td>
                <td>{ratio['benchmark']}</td>
                <td class="{status_class}">{ratio['status']}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h3>3.3 Solvency & Leverage Ratios</h3>
        <table>
            <tr><th>Ratio</th><th>Value</th><th>Benchmark</th><th>Status</th></tr>
    """
    
    for ratio in analysis['solvency_ratios']['ratios']:
        status_class = 'status-good' if ratio['status'] in ['Good', 'Safe'] else 'status-warning' if ratio['status'] == 'Grey Zone' else 'status-critical'
        html += f"""
            <tr>
                <td>{ratio['name']}</td>
                <td>{ratio['formatted']}</td>
                <td>{ratio['benchmark']}</td>
                <td class="{status_class}">{ratio['status']}</td>
            </tr>
        """
    
    html += f"""
        </table>
        
        <h3>3.4 DuPont Analysis</h3>
        <table>
            <tr><th>Component</th><th>Value</th><th>Formula</th></tr>
    """
    
    for comp in analysis['dupont_analysis']['components']:
        html += f"""
            <tr>
                <td>{comp['name']}</td>
                <td><strong>{comp['value']}</strong></td>
                <td style="font-style: italic;">{comp['formula']}</td>
            </tr>
        """
    
    html += f"""
        </table>
        
        <h2>4. IFRS Compliance Statement</h2>
        <div class="compliance-box">
            {compliance['content'].replace(chr(10), '<br>')}
        </div>
        
        <h2>5. Conclusions & Recommendations</h2>
        
        <h3>Key Conclusions:</h3>
        <ul>
    """
    
    for conclusion in recommendations['conclusions']:
        html += f"<li>{conclusion}</li>"
    
    html += """
        </ul>
        
        <h3>Strategic Recommendations:</h3>
    """
    
    for i, rec in enumerate(recommendations['recommendations'], 1):
        html += f'<div class="recommendation"><strong>{i}.</strong> {rec}</div>'
    
    html += f"""
        
        <div class="footer">
            <p>This report was automatically generated by the Financial Analysis System.</p>
            <p>Report ID: {metadata['company']}-{metadata['period']} | Generated: {metadata['report_date']}</p>
            <p><em>Disclaimer: This analysis is for informational purposes only and should not be considered as professional financial advice.</em></p>
        </div>
    </body>
    </html>
    """
    
    return html


@frappe.whitelist()
def export_analysis_to_pdf(company, year, period, period_number, data):
    """
    Export financial analysis to PDF
    """
    try:
        from frappe.utils.pdf import get_pdf
        import json
        
        if isinstance(data, str):
            data = json.loads(data)
        
        # Build HTML for PDF
        html = f"""
        <html dir="rtl">
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; direction: rtl; margin: 20px; }}
                h1 {{ color: #667eea; text-align: center; }}
                h2 {{ color: #764ba2; margin-top: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                td, th {{ padding: 10px; border: 1px solid #e5e7eb; text-align: right; }}
                th {{ background: #f3f4f6; font-weight: bold; }}
                .summary {{ background: #f0f4ff; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .insight {{ padding: 10px; margin: 8px 0; border-right: 4px solid #667eea; background: #f9fafb; }}
            </style>
        </head>
        <body>
            <h1>📊 تقرير التحليل المالي</h1>
            <div class="summary">
                <p><strong>الشركة:</strong> {company}</p>
                <p><strong>السنة:</strong> {year}</p>
                <p><strong>الفترة:</strong> {period} {period_number or ''}</p>
            </div>
            
            <h2>قائمة الدخل</h2>
            <table>
                <tr><th>البند</th><th>المبلغ</th></tr>
                <tr><td>الإيرادات</td><td>{data.get('summary', {}).get('revenue', 0):,.2f}</td></tr>
                <tr><td>المصروفات</td><td>{data.get('summary', {}).get('total_expenses', 0):,.2f}</td></tr>
                <tr><td>صافي الربح</td><td>{data.get('summary', {}).get('net_profit', 0):,.2f}</td></tr>
            </table>
            
            <h2>الميزانية العمومية</h2>
            <table>
                <tr><th>البند</th><th>المبلغ</th></tr>
                <tr><td>الأصول</td><td>{data.get('summary', {}).get('assets', 0):,.2f}</td></tr>
                <tr><td>الالتزامات</td><td>{data.get('summary', {}).get('liabilities', 0):,.2f}</td></tr>
                <tr><td>حقوق الملكية</td><td>{data.get('summary', {}).get('equity', 0):,.2f}</td></tr>
            </table>
            
            <h2>تحليل AI</h2>
            <div class="summary">
                {data.get('ai_report', 'لا يوجد تحليل AI متاح')}
            </div>
        </body>
        </html>
        """
        
        pdf = get_pdf(html)
        return {"pdf": pdf.encode('latin-1').hex() if isinstance(pdf, str) else pdf.hex()}
        
    except Exception as e:
        frappe.log_error(f"PDF Export Error: {str(e)}", "Financial Analysis")
        frappe.throw(_("Failed to export PDF"))


@frappe.whitelist()
def compare_periods(company, year, period1, period2):
    """
    Compare financial metrics between two periods
    """
    try:
        # Convert month/quarter names to numbers
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        p1 = month_map.get(period1.lower(), 1)
        p2 = month_map.get(period2.lower(), 1)
        
        data1 = get_financial_analysis(company, year, "monthly", p1)
        data2 = get_financial_analysis(company, year, "monthly", p2)
        
        revenue1 = data1['summary']['revenue']
        revenue2 = data2['summary']['revenue']
        profit1 = data1['summary']['net_profit']
        profit2 = data2['summary']['net_profit']
        
        revenue_change = ((revenue2 - revenue1) / revenue1 * 100) if revenue1 else 0
        profit_change = ((profit2 - profit1) / profit1 * 100) if profit1 else 0
        
        return {
            "revenue1": revenue1,
            "revenue2": revenue2,
            "revenue_change": revenue_change,
            "profit1": profit1,
            "profit2": profit2,
            "profit_change": profit_change
        }
        
    except Exception as e:
        frappe.log_error(f"Comparison Error: {str(e)}", "Financial Analysis")
        frappe.throw(_("Failed to compare periods"))


@frappe.whitelist()
def export_ledger_to_excel(company, from_date, to_date, **filters):
    """
    Export General Ledger to Excel format
    """
    entries = get_ledger_entries(company, from_date, to_date, **filters)
    
    if not entries:
        frappe.throw(_("No data to export"))
    
    return entries


@frappe.whitelist()
def get_financial_forecast(company, years=3):
    """
    Generate financial forecasts using trend analysis and machine learning-like projections
    """
    from datetime import datetime
    
    if not company:
        frappe.throw(_("Company is required"))
    
    current_year = datetime.now().year
    years_to_forecast = cint(years) or 3
    
    # Get historical data (last 5 years)
    historical_data = []
    for y in range(current_year - 5, current_year):
        data = get_financial_analysis(company, y, "annual", sections=["dashboard"])
        if data and data.get("summary"):
            historical_data.append({
                "year": y,
                "income": flt(data["summary"].get("income", 0)),
                "expense": flt(data["summary"].get("expense", 0)),
                "profit": flt(data["summary"].get("profit", 0)),
                "assets": flt(data["summary"].get("assets", 0)),
                "liabilities": flt(data["summary"].get("liabilities", 0))
            })
    
    if len(historical_data) < 2:
        return {
            "error": _("Insufficient historical data for forecasting"),
            "min_years_required": 2,
            "years_available": len(historical_data)
        }
    
    # Calculate growth rates using weighted moving average
    def calculate_growth_rate(values):
        if len(values) < 2:
            return 0
        weights = [i + 1 for i in range(len(values) - 1)]  # More recent = higher weight
        total_weight = sum(weights)
        weighted_growth = 0
        for i in range(len(values) - 1):
            if values[i] > 0:
                growth = (values[i + 1] - values[i]) / values[i]
                weighted_growth += growth * weights[i]
        return weighted_growth / total_weight if total_weight > 0 else 0
    
    incomes = [d["income"] for d in historical_data]
    expenses = [d["expense"] for d in historical_data]
    profits = [d["profit"] for d in historical_data]
    assets_hist = [d["assets"] for d in historical_data]
    
    income_growth = calculate_growth_rate(incomes)
    expense_growth = calculate_growth_rate(expenses)
    asset_growth = calculate_growth_rate(assets_hist)
    
    # Cap growth rates to realistic bounds (-30% to +50%)
    income_growth = max(min(income_growth, 0.5), -0.3)
    expense_growth = max(min(expense_growth, 0.5), -0.3)
    asset_growth = max(min(asset_growth, 0.5), -0.3)
    
    # Generate forecasts
    forecasts = []
    last_income = incomes[-1] if incomes else 0
    last_expense = expenses[-1] if expenses else 0
    last_assets = assets_hist[-1] if assets_hist else 0
    
    for i in range(1, years_to_forecast + 1):
        forecast_year = current_year + i
        
        # Apply growth with diminishing effect for longer horizons
        decay_factor = 0.9 ** (i - 1)  # 90% decay per year
        
        projected_income = last_income * ((1 + income_growth * decay_factor) ** i)
        projected_expense = last_expense * ((1 + expense_growth * decay_factor) ** i)
        projected_profit = projected_income - projected_expense
        projected_assets = last_assets * ((1 + asset_growth * decay_factor) ** i)
        
        # Calculate confidence interval (widens with time)
        confidence_range = 0.05 * i  # 5% per year
        
        forecasts.append({
            "year": forecast_year,
            "income": {
                "projected": flt(projected_income, 2),
                "low": flt(projected_income * (1 - confidence_range), 2),
                "high": flt(projected_income * (1 + confidence_range), 2)
            },
            "expense": {
                "projected": flt(projected_expense, 2),
                "low": flt(projected_expense * (1 - confidence_range), 2),
                "high": flt(projected_expense * (1 + confidence_range), 2)
            },
            "profit": {
                "projected": flt(projected_profit, 2),
                "low": flt((projected_income * (1 - confidence_range)) - (projected_expense * (1 + confidence_range)), 2),
                "high": flt((projected_income * (1 + confidence_range)) - (projected_expense * (1 - confidence_range)), 2)
            },
            "assets": {
                "projected": flt(projected_assets, 2),
                "low": flt(projected_assets * (1 - confidence_range), 2),
                "high": flt(projected_assets * (1 + confidence_range), 2)
            },
            "confidence_level": f"{int((1 - confidence_range) * 100)}%"
        })
    
    return {
        "historical": historical_data,
        "forecasts": forecasts,
        "growth_rates": {
            "income": flt(income_growth * 100, 2),
            "expense": flt(expense_growth * 100, 2),
            "assets": flt(asset_growth * 100, 2)
        },
        "methodology": "Weighted Moving Average with Decay Factor",
        "generated_at": frappe.utils.now()
    }


@frappe.whitelist()
def schedule_financial_report(company, report_type, frequency, email_to):
    """
    Schedule automated financial reports
    report_type: 'income', 'balance', 'full', 'summary'
    frequency: 'daily', 'weekly', 'monthly', 'quarterly'
    """
    import json
    
    if not company or not report_type or not frequency or not email_to:
        frappe.throw(_("All parameters are required"))
    
    # Validate frequency
    valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
    if frequency not in valid_frequencies:
        frappe.throw(_("Invalid frequency. Choose from: daily, weekly, monthly, quarterly"))
    
    # Create scheduled job entry
    schedule_name = f"financial_report_{company}_{report_type}_{frequency}"
    
    # Check if schedule already exists
    existing = frappe.db.exists("Scheduled Job Type", schedule_name)
    if existing:
        # Update existing schedule
        frappe.db.set_value("Scheduled Job Type", schedule_name, {
            "stopped": 0,
            "last_execution": None
        })
        return {
            "status": "updated",
            "schedule_name": schedule_name,
            "message": _("Report schedule updated successfully")
        }
    
    # Map frequency to cron expression
    cron_map = {
        "daily": "0 8 * * *",      # 8 AM daily
        "weekly": "0 8 * * 1",     # 8 AM Monday
        "monthly": "0 8 1 * *",    # 8 AM 1st of month
        "quarterly": "0 8 1 1,4,7,10 *"  # 8 AM 1st of Jan, Apr, Jul, Oct
    }
    
    # Store schedule info in site config or custom doctype
    schedule_data = {
        "company": company,
        "report_type": report_type,
        "frequency": frequency,
        "email_to": email_to,
        "cron": cron_map[frequency],
        "created_by": frappe.session.user,
        "created_at": frappe.utils.now()
    }
    
    # Save to site config (for simplicity) or use a custom doctype
    schedules = frappe.conf.get("financial_report_schedules", [])
    schedules.append(schedule_data)
    frappe.conf.update({"financial_report_schedules": schedules})
    
    return {
        "status": "created",
        "schedule_name": schedule_name,
        "schedule": schedule_data,
        "message": _("Report scheduled successfully")
    }


@frappe.whitelist()
def get_scheduled_reports(company=None):
    """Get list of scheduled financial reports"""
    schedules = frappe.conf.get("financial_report_schedules", [])
    if company:
        schedules = [s for s in schedules if s.get("company") == company]
    return schedules


@frappe.whitelist()
def get_competitor_benchmarks(company, industry=None):
    """
    Get industry benchmarks for comparison
    Uses standard ratios for different industries
    """
    # Industry benchmark data (simplified - in production, fetch from external API)
    benchmarks = {
        "retail": {
            "net_margin": {"low": 2, "avg": 4, "high": 7},
            "current_ratio": {"low": 1.0, "avg": 1.5, "high": 2.5},
            "debt_ratio": {"low": 30, "avg": 50, "high": 70},
            "roe": {"low": 8, "avg": 15, "high": 25},
            "inventory_turnover": {"low": 4, "avg": 8, "high": 15}
        },
        "manufacturing": {
            "net_margin": {"low": 3, "avg": 6, "high": 12},
            "current_ratio": {"low": 1.2, "avg": 2.0, "high": 3.0},
            "debt_ratio": {"low": 35, "avg": 55, "high": 75},
            "roe": {"low": 10, "avg": 18, "high": 30},
            "asset_turnover": {"low": 0.5, "avg": 1.0, "high": 1.8}
        },
        "services": {
            "net_margin": {"low": 5, "avg": 12, "high": 25},
            "current_ratio": {"low": 1.0, "avg": 1.8, "high": 3.5},
            "debt_ratio": {"low": 20, "avg": 40, "high": 60},
            "roe": {"low": 12, "avg": 22, "high": 40},
            "receivables_turnover": {"low": 6, "avg": 10, "high": 18}
        },
        "technology": {
            "net_margin": {"low": 8, "avg": 18, "high": 35},
            "current_ratio": {"low": 1.5, "avg": 2.5, "high": 5.0},
            "debt_ratio": {"low": 10, "avg": 30, "high": 50},
            "roe": {"low": 15, "avg": 25, "high": 45},
            "rd_ratio": {"low": 10, "avg": 18, "high": 30}
        },
        "default": {
            "net_margin": {"low": 3, "avg": 8, "high": 15},
            "current_ratio": {"low": 1.0, "avg": 1.8, "high": 3.0},
            "debt_ratio": {"low": 25, "avg": 45, "high": 65},
            "roe": {"low": 10, "avg": 18, "high": 30}
        }
    }
    
    # Get company's current ratios
    current_year = frappe.utils.now_datetime().year
    company_data = get_financial_analysis(company, current_year, "annual", sections=["ratios"])
    company_ratios = company_data.get("ratios", {})
    
    # Determine industry or use default
    industry_key = (industry or "default").lower()
    if industry_key not in benchmarks:
        industry_key = "default"
    
    industry_benchmarks = benchmarks[industry_key]
    
    # Compare company ratios against benchmarks
    comparison = {}
    for ratio_name, benchmark in industry_benchmarks.items():
        company_value = company_ratios.get(ratio_name, 0)
        
        if company_value < benchmark["low"]:
            performance = "below_average"
            rating = "⚠️"
        elif company_value < benchmark["avg"]:
            performance = "average"
            rating = "➖"
        elif company_value < benchmark["high"]:
            performance = "good"
            rating = "✅"
        else:
            performance = "excellent"
            rating = "🌟"
        
        comparison[ratio_name] = {
            "company_value": company_value,
            "industry_low": benchmark["low"],
            "industry_avg": benchmark["avg"],
            "industry_high": benchmark["high"],
            "performance": performance,
            "rating": rating,
            "percentile": calculate_percentile(company_value, benchmark)
        }
    
    return {
        "company": company,
        "industry": industry_key,
        "benchmarks": industry_benchmarks,
        "comparison": comparison,
        "overall_score": calculate_overall_benchmark_score(comparison)
    }


def calculate_percentile(value, benchmark):
    """Calculate which percentile the value falls into"""
    if value <= benchmark["low"]:
        return flt((value / benchmark["low"]) * 25, 0) if benchmark["low"] > 0 else 0
    elif value <= benchmark["avg"]:
        return flt(25 + ((value - benchmark["low"]) / (benchmark["avg"] - benchmark["low"])) * 25, 0)
    elif value <= benchmark["high"]:
        return flt(50 + ((value - benchmark["avg"]) / (benchmark["high"] - benchmark["avg"])) * 25, 0)
    else:
        return min(flt(75 + ((value - benchmark["high"]) / benchmark["high"]) * 25, 0), 100)


def calculate_overall_benchmark_score(comparison):
    """Calculate overall benchmark score (0-100)"""
    if not comparison:
        return 0
    
    total_percentile = sum(c["percentile"] for c in comparison.values())
    return flt(total_percentile / len(comparison), 0)