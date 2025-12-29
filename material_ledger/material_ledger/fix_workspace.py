import frappe
import json

def execute():
    # 1. Delete the old conflicting Page if it exists
    if frappe.db.exists("Page", "material-ledger"):
        print("Found old conflicting Page 'material-ledger'. Deleting...")
        frappe.delete_doc("Page", "material-ledger", force=True)
        print("Deleted old Page.")
    
    # 2. Reload the new Page to ensure it's there
    print("Reloading Page: material-ledger-report...")
    try:
        frappe.reload_doc("material_ledger", "page", "material-ledger-report")
        print("Page reloaded.")
    except Exception as e:
        print(f"Error reloading page: {e}")

    # 3. Reload Workspace to get fresh state from file (if possible)
    print("Reloading Workspace: Material Ledger...")
    try:
        # This might fail if DB has conflict, but let's try
        frappe.reload_doc("material_ledger", "workspace", "Material Ledger")
        print("Workspace reloaded.")
    except Exception as e:
        print(f"Error reloading workspace (expected if conflict exists): {e}")

    # 4. Fix the Workspace content in DB
    ws = frappe.get_doc("Workspace", "Material Ledger")
    print(f"Workspace content (DB): {ws.content}")
    
    # Fix Child Tables (Links and Shortcuts)
    for link in ws.links:
        if link.link_to == "material-ledger":
            print("Updating Link child table...")
            link.link_to = "material-ledger-report"
            
    for shortcut in ws.shortcuts:
        if shortcut.link_to == "material-ledger":
            print("Updating Shortcut child table...")
            shortcut.link_to = "material-ledger-report"
        
        # Fix doc_view validation error
        if shortcut.type == "Page" and shortcut.doc_view == "Page":
            print("Clearing invalid doc_view for Page shortcut...")
            shortcut.doc_view = ""

    # Force update content if it's still old
    content_data = json.loads(ws.content)
    updated = False
    for item in content_data:
        if item.get("type") == "shortcut" and item.get("data", {}).get("shortcut_name") == "Material Ledger":
            current_link = item["data"].get("link_to")
            current_view = item["data"].get("doc_view")
            
            if current_link != "material-ledger-report":
                item["data"]["link_to"] = "material-ledger-report"
                updated = True
                print("Updated shortcut link in content.")
            
            if current_view == "Page":
                item["data"]["doc_view"] = ""
                updated = True
                print("Cleared invalid doc_view in content.")

    if updated:
        ws.content = json.dumps(content_data)
        
    try:
        ws.save()
        print("Workspace saved with updated content.")
    except frappe.NameError:
        print("NameError during save - conflict might still persist in cache or DB.")
        # Try to force update via SQL as last resort
        frappe.db.set_value("Workspace", "Material Ledger", "content", ws.content)
        # Also update child tables via SQL if needed
        print("Forced update via SQL.")
    except frappe.LinkValidationError as e:
        print(f"LinkValidationError: {e}")
        # If validation fails, force update SQL for child tables
        frappe.db.sql("""UPDATE `tabWorkspace Link` SET link_to = 'material-ledger-report' WHERE parent = 'Material Ledger' AND link_to = 'material-ledger'""")
        frappe.db.sql("""UPDATE `tabWorkspace Shortcut` SET link_to = 'material-ledger-report', doc_view = '' WHERE parent = 'Material Ledger' AND link_to = 'material-ledger'""")
        frappe.db.set_value("Workspace", "Material Ledger", "content", ws.content)
        print("Forced update via SQL for links and content.")
    except frappe.ValidationError as e:
        print(f"ValidationError: {e}")
        # Force update via SQL since we know what we are doing
        frappe.db.sql("""UPDATE `tabWorkspace Shortcut` SET link_to = 'material-ledger-report', doc_view = '' WHERE parent = 'Material Ledger'""")
        frappe.db.set_value("Workspace", "Material Ledger", "content", ws.content)
        print("Forced update via SQL due to validation error.")

    frappe.db.commit()
