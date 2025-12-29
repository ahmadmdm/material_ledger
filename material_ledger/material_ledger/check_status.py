
import frappe
import json

def check_status():
    print("Checking Page 'material-ledger-report'...")
    if frappe.db.exists("Page", "material-ledger-report"):
        print("EXISTS: Page 'material-ledger-report'")
        page = frappe.get_doc("Page", "material-ledger-report")
        print(f"Page Title: {page.title}")
    else:
        print("MISSING: Page 'material-ledger-report'")

    print("\nChecking Page 'material-ledger' (Old)...")
    if frappe.db.exists("Page", "material-ledger"):
        print("EXISTS: Page 'material-ledger' (Should be deleted!)")
    else:
        print("GOOD: Page 'material-ledger' does not exist.")

    print("\nChecking Workspace 'Material Ledger'...")
    if frappe.db.exists("Workspace", "Material Ledger"):
        ws = frappe.get_doc("Workspace", "Material Ledger")
        print(f"Workspace found. Content length: {len(ws.content)}")
        
        # Check Shortcuts
        print("Shortcuts:")
        for s in ws.shortcuts:
            print(f" - Label: {s.label}, Type: {s.type}, Link To: {s.link_to}, Doc View: '{s.doc_view}'")
            
        # Check Content JSON
        try:
            content = json.loads(ws.content)
            print("\nContent JSON Shortcuts:")
            for item in content:
                if item.get("type") == "shortcut":
                    data = item.get("data", {})
                    print(f" - Name: {data.get('shortcut_name')}, Link To: {data.get('link_to')}, Doc View: '{data.get('doc_view')}'")
        except Exception as e:
            print(f"Error parsing content JSON: {e}")
            
    else:
        print("MISSING: Workspace 'Material Ledger'")

check_status()
