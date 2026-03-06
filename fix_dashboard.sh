#!/bin/bash
# Fix AI Dashboard problems
echo "🤖 Fixing AI Dashboard issues..."

cd /home/ahmad/frp

# 1. Build the app to ensure pages are included
echo "📦 Building material_ledger app..."
bench build --app material_ledger

# 2. Clear cache
echo "🧹 Clearing cache..."
bench clear-cache

# 3. Restart all processes
echo "🔄 Restarting system..."
bench restart

echo ""
echo "✅ AI Dashboard fixes completed!"
echo ""
echo "🌐 Please try accessing: http://localhost:8000/app/ai-dashboard"
echo ""
echo "📋 If page still not found, run these commands:"
echo "   1. cd /home/ahmad/frp"  
echo "   2. bench console"
echo "   3. Paste this:"
echo "      page = frappe.get_doc({'doctype': 'Page', 'page_name': 'ai-dashboard', 'title': 'AI Dashboard', 'module': 'Material Ledger'})"
echo "      page.insert()"
echo "      frappe.db.commit()"
echo "      exit()"