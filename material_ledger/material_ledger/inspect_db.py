
import frappe

def inspect_db():
    print("Inspecting Workspace 'Material Ledger' in DB...")
    
    # Check Parent
    ws = frappe.db.get_value("Workspace", "Material Ledger", "content")
    print(f"Content: {ws}")
    
    # Check Shortcuts table
    shortcuts = frappe.db.sql("""
        SELECT label, type, link_to, doc_view 
        FROM `tabWorkspace Shortcut` 
        WHERE parent = 'Material Ledger'
    """, as_dict=True)
    
    print("\nShortcuts (DB Table):")
    for s in shortcuts:
        print(f" - Label: {s.label}, Type: {s.type}, Link To: {s.link_to}, Doc View: '{s.doc_view}'")

    # Check Links table
    links = frappe.db.sql("""
        SELECT label, type, link_to, link_type 
        FROM `tabWorkspace Link` 
        WHERE parent = 'Material Ledger'
    """, as_dict=True)
    
    print("\nLinks (DB Table):")
    for l in links:
        print(f" - Label: {l.label}, Type: {l.type}, Link To: {l.link_to}, Link Type: {l.link_type}")

inspect_db()
