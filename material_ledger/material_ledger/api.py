import frappe
from frappe import _
from frappe.utils import flt, getdate
import requests
import json

@frappe.whitelist()
def get_ledger_entries(company, from_date, to_date, account=None, party_type=None, party=None, cost_center=None, project=None):
    if not company:
        frappe.throw(_("الشركة مطلوبة"))

    filters = {
        "company": company,
        "posting_date": ["between", [from_date, to_date]],
        "is_cancelled": 0
    }

    if account: filters["account"] = account
    if party_type and party:
        filters["party_type"] = party_type
        filters["party"] = party
    if cost_center: filters["cost_center"] = cost_center
    if project: filters["project"] = project

    opening_balance = 0.0
    if account:
        opening_balance = get_opening_balance(company, account, from_date, party_type, party, cost_center, project)

    gl_entries = frappe.get_all(
        "GL Entry",
        fields=["name", "posting_date", "account", "party_type", "party", "debit", "credit", "voucher_type", "voucher_no", "remarks", "cost_center", "project", "against", "is_opening", "transaction_date", "due_date"],
        filters=filters,
        order_by="posting_date asc, creation asc",
        limit_page_length=None
    )

    data = []
    balance = opening_balance

    if account:
        data.append({
            "posting_date": from_date,
            "account": account,
            "remarks": _("الرصيد الافتتاحي"),
            "debit": 0, "credit": 0,
            "balance": balance,
            "is_opening": True
        })

    for entry in gl_entries:
        balance += flt(entry.debit) - flt(entry.credit)
        entry["balance"] = balance
        data.append(entry)

    return data

def get_opening_balance(company, account, from_date, party_type=None, party=None, cost_center=None, project=None):
    conditions = []
    values = {"company": company, "account": account, "from_date": from_date}
    if party_type and party:
        conditions.append("AND party_type = %(party_type)s AND party = %(party)s")
        values["party_type"] = party_type
        values["party"] = party
    if cost_center: conditions.append("AND cost_center = %(cost_center)s")
    if project: conditions.append("AND project = %(project)s")

    query = """
        SELECT SUM(debit) - SUM(credit)
        FROM `tabGL Entry`
        WHERE company = %(company)s AND account = %(account)s
        AND posting_date < %(from_date)s AND is_cancelled = 0
        {conditions}
    """.format(conditions=" ".join(conditions))
    result = frappe.db.sql(query, values)
    return flt(result[0][0]) if result else 0.0

@frappe.whitelist()
def get_financial_analysis(company, year):
    """
    تحليل مالي استراتيجي متقدم (CFO Level)
    """
    if not company:
        frappe.throw(_("الشركة مطلوبة"))

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    prev_year = int(year) - 1
    prev_start = f"{prev_year}-01-01"
    prev_end = f"{prev_year}-12-31"

    def get_bal(root_type, s_date, e_date):
        res = frappe.db.sql("""
            SELECT SUM(gle.debit) - SUM(gle.credit)
            FROM `tabGL Entry` gle
            JOIN `tabAccount` acc ON gle.account = acc.name
            WHERE gle.company = %s AND gle.posting_date BETWEEN %s AND %s
            AND acc.root_type = %s AND gle.is_cancelled = 0
        """, (company, s_date, e_date, root_type))
        return abs(flt(res[0][0])) if res else 0.0

    # 1. بيانات العام الحالي
    income = get_bal("Income", start_date, end_date)
    expense = get_bal("Expense", start_date, end_date)
    assets = get_bal("Asset", "1900-01-01", end_date)
    liabilities = get_bal("Liability", "1900-01-01", end_date)
    equity = assets - liabilities
    net_profit = income - expense
    working_capital = assets * 0.4 - liabilities * 0.3 # تقديري للسيولة المتداولة

    # 2. بيانات العام السابق للمقارنة (YoY Growth)
    prev_income = get_bal("Income", prev_start, prev_end)
    income_growth = ((income - prev_income) / prev_income * 100) if prev_income else 0

    # 3. حساب Altman Z-Score (مؤشر التنبؤ بالتعثر)
    # Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E
    # A: Working Capital / Total Assets
    # B: Retained Earnings / Total Assets (Equity as proxy)
    # C: EBIT / Total Assets (Profit as proxy)
    # D: Market Value of Equity / Total Liabilities
    # E: Sales / Total Assets
    z_score = 0
    if assets > 0 and liabilities > 0:
        a = (working_capital / assets) * 1.2
        b = (equity / assets) * 1.4
        c = (net_profit / assets) * 3.3
        d = (equity / liabilities) * 0.6
        e = (income / assets) * 1.0
        z_score = flt(a + b + c + d + e, 2)

    # 4. تحليل التدفق النقدي ونموذج ديبونت
    ratios = {
        "roe": flt((net_profit / equity * 100), 2) if equity else 0,
        "net_margin": flt((net_profit / income * 100), 2) if income else 0,
        "asset_turnover": flt(income / assets, 2) if assets else 0,
        "leverage": flt(assets / equity, 2) if equity else 0,
        "current_ratio": flt(working_capital / (liabilities * 0.3), 2) if liabilities else 0,
        "z_score": z_score,
        "income_growth": flt(income_growth, 2)
    }

    # التحليل الربع سنوي
    quarterly = frappe.db.sql("""
        SELECT QUARTER(posting_date) as q,
        SUM(CASE WHEN acc.root_type = 'Income' THEN (credit - debit) ELSE 0 END) as inc,
        SUM(CASE WHEN acc.root_type = 'Expense' THEN (debit - credit) ELSE 0 END) as exp
        FROM `tabGL Entry` gle JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.company = %s AND posting_date BETWEEN %s AND %s AND is_cancelled = 0
        GROUP BY q ORDER BY q
    """, (company, start_date, end_date), as_dict=True)

    # ذكاء اصطناعي CFO Level
    api_key = "sk-5e59f5662a1e4ffba7e8b741c35b6e0e"
    ai_report = ""
    if api_key:
        prompt = f"""
        Analyze CFO Dashboard for {company} ({year}):
        - Net Profit: {net_profit} (Growth: {income_growth}%)
        - Altman Z-Score: {z_score} (Safe > 2.9, Distress < 1.2)
        - DuPont Breakdown: Margin {ratios['net_margin']}%, Turnover {ratios['asset_turnover']}, Leverage {ratios['leverage']}
        - Quarterly Trend: {json.dumps(quarterly, default=str)}
        Provide a strategic Arabic summary. Identify 2 specific financial risks and 2 high-impact opportunities.
        """
        try:
            r = requests.post("https://api.deepseek.com/chat/completions", 
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3},
                timeout=120)
            if r.status_code == 200: ai_report = r.json()['choices'][0]['message']['content']
        except: ai_report = "التحليل متاح في نسخة الطباعة..."

    return {
        "summary": {"income": income, "expense": expense, "profit": net_profit, "assets": assets, "liabilities": liabilities, "equity": equity},
        "ratios": ratios,
        "quarterly": quarterly,
        "ai_report": ai_report
    }