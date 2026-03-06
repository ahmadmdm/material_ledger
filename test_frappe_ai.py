"""
Frappe-based AI Integration Test
تست تكامل الذكاء الاصطناعي من داخل بيئة Frappe

Run this from bench console:
cd /home/ahmad/frp && bench console
>>> exec(open("apps/material_ledger/test_frappe_ai.py").read())
"""

import frappe
import json
import os
from datetime import datetime

def test_ai_integration():
    """Test AI integration from within Frappe environment"""
    
    print(f"""
🤖 AI Integration Test - Frappe Environment
تست تكامل الذكاء الاصطناعي - بيئة Frappe
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
    
    results = {}
    errors = []
    
    # Test 1: AI Service Import
    print("🔍 Testing AI Services...")
    try:
        from material_ledger.material_ledger.services.queue_service import AIQueueService
        from material_ledger.material_ledger.services.ai_prediction_service import AIPredictionService
        from material_ledger.material_ledger.services.ai_anomaly_service import AIAnomalyService
        from material_ledger.material_ledger.services.ai_investment_service import AIInvestmentService
        from material_ledger.material_ledger.services.ai_service import get_ai_service
        
        results['ai_services'] = "✅ All AI services imported successfully"
        print("   ✅ AI Services imported successfully")
        
        # Test AI service instance
        ai_service = get_ai_service()
        if ai_service:
            results['ai_service_instance'] = "✅ AI service instance created"
            print(f"   ✅ AI Service available: {ai_service.is_available()}")
        else:
            results['ai_service_instance'] = "❌ AI service instance failed"
            
    except Exception as e:
        results['ai_services'] = f"❌ AI services import failed: {e}"
        errors.append(f"AI Services: {e}")
        print(f"   ❌ AI services import failed: {e}")
    
    # Test 2: DocType Creation/Access
    print("🗃️  Testing DocTypes...")
    try:
        # Test if AI Job Queue DocType exists
        if frappe.db.exists("DocType", "AI Job Queue"):
            results['ai_job_queue_doctype'] = "✅ AI Job Queue DocType exists"
            print("   ✅ AI Job Queue DocType exists")
            
            # Try to create a test job
            test_job = frappe.get_doc({
                'doctype': 'AI Job Queue',
                'service_type': 'prediction',
                'company': 'Test Company',
                'status': 'pending',
                'parameters': '{"test": true}'
            })
            test_job.insert(ignore_permissions=True)
            
            # Clean up
            test_job.delete(ignore_permissions=True)
            
            results['ai_job_creation'] = "✅ AI Job creation/deletion works"
            print("   ✅ AI Job creation/deletion works")
            
        else:
            results['ai_job_queue_doctype'] = "❌ AI Job Queue DocType missing"
            
        # Test AI Result Cache DocType
        if frappe.db.exists("DocType", "AI Result Cache"):
            results['ai_cache_doctype'] = "✅ AI Result Cache DocType exists"  
            print("   ✅ AI Result Cache DocType exists")
        else:
            results['ai_cache_doctype'] = "❌ AI Result Cache DocType missing"
            
    except Exception as e:
        results['doctype_test'] = f"❌ DocType test failed: {e}"
        errors.append(f"DocTypes: {e}")
        print(f"   ❌ DocType test failed: {e}")
    
    # Test 3: API Endpoints
    print("🌐 Testing API Endpoints...")
    try:
        # Test importing API methods
        from material_ledger.material_ledger.api import (
            get_financial_health_score,
            get_ai_recommendations,
            get_risk_alerts,
            chat_with_ai_assistant
        )
        
        results['api_import'] = "✅ API endpoints imported successfully"
        print("   ✅ API endpoints imported successfully")
        
        # Test with a sample company if it exists
        companies = frappe.get_all("Company", limit=1)
        if companies:
            test_company = companies[0].name
            
            # Test health score (lightweight)
            try:
                health_result = get_financial_health_score(test_company)
                if isinstance(health_result, dict) and 'score' in health_result:
                    results['health_score_api'] = "✅ Health score API working"
                    print(f"   ✅ Health score API returned score: {health_result.get('score', 'N/A')}")
                else:
                    results['health_score_api'] = "⚠️ Health score API returned unexpected format"
            except Exception as e:
                results['health_score_api'] = f"❌ Health score API failed: {e}"
                print(f"   ❌ Health score API failed: {e}")
        else:
            results['api_test'] = "⚠️ No companies found for API testing"
            print("   ⚠️ No companies found for API testing")
            
    except Exception as e:
        results['api_endpoints'] = f"❌ API endpoint test failed: {e}"
        errors.append(f"API: {e}")
        print(f"   ❌ API endpoint test failed: {e}")
    
    # Test 4: Queue Service Functionality 
    print("⚙️ Testing Queue Service...")
    try:
        queue_service = AIQueueService()
        
        # Test queue service methods exist
        required_methods = ['create_ai_job', 'process_ai_job', 'get_job_status']
        missing_methods = []
        
        for method in required_methods:
            if not hasattr(queue_service, method):
                missing_methods.append(method)
        
        if not missing_methods:
            results['queue_methods'] = "✅ Queue service methods available"
            print("   ✅ All queue service methods available")
        else:
            results['queue_methods'] = f"❌ Missing methods: {missing_methods}"
            print(f"   ❌ Missing queue methods: {missing_methods}")
            
    except Exception as e:
        results['queue_service'] = f"❌ Queue service test failed: {e}"
        errors.append(f"Queue: {e}")
        print(f"   ❌ Queue service test failed: {e}")
    
    # Test 5: File Structure
    print("📁 Testing File Structure...")
    try:
        app_path = "/home/ahmad/frp/apps/material_ledger/material_ledger/material_ledger"
        
        required_files = [
            f"{app_path}/services/queue_service.py",
            f"{app_path}/services/ai_prediction_service.py", 
            f"{app_path}/services/ai_anomaly_service.py",
            f"{app_path}/services/ai_investment_service.py",
            f"{app_path}/page/ai_dashboard/ai_dashboard.html",
            f"{app_path}/page/ai_dashboard/ai_dashboard.js",
            f"{app_path}/doctype/ai_job_queue/ai_job_queue.json",
            f"{app_path}/doctype/ai_result_cache/ai_result_cache.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(os.path.basename(file_path))
        
        if not missing_files:
            results['file_structure'] = "✅ All required files present"
            print("   ✅ All required files present")
        else:
            results['file_structure'] = f"❌ Missing files: {missing_files}"
            print(f"   ❌ Missing files: {missing_files}")
            
    except Exception as e:
        results['file_structure'] = f"❌ File structure test failed: {e}"
        errors.append(f"Files: {e}")
        
    # Test 6: Dashboard Page
    print("🖥️  Testing Dashboard Page...")
    try:
        # Check if page is accessible via Frappe
        if frappe.db.exists("Page", "AI Dashboard"):
            results['dashboard_page'] = "✅ AI Dashboard page exists in database"
            print("   ✅ AI Dashboard page exists in database")
            
            # Check page document
            page_doc = frappe.get_doc("Page", "AI Dashboard")
            if page_doc.module == "Material Ledger":
                results['dashboard_module'] = "✅ Dashboard assigned to correct module"
                print("   ✅ Dashboard assigned to Material Ledger module")
            else:
                results['dashboard_module'] = f"❌ Wrong module: {page_doc.module}"
                
        else:
            results['dashboard_page'] = "❌ AI Dashboard page not found in database"
            print("   ❌ AI Dashboard page not found in database")
            
    except Exception as e:
        results['dashboard_page'] = f"❌ Dashboard test failed: {e}"
        errors.append(f"Dashboard: {e}")
        print(f"   ❌ Dashboard test failed: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY / خلاصة النتائج")
    print(f"{'='*60}")
    
    success_count = sum(1 for result in results.values() if result.startswith("✅"))
    total_tests = len(results)
    success_rate = success_count / total_tests if total_tests > 0 else 0
    
    print(f"\n📈 Results: {success_count}/{total_tests} tests passed ({success_rate*100:.0f}%)")
    
    for key, value in results.items():
        print(f"   {key}: {value}")
    
    if errors:
        print(f"\n🚨 Errors ({len(errors)}):")
        for i, error in enumerate(errors[:5], 1):
            print(f"   {i}. {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")
    
    # Recommendations
    print(f"\n🎯 Recommendations:")
    if success_rate >= 0.8:
        print("   🎉 EXCELLENT! AI system is ready for production use")
        print("   📋 Next steps: Set up API keys, configure AI endpoints, create test data")
    elif success_rate >= 0.6:
        print("   ✅ GOOD! System is mostly ready, address remaining issues")
        print("   🔧 Focus on fixing the failed tests above")
    else:
        print("   ⚠️ NEEDS ATTENTION! Critical issues need to be resolved")
        print("   🚨 Review errors carefully and fix before proceeding")
    
    return success_rate >= 0.6

# Auto-run if executed directly in console
if __name__ == "__main__" or "frappe" in globals():
    test_ai_integration()