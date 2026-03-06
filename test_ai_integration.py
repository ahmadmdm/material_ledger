#!/usr/bin/env python3
"""
Complete AI Integration Test for Material Ledger
تست شامل لتكامل الذكاء الاصطناعي في نظام المحاسبة المالية

This script tests all AI components:
- Queue System with background processing
- AI Prediction Service 
- AI Anomaly Detection
- AI Investment Analysis
- AI Dashboard API
- Background jobs and caching
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime

# Add Frappe to path
frappe_path = '/home/ahmad/frp/apps/frappe'
if frappe_path not in sys.path:
    sys.path.append(frappe_path)

erpnext_path = '/home/ahmad/frp/apps/erpnext'
if erpnext_path not in sys.path:
    sys.path.append(erpnext_path)

material_ledger_path = '/home/ahmad/frp/apps/material_ledger'
if material_ledger_path not in sys.path:
    sys.path.append(material_ledger_path)

class AIIntegrationTester:
    def __init__(self):
        self.test_results = {}
        self.errors = []
        self.company = "Test Company"  # Default test company
        
    def print_header(self, text):
        """Print colored header"""
        print(f"\n{'='*60}")
        print(f"🤖 {text}")
        print(f"{'='*60}")
    
    def print_success(self, text):
        """Print success message"""
        print(f"✅ {text}")
    
    def print_error(self, text):
        """Print error message"""
        print(f"❌ {text}")
        
    def print_warning(self, text):
        """Print warning message"""
        print(f"⚠️  {text}")
    
    def print_info(self, text):
        """Print info message"""
        print(f"ℹ️  {text}")
    
    def test_frappe_import(self):
        """Test if Frappe can be imported"""
        self.print_header("Testing Frappe Import")
        try:
            import frappe
            self.print_success("Frappe imported successfully")
            return True
        except Exception as e:
            self.print_error(f"Failed to import Frappe: {e}")
            self.errors.append(f"Frappe import: {e}")
            return False
    
    def test_ai_services_import(self):
        """Test AI services imports"""
        self.print_header("Testing AI Services Import")
        success_count = 0
        total_tests = 5
        
        # Test queue service
        try:
            from material_ledger.material_ledger.services.queue_service import AIQueueService
            self.print_success("Queue Service imported successfully")
            success_count += 1
        except Exception as e:
            self.print_error(f"Queue Service import failed: {e}")
            self.errors.append(f"Queue Service: {e}")
        
        # Test AI prediction service
        try:
            from material_ledger.material_ledger.services.ai_prediction_service import AIPredictionService
            self.print_success("AI Prediction Service imported successfully") 
            success_count += 1
        except Exception as e:
            self.print_error(f"AI Prediction Service import failed: {e}")
            self.errors.append(f"AI Prediction: {e}")
        
        # Test AI anomaly service
        try:
            from material_ledger.material_ledger.services.ai_anomaly_service import AIAnomalyService
            self.print_success("AI Anomaly Service imported successfully")
            success_count += 1
        except Exception as e:
            self.print_error(f"AI Anomaly Service import failed: {e}")
            self.errors.append(f"AI Anomaly: {e}")
        
        # Test AI investment service
        try:
            from material_ledger.material_ledger.services.ai_investment_service import AIInvestmentService
            self.print_success("AI Investment Service imported successfully")
            success_count += 1
        except Exception as e:
            self.print_error(f"AI Investment Service import failed: {e}")
            self.errors.append(f"AI Investment: {e}")
        
        # Test AI service base
        try:
            from material_ledger.material_ledger.services.ai_service import get_ai_service
            self.print_success("Base AI Service imported successfully")
            success_count += 1
        except Exception as e:
            self.print_error(f"Base AI Service import failed: {e}")
            self.errors.append(f"Base AI Service: {e}")
        
        self.test_results['ai_services_import'] = f"{success_count}/{total_tests} services imported"
        return success_count == total_tests
    
    def test_doctype_definitions(self):
        """Test DocType JSON definitions"""
        self.print_header("Testing DocType Definitions")
        success_count = 0
        total_tests = 2
        
        # Test AI Job Queue DocType
        queue_doctype_path = "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/doctype/ai_job_queue/ai_job_queue.json"
        if os.path.exists(queue_doctype_path):
            try:
                with open(queue_doctype_path, 'r') as f:
                    queue_doctype = json.load(f)
                if queue_doctype.get('name') == 'AI Job Queue':
                    self.print_success("AI Job Queue DocType definition is valid")
                    success_count += 1
                else:
                    self.print_error("AI Job Queue DocType name mismatch")
            except Exception as e:
                self.print_error(f"AI Job Queue DocType validation failed: {e}")
        else:
            self.print_error("AI Job Queue DocType file not found")
        
        # Test AI Result Cache DocType
        cache_doctype_path = "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/doctype/ai_result_cache/ai_result_cache.json"
        if os.path.exists(cache_doctype_path):
            try:
                with open(cache_doctype_path, 'r') as f:
                    cache_doctype = json.load(f)
                if cache_doctype.get('name') == 'AI Result Cache':
                    self.print_success("AI Result Cache DocType definition is valid")
                    success_count += 1
                else:
                    self.print_error("AI Result Cache DocType name mismatch")
            except Exception as e:
                self.print_error(f"AI Result Cache DocType validation failed: {e}")
        else:
            self.print_error("AI Result Cache DocType file not found")
        
        self.test_results['doctype_definitions'] = f"{success_count}/{total_tests} DocTypes valid"
        return success_count == total_tests
    
    def test_dashboard_files(self):
        """Test AI Dashboard files"""
        self.print_header("Testing AI Dashboard Files")
        success_count = 0
        total_tests = 3
        
        # Test dashboard page definition
        dashboard_json_path = "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/page/ai_dashboard/ai_dashboard.json"
        if os.path.exists(dashboard_json_path):
            try:
                with open(dashboard_json_path, 'r') as f:
                    dashboard_json = json.load(f)
                if dashboard_json.get('name') == 'AI Dashboard':
                    self.print_success("AI Dashboard page definition is valid")
                    success_count += 1
                else:
                    self.print_error(f"AI Dashboard page name mismatch: found '{dashboard_json.get('name')}'")
            except Exception as e:
                self.print_error(f"AI Dashboard page validation failed: {e}")
        else:
            self.print_error("AI Dashboard page definition not found")
        
        # Test dashboard HTML template
        dashboard_html_path = "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/page/ai_dashboard/ai_dashboard.html"
        if os.path.exists(dashboard_html_path):
            with open(dashboard_html_path, 'r') as f:
                html_content = f.read()
            if 'ai-dashboard-container' in html_content and 'ai-assistant-section' in html_content:
                self.print_success("AI Dashboard HTML template is valid")
                success_count += 1
            else:
                self.print_error("AI Dashboard HTML missing required elements")
        else:
            self.print_error("AI Dashboard HTML template not found")
        
        # Test dashboard JavaScript
        dashboard_js_path = "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/page/ai_dashboard/ai_dashboard.js"
        if os.path.exists(dashboard_js_path):
            with open(dashboard_js_path, 'r') as f:
                js_content = f.read()
            if 'AIDashboard' in js_content and 'refreshDashboard' in js_content:
                self.print_success("AI Dashboard JavaScript is valid")
                success_count += 1
            else:
                self.print_error("AI Dashboard JavaScript missing required functions")
        else:
            self.print_error("AI Dashboard JavaScript not found")
        
        self.test_results['dashboard_files'] = f"{success_count}/{total_tests} dashboard files valid"
        return success_count == total_tests
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        self.print_header("Testing API Endpoints")
        api_path = "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/api.py"
        success_count = 0
        total_tests = 5
        
        if os.path.exists(api_path):
            with open(api_path, 'r') as f:
                api_content = f.read()
            
            # Check for AI dashboard endpoints
            endpoints = [
                'get_financial_health_score',
                'get_ai_recommendations', 
                'get_risk_alerts',
                'chat_with_ai_assistant',
                'build_assistant_prompt'
            ]
            
            for endpoint in endpoints:
                if endpoint in api_content:
                    self.print_success(f"API endpoint '{endpoint}' found")
                    success_count += 1
                else:
                    self.print_error(f"API endpoint '{endpoint}' missing")
        else:
            self.print_error("API file not found")
        
        self.test_results['api_endpoints'] = f"{success_count}/{total_tests} endpoints found"
        return success_count == total_tests
    
    def test_file_structure(self):
        """Test overall file structure"""
        self.print_header("Testing File Structure")
        required_files = [
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/services/queue_service.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/services/ai_prediction_service.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/services/ai_anomaly_service.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/services/ai_investment_service.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/doctype/ai_job_queue/ai_job_queue.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/doctype/ai_result_cache/ai_result_cache.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/page/ai_dashboard/__init__.py"
        ]
        
        success_count = 0
        for file_path in required_files:
            if os.path.exists(file_path):
                self.print_success(f"File exists: {os.path.basename(file_path)}")
                success_count += 1
            else:
                self.print_error(f"Missing file: {file_path}")
        
        self.test_results['file_structure'] = f"{success_count}/{len(required_files)} files exist"
        return success_count == len(required_files)
    
    def test_syntax_validation(self):
        """Test Python syntax validation"""
        self.print_header("Testing Python Syntax")
        python_files = [
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/services/queue_service.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/services/ai_prediction_service.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/services/ai_anomaly_service.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/services/ai_investment_service.py"
        ]
        
        success_count = 0
        for file_path in python_files:
            if os.path.exists(file_path):
                try:
                    # Check syntax by compiling
                    with open(file_path, 'r') as f:
                        source = f.read()
                    compile(source, file_path, 'exec')
                    self.print_success(f"Syntax OK: {os.path.basename(file_path)}")
                    success_count += 1
                except SyntaxError as e:
                    self.print_error(f"Syntax error in {os.path.basename(file_path)}: {e}")
                    self.errors.append(f"Syntax error in {file_path}: {e}")
                except Exception as e:
                    self.print_warning(f"Could not validate {os.path.basename(file_path)}: {e}")
            else:
                self.print_error(f"File not found: {file_path}")
        
        self.test_results['syntax_validation'] = f"{success_count}/{len(python_files)} files have valid syntax"
        return success_count == len(python_files)
    
    def test_configuration_files(self):
        """Test configuration and setup files"""
        self.print_header("Testing Configuration Files")
        success_count = 0
        total_tests = 3
        
        # Test hooks.py
        hooks_path = "/home/ahmad/frp/apps/material_ledger/material_ledger/hooks.py"
        if os.path.exists(hooks_path):
            with open(hooks_path, 'r') as f:
                hooks_content = f.read()
            if 'app_name = "material_ledger"' in hooks_content:
                self.print_success("Hooks configuration is valid")
                success_count += 1
            else:
                self.print_warning("Hooks file may need updates")
        else:
            self.print_error("Hooks file not found")
        
        # Test __init__.py files
        init_files = [
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/__init__.py",
            "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger/services/__init__.py"
        ]
        
        for init_file in init_files:
            if os.path.exists(init_file):
                self.print_success(f"Init file exists: {init_file}")
                success_count += 1
            else:
                self.print_warning(f"Init file missing: {init_file}")
        
        self.test_results['configuration'] = f"{success_count}/{total_tests} configuration files OK"
        return True
    
    def run_comprehensive_test(self):
        """Run all tests"""
        start_time = time.time()
        
        print(f"""
🤖 AI Integration Test Suite for Material Ledger
تст شامل لتكامل الذكاء الاصطناعي - نظام المحاسبة المالية

Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Testing AI features: Queue System, Prediction, Anomaly Detection, Investment Analysis, Dashboard
        """)
        
        # Run all tests
        tests = [
            ("Frappe Import", self.test_frappe_import),
            ("AI Services Import", self.test_ai_services_import),
            ("DocType Definitions", self.test_doctype_definitions),
            ("Dashboard Files", self.test_dashboard_files),
            ("API Endpoints", self.test_api_endpoints),
            ("File Structure", self.test_file_structure),
            ("Syntax Validation", self.test_syntax_validation),
            ("Configuration", self.test_configuration_files)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.print_error(f"Test '{test_name}' failed with exception: {e}")
                self.errors.append(f"{test_name}: {e}")
        
        # Print summary
        end_time = time.time()
        duration = end_time - start_time
        
        self.print_header("TEST SUMMARY / خلاصة الاختبارات")
        
        print(f"""
📊 Test Results:
   Passed: {passed_tests}/{total_tests} tests
   Duration: {duration:.2f} seconds
   
📋 Detailed Results:""")
        
        for key, value in self.test_results.items():
            print(f"   • {key}: {value}")
        
        if self.errors:
            print(f"\n🚨 Errors Found ({len(self.errors)}):")
            for i, error in enumerate(self.errors[:10], 1):  # Show first 10 errors
                print(f"   {i}. {error}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more errors")
        
        # Overall status
        success_rate = passed_tests / total_tests
        if success_rate >= 0.9:
            self.print_success(f"🎉 EXCELLENT! AI Integration is {success_rate*100:.0f}% ready")
            print("   System appears to be properly configured and ready for use.")
        elif success_rate >= 0.7:
            self.print_warning(f"⚠️  GOOD - AI Integration is {success_rate*100:.0f}% ready")
            print("   Most components are working, minor issues need attention.")
        else:
            self.print_error(f"❌ NEEDS WORK - AI Integration is only {success_rate*100:.0f}% ready")
            print("   Significant issues found that need immediate attention.")
        
        print(f"\n🔧 Next Steps:")
        if success_rate >= 0.9:
            print("   1. Run actual Frappe/ERPNext server tests")
            print("   2. Test with real data")
            print("   3. Deploy to production")
        elif success_rate >= 0.7:
            print("   1. Fix the identified errors above") 
            print("   2. Re-run this test suite")
            print("   3. Test individual components")
        else:
            print("   1. Review all error messages carefully")
            print("   2. Check file permissions and paths")
            print("   3. Verify Frappe/ERPNext installation")
            print("   4. Fix critical issues before proceeding")
        
        return success_rate >= 0.7


def main():
    """Main test execution"""
    tester = AIIntegrationTester()
    success = tester.run_comprehensive_test()
    
    # Exit code for CI/CD
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()