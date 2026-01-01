# Copyright (c) 2025, Ahmad
# For license information, please see license.txt

"""
Financial Calculations Service Module
Handles all financial calculations and ratio analysis
"""

import frappe
from frappe import _
from frappe.utils import flt


class FinancialCalculator:
    """Service class for financial calculations"""
    
    @staticmethod
    def calculate_ratios(income, expense, net_profit, assets, liabilities, equity,
                        current_assets, current_liabilities, prev_income=0, prev_profit=0):
        """
        Calculate comprehensive financial ratios
        
        Returns:
            dict: Dictionary of all financial ratios
        """
        ratios = {
            # Profitability Ratios
            "roe": flt((net_profit / equity * 100), 2) if equity > 0 else 0,
            "roa": flt((net_profit / assets * 100), 2) if assets > 0 else 0,
            "net_margin": flt((net_profit / income * 100), 2) if income > 0 else 0,
            "operating_margin": flt((net_profit / income * 100), 2) if income > 0 else 0,
            
            # Efficiency Ratios
            "asset_turnover": flt(income / assets, 2) if assets > 0 else 0,
            
            # Leverage Ratios
            "leverage": flt(assets / equity, 2) if equity > 0 else 0,
            "debt_ratio": flt((liabilities / assets * 100), 2) if assets > 0 else 0,
            
            # Liquidity Ratios
            "current_ratio": flt(current_assets / current_liabilities, 2) if current_liabilities > 0 else 0,
            "quick_ratio": flt((current_assets * 0.7) / current_liabilities, 2) if current_liabilities > 0 else 0,
            
            # Growth Ratios
            "income_growth": flt(((income - prev_income) / prev_income * 100), 2) if prev_income else 0,
            "profit_growth": flt(((net_profit - prev_profit) / abs(prev_profit) * 100), 2) if prev_profit != 0 else 0,
            
            # Working Capital
            "working_capital": flt(current_assets - current_liabilities, 2),
            
            # Z-Score and DuPont (to be calculated)
            "z_score": 0,
            "dupont_roe": 0
        }
        
        # Calculate Altman Z-Score
        if assets > 0 and liabilities > 0:
            working_capital = current_assets - current_liabilities
            a = (working_capital / assets) * 1.2
            b = (equity / assets) * 1.4
            c = (net_profit / assets) * 3.3
            d = (equity / liabilities) * 0.6
            e = (income / assets) * 1.0
            ratios["z_score"] = flt(a + b + c + d + e, 2)
        
        # Calculate DuPont ROE
        if equity > 0 and assets > 0 and income > 0:
            profit_margin = net_profit / income
            asset_turnover = income / assets
            equity_multiplier = assets / equity
            ratios["dupont_roe"] = flt(profit_margin * asset_turnover * equity_multiplier * 100, 2)
        
        return ratios
    
    @staticmethod
    def calculate_health_score(ratios, prev_income=0, prev_profit=0):
        """
        Calculate overall financial health score (0-100)
        
        Args:
            ratios: Dictionary of financial ratios
            prev_income: Previous year income
            prev_profit: Previous year profit
            
        Returns:
            int: Health score between 0 and 100
        """
        score = 50  # Base score
        
        # ROE Impact (+15 to -15)
        roe = ratios.get('roe', 0)
        if roe > 15:
            score += 15
        elif roe > 10:
            score += 10
        elif roe > 5:
            score += 5
        elif roe < 0:
            score -= 15
        
        # Profitability (+10 to -15)
        net_margin = ratios.get('net_margin', 0)
        if net_margin > 15:
            score += 10
        elif net_margin > 10:
            score += 7
        elif net_margin < 0:
            score -= 15
        
        # Liquidity (+10 to -15)
        current_ratio = ratios.get('current_ratio', 0)
        if 1.5 <= current_ratio <= 3:
            score += 10
        elif current_ratio > 3:
            score += 5
        elif current_ratio < 1:
            score -= 15
        
        # Leverage (+10 to -10)
        leverage = ratios.get('leverage', 0)
        if leverage < 2:
            score += 10
        elif leverage > 3:
            score -= 10
        
        # Growth (+10 to -10)
        growth = ratios.get('income_growth', 0)
        if growth > 10:
            score += 10
        elif growth > 5:
            score += 5
        elif growth < -10:
            score -= 10
        
        # Z-Score (+10 to -20)
        z_score = ratios.get('z_score', 0)
        if z_score > 2.9:
            score += 10
        elif z_score < 1.8:
            score -= 20
        
        return min(max(score, 0), 100)
    
    @staticmethod
    def detect_risk_flags(ratios, profit, income, assets, liabilities):
        """
        Detect financial risk flags
        
        Returns:
            list: List of risk flag dictionaries
        """
        flags = []
        
        # Profitability Risk
        if profit < 0:
            flags.append({
                "level": "critical",
                "title": "إنهيار الربحية",
                "title_en": "Profitability Collapse",
                "message": "الشركة تحقق خسائر مالية - يتطلب تدخل فوري",
                "message_en": "Company is making losses - immediate action required",
                "code": "LOSS"
            })
        elif ratios.get('net_margin', 0) < 2:
            flags.append({
                "level": "warning",
                "title": "هامش ربح منخفض",
                "title_en": "Low Profit Margin",
                "message": "هامش الربح أقل من 2% - يحتاج تحسين العمليات",
                "message_en": "Profit margin below 2% - needs operational improvement",
                "code": "LOW_MARGIN"
            })
        
        # Growth Risk
        if ratios.get('income_growth', 0) < -5:
            flags.append({
                "level": "warning",
                "title": "انخفاض الإيرادات",
                "title_en": "Revenue Decline",
                "message": "انخفاض الإيرادات بنسبة تزيد عن 5% مقارنة بالسنة السابقة",
                "message_en": "Revenue declined by more than 5% YoY",
                "code": "REVENUE_DECLINE"
            })
        
        # Liquidity Risk
        if ratios.get('current_ratio', 0) < 1:
            flags.append({
                "level": "critical",
                "title": "مشكلة سيولة حرجة",
                "title_en": "Critical Liquidity Issue",
                "message": "الالتزامات قصيرة الأجل تتجاوز الأصول المتداولة",
                "message_en": "Current liabilities exceed current assets",
                "code": "LIQUIDITY_CRISIS"
            })
        
        # Leverage Risk
        if ratios.get('leverage', 0) > 3:
            flags.append({
                "level": "warning",
                "title": "ديون مرتفعة جداً",
                "title_en": "Very High Debt",
                "message": "نسبة الديون إلى حقوق الملكية مرتفعة - مخاطر إعادة هيكلة",
                "message_en": "High debt-to-equity ratio - restructuring risk",
                "code": "HIGH_DEBT"
            })
        elif ratios.get('debt_ratio', 0) > 70:
            flags.append({
                "level": "warning",
                "title": "نسبة مديونية مرتفعة",
                "title_en": "High Debt Ratio",
                "message": "أكثر من 70% من الأصول ممولة بالديون",
                "message_en": "More than 70% of assets financed by debt",
                "code": "HIGH_DEBT_RATIO"
            })
        
        # Z-Score Risk (Bankruptcy)
        z_score = ratios.get('z_score', 0)
        if z_score < 1.8:
            flags.append({
                "level": "critical",
                "title": "خطر إفلاس وشيك",
                "title_en": "Imminent Bankruptcy Risk",
                "message": "Z-Score أقل من 1.8 - احتمالية إفلاس عالية",
                "message_en": "Z-Score below 1.8 - high bankruptcy probability",
                "code": "BANKRUPTCY_RISK"
            })
        elif z_score < 2.9:
            flags.append({
                "level": "warning",
                "title": "منطقة رمادية",
                "title_en": "Grey Zone",
                "message": "Z-Score في منطقة خطر - يتطلب مراقبة دقيقة",
                "message_en": "Z-Score in danger zone - requires close monitoring",
                "code": "GREY_ZONE"
            })
        
        # ROA Risk
        if ratios.get('roa', 0) < 0:
            flags.append({
                "level": "critical",
                "title": "عدم كفاءة استخدام الأصول",
                "title_en": "Inefficient Asset Utilization",
                "message": "ROA سالب - الأصول لا تحقق أرباح",
                "message_en": "Negative ROA - assets not generating profits",
                "code": "LOW_ROA"
            })
        
        return flags
    
    @staticmethod
    def analyze_income_statement(income, expense, profit, prev_income=0, prev_profit=0):
        """Detailed Income Statement Analysis"""
        margin = (profit / income * 100) if income > 0 else 0
        prev_margin = (prev_profit / prev_income * 100) if prev_income > 0 else 0
        revenue_growth = ((income - prev_income) / prev_income * 100) if prev_income > 0 else 0
        profit_growth = ((profit - prev_profit) / abs(prev_profit) * 100) if prev_profit != 0 else 0
        
        analysis = {
            "gross_margin": flt(margin, 2),
            "margin_change": flt(margin - prev_margin, 2),
            "revenue_growth": flt(revenue_growth, 2),
            "profit_growth": flt(profit_growth, 2),
            "expense_ratio": flt((expense / income * 100), 2) if income > 0 else 0,
            "insights": []
        }
        
        # Generate insights
        if revenue_growth > 10:
            analysis["insights"].append({
                "ar": "نمو قوي في الإيرادات - استمرار التوسع في السوق",
                "en": "Strong revenue growth - continued market expansion"
            })
        elif revenue_growth < -5:
            analysis["insights"].append({
                "ar": "⚠️ انخفاض الإيرادات - يتطلب مراجعة استراتيجية المبيعات",
                "en": "⚠️ Revenue decline - requires sales strategy review"
            })
        
        if margin > 20:
            analysis["insights"].append({
                "ar": "هامش ربح ممتاز - كفاءة تشغيلية عالية",
                "en": "Excellent profit margin - high operational efficiency"
            })
        elif margin < 5:
            analysis["insights"].append({
                "ar": "⚠️ هامش ربح منخفض - ضغوط على التكاليف",
                "en": "⚠️ Low profit margin - cost pressures"
            })
        
        if profit_growth > 15:
            analysis["insights"].append({
                "ar": "نمو استثنائي في الأرباح",
                "en": "Exceptional profit growth"
            })
        
        return analysis
    
    @staticmethod
    def analyze_balance_sheet(assets, liabilities, equity, prev_assets=0, prev_liabilities=0):
        """Detailed Balance Sheet Analysis"""
        debt_to_equity = (liabilities / equity) if equity > 0 else 0
        debt_to_assets = (liabilities / assets * 100) if assets > 0 else 0
        asset_growth = ((assets - prev_assets) / prev_assets * 100) if prev_assets > 0 else 0
        
        analysis = {
            "debt_to_equity": flt(debt_to_equity, 2),
            "debt_to_assets": flt(debt_to_assets, 2),
            "asset_growth": flt(asset_growth, 2),
            "equity_ratio": flt((equity / assets * 100), 2) if assets > 0 else 0,
            "insights": []
        }
        
        if debt_to_equity < 0.5:
            analysis["insights"].append({
                "ar": "هيكل تمويل محافظ - اعتماد قليل على الديون",
                "en": "Conservative financing structure - low debt reliance"
            })
        elif debt_to_equity > 2:
            analysis["insights"].append({
                "ar": "⚠️ ديون مرتفعة مقارنة بحقوق الملكية",
                "en": "⚠️ High debt compared to equity"
            })
        
        if asset_growth > 20:
            analysis["insights"].append({
                "ar": "نمو كبير في الأصول - توسع في الاستثمارات",
                "en": "Significant asset growth - investment expansion"
            })
        elif asset_growth < 0:
            analysis["insights"].append({
                "ar": "⚠️ انكماش في قاعدة الأصول",
                "en": "⚠️ Contraction in asset base"
            })
        
        if debt_to_assets > 70:
            analysis["insights"].append({
                "ar": "⚠️ نسبة مديونية عالية جداً",
                "en": "⚠️ Very high debt ratio"
            })
        elif debt_to_assets < 30:
            analysis["insights"].append({
                "ar": "وضع مالي قوي - ديون منخفضة",
                "en": "Strong financial position - low debt"
            })
        
        return analysis
    
    @staticmethod
    def analyze_cashflow(cash_flow, net_profit):
        """Detailed Cash Flow Analysis"""
        operating = cash_flow.get("operating", 0)
        investing = cash_flow.get("investing", 0)
        financing = cash_flow.get("financing", 0)
        net = cash_flow.get("net", 0)
        
        operating_margin = (operating / net_profit * 100) if net_profit > 0 else 0
        free_cash_flow = operating + investing
        
        analysis = {
            "operating_margin": flt(operating_margin, 2),
            "free_cash_flow": flt(free_cash_flow, 2),
            "cash_conversion": flt(operating_margin, 2),
            "insights": []
        }
        
        if operating > net_profit:
            analysis["insights"].append({
                "ar": "تدفق نقدي تشغيلي قوي - أفضل من الأرباح المحاسبية",
                "en": "Strong operating cash flow - better than accounting profits"
            })
        elif operating < 0:
            analysis["insights"].append({
                "ar": "⚠️ تدفق نقدي سالب من العمليات",
                "en": "⚠️ Negative operating cash flow"
            })
        
        if free_cash_flow > 0:
            analysis["insights"].append({
                "ar": "توليد تدفق نقدي حر إيجابي",
                "en": "Generating positive free cash flow"
            })
        else:
            analysis["insights"].append({
                "ar": "⚠️ التدفق النقدي الحر سالب - استثمارات تفوق التشغيل",
                "en": "⚠️ Negative free cash flow - investments exceed operations"
            })
        
        if net < 0:
            analysis["insights"].append({
                "ar": "⚠️ صافي تدفق نقدي سالب - مراقبة السيولة",
                "en": "⚠️ Negative net cash flow - monitor liquidity"
            })
        
        return analysis
