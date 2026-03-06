# Copyright (c) 2026, Ahmad
# For license information, please see license.txt

"""
AI Anomaly Detection Service
Detects unusual patterns, potential fraud, and data inconsistencies
"""

import frappe
from frappe import _
from frappe.utils import flt, now, getdate
import json
import statistics
import math
from collections import defaultdict


class AIAnomalyService:
    """Service for detecting financial anomalies using AI and statistical methods"""
    
    def __init__(self):
        self.chunk_size = 1000
        self.anomaly_threshold = 2.5  # Standard deviations for statistical anomaly
        self.high_risk_threshold = 3.0
        
    def get_transaction_data(self, company, filters):
        """
        Get transaction data for anomaly detection
        
        Args:
            company: Company name  
            filters: Dictionary with date ranges, accounts, etc.
            
        Returns:
            list: Transaction data for analysis
        """
        from_date = filters.get('from_date', '2023-01-01')
        to_date = filters.get('to_date', now().split(' ')[0])
        
        # Get GL entries with detailed information
        gl_entries = frappe.db.sql("""
            SELECT 
                name,
                posting_date,
                account,
                debit,
                credit,
                (debit - credit) as net_amount,
                ABS(debit - credit) as abs_amount,
                voucher_type,
                voucher_no,
                party_type,
                party,
                cost_center,
                project,
                remarks,
                creation,
                modified,
                owner,
                modified_by,
                HOUR(creation) as creation_hour,
                DAYOFWEEK(posting_date) as day_of_week,
                is_opening
            FROM `tabGL Entry`
            WHERE 
                company = %(company)s 
                AND posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND is_cancelled = 0
            ORDER BY posting_date, creation
        """, {
            'company': company,
            'from_date': from_date,
            'to_date': to_date
        }, as_dict=True)
        
        # Enrich with additional data
        enriched_entries = []
        for entry in gl_entries:
            # Add account information
            account_info = frappe.db.get_value(
                'Account', entry.account, 
                ['account_type', 'root_type', 'is_group'], as_dict=True
            ) or {}
            
            enriched_entry = entry.copy()
            enriched_entry.update(account_info)
            
            # Calculate time-based features
            enriched_entry['is_weekend'] = entry.day_of_week in [1, 7]  # Sunday=1, Saturday=7
            enriched_entry['is_after_hours'] = entry.creation_hour < 8 or entry.creation_hour > 18
            
            enriched_entries.append(enriched_entry)
            
        return enriched_entries
    
    def chunk_transaction_data(self, data):
        """Split transaction data into processable chunks"""
        chunks = []
        for i in range(0, len(data), self.chunk_size):
            chunks.append(data[i:i + self.chunk_size])
        return chunks
    
    def detect_chunk_anomalies(self, chunk_data):
        """
        Detect anomalies in a data chunk
        
        Args:
            chunk_data: List of transaction records
            
        Returns:
            list: List of detected anomalies
        """
        anomalies = []
        
        if not chunk_data or len(chunk_data) < 10:
            return anomalies
        
        # Different anomaly detection methods
        anomalies.extend(self._detect_amount_anomalies(chunk_data))
        anomalies.extend(self._detect_timing_anomalies(chunk_data))
        anomalies.extend(self._detect_pattern_anomalies(chunk_data))
        anomalies.extend(self._detect_duplicate_anomalies(chunk_data))
        anomalies.extend(self._detect_account_anomalies(chunk_data))
        anomalies.extend(self._detect_user_behavior_anomalies(chunk_data))
        
        # AI-powered anomaly detection
        ai_anomalies = self._ai_anomaly_detection(chunk_data)
        anomalies.extend(ai_anomalies)
        
        return anomalies
    
    def _detect_amount_anomalies(self, data):
        """Detect unusual amounts using statistical analysis"""
        anomalies = []
        
        # Group by account for amount analysis
        account_amounts = defaultdict(list)
        for entry in data:
            account_amounts[entry['account']].append(entry['abs_amount'])
        
        for account, amounts in account_amounts.items():
            if len(amounts) < 5:  # Need sufficient data
                continue
                
            mean_amount = statistics.mean(amounts)
            stdev_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
            
            if stdev_amount == 0:
                continue
                
            # Find outliers
            for entry in data:
                if entry['account'] == account:
                    z_score = abs((entry['abs_amount'] - mean_amount) / stdev_amount)
                    
                    if z_score > self.anomaly_threshold:
                        severity = "high" if z_score > self.high_risk_threshold else "medium"
                        
                        anomalies.append({
                            'type': 'unusual_amount',
                            'severity': severity,
                            'entry_name': entry['name'],
                            'account': account,
                            'amount': entry['abs_amount'],
                            'expected_range': f"{mean_amount - 2*stdev_amount:.0f} - {mean_amount + 2*stdev_amount:.0f}",
                            'z_score': z_score,
                            'posting_date': entry['posting_date'],
                            'description': f"مبلغ غير عادي: {entry['abs_amount']:,.0f} (متوسط الحساب: {mean_amount:,.0f})",
                            'details': entry
                        })
        
        return anomalies
    
    def _detect_timing_anomalies(self, data):
        """Detect unusual timing patterns"""
        anomalies = []
        
        # After-hours transactions
        after_hours = [entry for entry in data if entry.get('is_after_hours')]
        for entry in after_hours:
            if entry['abs_amount'] > 10000:  # High amount after hours
                anomalies.append({
                    'type': 'after_hours_transaction',
                    'severity': 'medium',
                    'entry_name': entry['name'],
                    'posting_date': entry['posting_date'],
                    'creation_time': entry['creation'],
                    'amount': entry['abs_amount'],
                    'description': f"معاملة بعد ساعات العمل: {entry['abs_amount']:,.0f} في {entry['creation_hour']}:00",
                    'details': entry
                })
        
        # Weekend transactions
        weekend_transactions = [entry for entry in data if entry.get('is_weekend')]
        for entry in weekend_transactions:
            if entry['abs_amount'] > 50000:  # High amount on weekend
                anomalies.append({
                    'type': 'weekend_transaction',
                    'severity': 'medium',
                    'entry_name': entry['name'],
                    'posting_date': entry['posting_date'],
                    'amount': entry['abs_amount'],
                    'description': f"معاملة في نهاية الأسبوع: {entry['abs_amount']:,.0f}",
                    'details': entry
                })
        
        # Rapid sequence transactions
        sorted_data = sorted(data, key=lambda x: x['creation'])
        for i in range(1, len(sorted_data)):
            current = sorted_data[i]
            previous = sorted_data[i-1]
            
            # Check if same user, close timing, similar amounts
            if (current['owner'] == previous['owner'] and
                current['account'] == previous['account'] and
                abs(current['abs_amount'] - previous['abs_amount']) < 100):
                
                time_diff = (getdate(current['creation']) - getdate(previous['creation'])).seconds
                if time_diff < 60:  # Within 1 minute
                    anomalies.append({
                        'type': 'rapid_sequence',
                        'severity': 'high',
                        'entry_name': current['name'],
                        'related_entry': previous['name'],
                        'time_gap': time_diff,
                        'description': f"معاملات متتابعة سريعة خلال {time_diff} ثانية",
                        'details': current
                    })
        
        return anomalies
    
    def _detect_pattern_anomalies(self, data):
        """Detect unusual patterns in transactions"""
        anomalies = []
        
        # Round amount pattern (potential manipulation)
        round_amounts = [entry for entry in data if entry['abs_amount'] % 1000 == 0 and entry['abs_amount'] > 10000]
        if len(round_amounts) > len(data) * 0.3:  # More than 30% are round amounts
            for entry in round_amounts[-5:]:  # Flag recent ones
                anomalies.append({
                    'type': 'round_amount_pattern',
                    'severity': 'medium',
                    'entry_name': entry['name'],
                    'amount': entry['abs_amount'],
                    'description': f"نمط مبالغ مدورة مشبوه: {entry['abs_amount']:,.0f}",
                    'details': entry
                })
        
        # Identical amounts pattern
        amount_counts = defaultdict(list)
        for entry in data:
            amount_counts[entry['abs_amount']].append(entry)
        
        for amount, entries in amount_counts.items():
            if len(entries) >= 5 and amount > 1000:  # 5+ identical amounts
                for entry in entries[-3:]:  # Flag recent ones
                    anomalies.append({
                        'type': 'identical_amounts',
                        'severity': 'medium',
                        'entry_name': entry['name'],
                        'amount': amount,
                        'count': len(entries),
                        'description': f"مبلغ متكرر مشبوه: {amount:,.0f} ({len(entries)} مرات)",
                        'details': entry
                    })
        
        return anomalies
    
    def _detect_duplicate_anomalies(self, data):
        """Detect potential duplicate or reversed transactions"""
        anomalies = []
        
        # Group by date and amount for duplicate detection
        date_amount_groups = defaultdict(list)
        for entry in data:
            key = f"{entry['posting_date']}_{entry['abs_amount']}"
            date_amount_groups[key].append(entry)
        
        for key, entries in date_amount_groups.items():
            if len(entries) >= 2:
                # Check for potential duplicates
                for i in range(len(entries)):
                    for j in range(i+1, len(entries)):
                        entry1, entry2 = entries[i], entries[j]
                        
                        # Same account, same amount, same date = potential duplicate
                        if (entry1['account'] == entry2['account'] and
                            entry1['voucher_type'] == entry2['voucher_type']):
                            
                            anomalies.append({
                                'type': 'potential_duplicate',
                                'severity': 'high',
                                'entry_name': entry1['name'],
                                'related_entry': entry2['name'],
                                'amount': entry1['abs_amount'],
                                'description': f"معاملة مكررة محتملة: {entry1['abs_amount']:,.0f}",
                                'details': entry1
                            })
        
        return anomalies
    
    def _detect_account_anomalies(self, data):
        """Detect unusual account usage patterns"""
        anomalies = []
        
        # Unusual account combinations
        account_pairs = defaultdict(int)
        for entry in data:
            # Find related entries in same voucher
            related_entries = [e for e in data if e['voucher_no'] == entry['voucher_no']]
            
            if len(related_entries) == 2:  # Simple two-account transaction
                accounts = sorted([e['account'] for e in related_entries])
                pair_key = f"{accounts[0]}|{accounts[1]}"
                account_pairs[pair_key] += 1
        
        # Flag rare account combinations with high amounts
        rare_pairs = {k: v for k, v in account_pairs.items() if v == 1}
        for entry in data:
            related_entries = [e for e in data if e['voucher_no'] == entry['voucher_no']]
            if len(related_entries) == 2:
                accounts = sorted([e['account'] for e in related_entries])
                pair_key = f"{accounts[0]}|{accounts[1]}"
                
                if pair_key in rare_pairs and entry['abs_amount'] > 100000:
                    anomalies.append({
                        'type': 'unusual_account_combination',
                        'severity': 'medium',
                        'entry_name': entry['name'],
                        'account_pair': pair_key,
                        'amount': entry['abs_amount'],
                        'description': f"تركيبة حسابات غير عادية: {accounts[0]} ← {accounts[1]}",
                        'details': entry
                    })
        
        return anomalies
    
    def _detect_user_behavior_anomalies(self, data):
        """Detect unusual user behavior patterns"""
        anomalies = []
        
        # User transaction patterns
        user_stats = defaultdict(lambda: {
            'transactions': [],
            'total_amount': 0,
            'avg_amount': 0,
            'max_amount': 0,
            'accounts_used': set()
        })
        
        for entry in data:
            user = entry['owner']
            user_stats[user]['transactions'].append(entry)
            user_stats[user]['total_amount'] += entry['abs_amount']
            user_stats[user]['accounts_used'].add(entry['account'])
            if entry['abs_amount'] > user_stats[user]['max_amount']:
                user_stats[user]['max_amount'] = entry['abs_amount']
        
        # Calculate averages and detect anomalies
        for user, stats in user_stats.items():
            if len(stats['transactions']) < 3:
                continue
                
            stats['avg_amount'] = stats['total_amount'] / len(stats['transactions'])
            amounts = [t['abs_amount'] for t in stats['transactions']]
            
            if len(amounts) > 1:
                stdev = statistics.stdev(amounts)
                mean_amount = statistics.mean(amounts)
                
                # Flag transactions significantly above user's normal pattern
                for transaction in stats['transactions']:
                    if stdev > 0:
                        z_score = (transaction['abs_amount'] - mean_amount) / stdev
                        
                        if z_score > 2.5:  # Significantly above normal
                            anomalies.append({
                                'type': 'unusual_user_amount',
                                'severity': 'medium',
                                'entry_name': transaction['name'],
                                'user': user,
                                'amount': transaction['abs_amount'],
                                'user_avg': mean_amount,
                                'z_score': z_score,
                                'description': f"مبلغ غير عادي للمستخدم {user}: {transaction['abs_amount']:,.0f} (متوسطه: {mean_amount:,.0f})",
                                'details': transaction
                            })
        
        return anomalies
    
    def _ai_anomaly_detection(self, data):
        """AI-powered anomaly detection using advanced analysis"""
        anomalies = []
        
        try:
            # Use AI service if available
            from material_ledger.material_ledger.services.ai_service import get_ai_service
            
            ai_service = get_ai_service()
            if not ai_service.is_available():
                return self._statistical_ai_fallback(data)
            
            # Prepare data for AI analysis
            analysis_prompt = self._build_anomaly_prompt(data)
            
            # Get AI analysis
            ai_response = ai_service._call_deepseek(analysis_prompt) if hasattr(ai_service, '_call_deepseek') else None
            
            if ai_response:
                ai_anomalies = self._parse_ai_anomalies(ai_response, data)
                anomalies.extend(ai_anomalies)
            
        except Exception as e:
            frappe.log_error(f"AI Anomaly Detection Error: {str(e)}", "AI Anomaly Service")
            # Fallback to statistical methods
            anomalies.extend(self._statistical_ai_fallback(data))
        
        return anomalies
    
    def _build_anomaly_prompt(self, data):
        """Build prompt for AI anomaly detection"""
        # Summarize key statistics
        total_transactions = len(data)
        total_amount = sum(d['abs_amount'] for d in data)
        avg_amount = total_amount / total_transactions if total_transactions > 0 else 0
        
        # Get largest transactions
        largest_transactions = sorted(data, key=lambda x: x['abs_amount'], reverse=True)[:5]
        
        # Get account distribution
        account_counts = defaultdict(int)
        for d in data:
            account_counts[d['account']] += 1
        top_accounts = sorted(account_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        prompt = f"""
كمحلل مالي متخصص في اكتشاف الاحتيال والشذوذ المالي، قم بتحليل البيانات التالية:

📊 **إحصائيات عامة:**
- عدد المعاملات: {total_transactions:,}
- إجمالي المبالغ: {total_amount:,.0f}
- متوسط المبلغ: {avg_amount:,.0f}

💰 **أكبر المعاملات:**
{chr(10).join([f"- {t['posting_date']} | {t['account']} | {t['abs_amount']:,.0f} | {t['voucher_type']}" for t in largest_transactions[:3]])}

🏦 **أكثر الحسابات نشاطاً:**
{chr(10).join([f"- {acc}: {count} معاملة" for acc, count in top_accounts[:3]])}

🔍 **ابحث عن الأنماط التالية:**
1. معاملات مشبوهة أو غير عادية
2. أنماط قد تشير إلى احتيال
3. تسلسلات زمنية غريبة
4. مبالغ أو توقيتات غير منطقية
5. استخدام غير طبيعي للحسابات

🎯 **المطلوب:**
حدد أي شذوذ أو مخاطر محتملة مع:
- نوع الشذوذ
- مستوى الخطورة (منخفض/متوسط/عالي)
- السبب والتفسير
- التوصيات للتحقق

قدم النتائج بتنسيق JSON:
```json
{{
  "anomalies": [
    {{
      "type": "نوع الشذوذ",
      "severity": "عالي/متوسط/منخفض", 
      "description": "وصف المشكلة",
      "recommendation": "التوصية"
    }}
  ],
  "overall_risk": "عالي/متوسط/منخفض",
  "summary": "ملخص التحليل"
}}
```
"""
        return prompt
    
    def _parse_ai_anomalies(self, ai_response, data):
        """Parse AI response into structured anomalies"""
        anomalies = []
        
        try:
            import re
            json_match = re.search(r'```json\n(.*?)\n```', ai_response, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group(1))
                
                for ai_anomaly in ai_data.get('anomalies', []):
                    # Map AI anomaly to our format
                    anomaly = {
                        'type': 'ai_detected_anomaly',
                        'severity': ai_anomaly.get('severity', 'medium'),
                        'ai_type': ai_anomaly.get('type', 'unknown'),
                        'description': ai_anomaly.get('description', ''),
                        'recommendation': ai_anomaly.get('recommendation', ''),
                        'source': 'ai_analysis',
                        'details': ai_data
                    }
                    anomalies.append(anomaly)
                    
        except Exception as e:
            frappe.log_error(f"AI Anomaly Parsing Error: {str(e)}", "AI Anomaly Service")
        
        return anomalies
    
    def _statistical_ai_fallback(self, data):
        """Statistical fallback when AI is not available"""
        anomalies = []
        
        # Advanced statistical anomaly detection
        if len(data) < 10:
            return anomalies
        
        # Benford's Law analysis for fraud detection
        first_digits = []
        for entry in data:
            if entry['abs_amount'] > 0:
                first_digit = int(str(int(entry['abs_amount']))[0])
                first_digits.append(first_digit)
        
        if len(first_digits) > 50:  # Need sufficient data for Benford's law
            expected_benford = [30.1, 17.6, 12.5, 9.7, 7.9, 6.7, 5.8, 5.1, 4.6]  # Benford percentages
            actual_distribution = []
            
            for digit in range(1, 10):
                count = first_digits.count(digit)
                percentage = (count / len(first_digits)) * 100
                actual_distribution.append(percentage)
            
            # Calculate chi-square test statistic
            chi_square = sum((actual - expected)**2 / expected 
                           for actual, expected in zip(actual_distribution, expected_benford))
            
            if chi_square > 15.51:  # Critical value for 8 degrees of freedom at 95% confidence
                anomalies.append({
                    'type': 'benford_law_violation',
                    'severity': 'high',
                    'chi_square': chi_square,
                    'description': f"انتهاك قانون بنفورد (مؤشر احتيال محتمل) - قيمة كاي تربيع: {chi_square:.2f}",
                    'recommendation': "فحص شامل للمعاملات المالية - قد يدل على تلاعب في الأرقام"
                })
        
        return anomalies
    
    def generate_anomaly_report(self, anomalies):
        """
        Generate comprehensive anomaly detection report
        
        Args:
            anomalies: List of all detected anomalies
            
        Returns:
            dict: Comprehensive anomaly report
        """
        if not anomalies:
            return {
                "status": "clean",
                "total_anomalies": 0,
                "summary": "لم يتم اكتشاف أي شذوذ مالي",
                "risk_level": "منخفض"
            }
        
        # Categorize anomalies by type and severity
        by_type = defaultdict(list)
        by_severity = defaultdict(list)
        
        for anomaly in anomalies:
            by_type[anomaly['type']].append(anomaly)
            by_severity[anomaly.get('severity', 'medium')].append(anomaly)
        
        # Calculate overall risk level
        high_risk_count = len(by_severity['high'])
        medium_risk_count = len(by_severity['medium'])
        total_anomalies = len(anomalies)
        
        if high_risk_count > 5:
            overall_risk = "عالي جداً"
        elif high_risk_count > 2:
            overall_risk = "عالي"
        elif medium_risk_count > 10:
            overall_risk = "متوسط"
        elif total_anomalies > 0:
            overall_risk = "منخفض"
        else:
            overall_risk = "آمن"
        
        # Generate detailed analysis
        analysis = self._generate_anomaly_analysis(anomalies, by_type, by_severity)
        
        # Prioritize anomalies
        prioritized_anomalies = self._prioritize_anomalies(anomalies)
        
        # Generate recommendations
        recommendations = self._generate_anomaly_recommendations(by_type, by_severity)
        
        return {
            "status": "anomalies_detected",
            "total_anomalies": total_anomalies,
            "by_severity": {
                "high": len(by_severity['high']),
                "medium": len(by_severity['medium']),
                "low": len(by_severity['low'])
            },
            "by_type": {type_name: len(type_anomalies) for type_name, type_anomalies in by_type.items()},
            "overall_risk": overall_risk,
            "analysis": analysis,
            "prioritized_anomalies": prioritized_anomalies[:20],  # Top 20 for display
            "recommendations": recommendations,
            "generated_at": now(),
            "full_anomalies": anomalies  # For detailed investigation
        }
    
    def _generate_anomaly_analysis(self, anomalies, by_type, by_severity):
        """Generate detailed analysis of anomalies"""
        analysis = f"""
🚨 **تقرير اكتشاف الشذوذ المالي**

📊 **الإحصائيات العامة:**
- إجمالي الحالات المكتشفة: {len(anomalies)}
- مخاطر عالية: {len(by_severity['high'])}
- مخاطر متوسطة: {len(by_severity['medium'])}
- مخاطر منخفضة: {len(by_severity['low'])}

🔍 **أنواع الشذوذ المكتشفة:**
"""
        
        for anomaly_type, type_anomalies in by_type.items():
            type_names = {
                'unusual_amount': 'مبالغ غير عادية',
                'after_hours_transaction': 'معاملات بعد ساعات العمل',
                'weekend_transaction': 'معاملات نهاية الأسبوع',
                'rapid_sequence': 'معاملات متتابعة سريعة',
                'round_amount_pattern': 'نمط مبالغ مدورة',
                'identical_amounts': 'مبالغ متطابقة',
                'potential_duplicate': 'معاملات مكررة محتملة',
                'unusual_account_combination': 'تركيبات حسابات غير عادية',
                'unusual_user_amount': 'أنماط مستخدم غير عادية',
                'ai_detected_anomaly': 'شذوذ مكتشف بالذكاء الاصطناعي',
                'benford_law_violation': 'انتهاك قانون بنفورد'
            }
            
            type_name_ar = type_names.get(anomaly_type, anomaly_type)
            analysis += f"- {type_name_ar}: {len(type_anomalies)} حالة\n"
        
        analysis += f"""

⚠️ **أهم المخاطر المكتشفة:**
"""
        high_risk_types = [t for t, anomalies in by_type.items() if any(a.get('severity') == 'high' for a in anomalies)]
        
        for risk_type in high_risk_types[:3]:  # Top 3 high-risk types
            risk_count = len([a for a in by_type[risk_type] if a.get('severity') == 'high'])
            analysis += f"- {risk_type}: {risk_count} حالة عالية الخطورة\n"
        
        return analysis
    
    def _prioritize_anomalies(self, anomalies):
        """Prioritize anomalies by severity and potential impact"""
        # Define priority scores
        severity_scores = {'high': 100, 'medium': 50, 'low': 10}
        type_scores = {
            'potential_duplicate': 90,
            'benford_law_violation': 95,
            'rapid_sequence': 85,
            'unusual_amount': 70,
            'ai_detected_anomaly': 80
        }
        
        scored_anomalies = []
        for anomaly in anomalies:
            score = severity_scores.get(anomaly.get('severity', 'medium'), 50)
            score += type_scores.get(anomaly['type'], 30)
            
            # Boost score for high amounts
            if 'amount' in anomaly and anomaly['amount'] > 100000:
                score += 20
            
            anomaly['priority_score'] = score
            scored_anomalies.append(anomaly)
        
        # Sort by priority score
        return sorted(scored_anomalies, key=lambda x: x['priority_score'], reverse=True)
    
    def _generate_anomaly_recommendations(self, by_type, by_severity):
        """Generate specific recommendations based on anomaly types"""
        recommendations = []
        
        if 'potential_duplicate' in by_type:
            recommendations.append("🔍 **فحص المعاملات المكررة**: راجع المعاملات المكررة المحتملة وتأكد من صحتها")
        
        if 'benford_law_violation' in by_type:
            recommendations.append("🚨 **فحص شامل للاحتيال**: انتهاك قانون بنفورد يتطلب مراجعة شاملة للمعاملات")
        
        if 'after_hours_transaction' in by_type:
            recommendations.append("⏰ **مراجعة سياسات الوقت**: ضع ضوابط أكثر صرامة للمعاملات خارج ساعات العمل")
        
        if 'unusual_amount' in by_type:
            recommendations.append("💰 **صلاحيات الاعتماد**: طبق حدود اعتماد أكثر صرامة للمبالغ الكبيرة")
        
        if len(by_severity['high']) > 5:
            recommendations.append("🔒 **تعزيز الأمان**: عدد كبير من المخاطر العالية - راجع أنظمة الأمان والضوابط الداخلية")
        
        if not recommendations:
            recommendations.append("✅ **متابعة روتينية**: استمر في المراقبة المنتظمة للمحافظة على الجودة")
        
        return recommendations


# API Endpoints
@frappe.whitelist()
def start_anomaly_detection(company, filters=None):
    """API endpoint to start anomaly detection job"""
    if not filters:
        filters = {}
    if isinstance(filters, str):
        filters = json.loads(filters)
        
    from material_ledger.material_ledger.services.queue_service import queue_ai_analysis
    return queue_ai_analysis("anomaly_detection", company, filters)


@frappe.whitelist()
def get_anomaly_status(job_id):
    """API endpoint to get anomaly detection job status"""
    from material_ledger.material_ledger.services.queue_service import get_ai_job_status
    return get_ai_job_status(job_id)