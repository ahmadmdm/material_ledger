#!/usr/bin/env python3
"""
Create AI Dashboard Page in Frappe
Run this from bench console:
>>> exec(open("apps/material_ledger/create_dashboard_page.py").read())
"""

import frappe

def create_ai_dashboard_page():
    """Create AI Dashboard page if it doesn't exist"""
    
    print("🤖 Creating AI Dashboard page...")
    
    # Check if page already exists
    if frappe.db.exists("Page", "AI Dashboard"):
        print("✅ AI Dashboard page already exists")
        return True
    
    try:
        # Create the page document
        page_doc = frappe.get_doc({
            "doctype": "Page",
            "page_name": "ai-dashboard",
            "title": "AI Financial Dashboard",
            "module": "Material Ledger", 
            "standard": "Yes",
            "description": "AI-powered interactive dashboard for financial analysis",
            "roles": [
                {"role": "Accounts Manager"},
                {"role": "System Manager"},
                {"role": "Accounts User"}
            ]
        })
        
        page_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"✅ AI Dashboard page created successfully: {page_doc.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating AI Dashboard page: {str(e)}")
        return False

def verify_ai_system():
    """Verify that AI system components are properly set up"""
    
    print("\n🔍 Verifying AI System Components...")
    
    # Check Page
    if frappe.db.exists("Page", "AI Dashboard"):
        print("✅ AI Dashboard page exists")
    else:
        print("❌ AI Dashboard page missing")
    
    # Check DocTypes
    doctypes = ["AI Job Queue", "AI Result Cache"]
    for doctype in doctypes:
        if frappe.db.exists("DocType", doctype):
            print(f"✅ {doctype} DocType exists")
        else:
            print(f"❌ {doctype} DocType missing")
    
    # Check API endpoints
    try:
        from material_ledger.material_ledger.api import get_financial_health_score
        print("✅ AI API endpoints available")
    except ImportError as e:
        print(f"❌ AI API endpoints error: {e}")
    
    return True

if __name__ == "__main__":
    # Auto-run if executed in console
    create_ai_dashboard_page()
    verify_ai_system()
    
    print("\n🎯 Next steps:")
    print("1. Navigate to: http://localhost:8000/app/ai-dashboard") 
    print("2. Test AI Dashboard functionality")
    print("3. Create AI analysis jobs")
    
# Auto-execute in console
create_ai_dashboard_page()
verify_ai_system()