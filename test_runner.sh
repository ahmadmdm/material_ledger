#!/bin/bash
# AI Integration Test Runner
# Script to test AI integration in proper Frappe environment

echo "🤖 AI Integration Test for Material Ledger"
echo "=========================================="
echo "Testing in Frappe Environment..."

cd /home/ahmad/frp

# Check if Frappe is available
if [ ! -d "apps/frappe" ]; then
    echo "❌ Frappe not found. Please run from Frappe directory."
    exit 1
fi

# Check if bench is available
if ! command -v bench &> /dev/null; then
    echo "❌ Bench command not found. Please install Frappe bench."
    exit 1
fi

echo "✅ Frappe environment detected"

# Run the Frappe-based test
echo ""
echo "🔄 Running AI integration test in Frappe console..."

bench console << 'EOF'
try:
    exec(open("apps/material_ledger/test_frappe_ai.py").read())
    print("\n✅ AI Integration test completed successfully!")
except Exception as e:
    print(f"\n❌ AI Integration test failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    exit()
EOF

echo ""
echo "📋 Test completed. Check output above for results."
echo ""
echo "🔧 Manual test instructions:"
echo "1. Run: cd /home/ahmad/frp && bench console"
echo "2. Execute: exec(open('apps/material_ledger/test_frappe_ai.py').read())"
echo ""
echo "📖 For production deployment:"
echo "1. bench start"
echo "2. Navigate to: http://localhost:8000/app/ai-dashboard"
echo "3. Test AI features with real data"