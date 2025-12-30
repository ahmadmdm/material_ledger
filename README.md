# Material Ledger - Professional Edition

<div align="center">
  <h3>🎯 Professional General Ledger & Financial Analysis System</h3>
  <p>Built with Frappe Framework - Following Professional UI/UX Standards</p>
</div>

---

## ✨ Features

### 📊 **Material Ledger Report**
- Comprehensive General Ledger view with advanced filtering
- Real-time balance calculations
- Support for multi-dimensional analysis (Account, Cost Center, Project, Party)
- Group by account functionality
- Professional export to Excel
- Print-optimized layouts
- RTL (Arabic) and LTR (English) support

### 💼 **Financial Analysis Dashboard**
- Strategic CFO-level financial analysis
- Complete financial statements:
  - Income Statement
  - Balance Sheet
  - Cash Flow Statement
  - Statement of Changes in Equity
- Key Performance Indicators (KPIs)
- Quarterly performance tracking
- Year-over-year comparison
- AI-powered strategic insights
- DuPont Analysis
- Altman Z-Score (bankruptcy prediction)

### 🎨 **Professional UI/UX**
- Built with Frappe UI design system
- Responsive design for all screen sizes
- Clean, modern interface
- Professional color scheme
- Accessible and user-friendly
- Print-ready reports (A4 format)

---

## 🚀 Installation

### Prerequisites
- Frappe Framework v14 or v15
- ERPNext (recommended)
- Python 3.10+
- Node.js 18+

### Installation Steps

```bash
# Navigate to your bench directory
cd $PATH_TO_YOUR_BENCH

# Get the app from repository
bench get-app $URL_OF_THIS_REPO --branch main

# Install on your site
bench --site your-site-name install-app material_ledger

# Build assets
bench build --app material_ledger

# Restart bench
bench restart
```

---

## 📖 Usage

### Material Ledger Report

1. Navigate to: **Accounting > Material Ledger**
2. Select filters:
   - Company (required)
   - Date range
   - Account (optional)
   - Cost Center (optional)
   - Project (optional)
   - Party Type & Party (optional)
3. Click **Refresh** to load data
4. Use **Group by Account** toggle for grouped view
5. Export to Excel or Print as needed

### Financial Analysis

1. Navigate to: **Accounting > Financial Analysis**
2. Select:
   - Company (required)
   - Year
   - Quarter (optional - defaults to full year)
3. Click **Analyze** to generate comprehensive analysis
4. Review:
   - KPI cards
   - AI strategic report
   - Financial statements (4 tabs)
   - Charts and visualizations
5. Print for professional reporting

---

## 🔧 Configuration

### API Configuration (Optional)

For AI-powered analysis, configure DeepSeek API key in `site_config.json`:

```json
{
  "deepseek_api_key": "your-api-key-here"
}
```

### Permissions

The app respects Frappe's role-based permissions:
- **Material Ledger**: Accounts Manager, Accounts User, System Manager
- **Financial Analysis**: System Manager, Administrator

---

## 🎯 Key Improvements (v2.0)

### From Vuetify to Frappe UI
- ✅ Removed Vuetify dependency
- ✅ Native Frappe UI components
- ✅ Better performance
- ✅ Consistent with ERPNext design

### Enhanced Features
- ✅ Professional CSS styling
- ✅ Improved data validation
- ✅ Better error handling
- ✅ Optimized API calls
- ✅ Enhanced print layouts
- ✅ Comprehensive documentation

### Code Quality
- ✅ Clean, maintainable code
- ✅ Proper code comments
- ✅ Follows Python PEP 8
- ✅ JavaScript best practices
- ✅ Modular architecture

---

## 🛠️ Development

### Setup Development Environment

```bash
cd apps/material_ledger

# Install pre-commit hooks
pre-commit install

# Run linting
pre-commit run --all-files
```

### Code Standards

This app uses `pre-commit` for code quality:
- **ruff** - Python linting and formatting
- **eslint** - JavaScript linting
- **prettier** - Code formatting
- **pyupgrade** - Python syntax upgrades

### File Structure

```
material_ledger/
├── material_ledger/
│   ├── material_ledger/
│   │   ├── api.py              # Backend API methods
│   │   ├── page/
│   │   │   ├── material_ledger_report/
│   │   │   │   ├── material_ledger_report.js
│   │   │   │   ├── material_ledger_report_new.js  # New Frappe UI version
│   │   │   │   ├── material_ledger_report.css
│   │   │   │   └── material_ledger_report.json
│   │   │   └── financial_analysis/
│   │   │       ├── financial_analysis.js
│   │   │       ├── financial_analysis_new.js      # New Frappe UI version
│   │   │       └── financial_analysis.json
│   ├── public/
│   │   └── css/
│   │       └── material_ledger.css                # Global styles
│   └── hooks.py                                   # App hooks
├── README.md
├── pyproject.toml
└── license.txt
```

---

## 📊 Technical Specifications

### Backend (Python)
- **Framework**: Frappe Framework
- **Database**: MariaDB/MySQL
- **API**: RESTful with `@frappe.whitelist()`
- **Performance**: Optimized SQL queries

### Frontend (JavaScript)
- **Framework**: Vanilla JavaScript with Frappe UI
- **Charts**: Frappe Charts
- **UI Components**: Native Frappe components
- **Responsive**: Mobile-first design

### Styling (CSS)
- **Design System**: Frappe UI variables
- **Architecture**: BEM-inspired naming
- **Features**: Print styles, RTL support, Dark mode ready

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run linting and tests
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Contribution Guidelines
- Follow existing code style
- Add comments for complex logic
- Update documentation
- Test thoroughly before submitting

---

## 📝 License

MIT License - See [license.txt](license.txt) for details

---

## 🙏 Credits

- **Developer**: Trae
- **Framework**: [Frappe Framework](https://frappeframework.com)
- **UI Design**: Following Frappe UI standards
- **Icons**: Frappe Icons & Material Design Icons

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: trae@example.com
- Documentation: See `DEVELOPMENT_GUIDE.md`

---

## 🎓 Learning Resources

- [Frappe Framework Documentation](https://frappeframework.com/docs)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Frappe UI Guidelines](https://frappeframework.com/docs/user/en/ui)

---

<div align="center">
  <p>Made with ❤️ for the Frappe Community</p>
  <p><strong>Version 2.0.0</strong> - Professional Edition</p>
</div>
