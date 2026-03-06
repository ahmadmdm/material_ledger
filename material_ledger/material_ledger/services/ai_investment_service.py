# Copyright (c) 2026, Ahmad
# For license information, please see license.txt

"""
AI Investment Analysis Service
Analyzes investment opportunities, ROI, and financial scenarios
"""

import frappe
from frappe import _
from frappe.utils import flt, now, add_months, getdate
import json
import statistics
import math
from collections import defaultdict


class AIInvestmentService:
    """Service for AI-powered investment analysis"""
    
    def __init__(self):
        self.risk_free_rate = 0.03  # 3% risk-free rate
        self.market_rate = 0.08     # 8% market return
        
    def get_investment_data(self, company, filters):
        """
        Get investment-related data for analysis
        
        Args:
            company: Company name
            filters: Dictionary with analysis parameters
            
        Returns:
            dict: Investment data for analysis
        """
        from_date = filters.get('from_date', '2023-01-01')
        to_date = filters.get('to_date', now().split(' ')[0])
        
        # Get financial data for investment analysis
        investment_data = {
            'financial_statements': self._get_financial_statements(company, from_date, to_date),
            'cash_flows': self._get_cash_flow_data(company, from_date, to_date),
            'assets': self._get_asset_data(company, from_date, to_date),
            'projects': self._get_project_data(company, from_date, to_date),
            'market_data': self._get_market_indicators(company),
            'industry_benchmarks': self._get_industry_benchmarks(company)
        }
        
        return investment_data
    
    def _get_financial_statements(self, company, from_date, to_date):
        """Get key financial statement data"""
        # Revenue and profitability data
        financial_data = frappe.db.sql("""
            SELECT 
                YEAR(posting_date) as year,
                MONTH(posting_date) as month,
                SUM(CASE 
                    WHEN account IN (
                        SELECT name FROM `tabAccount` 
                        WHERE root_type = 'Income' AND company = %(company)s
                    ) THEN credit - debit 
                    ELSE 0 
                END) as revenue,
                SUM(CASE 
                    WHEN account IN (
                        SELECT name FROM `tabAccount` 
                        WHERE root_type = 'Expense' AND company = %(company)s
                    ) THEN debit - credit 
                    ELSE 0 
                END) as expenses,
                SUM(CASE 
                    WHEN account IN (
                        SELECT name FROM `tabAccount` 
                        WHERE root_type = 'Asset' AND company = %(company)s
                    ) THEN debit - credit 
                    ELSE 0 
                END) as assets,
                SUM(CASE 
                    WHEN account IN (
                        SELECT name FROM `tabAccount` 
                        WHERE root_type = 'Liability' AND company = %(company)s
                    ) THEN credit - debit 
                    ELSE 0 
                END) as liabilities
            FROM `tabGL Entry`
            WHERE 
                company = %(company)s 
                AND posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND is_cancelled = 0
            GROUP BY YEAR(posting_date), MONTH(posting_date)
            ORDER BY year, month
        """, {
            'company': company,
            'from_date': from_date,
            'to_date': to_date
        }, as_dict=True)
        
        return financial_data
    
    def _get_cash_flow_data(self, company, from_date, to_date):
        """Get cash flow analysis data"""
        cash_flow_data = frappe.db.sql("""
            SELECT 
                posting_date,
                SUM(CASE 
                    WHEN account IN (
                        SELECT name FROM `tabAccount` 
                        WHERE account_type IN ('Cash', 'Bank') AND company = %(company)s
                    ) THEN debit - credit 
                    ELSE 0 
                END) as net_cash_flow,
                voucher_type,
                project
            FROM `tabGL Entry`
            WHERE 
                company = %(company)s 
                AND posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND is_cancelled = 0
                AND account IN (
                    SELECT name FROM `tabAccount` 
                    WHERE account_type IN ('Cash', 'Bank') AND company = %(company)s
                )
            GROUP BY posting_date, voucher_type, project
            ORDER BY posting_date
        """, {
            'company': company,
            'from_date': from_date,
            'to_date': to_date
        }, as_dict=True)
        
        return cash_flow_data
    
    def _get_asset_data(self, company, from_date, to_date):
        """Get asset performance data"""
        # Fixed assets and their performance
        asset_data = frappe.db.sql("""
            SELECT 
                a.name,
                a.asset_name,
                a.item_code,
                a.purchase_date,
                a.gross_purchase_amount,
                a.value_after_depreciation,
                a.total_number_of_depreciations,
                a.frequency_of_depreciation,
                SUM(ads.depreciation_amount) as total_depreciation
            FROM `tabAsset` a
            LEFT JOIN `tabDepreciation Schedule` ads ON a.name = ads.parent
            WHERE a.company = %(company)s
            AND a.purchase_date BETWEEN %(from_date)s AND %(to_date)s
            GROUP BY a.name
            ORDER BY a.purchase_date
        """, {
            'company': company,
            'from_date': from_date,
            'to_date': to_date
        }, as_dict=True)
        
        return asset_data
    
    def _get_project_data(self, company, from_date, to_date):
        """Get project investment data"""
        project_data = frappe.db.sql("""
            SELECT 
                p.name,
                p.project_name,
                p.status,
                p.project_type,
                p.estimated_costing,
                p.total_expense_claim,
                p.total_purchase_cost,
                p.total_sales_amount,
                p.total_billable_amount,
                p.expected_start_date,
                p.expected_end_date,
                p.percent_complete,
                (p.total_sales_amount - p.total_purchase_cost - p.total_expense_claim) as project_profit
            FROM `tabProject` p
            WHERE p.company = %(company)s
            AND p.expected_start_date >= %(from_date)s
            ORDER BY p.expected_start_date DESC
        """, {
            'company': company,
            'from_date': from_date
        }, as_dict=True)
        
        return project_data
    
    def _get_market_indicators(self, company):
        """Get market and economic indicators"""
        # This would typically connect to external data sources
        # For now, we'll use estimated indicators
        return {
            'inflation_rate': 0.06,      # 6% inflation
            'interest_rate': 0.05,       # 5% interest rate
            'gdp_growth': 0.04,          # 4% GDP growth
            'industry_growth': 0.07,     # 7% industry growth
            'currency': 'SAR',
            'economic_outlook': 'positive'
        }
    
    def _get_industry_benchmarks(self, company):
        """Get industry benchmark ratios"""
        # This would typically come from industry databases
        # For now, we'll use standard benchmarks
        return {
            'avg_roe': 0.12,             # 12% ROE
            'avg_roa': 0.08,             # 8% ROA
            'avg_profit_margin': 0.10,   # 10% profit margin
            'avg_current_ratio': 2.0,     # Current ratio
            'avg_debt_ratio': 0.40,      # 40% debt ratio
            'avg_asset_turnover': 1.5    # Asset turnover
        }
    
    def analyze_investments(self, investment_data):
        """
        Perform comprehensive investment analysis
        
        Args:
            investment_data: Dictionary of investment-related data
            
        Returns:
            dict: Comprehensive investment analysis results
        """
        results = {
            'roi_analysis': self._analyze_roi(investment_data),
            'npv_analysis': self._calculate_npv(investment_data),
            'risk_analysis': self._analyze_investment_risk(investment_data),
            'scenario_analysis': self._scenario_analysis(investment_data),
            'portfolio_analysis': self._portfolio_analysis(investment_data),
            'recommendations': self._generate_investment_recommendations(investment_data),
            'ai_insights': self._ai_investment_insights(investment_data)
        }
        
        return results
    
    def _analyze_roi(self, data):
        """Analyze Return on Investment for various assets/projects"""
        roi_analysis = []
        
        # Project ROI Analysis
        projects = data.get('projects', [])
        for project in projects:
            if project.get('total_purchase_cost', 0) > 0:
                investment = project['total_purchase_cost'] + project.get('total_expense_claim', 0)
                returns = project.get('total_sales_amount', 0)
                roi = ((returns - investment) / investment * 100) if investment > 0 else 0
                
                roi_analysis.append({
                    'type': 'project',
                    'name': project['project_name'],
                    'investment': investment,
                    'returns': returns,
                    'roi_percentage': roi,
                    'status': project.get('status', 'Unknown'),
                    'completion': project.get('percent_complete', 0),
                    'evaluation': self._evaluate_roi(roi)
                })
        
        # Asset ROI Analysis
        assets = data.get('assets', [])
        for asset in assets:
            purchase_amount = asset.get('gross_purchase_amount', 0)
            current_value = purchase_amount - asset.get('total_depreciation', 0)
            
            if purchase_amount > 0:
                # Calculate ROI based on current value vs purchase
                asset_roi = ((current_value - purchase_amount) / purchase_amount * 100)
                
                roi_analysis.append({
                    'type': 'asset',
                    'name': asset['asset_name'],
                    'investment': purchase_amount,
                    'current_value': current_value,
                    'roi_percentage': asset_roi,
                    'depreciation': asset.get('total_depreciation', 0),
                    'evaluation': self._evaluate_roi(asset_roi)
                })
        
        # Overall ROI Summary
        if roi_analysis:
            avg_roi = statistics.mean([r['roi_percentage'] for r in roi_analysis])
            best_investment = max(roi_analysis, key=lambda x: x['roi_percentage'])
            worst_investment = min(roi_analysis, key=lambda x: x['roi_percentage'])
        else:
            avg_roi = 0
            best_investment = None
            worst_investment = None
        
        return {
            'individual_investments': roi_analysis,
            'summary': {
                'average_roi': avg_roi,
                'best_investment': best_investment,
                'worst_investment': worst_investment,
                'total_investments': len(roi_analysis)
            }
        }
    
    def _evaluate_roi(self, roi):
        """Evaluate ROI performance"""
        if roi > 15:
            return "ممتاز"
        elif roi > 10:
            return "جيد جداً"
        elif roi > 5:
            return "جيد"
        elif roi > 0:
            return "مقبول"
        else:
            return "ضعيف"
    
    def _calculate_npv(self, data):
        """Calculate Net Present Value for investments"""
        npv_analysis = []
        discount_rate = 0.10  # 10% discount rate
        
        # Analyze cash flows for NPV calculation
        cash_flows = data.get('cash_flows', [])
        projects = data.get('projects', [])
        
        # Group cash flows by project
        project_cash_flows = defaultdict(list)
        for cf in cash_flows:
            if cf.get('project'):
                project_cash_flows[cf['project']].append(cf)
        
        for project in projects:
            project_name = project['name']
            if project_name in project_cash_flows:
                # Calculate NPV for project
                cf_data = project_cash_flows[project_name]
                
                # Sort cash flows by date
                sorted_cf = sorted(cf_data, key=lambda x: x['posting_date'])
                
                # Calculate NPV
                npv = 0
                initial_investment = -abs(project.get('total_purchase_cost', 0))
                
                # Add initial investment
                npv += initial_investment
                
                # Add discounted future cash flows
                for i, cf in enumerate(sorted_cf):
                    period = i + 1
                    discounted_cf = cf['net_cash_flow'] / ((1 + discount_rate) ** period)
                    npv += discounted_cf
                
                # Calculate IRR (simplified)
                irr = self._calculate_simple_irr(initial_investment, [cf['net_cash_flow'] for cf in sorted_cf])
                
                npv_analysis.append({
                    'project': project_name,
                    'initial_investment': initial_investment,
                    'npv': npv,
                    'irr': irr,
                    'payback_period': self._calculate_payback_period(initial_investment, sorted_cf),
                    'evaluation': self._evaluate_npv(npv, irr)
                })
        
        return npv_analysis
    
    def _calculate_simple_irr(self, initial_investment, cash_flows):
        """Calculate approximate IRR using simple method"""
        if not cash_flows or initial_investment >= 0:
            return 0
        
        total_cash_flow = sum(cash_flows)
        if total_cash_flow <= 0:
            return -100
        
        # Simple IRR approximation
        avg_annual_return = total_cash_flow / len(cash_flows)
        irr = (avg_annual_return / abs(initial_investment)) * 100
        
        return min(irr, 100)  # Cap at 100%
    
    def _calculate_payback_period(self, initial_investment, cash_flows):
        """Calculate payback period"""
        if not cash_flows or initial_investment >= 0:
            return float('inf')
        
        cumulative_cash_flow = 0
        for i, cf in enumerate(cash_flows):
            cumulative_cash_flow += cf['net_cash_flow']
            if cumulative_cash_flow >= abs(initial_investment):
                return i + 1
        
        return float('inf')
    
    def _evaluate_npv(self, npv, irr):
        """Evaluate NPV and IRR performance"""
        if npv > 50000 and irr > 15:
            return "استثمار ممتاز"
        elif npv > 0 and irr > 10:
            return "استثمار جيد"
        elif npv > 0:
            return "استثمار مقبول"
        else:
            return "استثمار غير مربح"
    
    def _analyze_investment_risk(self, data):
        """Analyze investment risks"""
        risk_factors = []
        
        # Market risk analysis
        market_data = data.get('market_data', {})
        if market_data.get('economic_outlook') == 'negative':
            risk_factors.append({
                'type': 'market_risk',
                'level': 'high',
                'description': 'توقعات اقتصادية سلبية',
                'impact': 'عالي'
            })
        
        # Liquidity risk
        financial_data = data.get('financial_statements', [])
        if financial_data:
            latest_data = financial_data[-1]
            current_ratio = latest_data.get('assets', 0) / max(latest_data.get('liabilities', 1), 1)
            
            if current_ratio < 1.5:
                risk_factors.append({
                    'type': 'liquidity_risk',
                    'level': 'medium' if current_ratio > 1.0 else 'high',
                    'description': f'نسبة سيولة منخفضة: {current_ratio:.2f}',
                    'impact': 'متوسط للعالي'
                })
        
        # Concentration risk (project portfolio)
        projects = data.get('projects', [])
        if projects:
            total_investment = sum(p.get('total_purchase_cost', 0) for p in projects)
            max_project_investment = max(p.get('total_purchase_cost', 0) for p in projects) if projects else 0
            
            concentration_ratio = (max_project_investment / total_investment * 100) if total_investment > 0 else 0
            
            if concentration_ratio > 30:
                risk_factors.append({
                    'type': 'concentration_risk',
                    'level': 'medium' if concentration_ratio < 50 else 'high',
                    'description': f'تركز عالي في استثمار واحد: {concentration_ratio:.1f}%',
                    'impact': 'متوسط للعالي'
                })
        
        # Overall risk assessment
        high_risks = len([r for r in risk_factors if r['level'] == 'high'])
        medium_risks = len([r for r in risk_factors if r['level'] == 'medium'])
        
        if high_risks > 2:
            overall_risk = 'عالي'
        elif high_risks > 0 or medium_risks > 2:
            overall_risk = 'متوسط'
        else:
            overall_risk = 'منخفض'
        
        return {
            'risk_factors': risk_factors,
            'overall_risk': overall_risk,
            'risk_score': high_risks * 3 + medium_risks * 1,
            'recommendations': self._generate_risk_recommendations(risk_factors)
        }
    
    def _generate_risk_recommendations(self, risk_factors):
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        for risk in risk_factors:
            if risk['type'] == 'liquidity_risk':
                recommendations.append("💧 تحسين السيولة: زيادة النقد المتاح أو تقليل الالتزامات قصيرة المدى")
            elif risk['type'] == 'concentration_risk':
                recommendations.append("📊 تنويع المحفظة: توزيع الاستثمارات على قطاعات ومشاريع متنوعة")
            elif risk['type'] == 'market_risk':
                recommendations.append("🛡️ حماية السوق: استخدام أدوات التحوط أو تأجيل الاستثمارات الكبيرة")
        
        if not recommendations:
            recommendations.append("✅ إدارة المخاطر جيدة - حافظ على المراقبة المنتظمة")
        
        return recommendations
    
    def _scenario_analysis(self, data):
        """Perform scenario analysis (best, worst, most likely)"""
        scenarios = {}
        
        # Get base financial data
        financial_data = data.get('financial_statements', [])
        if not financial_data:
            return scenarios
        
        # Calculate base metrics
        recent_data = financial_data[-3:] if len(financial_data) >= 3 else financial_data
        avg_revenue = statistics.mean([d['revenue'] for d in recent_data])
        avg_expenses = statistics.mean([d['expenses'] for d in recent_data])
        avg_profit = avg_revenue - avg_expenses
        
        # Best case scenario (15% growth, 5% cost reduction)
        scenarios['best_case'] = {
            'description': 'السيناريو الأفضل',
            'assumptions': ['نمو إيرادات 15%', 'خفض تكاليف 5%', 'ظروف اقتصادية مثالية'],
            'projected_revenue': avg_revenue * 1.15,
            'projected_expenses': avg_expenses * 0.95,
            'projected_profit': (avg_revenue * 1.15) - (avg_expenses * 0.95),
            'profit_improvement': (((avg_revenue * 1.15) - (avg_expenses * 0.95)) - avg_profit) / avg_profit * 100 if avg_profit != 0 else 0,
            'probability': 20
        }
        
        # Most likely scenario (5% growth, 3% cost increase)
        scenarios['most_likely'] = {
            'description': 'السيناريو الأكثر احتمالاً',
            'assumptions': ['نمو إيرادات 5%', 'زيادة تكاليف 3%', 'ظروف اقتصادية عادية'],
            'projected_revenue': avg_revenue * 1.05,
            'projected_expenses': avg_expenses * 1.03,
            'projected_profit': (avg_revenue * 1.05) - (avg_expenses * 1.03),
            'profit_improvement': (((avg_revenue * 1.05) - (avg_expenses * 1.03)) - avg_profit) / avg_profit * 100 if avg_profit != 0 else 0,
            'probability': 60
        }
        
        # Worst case scenario (10% revenue decline, 8% cost increase)
        scenarios['worst_case'] = {
            'description': 'السيناريو الأسوأ',
            'assumptions': ['انخفاض إيرادات 10%', 'زيادة تكاليف 8%', 'ظروف اقتصادية صعبة'],
            'projected_revenue': avg_revenue * 0.90,
            'projected_expenses': avg_expenses * 1.08,
            'projected_profit': (avg_revenue * 0.90) - (avg_expenses * 1.08),
            'profit_improvement': (((avg_revenue * 0.90) - (avg_expenses * 1.08)) - avg_profit) / avg_profit * 100 if avg_profit != 0 else 0,
            'probability': 20
        }
        
        # Calculate expected value
        expected_profit = (
            scenarios['best_case']['projected_profit'] * 0.20 +
            scenarios['most_likely']['projected_profit'] * 0.60 +
            scenarios['worst_case']['projected_profit'] * 0.20
        )
        
        scenarios['expected_value'] = {
            'description': 'القيمة المتوقعة',
            'projected_profit': expected_profit,
            'profit_improvement': (expected_profit - avg_profit) / avg_profit * 100 if avg_profit != 0 else 0
        }
        
        return scenarios
    
    def _portfolio_analysis(self, data):
        """Analyze investment portfolio performance"""
        projects = data.get('projects', [])
        assets = data.get('assets', [])
        
        if not projects and not assets:
            return {'status': 'no_portfolio_data'}
        
        # Portfolio composition
        total_project_investment = sum(p.get('total_purchase_cost', 0) for p in projects)
        total_asset_investment = sum(a.get('gross_purchase_amount', 0) for a in assets)
        total_investment = total_project_investment + total_asset_investment
        
        portfolio_composition = {
            'projects': {
                'amount': total_project_investment,
                'percentage': (total_project_investment / total_investment * 100) if total_investment > 0 else 0
            },
            'assets': {
                'amount': total_asset_investment,
                'percentage': (total_asset_investment / total_investment * 100) if total_investment > 0 else 0
            }
        }
        
        # Portfolio performance metrics
        completed_projects = [p for p in projects if p.get('status') == 'Completed']
        project_returns = []
        
        for project in completed_projects:
            investment = project.get('total_purchase_cost', 0) + project.get('total_expense_claim', 0)
            returns = project.get('total_sales_amount', 0)
            if investment > 0:
                roi = (returns - investment) / investment
                project_returns.append(roi)
        
        # Calculate portfolio metrics
        if project_returns:
            portfolio_return = statistics.mean(project_returns)
            portfolio_volatility = statistics.stdev(project_returns) if len(project_returns) > 1 else 0
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        else:
            portfolio_return = 0
            portfolio_volatility = 0
            sharpe_ratio = 0
        
        return {
            'composition': portfolio_composition,
            'total_investment': total_investment,
            'performance': {
                'average_return': portfolio_return * 100,
                'volatility': portfolio_volatility * 100,
                'sharpe_ratio': sharpe_ratio,
                'number_of_investments': len(projects) + len(assets)
            },
            'diversification_score': self._calculate_diversification_score(projects, assets)
        }
    
    def _calculate_diversification_score(self, projects, assets):
        """Calculate portfolio diversification score"""
        # Count different types/sectors
        project_types = set(p.get('project_type', 'Other') for p in projects)
        asset_types = set(a.get('item_code', 'Other') for a in assets)
        
        total_investments = len(projects) + len(assets)
        unique_types = len(project_types) + len(asset_types)
        
        if total_investments == 0:
            return 0
        
        # Score from 0-100 based on diversification
        diversification_ratio = unique_types / total_investments
        score = min(100, diversification_ratio * 100 * 2)  # Multiply by 2 for scoring
        
        if score > 80:
            grade = "ممتاز"
        elif score > 60:
            grade = "جيد"
        elif score > 40:
            grade = "متوسط"
        else:
            grade = "ضعيف"
        
        return {
            'score': score,
            'grade': grade,
            'unique_investments': unique_types,
            'total_investments': total_investments
        }
    
    def _ai_investment_insights(self, data):
        """Generate AI-powered investment insights"""
        try:
            from material_ledger.material_ledger.services.ai_service import get_ai_service
            
            ai_service = get_ai_service()
            if not ai_service.is_available():
                return self._statistical_investment_insights(data)
            
            # Build AI analysis prompt
            prompt = self._build_investment_prompt(data)
            
            # Get AI insights
            ai_response = ai_service._call_deepseek(prompt) if hasattr(ai_service, '_call_deepseek') else None
            
            if ai_response:
                return self._parse_ai_investment_insights(ai_response)
            else:
                return self._statistical_investment_insights(data)
                
        except Exception as e:
            frappe.log_error(f"AI Investment Insights Error: {str(e)}", "AI Investment Service")
            return self._statistical_investment_insights(data)
    
    def _build_investment_prompt(self, data):
        """Build prompt for AI investment analysis"""
        # Summarize key data
        projects = data.get('projects', [])
        financial_data = data.get('financial_statements', [])
        market_data = data.get('market_data', {})
        
        if financial_data:
            latest_financial = financial_data[-1]
            revenue = latest_financial.get('revenue', 0)
            profit = latest_financial.get('revenue', 0) - latest_financial.get('expenses', 0)
        else:
            revenue = 0
            profit = 0
        
        total_project_investment = sum(p.get('total_purchase_cost', 0) for p in projects)
        completed_projects = len([p for p in projects if p.get('status') == 'Completed'])
        
        prompt = f"""
كmحلل استثماري خبير متخصص في تقييم الفرص الاستثمارية، قم بتحليل البيانات التالية:

💼 **الوضع المالي الحالي:**
- الإيرادات الحالية: {revenue:,.0f}
- الأرباح الحالية: {profit:,.0f}
- إجمالي الاستثمارات في المشاريع: {total_project_investment:,.0f}
- عدد المشاريع المكتملة: {completed_projects} من أصل {len(projects)}

📊 **المؤشرات الاقتصادية:**
- معدل النمو الاقتصادي: {market_data.get('gdp_growth', 0)*100:.1f}%
- معدل التضخم: {market_data.get('inflation_rate', 0)*100:.1f}%
- معدل الفائدة: {market_data.get('interest_rate', 0)*100:.1f}%
- التوقعات الاقتصادية: {market_data.get('economic_outlook', 'غير محدد')}

🎯 **المطلوب تحليله:**

1. **تقييم الأداء الاستثماري الحالي**
2. **تحديد الفرص الاستثمارية المتاحة**
3. **تحليل المخاطر والعوائد المتوقعة**
4. **استراتيجيات التحسين والنمو**
5. **توصيات الاستثمار قصيرة وطويلة المدى**

قدم تحليلاً شاملاً يتضمن:

```json
{
  "current_performance": {
    "score": "تقييم من 1-10",
    "strengths": ["نقاط القوة"],
    "weaknesses": ["نقاط الضعف"]
  },
  "opportunities": [
    {
      "type": "نوع الفرصة",
      "description": "وصف الفرصة",
      "expected_return": "العائد المتوقع",
      "risk_level": "منخفض/متوسط/عالي",
      "time_horizon": "قصير/متوسط/طويل المدى"
    }
  ],
  "recommendations": [
    {
      "action": "الإجراء المطلوب",
      "priority": "عالي/متوسط/منخفض",
      "expected_impact": "التأثير المتوقع",
      "timeline": "الإطار الزمني"
    }
  ],
  "strategic_insights": {
    "market_outlook": "نظرة السوق",
    "competitive_position": "الموقع التنافسي",
    "growth_strategy": "استراتيجية النمو"
  }
}
```

استخدم خبرتك في التحليل المالي لتقديم رؤى عملية قابلة للتنفيذ.
"""
        return prompt
    
    def _parse_ai_investment_insights(self, ai_response):
        """Parse AI investment insights response"""
        try:
            import re
            json_match = re.search(r'```json\n(.*?)\n```', ai_response, re.DOTALL)
            if json_match:
                insights = json.loads(json_match.group(1))
                return {
                    'source': 'ai_analysis',
                    'insights': insights,
                    'raw_response': ai_response
                }
        except Exception as e:
            frappe.log_error(f"AI Investment Parsing Error: {str(e)}", "AI Investment Service")
        
        # Fallback to basic parsing
        return {
            'source': 'ai_analysis',
            'insights': {
                'summary': 'تحليل AI متاح - راجع النص الكامل',
                'raw_text': ai_response
            }
        }
    
    def _statistical_investment_insights(self, data):
        """Statistical fallback investment insights"""
        insights = []
        
        projects = data.get('projects', [])
        financial_data = data.get('financial_statements', [])
        
        # Analyze project success rate
        if projects:
            completed_projects = [p for p in projects if p.get('status') == 'Completed']
            success_rate = len(completed_projects) / len(projects) * 100
            
            if success_rate > 80:
                insights.append("✅ معدل نجاح مشاريع ممتاز - استمر في نفس النهج")
            elif success_rate > 60:
                insights.append("👍 معدل نجاح مشاريع جيد - يمكن التحسين")
            else:
                insights.append("⚠️ معدل نجاح مشاريع منخفض - راجع عمليات إدارة المشاريع")
        
        # Analyze financial trends
        if len(financial_data) >= 3:
            recent_profits = []
            for fd in financial_data[-3:]:
                profit = fd.get('revenue', 0) - fd.get('expenses', 0)
                recent_profits.append(profit)
            
            if all(recent_profits[i] < recent_profits[i+1] for i in range(len(recent_profits)-1)):
                insights.append("📈 اتجاه أرباح متنامي - فرصة للاستثمار التوسعي")
            elif all(recent_profits[i] > recent_profits[i+1] for i in range(len(recent_profits)-1)):
                insights.append("📉 اتجاه أرباح متناقص - ركز على تحسين الكفاءة")
        
        return {
            'source': 'statistical_analysis',
            'insights': insights
        }
    
    def _generate_investment_recommendations(self, data):
        """Generate specific investment recommendations"""
        recommendations = []
        
        # Analyze current portfolio
        projects = data.get('projects', [])
        financial_data = data.get('financial_statements', [])
        market_data = data.get('market_data', {})
        
        # Cash position recommendation
        if financial_data:
            latest_data = financial_data[-1]
            current_ratio = latest_data.get('assets', 0) / max(latest_data.get('liabilities', 1), 1)
            
            if current_ratio > 3:
                recommendations.append({
                    'type': 'liquidity_optimization',
                    'priority': 'medium',
                    'action': 'استثمار الفائض النقدي',
                    'description': 'لديك سيولة عالية - استثمر الفائض في فرص مدرة للدخل',
                    'expected_impact': 'زيادة العوائد بنسبة 5-8%'
                })
        
        # Diversification recommendation
        if projects:
            project_types = set(p.get('project_type', 'Other') for p in projects)
            if len(project_types) < 3:
                recommendations.append({
                    'type': 'diversification',
                    'priority': 'high',
                    'action': 'تنويع المحفظة الاستثمارية',
                    'description': 'قم بتنويع استثماراتك عبر قطاعات مختلفة لتقليل المخاطر',
                    'expected_impact': 'تقليل المخاطر بنسبة 20-30%'
                })
        
        # Market timing recommendation
        economic_outlook = market_data.get('economic_outlook', '')
        if economic_outlook == 'positive':
            recommendations.append({
                'type': 'market_timing',
                'priority': 'high',
                'action': 'زيادة الاستثمارات',
                'description': 'الظروف الاقتصادية إيجابية - فرصة جيدة لزيادة الاستثمار',
                'expected_impact': 'نمو محتمل 10-15%'
            })
        
        # Technology investment recommendation
        recommendations.append({
            'type': 'technology',
            'priority': 'medium',
            'action': 'الاستثمار في التكنولوجيا',
            'description': 'استثمر في التكنولوجيا والأتمتة لتحسين الكفاءة',
            'expected_impact': 'تحسين الإنتاجية بنسبة 15-25%'
        })
        
        return recommendations


# API Endpoints
@frappe.whitelist()
def start_investment_analysis(company, filters=None):
    """API endpoint to start investment analysis job"""
    if not filters:
        filters = {}
    if isinstance(filters, str):
        filters = json.loads(filters)
        
    from material_ledger.material_ledger.services.queue_service import queue_ai_analysis
    return queue_ai_analysis("investment_analysis", company, filters)


@frappe.whitelist()
def get_investment_status(job_id):
    """API endpoint to get investment analysis job status"""
    from material_ledger.material_ledger.services.queue_service import get_ai_job_status
    return get_ai_job_status(job_id)