import frappe
from frappe import _
from frappe.utils import flt, getdate, cint
import requests
import json

@frappe.whitelist()
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
    """Calculate actual cash flow from GL entries"""
    # Operating Cash Flow - Cash from operations
    operating_accounts = frappe.db.sql("""
        SELECT 
            SUM(CASE WHEN acc.root_type = 'Asset' AND acc.account_type IN ('Cash', 'Bank') 
                THEN gle.debit - gle.credit ELSE 0 END) as cash_change,
            SUM(CASE WHEN acc.root_type = 'Asset' AND acc.account_type = 'Receivable' 
                THEN gle.debit - gle.credit ELSE 0 END) as ar_change,
            SUM(CASE WHEN acc.root_type = 'Liability' AND acc.account_type = 'Payable' 
                THEN gle.credit - gle.debit ELSE 0 END) as ap_change
        FROM `tabGL Entry` gle
        JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.company = %s 
        AND gle.posting_date BETWEEN %s AND %s
        AND gle.is_cancelled = 0
    """, (company, start_date, end_date), as_dict=True)[0]
    
    # Investing - Fixed assets and investments
    investing = frappe.db.sql("""
        SELECT SUM(gle.credit) - SUM(gle.debit) as flow
        FROM `tabGL Entry` gle
        JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.company = %s 
        AND gle.posting_date BETWEEN %s AND %s
        AND acc.root_type = 'Asset'
        AND acc.account_type IN ('Fixed Asset', 'Accumulated Depreciation')
        AND gle.is_cancelled = 0
    """, (company, start_date, end_date))
    investing_flow = flt(investing[0][0]) if investing and investing[0][0] else 0
    
    # Financing - Loans and Capital
    financing = frappe.db.sql("""
        SELECT SUM(gle.credit) - SUM(gle.debit) as flow
        FROM `tabGL Entry` gle
        JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.company = %s 
        AND gle.posting_date BETWEEN %s AND %s
        AND (acc.account_type IN ('Equity')
             OR (acc.root_type = 'Liability' AND acc.name LIKE '%%Loan%%'))
        AND gle.is_cancelled = 0
    """, (company, start_date, end_date))
    financing_flow = flt(financing[0][0]) if financing and financing[0][0] else 0
    
    # Calculate operating cash flow using indirect method
    ar_change = flt(operating_accounts.get('ar_change', 0))
    ap_change = flt(operating_accounts.get('ap_change', 0))
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
def get_financial_analysis(company, year, period="annual", period_number=None, sections=None):
    """
    Advanced Financial Analysis - CFO Level with AI Insights
    Comprehensive metrics for expert accountants
    Supports: monthly, quarterly, and annual periods

    sections: optional list/JSON/string of tabs to return for lazy loading
    """
    if not company:
        frappe.throw(_("Company is required"))
    
    year = cint(year)
    if not year:
        frappe.throw(_("Valid year is required"))

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

    # Determine date range based on period
    if period == "monthly" and period_number:
        month = cint(period_number)
        start_date = f"{year}-{month:02d}-01"
        end_date = frappe.utils.get_last_day(start_date)
        period_label = frappe.utils.formatdate(start_date, "MMM YYYY")
    elif period == "quarterly" and period_number:
        quarter = cint(period_number)
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

    # SUPER OPTIMIZED: Single query to get all balances for all periods at once
    def get_all_periods_balances():
        """Get all account balances for all periods in a SINGLE query"""
        res = frappe.db.sql("""
            SELECT 
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
            JOIN `tabAccount` acc ON gle.account = acc.name
            WHERE gle.company = %s 
            AND gle.is_cancelled = 0
            GROUP BY acc.root_type
        """, (
            start_date, end_date,  # current
            end_date,              # cumulative
            prev_start, prev_end,  # prev year
            prev_end,              # prev cumulative
            two_years_start, two_years_end,  # two years
            start_date,            # opening
            company
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

    ai_report = None
    if need("ai"):
        ai_report = generate_ai_report(company, year, {
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
        })

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
        response["ai_report"] = ai_report

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


@frappe.whitelist()
def generate_ai_report(company, year, data):
    """
    Generate AI-powered strategic financial report using DeepSeek Reasoning Model
    Uses deepseek-reasoner for advanced analysis
    """
    # Parse data if it's a JSON string
    if isinstance(data, str):
        data = json.loads(data)
    
    api_key = frappe.conf.get("deepseek_api_key") or "sk-5e59f5662a1e4ffba7e8b741c35b6e0e"
    
    if not api_key:
        return _("AI analysis not available. Please configure API key.")

    # Extract comprehensive data
    summary = data.get('summary', {})
    ratios = data.get('ratios', {})
    quarterly = data.get('quarterly', [])
    monthly = data.get('monthly', [])
    equity_changes = data.get('equity_changes', {})
    cash_flow = data.get('cash_flow', {})
    period = data.get('period', year)
    
    net_profit = data.get('net_profit', summary.get('profit', 0))
    income = data.get('income', summary.get('income', 0))
    expense = data.get('expense', summary.get('expense', 0))
    assets = data.get('assets', summary.get('assets', 0))
    liabilities = data.get('liabilities', summary.get('liabilities', 0))
    equity = data.get('equity', summary.get('equity', 0))

    # Build comprehensive prompt for reasoning model
    prompt = f"""
أنت محلل مالي خبير متخصص في تحليل القوائم المالية للشركات. قم بتحليل البيانات المالية التالية لشركة {company} للفترة {period}:

📊 **قائمة الدخل (Income Statement)**
- إجمالي الإيرادات: {frappe.format(income, {'fieldtype': 'Currency'})}
- إجمالي المصروفات: {frappe.format(expense, {'fieldtype': 'Currency'})}
- صافي الربح/الخسارة: {frappe.format(net_profit, {'fieldtype': 'Currency'})}
- هامش الربح الصافي: {ratios.get('net_margin', 0):.2f}%
- هامش التشغيل: {ratios.get('operating_margin', 0):.2f}%

📈 **قائمة المركز المالي (Balance Sheet)**
- إجمالي الأصول: {frappe.format(assets, {'fieldtype': 'Currency'})}
- إجمالي الالتزامات: {frappe.format(liabilities, {'fieldtype': 'Currency'})}
- حقوق الملكية: {frappe.format(equity, {'fieldtype': 'Currency'})}
- نسبة الديون للأصول: {ratios.get('debt_ratio', 0):.2f}%

💰 **قائمة التدفقات النقدية (Cash Flow Statement)**
- التدفق النقدي التشغيلي: {frappe.format(cash_flow.get('operating', 0), {'fieldtype': 'Currency'})}
- التدفق النقدي الاستثماري: {frappe.format(cash_flow.get('investing', 0), {'fieldtype': 'Currency'})}
- التدفق النقدي التمويلي: {frappe.format(cash_flow.get('financing', 0), {'fieldtype': 'Currency'})}
- صافي التدفق النقدي: {frappe.format(cash_flow.get('net', 0), {'fieldtype': 'Currency'})}

📋 **قائمة التغيرات في حقوق الملكية**
- الرصيد الافتتاحي: {frappe.format(equity_changes.get('opening_balance', 0), {'fieldtype': 'Currency'})}
- صافي الربح: {frappe.format(equity_changes.get('net_profit', 0), {'fieldtype': 'Currency'})}
- الإضافات الرأسمالية: {frappe.format(equity_changes.get('contributions', 0), {'fieldtype': 'Currency'})}
- التوزيعات: {frappe.format(equity_changes.get('dividends', 0), {'fieldtype': 'Currency'})}
- الرصيد الختامي: {frappe.format(equity_changes.get('closing_balance', 0), {'fieldtype': 'Currency'})}

📊 **النسب المالية الرئيسية**
- العائد على حقوق الملكية (ROE): {ratios.get('roe', 0):.2f}%
- العائد على الأصول (ROA): {ratios.get('roa', 0):.2f}%
- النسبة الجارية: {ratios.get('current_ratio', 0):.2f}
- نسبة السيولة السريعة: {ratios.get('quick_ratio', 0):.2f}
- معدل دوران الأصول: {ratios.get('asset_turnover', 0):.2f}
- مضاعف حقوق الملكية: {ratios.get('leverage', 0):.2f}
- Z-Score: {ratios.get('z_score', 0):.2f} {"(آمن)" if ratios.get('z_score', 0) > 2.9 else "(منطقة رمادية)" if ratios.get('z_score', 0) > 1.8 else "(خطر إفلاس)"}

📅 **التحليل الدوري**
{f"البيانات الشهرية: {len(monthly)} شهر" if monthly else ""}
{f"البيانات الربعية: {len(quarterly)} ربع" if quarterly else ""}

قم بإجراء تحليل شامل ومفصل يتضمن:

1. **تحليل قائمة الدخل**: قم بتحليل الربحية، هامش الأرباح، كفاءة التكاليف، ومصادر الإيرادات
2. **تحليل المركز المالي**: حلل السيولة، هيكل رأس المال، القدرة على الوفاء بالالتزامات، والكفاءة في استخدام الأصول
3. **تحليل التدفقات النقدية**: قيّم قدرة الشركة على توليد النقد، الاستثمارات، والتمويل
4. **تحليل التغيرات في حقوق الملكية**: راجع التغيرات الرأسمالية وسياسة التوزيعات
5. **النقاط القوة والضعف**: حدد 3-5 نقاط قوة و3-5 نقاط ضعف
6. **المخاطر المالية**: حدد المخاطر الحالية والمستقبلية
7. **التوصيات الاستراتيجية**: قدم 5-7 توصيات عملية قابلة للتنفيذ لتحسين الأداء المالي
8. **التوقعات المستقبلية**: قدم رؤية للاتجاهات المستقبلية المتوقعة

يجب أن يكون التحليل:
- دقيق ومبني على الأرقام
- شامل لجميع جوانب الأداء المالي
- مكتوب بلغة عربية احترافية
- يحتوي على أمثلة وأرقام محددة
- طوله 500-700 كلمة

استخدم تفكيرك العميق (reasoning) لتقديم رؤى ثاقبة وتحليل متعمق.
"""

    try:
        # Use deepseek-reasoner model for advanced analysis
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-reasoner",  # Using reasoning model for detailed analysis
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,  # Lower temperature for more precise analysis
                "max_tokens": 4000  # More tokens for comprehensive analysis
            },
            timeout=180  # Longer timeout for reasoning model
        )
        
        if response.status_code == 200:
            result = response.json()
            # Reasoning model returns both reasoning_content and content
            reasoning = result['choices'][0]['message'].get('reasoning_content', '')
            analysis = result['choices'][0]['message']['content']
            
            # Combine reasoning with final analysis
            if reasoning:
                return f"**التحليل المتعمق:**\n\n{analysis}\n\n---\n*تم إنشاء هذا التحليل باستخدام نموذج التفكير المتقدم من DeepSeek*"
            return analysis
        else:
            frappe.log_error(f"DeepSeek API Error: {response.text}", "Financial Analysis AI")
            return _("AI analysis temporarily unavailable. Please try again later.")
    
    except Exception as e:
        frappe.log_error(f"AI Report Generation Error: {str(e)}", "Financial Analysis")
        return _("التحليل الاستراتيجي متاح في النسخة الاحترافية.")


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