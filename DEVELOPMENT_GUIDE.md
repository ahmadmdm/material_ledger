# AI System Context: Frappe + Vue.js/Vuetify SPA Architecture

This document serves as the **Master Context** for AI models to understand, replicate, and extend the "Material Ledger" application architecture. Use this guide to ensure consistency in future development tasks.

---

## 1. Architectural Overview
**Goal:** Build rich, interactive Single Page Applications (SPAs) embedded directly within Frappe Pages without external build tools (Webpack/Vite).
**Core Constraint:** The environment is a standard Frappe Desk installation. We must inject Vue.js and Vuetify at runtime via CDN to avoid build complexity and dependency hell.

## 2. Technology Stack & Versioning
*   **Backend:** Frappe Framework (Python)
*   **Frontend Core:** jQuery (Built-in to Frappe) wrapper for initialization.
*   **Frontend UI:** Vue.js (v2.6.14) + Vuetify (v2.x).
*   **Loading Mechanism:** Dynamic Script Injection (Sequential Loading).

## 3. Mandatory Coding Patterns (Strict Adherence Required)

### A. The "Page Controller" Pattern (JavaScript)
**File:** `*.page.js`
**Rule 1 (Syntax):** DO NOT use ES6 Classes (`class Page { ... }`) at the top level. This causes `SyntaxError` in some Frappe minify/build steps. Use Functional Scope.
**Rule 2 (Loading):** Scripts must be loaded sequentially (Vue first, then Vuetify).

**Standard Boilerplate:**
```javascript
frappe.pages['page-name'].on_page_load = function(wrapper) {
    // 1. Initialize Wrapper
    var me = {};
    me.wrapper = $(wrapper);

    // 2. Script Loader Utility
    function load_scripts(scripts, callback) {
        if (!scripts || scripts.length === 0) { callback(); return; }
        let el = document.createElement('script');
        el.src = scripts[0];
        el.onload = () => load_scripts(scripts.slice(1), callback);
        document.head.appendChild(el);
    }

    // 3. Main Vue Logic
    function render_vue() {
        const template = `
            <div id="app-container">
                <v-app>
                    <v-main> ... content ... </v-main>
                </v-app>
            </div>
        `;
        
        me.wrapper.find(".layout-main-section").html(template);

        new Vue({
            el: '#app-container',
            vuetify: new Vuetify({ rtl: frappe.boot.sysdefaults.rtl === 1 }),
            data: { ... },
            methods: {
                fetchData() {
                    frappe.call({ method: 'path.to.api', callback: (r) => { ... } });
                }
            }
        });
    }

    // 4. Execution
    load_scripts([
        "https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js",
        "https://cdn.jsdelivr.net/npm/vuetify@2.x/dist/vuetify.js"
    ], render_vue);
};
```

### B. The "Backend Logic" Pattern (Python)
**File:** `api.py`
**Rule:** Offload ALL heavy computation (grouping, running balances) to Python. The Frontend should receive "Render-Ready" data.

**Standard Boilerplate:**
```python
import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_report_data(filters=None):
    # 1. Fetch Raw Data
    data = frappe.get_all("DocType", filters=filters, fields=["*"])
    
    # 2. Post-Process (e.g., Running Balance)
    balance = 0.0
    for row in data:
        balance += flt(row.debit) - flt(row.credit)
        row['balance'] = balance
        
    return data
```

## 4. Common Pitfalls & Solutions (Knowledge Base)

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **SyntaxError: Unexpected identifier** | Using `class` syntax in Page JS. | Refactor to `function` based structure (see Pattern A). |
| **Vuetify Styles Missing** | CSS not injected. | Manually inject `<link href="..." rel="stylesheet">` in the template string. |
| **URL Conflict** | Workspace and Page share the same name. | Rename Page to `*-report` or `*-page`. Update Workspace shortcuts. |
| **Navigation Fails** | Using `<a href="/app/...">`. | Use `frappe.set_route("Form", doctype, name)` inside a Vue method. |
| **Stale Code** | Browser caching JS files. | Run `bench clear-cache` and use Hard Reload (Ctrl+Shift+R). |

## 5. Development Workflow for AI Agents

1.  **Receive Requirement**: "Create a report for X".
2.  **Scaffold**:
    *   Create `api.py` with dummy data return.
    *   Create `page.js` with the **Standard Boilerplate**.
3.  **Integrate**:
    *   Update `api.py` to fetch real data.
    *   Update `page.js` template with `v-data-table`.
4.  **Refine**:
    *   Add Filters (Vue `v-model` <-> `frappe.call` args).
    *   Add Charts/Cards (Vuetify Components).
5.  **Verify**:
    *   Check for Console Errors.
    *   Verify Mobile Responsiveness (Vuetify handles this naturally).

---
**End of Context**
