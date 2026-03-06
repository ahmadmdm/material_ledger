# Copyright (c) 2026, Ahmad
# For license information, please see license.txt

"""
AI Prediction Service for Financial Forecasting
Uses AI to predict financial trends, cash flow, and performance
"""

import frappe
from frappe import _
from frappe.utils import flt, add_months, getdate, now
import json
import statistics
import numpy as np
from sklearn.linear_model import LinearRegression
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class AIPredictionService:
    """Service for AI-powered financial predictions"""
    
    def __init__(self):
        self.chunk_size = 500
        self.prediction_months = 12  # Predict 12 months ahead
        
    def get_historical_data(self, company, filters):
        """
        Get historical financial data for prediction
        
        Args:
            company: Company name
            filters: Dictionary with date ranges, accounts, etc.
            
        Returns:
            list: Historical financial data
        """
        from_date = filters.get('from_date', '2020-01-01')
        to_date = filters.get('to_date', now().split(' ')[0])
        
        # Get GL entries for analysis
        gl_entries = frappe.db.sql("""
            SELECT 
                posting_date,
                account,
                debit,
                credit,
                (debit - credit) as net_amount,
                cost_center,
                project,
                MONTH(posting_date) as month,
                YEAR(posting_date) as year,
                QUARTER(posting_date) as quarter
            FROM `tabGL Entry`
            WHERE 
                company = %(company)s 
                AND posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND is_cancelled = 0
            ORDER BY posting_date
        """, {
            'company': company,
            'from_date': from_date,
            'to_date': to_date
        }, as_dict=True)
        
        return self._aggregate_monthly_data(gl_entries)
    
    def _aggregate_monthly_data(self, gl_entries):
        """Aggregate GL entries by month for trend analysis"""
        monthly_data = {}
        
        for entry in gl_entries:
            month_key = f"{entry.year}-{entry.month:02d}"
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'date': month_key,
                    'revenue': 0,
                    'expenses': 0,
                    'assets': 0,
                    'liabilities': 0,
                    'equity': 0,
                    'cash_flow': 0
                }
            
            # Categorize accounts
            account_type = frappe.db.get_value('Account', entry.account, 'account_type')
            root_type = frappe.db.get_value('Account', entry.account, 'root_type')
            
            if root_type == 'Income':
                monthly_data[month_key]['revenue'] += flt(entry.credit - entry.debit)
            elif root_type == 'Expense':
                monthly_data[month_key]['expenses'] += flt(entry.debit - entry.credit)
            elif root_type == 'Asset':
                monthly_data[month_key]['assets'] += flt(entry.debit - entry.credit)
            elif root_type == 'Liability':
                monthly_data[month_key]['liabilities'] += flt(entry.credit - entry.debit)
            elif root_type == 'Equity':
                monthly_data[month_key]['equity'] += flt(entry.credit - entry.debit)
                
            # Cash flow approximation
            if account_type in ['Cash', 'Bank']:
                monthly_data[month_key]['cash_flow'] += flt(entry.debit - entry.credit)
        
        return list(monthly_data.values())
    
    def chunk_financial_data(self, data):
        """Split data into processable chunks"""
        chunks = []
        for i in range(0, len(data), self.chunk_size):
            chunks.append(data[i:i + self.chunk_size])
        return chunks
    
    def predict_chunk(self, chunk_data):
        """
        Predict financial trends for a data chunk
        
        Args:
            chunk_data: List of monthly financial data
            
        Returns:
            dict: Predictions for this chunk
        """
        if not chunk_data or len(chunk_data) < 3:
            return {"predictions": [], "confidence": 0}
        
        # Use both traditional and AI methods
        traditional_predictions = self._traditional_forecast(chunk_data)
        ai_predictions = self._ai_forecast(chunk_data)
        
        # Combine predictions with weights
        combined_predictions = self._combine_prediction_methods(
            traditional_predictions, ai_predictions
        )
        
        return {
            "predictions": combined_predictions,
            "confidence": self._calculate_confidence(chunk_data),
            "trend_analysis": self._analyze_trends(chunk_data),
            "seasonality": self._detect_seasonality(chunk_data)
        }
    
    def _traditional_forecast(self, data):
        """Traditional statistical forecasting"""
        predictions = []
        
        # Extract time series data
        revenue_series = [d['revenue'] for d in data]
        expenses_series = [d['expenses'] for d in data]
        cash_flow_series = [d['cash_flow'] for d in data]
        
        # Simple moving average and trend analysis
        for i in range(self.prediction_months):
            revenue_pred = self._predict_series(revenue_series, i + 1)
            expenses_pred = self._predict_series(expenses_series, i + 1)
            cash_flow_pred = self._predict_series(cash_flow_series, i + 1)
            
            # Calculate projected month
            last_date = data[-1]['date'] if data else "2026-01"
            projected_date = self._add_months_to_date(last_date, i + 1)
            
            predictions.append({
                'date': projected_date,
                'revenue': revenue_pred,
                'expenses': expenses_pred,
                'profit': revenue_pred - expenses_pred,
                'cash_flow': cash_flow_pred,
                'method': 'traditional'
            })
            
        return predictions
    
    def _ai_forecast(self, data):
        """AI-powered forecasting using available AI service"""
        try:
            from material_ledger.material_ledger.services.ai_service import get_ai_service
            
            ai_service = get_ai_service()
            if not ai_service.is_available():
                return self._fallback_ai_forecast(data)
            
            # Prepare data for AI analysis
            analysis_prompt = self._build_prediction_prompt(data)
            
            # Get AI predictions
            ai_response = ai_service._call_deepseek(analysis_prompt) if hasattr(ai_service, '_call_deepseek') else None
            
            if ai_response:
                return self._parse_ai_predictions(ai_response)
            else:
                return self._fallback_ai_forecast(data)
                
        except Exception as e:
            frappe.log_error(f"AI Forecast Error: {str(e)}", "AI Prediction Service")
            return self._fallback_ai_forecast(data)
    
    def _fallback_ai_forecast(self, data):
        """Fallback AI-like prediction using statistical methods"""
        if not HAS_SKLEARN or len(data) < 6:
            return self._simple_trend_forecast(data)
            
        try:
            # Prepare data for sklearn
            X = np.array([[i] for i in range(len(data))])
            
            predictions = []
            
            for metric in ['revenue', 'expenses', 'cash_flow']:
                y = np.array([d.get(metric, 0) for d in data])
                
                # Linear regression model
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict future values
                future_X = np.array([[len(data) + i] for i in range(1, self.prediction_months + 1)])
                future_y = model.predict(future_X)
                
                # Store predictions
                for i, pred_value in enumerate(future_y):
                    if i >= len(predictions):
                        last_date = data[-1]['date'] if data else "2026-01"
                        projected_date = self._add_months_to_date(last_date, i + 1)
                        predictions.append({
                            'date': projected_date,
                            'method': 'ml_fallback'
                        })
                    
                    predictions[i][metric] = max(0, flt(pred_value))  # Ensure non-negative
            
            # Calculate profit
            for pred in predictions:
                pred['profit'] = pred.get('revenue', 0) - pred.get('expenses', 0)
            
            return predictions
            
        except Exception as e:
            frappe.log_error(f"ML Forecast Error: {str(e)}", "AI Prediction Service")
            return self._simple_trend_forecast(data)
    
    def _simple_trend_forecast(self, data):
        """Simple trend-based forecast as ultimate fallback"""
        predictions = []
        
        if not data or len(data) < 2:
            return predictions
            
        # Calculate simple trends
        recent_data = data[-6:] if len(data) >= 6 else data
        
        revenue_trend = self._calculate_trend([d['revenue'] for d in recent_data])
        expenses_trend = self._calculate_trend([d['expenses'] for d in recent_data])
        cash_trend = self._calculate_trend([d['cash_flow'] for d in recent_data])
        
        last_values = data[-1]
        
        for i in range(self.prediction_months):
            revenue_pred = last_values['revenue'] + (revenue_trend * (i + 1))
            expenses_pred = last_values['expenses'] + (expenses_trend * (i + 1))
            cash_pred = last_values['cash_flow'] + (cash_trend * (i + 1))
            
            last_date = data[-1]['date'] if data else "2026-01"
            projected_date = self._add_months_to_date(last_date, i + 1)
            
            predictions.append({
                'date': projected_date,
                'revenue': max(0, revenue_pred),
                'expenses': max(0, expenses_pred),
                'profit': revenue_pred - expenses_pred,
                'cash_flow': cash_pred,
                'method': 'simple_trend'
            })
            
        return predictions
    
    def _build_prediction_prompt(self, data):
        """Build prompt for AI prediction"""
        # Summarize recent trends
        recent_data = data[-12:] if len(data) >= 12 else data
        
        revenue_trend = [d['revenue'] for d in recent_data]
        expenses_trend = [d['expenses'] for d in recent_data]
        
        monthly_summary = []
        for d in recent_data[-6:]:  # Last 6 months
            monthly_summary.append(f"📅 {d['date']}: الإيرادات {d['revenue']:,.0f}, المصروفات {d['expenses']:,.0f}, الربح {(d['revenue'] - d['expenses']):,.0f}")
        
        prompt = f"""
كمحلل مالي خبير، قم بالتنبؤ بالأداء المالي للأشهر الـ 12 القادمة بناء على البيانات التاريخية التالية:

📊 **البيانات الحديثة:**
{chr(10).join(monthly_summary)}

📈 **الاتجاهات المكتشفة:**
- متوسط الإيرادات الشهرية: {statistics.mean(revenue_trend):,.0f}
- متوسط المصروفات الشهرية: {statistics.mean(expenses_trend):,.0f}
- اتجاه النمو في الإيرادات: {self._calculate_trend(revenue_trend):+,.0f} شهرياً
- اتجاه النمو في المصروفات: {self._calculate_trend(expenses_trend):+,.0f} شهرياً

المطلوب:
1. توقع الإيرادات والمصروفات لكل شهر من الأشهر الـ 12 القادمة
2. تحليل المخاطر المحتملة
3. توصيات لتحسين الأداء
4. تحديد الفرص المتاحة

يجب أن تكون التوقعات:
- واقعية ومبنية على البيانات
- تأخذ بعين الاعتبار الموسمية
- تتضمن أفضل وأسوأ السيناريوهات
- مدعومة بالتبرير المنطقي

قدم الرد بتنسيق JSON يحتوي على:
```json
{{
  "predictions": [
    {{
      "date": "2026-04",
      "revenue": 150000,
      "expenses": 120000,
      "profit": 30000,
      "confidence": 85
    }}
  ],
  "risks": ["..."],
  "opportunities": ["..."],
  "recommendations": ["..."]
}}
```
"""
        return prompt
    
    def _parse_ai_predictions(self, ai_response):
        """Parse AI response into structured predictions"""
        try:
            # Try to extract JSON from AI response
            import re
            json_match = re.search(r'```json\n(.*?)\n```', ai_response, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group(1))
                return ai_data.get('predictions', [])
        except:
            pass
        
        # If parsing fails, return empty predictions
        return []
    
    def _predict_series(self, series, months_ahead):
        """Predict future value using moving average and trend"""
        if not series or len(series) < 3:
            return 0
            
        # Use last 6 months for prediction
        recent_series = series[-6:] if len(series) >= 6 else series
        
        # Moving average
        moving_avg = statistics.mean(recent_series)
        
        # Trend calculation
        trend = self._calculate_trend(recent_series)
        
        # Apply trend for future months
        prediction = moving_avg + (trend * months_ahead)
        
        return max(0, prediction)  # Ensure non-negative
    
    def _calculate_trend(self, series):
        """Calculate linear trend in a series"""
        if len(series) < 2:
            return 0
            
        n = len(series)
        x = list(range(n))
        y = series
        
        # Linear regression coefficients
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
            
        return numerator / denominator
    
    def _add_months_to_date(self, date_str, months):
        """Add months to date string"""
        try:
            year, month = map(int, date_str.split('-'))
            month += months
            while month > 12:
                month -= 12
                year += 1
            return f"{year}-{month:02d}"
        except:
            return date_str
    
    def _calculate_confidence(self, data):
        """Calculate prediction confidence based on data quality"""
        if not data or len(data) < 3:
            return 30
            
        # Base confidence on data consistency and volume
        base_confidence = min(90, 50 + len(data) * 2)
        
        # Reduce confidence for high volatility
        revenue_series = [d['revenue'] for d in data[-6:]]
        if len(revenue_series) > 1:
            volatility = statistics.stdev(revenue_series) / (statistics.mean(revenue_series) + 1)
            volatility_penalty = min(30, volatility * 100)
            base_confidence -= volatility_penalty
        
        return max(30, int(base_confidence))
    
    def _analyze_trends(self, data):
        """Analyze trends in the data"""
        if len(data) < 3:
            return {"trend": "insufficient_data"}
            
        revenue_series = [d['revenue'] for d in data]
        expenses_series = [d['expenses'] for d in data]
        
        revenue_trend = self._calculate_trend(revenue_series)
        expenses_trend = self._calculate_trend(expenses_series)
        
        return {
            "revenue_trend": "increasing" if revenue_trend > 0 else "decreasing" if revenue_trend < 0 else "stable",
            "expenses_trend": "increasing" if expenses_trend > 0 else "decreasing" if expenses_trend < 0 else "stable",
            "revenue_growth_rate": revenue_trend,
            "expenses_growth_rate": expenses_trend,
            "profitability_trend": "improving" if revenue_trend > expenses_trend else "declining"
        }
    
    def _detect_seasonality(self, data):
        """Detect seasonal patterns in the data"""
        if len(data) < 12:
            return {"has_seasonality": False}
            
        # Group by month to detect patterns
        monthly_averages = {}
        for d in data:
            if '-' in d['date']:
                month = int(d['date'].split('-')[1])
                if month not in monthly_averages:
                    monthly_averages[month] = []
                monthly_averages[month].append(d['revenue'])
        
        # Calculate seasonal factors
        if len(monthly_averages) >= 4:
            seasonal_factors = {}
            overall_avg = statistics.mean([d['revenue'] for d in data])
            
            for month, revenues in monthly_averages.items():
                month_avg = statistics.mean(revenues)
                seasonal_factors[month] = month_avg / (overall_avg + 1)
            
            # Detect significant seasonality
            factor_range = max(seasonal_factors.values()) - min(seasonal_factors.values())
            has_seasonality = factor_range > 0.2  # 20% variation
            
            return {
                "has_seasonality": has_seasonality,
                "seasonal_factors": seasonal_factors,
                "peak_month": max(seasonal_factors, key=seasonal_factors.get),
                "low_month": min(seasonal_factors, key=seasonal_factors.get)
            }
        
        return {"has_seasonality": False}
    
    def _combine_prediction_methods(self, traditional, ai_predictions):
        """Combine traditional and AI predictions with intelligent weighting"""
        # Weight: 60% traditional (more reliable), 40% AI (more insightful)
        traditional_weight = 0.6
        ai_weight = 0.4
        
        combined = []
        
        # If AI predictions are available, combine them
        if ai_predictions and len(ai_predictions) > 0:
            for i in range(min(len(traditional), len(ai_predictions))):
                trad_pred = traditional[i]
                ai_pred = ai_predictions[i]
                
                combined_pred = {
                    'date': trad_pred['date'],
                    'revenue': (trad_pred['revenue'] * traditional_weight + 
                              ai_pred.get('revenue', trad_pred['revenue']) * ai_weight),
                    'expenses': (trad_pred['expenses'] * traditional_weight + 
                               ai_pred.get('expenses', trad_pred['expenses']) * ai_weight),
                    'cash_flow': (trad_pred['cash_flow'] * traditional_weight + 
                                ai_pred.get('cash_flow', trad_pred['cash_flow']) * ai_weight),
                    'method': 'combined'
                }
                combined_pred['profit'] = combined_pred['revenue'] - combined_pred['expenses']
                combined.append(combined_pred)
        else:
            # Fall back to traditional predictions
            combined = traditional
        
        return combined
    
    def combine_predictions(self, chunk_predictions):
        """
        Combine predictions from multiple data chunks
        
        Args:
            chunk_predictions: List of prediction dictionaries from chunks
            
        Returns:
            dict: Combined final prediction results
        """
        if not chunk_predictions:
            return {"predictions": [], "confidence": 0}
        
        # Combine all predictions
        all_predictions = []
        all_confidences = []
        all_trends = []
        
        for chunk_pred in chunk_predictions:
            if chunk_pred.get('predictions'):
                all_predictions.extend(chunk_pred['predictions'])
            if chunk_pred.get('confidence'):
                all_confidences.append(chunk_pred['confidence'])
            if chunk_pred.get('trend_analysis'):
                all_trends.append(chunk_pred['trend_analysis'])
        
        # Calculate overall confidence
        overall_confidence = statistics.mean(all_confidences) if all_confidences else 50
        
        # Remove duplicates and sort by date
        unique_predictions = {}
        for pred in all_predictions:
            date_key = pred['date']
            if date_key not in unique_predictions:
                unique_predictions[date_key] = pred
            else:
                # Average if duplicate
                existing = unique_predictions[date_key]
                for key in ['revenue', 'expenses', 'profit', 'cash_flow']:
                    if key in pred and key in existing:
                        existing[key] = (existing[key] + pred[key]) / 2
        
        final_predictions = sorted(unique_predictions.values(), key=lambda x: x['date'])
        
        # Generate comprehensive analysis
        analysis = self._generate_prediction_analysis(final_predictions, all_trends)
        
        return {
            "predictions": final_predictions[:self.prediction_months],  # Limit to requested months
            "confidence": int(overall_confidence),
            "analysis": analysis,
            "summary": self._generate_prediction_summary(final_predictions),
            "risks": self._identify_prediction_risks(final_predictions),
            "opportunities": self._identify_opportunities(final_predictions),
            "generated_at": now()
        }
    
    def _generate_prediction_analysis(self, predictions, trends):
        """Generate comprehensive prediction analysis"""
        if not predictions:
            return "لا توجد توقعات متاحة"
            
        total_predicted_revenue = sum(p['revenue'] for p in predictions)
        total_predicted_expenses = sum(p['expenses'] for p in predictions)
        total_predicted_profit = total_predicted_revenue - total_predicted_expenses
        
        analysis = f"""
📈 **تحليل التوقعات المالية للأشهر الـ {len(predictions)} القادمة:**

💰 **الإجماليات المتوقعة:**
- إجمالي الإيرادات المتوقعة: {total_predicted_revenue:,.0f}
- إجمالي المصروفات المتوقعة: {total_predicted_expenses:,.0f}  
- إجمالي الأرباح المتوقعة: {total_predicted_profit:,.0f}
- متوسط الربح الشهري: {total_predicted_profit/len(predictions):,.0f}

📊 **أفضل وأسوأ الأشهر المتوقعة:**
- أعلى ربح متوقع: {max(p['profit'] for p in predictions):,.0f} في {max(predictions, key=lambda x: x['profit'])['date']}
- أقل ربح متوقع: {min(p['profit'] for p in predictions):,.0f} في {min(predictions, key=lambda x: x['profit'])['date']}

🎯 **التوصيات الاستراتيجية:**
- ركز على الأشهر عالية الربحية لتعظيم العوائد
- ضع خطط طوارئ للأشهر منخفضة الأداء
- راقب التدفق النقدي بعناية خلال فترات الانخفاض
"""
        return analysis
    
    def _generate_prediction_summary(self, predictions):
        """Generate executive summary of predictions"""
        if not predictions:
            return "لا توجد توقعات"
            
        avg_monthly_revenue = statistics.mean(p['revenue'] for p in predictions)
        avg_monthly_profit = statistics.mean(p['profit'] for p in predictions)
        
        growth_trend = "نمو إيجابي" if predictions[-1]['revenue'] > predictions[0]['revenue'] else "تراجع"
        
        return {
            "avg_monthly_revenue": avg_monthly_revenue,
            "avg_monthly_profit": avg_monthly_profit,
            "growth_trend": growth_trend,
            "total_months": len(predictions)
        }
    
    def _identify_prediction_risks(self, predictions):
        """Identify potential risks from predictions"""
        risks = []
        
        if not predictions:
            return risks
            
        # Check for negative profit months
        negative_months = [p for p in predictions if p['profit'] < 0]
        if negative_months:
            risks.append(f"توقع خسائر في {len(negative_months)} شهر من أصل {len(predictions)} أشهر")
        
        # Check for declining trend
        if len(predictions) >= 6:
            first_half_avg = statistics.mean(p['profit'] for p in predictions[:len(predictions)//2])
            second_half_avg = statistics.mean(p['profit'] for p in predictions[len(predictions)//2:])
            
            if second_half_avg < first_half_avg * 0.9:  # 10% decline
                risks.append("اتجاه تنازلي في الأرباح خلال النصف الثاني من فترة التوقع")
        
        # Check for high volatility
        profit_values = [p['profit'] for p in predictions]
        if len(profit_values) > 1:
            volatility = statistics.stdev(profit_values) / (statistics.mean(profit_values) + 1)
            if volatility > 0.3:  # High volatility
                risks.append("تقلبات عالية في الأرباح المتوقعة تشير إلى عدم استقرار")
        
        return risks
    
    def _identify_opportunities(self, predictions):
        """Identify opportunities from predictions"""
        opportunities = []
        
        if not predictions:
            return opportunities
            
        # Find growth opportunities
        revenue_values = [p['revenue'] for p in predictions]
        if len(revenue_values) >= 3:
            trend = self._calculate_trend(revenue_values)
            if trend > 0:
                opportunities.append(f"فرصة نمو في الإيرادات بمعدل {trend:,.0f} شهرياً")
        
        # Find high profit months
        high_profit_months = [p for p in predictions if p['profit'] > statistics.mean(p['profit'] for p in predictions) * 1.2]
        if high_profit_months:
            opportunities.append(f"فرص استثنائية في {len(high_profit_months)} شهر لتحقيق أرباح مرتفعة")
        
        # Cash flow opportunities
        cash_flows = [p.get('cash_flow', 0) for p in predictions]
        if any(cf > 0 for cf in cash_flows):
            opportunities.append("تدفق نقدي إيجابي متوقع يفتح المجال للاستثمار والتوسع")
        
        return opportunities


# API Endpoints
@frappe.whitelist()
def start_financial_prediction(company, filters=None):
    """API endpoint to start financial prediction job"""
    if not filters:
        filters = {}
    if isinstance(filters, str):
        filters = json.loads(filters)
        
    from material_ledger.material_ledger.services.queue_service import queue_ai_analysis
    return queue_ai_analysis("financial_prediction", company, filters)


@frappe.whitelist()
def get_prediction_status(job_id):
    """API endpoint to get prediction job status"""
    from material_ledger.material_ledger.services.queue_service import get_ai_job_status
    return get_ai_job_status(job_id)