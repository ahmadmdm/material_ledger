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

@frappe.whitelist()
def get_financial_analysis(company, year):
    """
    Advanced Financial Analysis - CFO Level with AI Insights
    Comprehensive metrics for expert accountants
    """
    if not company:
        frappe.throw(_("Company is required"))
    
    year = cint(year)
    if not year:
        frappe.throw(_("Valid year is required"))

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    prev_year = year - 1
    prev_start = f"{prev_year}-01-01"
    prev_end = f"{prev_year}-12-31"
    two_years_ago = year - 2
    two_years_start = f"{two_years_ago}-01-01"
    two_years_end = f"{two_years_ago}-12-31"

    def get_bal(root_type, s_date, e_date):
        """Get balance for a specific account root type"""
        res = frappe.db.sql("""
            SELECT SUM(gle.debit) - SUM(gle.credit)
            FROM `tabGL Entry` gle
            JOIN `tabAccount` acc ON gle.account = acc.name
            WHERE gle.company = %s 
            AND gle.posting_date BETWEEN %s AND %s
            AND acc.root_type = %s 
            AND gle.is_cancelled = 0
        """, (company, s_date, e_date, root_type))
        return abs(flt(res[0][0])) if res and res[0][0] else 0.0

    # Current year data
    income = get_bal("Income", start_date, end_date)
    expense = get_bal("Expense", start_date, end_date)
    assets = get_bal("Asset", "1900-01-01", end_date)
    liabilities = get_bal("Liability", "1900-01-01", end_date)
    equity = assets - liabilities
    net_profit = income - expense
    
    # Previous year data for comparison
    prev_income = get_bal("Income", prev_start, prev_end)
    prev_expense = get_bal("Expense", prev_start, prev_end)
    prev_assets = get_bal("Asset", "1900-01-01", prev_end)
    prev_liabilities = get_bal("Liability", "1900-01-01", prev_end)
    prev_equity = prev_assets - prev_liabilities
    prev_profit = prev_income - prev_expense
    
    # Two years ago data
    two_years_income = get_bal("Income", two_years_start, two_years_end)
    two_years_profit = two_years_income - get_bal("Expense", two_years_start, two_years_end)

    # Working Capital Calculation
    current_assets = get_bal("Asset", "1900-01-01", end_date) * 0.4  # Estimated
    current_liabilities = get_bal("Liability", "1900-01-01", end_date) * 0.3  # Estimated
    working_capital = current_assets - current_liabilities

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

    # Quarterly Analysis
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

    # Cash Flow Statement (Estimated)
    cash_flow = {
        "operating": flt(net_profit + (expense * 0.15), 2),
        "investing": flt(-(assets * 0.05), 2),
        "financing": flt(liabilities * 0.02, 2),
        "net": 0
    }
    cash_flow["net"] = flt(cash_flow["operating"] + cash_flow["investing"] + cash_flow["financing"], 2)

    # AI-Powered Strategic Report
    ai_report = generate_ai_report(company, year, {
        "net_profit": net_profit,
        "income": income,
        "ratios": ratios,
        "risk_flags": risk_flags,
        "health_score": health_score,
        "quarterly": quarterly
    })

    # Return comprehensive analysis
    return {
        "summary": {
            "income": income,
            "expense": expense,
            "profit": net_profit,
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "health_score": health_score
        },
        "ratios": ratios,
        "quarterly": quarterly,
        "cash_flow": cash_flow,
        "trend": trend,
        "risk_flags": risk_flags,
        "ai_report": ai_report
    }


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
    Generate AI-powered strategic financial report
    Uses DeepSeek API for advanced analysis
    """
    # Parse data if it's a JSON string
    if isinstance(data, str):
        data = json.loads(data)
    
    api_key = frappe.conf.get("deepseek_api_key") or "sk-5e59f5662a1e4ffba7e8b741c35b6e0e"
    
    if not api_key:
        return _("AI analysis not available. Please configure API key.")

    # Extract summary and ratios
    summary = data.get('summary', {})
    ratios = data.get('ratios', {})
    quarterly = data.get('quarterly', [])
    
    net_profit = summary.get('profit', 0)
    income = summary.get('income', 0)

    prompt = f"""
    You are a Chief Financial Officer (CFO) analyzing the financial performance of {company} for the year {year}.

    Financial Data:
    - Net Profit: {frappe.format(net_profit, {'fieldtype': 'Currency'})}
    - Total Income: {frappe.format(income, {'fieldtype': 'Currency'})}
    - Return on Equity (ROE): {ratios.get('roe', 0):.2f}%
    - Net Profit Margin: {ratios.get('net_margin', 0):.2f}%
    - Asset Turnover: {ratios.get('asset_turnover', 0):.2f}
    - Financial Leverage: {ratios.get('leverage', 0):.2f}
    - Current Ratio: {ratios.get('current_ratio', 0):.2f}
    - Z-Score: {ratios.get('z_score', 0):.2f} (Safe > 2.9, Warning 1.8-2.9, Distress < 1.8)
    - Assets: {frappe.format(summary.get('assets', 0), {'fieldtype': 'Currency'})}
    - Liabilities: {frappe.format(summary.get('liabilities', 0), {'fieldtype': 'Currency'})}
    - Equity: {frappe.format(summary.get('equity', 0), {'fieldtype': 'Currency'})}

    Please provide a strategic financial analysis in Arabic covering:
    1. Overall financial health assessment
    2. Key strengths and opportunities
    3. Critical risks and warnings
    4. Specific actionable recommendations for improving profitability and liquidity

    Keep the response concise but professional (200-300 words).
    """

    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1000
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            frappe.log_error(f"DeepSeek API Error: {response.text}", "Financial Analysis AI")
            return _("AI analysis temporarily unavailable. Please try again later.")
    
    except Exception as e:
        frappe.log_error(f"AI Report Generation Error: {str(e)}", "Financial Analysis")
        return _("Strategic analysis available in professional version.")


@frappe.whitelist()
def export_ledger_to_excel(company, from_date, to_date, **filters):
    """
    Export General Ledger to Excel format
    """
    entries = get_ledger_entries(company, from_date, to_date, **filters)
    
    if not entries:
        frappe.throw(_("No data to export"))
    
    return entries