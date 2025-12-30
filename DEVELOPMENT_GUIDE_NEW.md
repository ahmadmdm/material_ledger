# Material Ledger - Development Guide

## 🏗️ Architecture Overview

This application is built on Frappe Framework using professional UI/UX standards. It has been migrated from Vuetify to native Frappe UI components for better integration and performance.

### System Architecture

The application follows a three-tier architecture:
1. **Presentation Layer**: Frappe UI components (JavaScript + CSS)
2. **Business Logic Layer**: Python API methods
3. **Data Layer**: MariaDB with Frappe ORM

---

## 📁 Project Structure

```
material_ledger/
├── material_ledger/
│   ├── material_ledger/
│   │   ├── api.py                          # Backend API
│   │   └── page/
│   │       ├── material_ledger_report/     # General Ledger Page
│   │       └── financial_analysis/         # Financial Analysis Page
│   ├── public/
│   │   └── css/
│   │       └── material_ledger.css         # Global styles
│   └── hooks.py                            # App configuration
├── README.md
├── DEVELOPMENT_GUIDE.md
└── pyproject.toml
```

---

## 🚀 Quick Start

### Installation

```bash
cd ~/frappe-bench
bench get-app https://github.com/your-repo/material_ledger
bench --site your-site install-app material_ledger
bench build --app material_ledger
bench restart
```

### Development Mode

```bash
# Enable developer mode
bench --site your-site set-config developer_mode 1

# Watch for changes
bench watch
```

---

## 🎨 Frontend Development

### Frappe Page Structure

```javascript
frappe.pages['page-name'].on_page_load = function(wrapper) {
    // 1. Create app page
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Page Title',
        single_column: true
    });

    // 2. Add filters
    page.add_field({
        fieldname: 'company',
        label: 'Company',
        fieldtype: 'Link',
        options: 'Company',
        change: function() {
            // Handle change
        }
    });

    // 3. Set actions
    page.set_primary_action('Action', () => performAction());
    
    // 4. Build UI
    buildInterface();
};
```

### Using Frappe UI Components

**Cards:**
```html
<div class="frappe-card">
    <div class="frappe-card-head">
        <strong class="frappe-card-title">Title</strong>
    </div>
    <div class="frappe-card-body">
        Content
    </div>
</div>
```

**Tables:**
```html
<table class="table table-bordered">
    <thead>
        <tr>
            <th>Column 1</th>
            <th>Column 2</th>
        </tr>
    </thead>
    <tbody></tbody>
</table>
```

---

## 🐍 Backend Development

### API Method Template

```python
@frappe.whitelist()
def api_method(param1, param2):
    """
    Method description
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        dict: Response data
    """
    # Validation
    if not param1:
        frappe.throw(_("Parameter required"))
    
    # Business logic
    result = process_data(param1, param2)
    
    return result
```

### Database Queries

```python
# Using ORM
entries = frappe.get_all(
    'DocType',
    fields=['field1', 'field2'],
    filters={'company': company},
    order_by='posting_date desc'
)

# Using SQL
result = frappe.db.sql("""
    SELECT field1, field2
    FROM `tabDocType`
    WHERE company = %(company)s
""", {'company': company}, as_dict=True)
```

---

## 🎯 Best Practices

### Python
- Use type hints where possible
- Add docstrings to all functions
- Use `frappe.throw()` for user-facing errors
- Log technical errors with `frappe.log_error()`
- Use `frappe.utils` for formatting

### JavaScript
- Use modern ES6+ syntax
- Handle errors gracefully
- Show user feedback with `frappe.show_alert()`
- Format data with `frappe.format()`
- Use CSS variables for styling

### CSS
- Use Frappe UI variables
- Follow BEM naming convention
- Mobile-first responsive design
- Add print styles where needed

---

## 🧪 Testing

### Manual Testing

1. **Material Ledger Report**
   - Test all filters
   - Verify calculations
   - Check grouping feature
   - Test export/print

2. **Financial Analysis**
   - Test all periods
   - Verify KPIs
   - Check all statements
   - Test charts rendering

### API Testing

```python
# In bench console
bench console

# Test methods
from material_ledger.material_ledger.api import get_ledger_entries
result = get_ledger_entries(
    company='Test Company',
    from_date='2024-01-01',
    to_date='2024-12-31'
)
```

---

## 🛠️ Common Tasks

### Adding a New Filter

```javascript
page.add_field({
    fieldname: 'new_filter',
    label: 'New Filter',
    fieldtype: 'Link',
    options: 'DocType',
    change: function() {
        state.filters.new_filter = this.get_value();
        loadData();
    }
});
```

### Adding a New API Method

```python
@frappe.whitelist()
def new_method(param):
    """Method description"""
    # Implementation
    return result
```

### Adding Styles

```css
/* In material_ledger.css */
.custom-class {
    property: value;
}
```

---

## 🚀 Deployment

```bash
# Build production assets
bench build --app material_ledger

# Clear cache
bench --site all clear-cache

# Restart
sudo supervisorctl restart all
```

---

## 📚 Resources

- [Frappe Framework Docs](https://frappeframework.com/docs)
- [Frappe UI Guidelines](https://frappeframework.com/docs/user/en/ui)
- [ERPNext Developer Guide](https://docs.erpnext.com/docs/developer)

---

## 💡 Tips

1. Always clear cache after changes
2. Use browser DevTools for debugging
3. Check console for JavaScript errors
4. Monitor API calls in Network tab
5. Test in both desktop and mobile views

---

## 🐛 Troubleshooting

**Changes not reflecting?**
```bash
bench clear-cache
bench build --app material_ledger
```

**Permission issues?**
- Check role permissions in JSON files

**SQL errors?**
- Verify field names match database

---

<div align="center">
  <p><strong>Happy Coding! 🚀</strong></p>
</div>
