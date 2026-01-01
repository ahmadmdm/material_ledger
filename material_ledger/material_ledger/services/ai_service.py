# Copyright (c) 2025, Ahmad
# For license information, please see license.txt

"""
AI Service Module for Material Ledger
Handles all AI-related operations including report generation
"""

import frappe
from frappe import _
from frappe.utils import flt
import requests
import json


class AIService:
    """Service class for AI operations"""
    
    def __init__(self):
        self.settings = self._get_settings()
        self.api_key = None
        self.provider = None
        self.model = None
        self._initialize()
    
    def _get_settings(self):
        """Get settings from DocType"""
        try:
            from material_ledger.material_ledger.doctype.material_ledger_settings.material_ledger_settings import MaterialLedgerSettings
            return MaterialLedgerSettings.get_settings()
        except Exception:
            return {
                "enable_ai_analysis": True,
                "ai_provider": "DeepSeek",
                "ai_model": "deepseek-reasoner"
            }
    
    def _initialize(self):
        """Initialize AI service with API key"""
        if not self.settings.get("enable_ai_analysis"):
            return
        
        try:
            from material_ledger.material_ledger.doctype.material_ledger_settings.material_ledger_settings import MaterialLedgerSettings
            self.api_key = MaterialLedgerSettings.get_api_key()
        except Exception:
            # Fallback to site config (but NOT hardcoded!)
            self.api_key = frappe.conf.get("deepseek_api_key")
        
        self.provider = self.settings.get("ai_provider", "DeepSeek")
        self.model = self.settings.get("ai_model", "deepseek-reasoner")
    
    def is_available(self):
        """Check if AI service is available"""
        return bool(self.api_key and self.settings.get("enable_ai_analysis"))
    
    def generate_financial_report(self, company, year, data):
        """
        Generate AI-powered strategic financial report
        
        Args:
            company: Company name
            year: Fiscal year
            data: Financial data dictionary
            
        Returns:
            str: AI-generated analysis report
        """
        if not self.is_available():
            return _("AI analysis not available. Please configure API key in Material Ledger Settings.")
        
        # Parse data if string
        if isinstance(data, str):
            data = json.loads(data)
        
        prompt = self._build_financial_prompt(company, year, data)
        
        try:
            if self.provider == "DeepSeek":
                return self._call_deepseek(prompt)
            elif self.provider == "OpenAI":
                return self._call_openai(prompt)
            else:
                return _("AI provider not configured properly.")
        
        except Exception as e:
            frappe.log_error(f"AI Report Generation Error: {str(e)}", "Material Ledger AI")
            return _("AI analysis temporarily unavailable. Error: {0}").format(str(e))
    
    def _call_deepseek(self, prompt):
        """Call DeepSeek API"""
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 4000
            },
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            reasoning = result['choices'][0]['message'].get('reasoning_content', '')
            analysis = result['choices'][0]['message']['content']
            
            if reasoning:
                return f"**التحليل المتعمق:**\n\n{analysis}\n\n---\n*تم إنشاء هذا التحليل باستخدام نموذج التفكير المتقدم من DeepSeek*"
            return analysis
        else:
            frappe.log_error(f"DeepSeek API Error: {response.text}", "Material Ledger AI")
            return _("AI analysis temporarily unavailable. Please try again later.")
    
    def _call_openai(self, prompt):
        """Call OpenAI API"""
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 4000
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            frappe.log_error(f"OpenAI API Error: {response.text}", "Material Ledger AI")
            return _("AI analysis temporarily unavailable. Please try again later.")
    
    def _build_financial_prompt(self, company, year, data):
        """Build comprehensive prompt for financial analysis"""
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
        return prompt


# Singleton instance
_ai_service = None

def get_ai_service():
    """Get or create AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


@frappe.whitelist()
def generate_ai_report(company, year, data):
    """
    API endpoint for generating AI report
    Uses the new settings-based configuration
    """
    service = get_ai_service()
    return service.generate_financial_report(company, year, data)
