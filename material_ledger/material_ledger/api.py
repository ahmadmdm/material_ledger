import frappe
from frappe import _
from frappe.utils import flt, getdate

@frappe.whitelist()
def get_ledger_entries(company, from_date, to_date, account=None, party_type=None, party=None, cost_center=None, project=None):
    """
    Fetch GL Entries with running balance.
    """
    if not company:
        frappe.throw(_("Company is required"))

    filters = {
        "company": company,
        "posting_date": ["between", [from_date, to_date]],
        "is_cancelled": 0
    }

    if account:
        filters["account"] = account
    if party_type and party:
        filters["party_type"] = party_type
        filters["party"] = party
    if cost_center:
        filters["cost_center"] = cost_center
    if project:
        filters["project"] = project

    # Fetch opening balance if account is specified
    opening_balance = 0.0
    if account:
        opening_balance = get_opening_balance(company, account, from_date, party_type, party, cost_center, project)

    gl_entries = frappe.get_all(
        "GL Entry",
        fields=["name", "posting_date", "account", "party_type", "party", "debit", "credit", "voucher_type", "voucher_no", "remarks", "cost_center", "project", "against", "is_opening", "transaction_date", "due_date"],
        filters=filters,
        order_by="posting_date asc, creation asc",
        limit_page_length=None
    )

    data = []
    balance = opening_balance

    # Add opening balance row
    if account:
        data.append({
            "posting_date": from_date,
            "account": account,
            "remarks": _("Opening Balance"),
            "debit": 0,
            "credit": 0,
            "balance": balance,
            "is_opening": True
        })

    for entry in gl_entries:
        balance += flt(entry.debit) - flt(entry.credit)
        entry["balance"] = balance
        data.append(entry)

    return data

def get_opening_balance(company, account, from_date, party_type=None, party=None, cost_center=None, project=None):
    conditions = []
    values = {
        "company": company,
        "account": account,
        "from_date": from_date
    }

    if party_type and party:
        conditions.append("AND party_type = %(party_type)s AND party = %(party)s")
        values["party_type"] = party_type
        values["party"] = party
    
    if cost_center:
        conditions.append("AND cost_center = %(cost_center)s")
        values["cost_center"] = cost_center
        
    if project:
        conditions.append("AND project = %(project)s")
        values["project"] = project

    query = """
        SELECT SUM(debit) - SUM(credit)
        FROM `tabGL Entry`
        WHERE company = %(company)s
        AND account = %(account)s
        AND posting_date < %(from_date)s
        AND is_cancelled = 0
        {conditions}
    """.format(conditions=" ".join(conditions))

    result = frappe.db.sql(query, values)

    return flt(result[0][0]) if result else 0.0
