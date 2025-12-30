frappe.pages['financial-analysis'].on_page_load = function(wrapper) {
    console.log("🎯 Financial Analysis - Expert Accountant Edition v8.0");
    
    const userLang = frappe.boot.lang || 'en';
    const isRtl = userLang === 'ar';
    
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: isRtl ? '📊 التحليل المالي الاحترافي' : '📊 Professional Financial Analysis',
        single_column: true
    });

    addProfessionalStyles();
    
    let state = {
        loading: false,
        data: null,
        filters: { company: "", year: new Date().getFullYear(), period: "annual", period_number: null },
        activeStatement: 'dashboard'
    };

    const t = (key) => {
        const trans = {
            en: {
                company: 'Company', year: 'Fiscal Year', refresh: 'Analyze',
                dashboard: 'Executive Dashboard', income: 'Income Statement', 
                balance: 'Balance Sheet', cash: 'Cash Flow', ratios: 'Financial Ratios',
                health_score: 'Financial Health Score', risk_alerts: 'Risk Alerts',
                dupont: 'DuPont Analysis', working_capital: 'Working Capital',
                revenue: 'Revenue', expenses: 'Expenses', net_income: 'Net Income',
                no_data: 'No data', loading: 'Analyzing...', generate_ai: 'AI Insights',
                equity_changes: 'Changes in Equity', monthly: 'Monthly', quarterly: 'Quarterly',
                annual: 'Annual', period: 'Period', select_month: 'Select Month',
                select_quarter: 'Select Quarter', ai_analysis: 'AI Deep Analysis'
            },
            ar: {
                company: 'الشركة', year: 'السنة المالية', refresh: 'تحليل',
                dashboard: 'لوحة التحكم التنفيذية', income: 'قائمة الدخل',
                balance: 'الميزانية العمومية', cash: 'التدفقات النقدية', ratios: 'النسب المالية',
                health_score: 'درجة الصحة المالية', risk_alerts: 'تنبيهات المخاطر',
                dupont: 'تحليل دوبونت', working_capital: 'رأس المال العامل',
                revenue: 'الإيرادات', expenses: 'المصروفات', net_income: 'صافي الدخل',
                no_data: 'لا توجد بيانات', loading: 'جاري التحليل...', generate_ai: 'رؤى AI',
                equity_changes: 'التغيرات في حقوق الملكية', monthly: 'شهري', quarterly: 'ربعي',
                annual: 'سنوي', period: 'الفترة', select_month: 'اختر الشهر',
                select_quarter: 'اختر الربع', ai_analysis: 'التحليل العميق بالذكاء الاصطناعي'
            }
        };
        return trans[isRtl ? 'ar' : 'en'][key] || key;
    };

    buildProfessionalUI();
    setupFilters();
    setupActions();
    fetchCompanies();

    function addProfessionalStyles() {
        const styles = `
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
                
                .page-content { font-family: 'Inter', sans-serif !important; background: #f8fafc; }
                
                .health-score-circle { 
                    width: 200px; height: 200px; border-radius: 50%; 
                    display: flex; flex-direction: column; align-items: center; 
                    justify-content: center; font-weight: 900; font-size: 48px;
                    position: relative; box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }
                
                .health-score-circle.excellent { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; }
                .health-score-circle.good { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; }
                .health-score-circle.fair { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; }
                .health-score-circle.poor { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; }
                
                .risk-flag { 
                    padding: 16px; margin: 12px 0; border-radius: 10px; 
                    border-left: 5px solid; display: flex; align-items: flex-start; gap: 15px;
                }
                .risk-flag.critical { background: #fef2f2; border-left-color: #dc2626; }
                .risk-flag.warning { background: #fffbeb; border-left-color: #f59e0b; }
                
                .risk-flag-icon { 
                    font-size: 24px; min-width: 30px;
                }
                .risk-flag.critical .risk-flag-icon { color: #dc2626; }
                .risk-flag.warning .risk-flag-icon { color: #f59e0b; }
                
                .stat-card:hover { transform: translateY(-5px); box-shadow: 0 20px 50px rgba(0,0,0,0.15) !important; }
                .modern-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.25) !important; }
                
                .dashboard-tab { 
                    padding: 12px 24px; background: white; border: 2px solid #e5e7eb; 
                    border-radius: 10px; cursor: pointer; transition: all 0.3s; 
                    font-weight: 700; font-size: 13px;
                }
                .dashboard-tab:hover { border-color: #667eea; background: #f0f4ff; }
                .dashboard-tab.active { 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; border-color: #667eea;
                }
                
                .dupont-container { 
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;
                    margin-top: 20px;
                }
                
                .dupont-box { 
                    background: white; padding: 20px; border-radius: 12px; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center;
                    border-top: 4px solid #667eea;
                }
                
                .dupont-box .label { font-size: 13px; color: #6b7280; font-weight: 600; text-transform: uppercase; }
                .dupont-box .value { font-size: 28px; font-weight: 900; color: #667eea; margin-top: 8px; font-family: monospace; }
                
                .trend-chart { margin-top: 20px; }
                
                @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
                .fade-in { animation: slideIn 0.6s ease-out; }
                
                @media print { .no-print, .dashboard-tabs { display: none !important; } }
            </style>
        `;
        $('head').append(styles);
    }

    function buildProfessionalUI() {
        const heroHTML = `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 15px 50px rgba(102, 126, 234, 0.4); color: white;">
                <h2 style="margin: 0; font-size: 28px; font-weight: 800; display: flex; align-items: center; gap: 12px;">
                    <i class="fa fa-line-chart"></i>
                    <span id="hero-company-name">--</span>
                </h2>
                <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 14px;">
                    <i class="fa fa-calendar"></i> ${t('year')}: <span id="hero-year">--</span>
                </p>
            </div>
        `;

        const tabsHTML = `
            <div class="dashboard-tabs no-print" style="display: flex; gap: 12px; margin-bottom: 25px; flex-wrap: wrap;">
                <div class="dashboard-tab active" data-tab="dashboard"><i class="fa fa-th-large"></i> ${t('dashboard')}</div>
                <div class="dashboard-tab" data-tab="income"><i class="fa fa-money"></i> ${t('income')}</div>
                <div class="dashboard-tab" data-tab="balance"><i class="fa fa-balance-scale"></i> ${t('balance')}</div>
                <div class="dashboard-tab" data-tab="cash"><i class="fa fa-exchange"></i> ${t('cash')}</div>
                <div class="dashboard-tab" data-tab="equity"><i class="fa fa-users"></i> ${t('equity_changes')}</div>
                <div class="dashboard-tab" data-tab="dupont"><i class="fa fa-chart-pie"></i> ${t('dupont')}</div>
                <div class="dashboard-tab" data-tab="ratios"><i class="fa fa-bar-chart"></i> ${t('ratios')}</div>
                <div class="dashboard-tab" data-tab="ai"><i class="fa fa-magic"></i> ${t('ai_analysis')}</div>
            </div>
        `;

        const contentHTML = `
            <div class="dashboard-content">
                <div id="dashboard-tab" class="dashboard-section" style="display: block;"></div>
                <div id="income-tab" class="dashboard-section" style="display: none;"></div>
                <div id="balance-tab" class="dashboard-section" style="display: none;"></div>
                <div id="cash-tab" class="dashboard-section" style="display: none;"></div>
                <div id="equity-tab" class="dashboard-section" style="display: none;"></div>
                <div id="dupont-tab" class="dashboard-section" style="display: none;"></div>
                <div id="ratios-tab" class="dashboard-section" style="display: none;"></div>
                <div id="ai-tab" class="dashboard-section" style="display: none;"></div>
            </div>
        `;

        $(wrapper).find('.page-content').append(heroHTML + tabsHTML + contentHTML);
        
        $('.dashboard-tab').on('click', function() {
            const tab = $(this).data('tab');
            $('.dashboard-tab').removeClass('active');
            $(this).addClass('active');
            $('.dashboard-section').hide();
            $(`#${tab}-tab`).show();
        });
    }

    function setupFilters() {
        page.add_field({ fieldname: 'company', label: t('company'), fieldtype: 'Link', options: 'Company', reqd: 1,
            change: function() { state.filters.company = this.get_value(); $('#hero-company-name').text(state.filters.company); }
        });
        page.add_field({ fieldname: 'year', label: t('year'), fieldtype: 'Int', default: state.filters.year,
            change: function() { state.filters.year = this.get_value(); $('#hero-year').text(state.filters.year); }
        });
        
        // Period selector
        page.add_field({ 
            fieldname: 'period', 
            label: t('period'), 
            fieldtype: 'Select', 
            options: ['Annual\nQuarterly\nMonthly'],
            default: 'Annual',
            change: function() { 
                state.filters.period = this.get_value().toLowerCase(); 
                updatePeriodFilters();
            }
        });
        
        // Period number field (hidden by default)
        page.add_field({ 
            fieldname: 'period_number', 
            label: '', 
            fieldtype: 'Select', 
            options: '',
            change: function() { 
                state.filters.period_number = this.get_value();
            }
        });
        
        // Hide period number initially
        page.fields_dict.period_number.$wrapper.hide();
    }
    
    function updatePeriodFilters() {
        const period = state.filters.period;
        const periodField = page.fields_dict.period_number;
        
        if (period === 'monthly') {
            periodField.df.label = t('select_month');
            periodField.df.options = 'January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember';
            periodField.$wrapper.show();
            periodField.refresh();
        } else if (period === 'quarterly') {
            periodField.df.label = t('select_quarter');
            periodField.df.options = 'Q1\nQ2\nQ3\nQ4';
            periodField.$wrapper.show();
            periodField.refresh();
        } else {
            periodField.$wrapper.hide();
            state.filters.period_number = null;
        }
    }

    function setupActions() {
        page.set_primary_action(t('refresh'), fetchAnalysis, 'refresh');
    }

    function fetchCompanies() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: { doctype: 'Company', fields: ['name'] },
            callback: (r) => {
                if (r.message && r.message.length) {
                    state.filters.company = r.message[0].name;
                    page.fields_dict.company.set_value(state.filters.company);
                    $('#hero-company-name').text(state.filters.company);
                    $('#hero-year').text(state.filters.year);
                    setTimeout(() => fetchAnalysis(), 500);
                }
            }
        });
    }

    function fetchAnalysis() {
        if (!state.filters.company) return;
        state.loading = true;
        $('.dashboard-section').html('<div style="padding: 60px; text-align: center;"><i class="fa fa-spinner fa-spin" style="font-size: 48px; color: #667eea;"></i><div style="margin-top: 15px; color: #6b7280; font-weight: 600;">' + t('loading') + '</div></div>');

        // Convert period_number based on period type
        let periodNum = null;
        if (state.filters.period === 'monthly' && state.filters.period_number) {
            const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
            periodNum = months.indexOf(state.filters.period_number) + 1;
        } else if (state.filters.period === 'quarterly' && state.filters.period_number) {
            periodNum = parseInt(state.filters.period_number.replace('Q', ''));
        }

        frappe.call({
            method: 'material_ledger.material_ledger.api.get_financial_analysis',
            args: { 
                company: state.filters.company, 
                year: state.filters.year,
                period: state.filters.period,
                period_number: periodNum
            },
            callback: (r) => {
                state.loading = false;
                if (r.message) {
                    console.log('📊 Financial Data:', r.message);
                    state.data = r.message;
                    renderDashboard();
                    renderIncomeStatement();
                    renderBalanceSheet();
                    renderCashFlow();
                    renderEquityChanges();
                    renderDuPont();
                    renderRatios();
                    renderAIAnalysis();
                    frappe.show_alert({ message: '✅ ' + (isRtl ? 'تم التحليل بنجاح' : 'Analysis completed'), indicator: 'green' });
                }
            }
        });
    }

    function renderDashboard() {
        if (!state.data) return;
        
        const health = state.data.summary.health_score || 0;
        const healthStatus = health >= 80 ? 'excellent' : health >= 60 ? 'good' : health >= 40 ? 'fair' : 'poor';
        const risks = state.data.risk_flags || [];

        let html = `
            <div class="fade-in" style="display: grid; grid-template-columns: 1fr 2fr; gap: 25px; align-items: start;">
                <div style="text-align: center;">
                    <div class="health-score-circle ${healthStatus}">
                        <div>${health}</div>
                        <div style="font-size: 14px; margin-top: 5px; opacity: 0.9;">${t('health_score')}</div>
                    </div>
                </div>
                <div>
                    <h3 style="margin: 0 0 20px 0; font-size: 22px; font-weight: 800;">${t('risk_alerts')}</h3>
                    ${risks.length ? risks.map(flag => `
                        <div class="risk-flag ${flag.level}">
                            <div class="risk-flag-icon">
                                ${flag.level === 'critical' ? '<i class="fa fa-exclamation-triangle"></i>' : '<i class="fa fa-warning"></i>'}
                            </div>
                            <div style="flex: 1;">
                                <div style="font-weight: 700; margin-bottom: 4px;">${flag.title}</div>
                                <div style="font-size: 13px; color: #6b7280;">${flag.message}</div>
                            </div>
                        </div>
                    `).join('') : '<div style="padding: 20px; background: #f0fdf4; border-radius: 10px; color: #15803d; font-weight: 600;">✅ لا توجد تنبيهات خطيرة</div>'}
                </div>
            </div>
            
            <div style="margin-top: 30px; display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
                <div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 28px; border-radius: 14px; color: white; box-shadow: 0 12px 35px rgba(102, 126, 234, 0.35);">
                    <div style="font-size: 13px; opacity: 0.9; text-transform: uppercase; font-weight: 700;">${t('revenue')}</div>
                    <div style="font-size: 32px; font-weight: 900; margin-top: 10px; font-family: monospace;">${frappe.format(state.data.summary.income, {fieldtype: 'Currency'})}</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 28px; border-radius: 14px; color: white; box-shadow: 0 12px 35px rgba(240, 147, 251, 0.35);">
                    <div style="font-size: 13px; opacity: 0.9; text-transform: uppercase; font-weight: 700;">${t('expenses')}</div>
                    <div style="font-size: 32px; font-weight: 900; margin-top: 10px; font-family: monospace;">${frappe.format(state.data.summary.expense, {fieldtype: 'Currency'})}</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 28px; border-radius: 14px; color: white; box-shadow: 0 12px 35px rgba(79, 172, 254, 0.35);">
                    <div style="font-size: 13px; opacity: 0.9; text-transform: uppercase; font-weight: 700;">${t('net_income')}</div>
                    <div style="font-size: 32px; font-weight: 900; margin-top: 10px; font-family: monospace; color: ${state.data.summary.profit >= 0 ? 'white' : '#ff6b6b'};">${frappe.format(state.data.summary.profit, {fieldtype: 'Currency'})}</div>
                </div>
            </div>
        `;
        
        $('#dashboard-tab').html(html);
    }

    function renderDuPont() {
        if (!state.data) return;
        
        const ratios = state.data.ratios;
        const dupont = ratios.dupont_roe || ratios.roe;

        let html = `
            <div class="fade-in">
                <h3 style="margin: 0 0 20px 0; font-size: 22px; font-weight: 800;">📈 DuPont ROE Analysis</h3>
                <p style="color: #6b7280; margin-bottom: 20px;">تحليل العائد على حقوق الملكية من خلال مكوناته الثلاثة</p>
                
                <div class="dupont-container">
                    <div class="dupont-box">
                        <div class="label">Profit Margin</div>
                        <div class="value">${(ratios.net_margin || 0).toFixed(2)}%</div>
                        <div style="margin-top: 5px; font-size: 12px; color: #9ca3af;">صافي الربح / الإيرادات</div>
                    </div>
                    <div class="dupont-box">
                        <div class="label">Asset Turnover</div>
                        <div class="value">${(ratios.asset_turnover || 0).toFixed(2)}</div>
                        <div style="margin-top: 5px; font-size: 12px; color: #9ca3af;">الإيرادات / الأصول</div>
                    </div>
                    <div class="dupont-box">
                        <div class="label">Equity Multiplier</div>
                        <div class="value">${(ratios.leverage || 0).toFixed(2)}</div>
                        <div style="margin-top: 5px; font-size: 12px; color: #9ca3af;">الأصول / حقوق الملكية</div>
                    </div>
                    <div class="dupont-box" style="border-top-color: #10b981;">
                        <div class="label">ROE (DuPont)</div>
                        <div class="value" style="color: #10b981;">${dupont.toFixed(2)}%</div>
                        <div style="margin-top: 5px; font-size: 12px; color: #9ca3af;">العائد على حقوق الملكية</div>
                    </div>
                </div>
            </div>
        `;
        
        $('#dupont-tab').html(html);
    }

    function renderIncomeStatement() {
        if (!state.data?.summary) return;
        const s = state.data.summary;
        const analysis = state.data.income_statement_analysis || {};
        const monthly = state.data.monthly || [];
        const quarterly = state.data.quarterly || [];
        
        let html = `
            <div class="fade-in" style="background: white; border-radius: 14px; box-shadow: 0 4px 25px rgba(0,0,0,0.08); overflow: hidden;">
                <div style="padding: 24px 28px; border-bottom: 1px solid #e5e7eb; background: linear-gradient(to right, #f9fafb, #ffffff);">
                    <h3 style="margin: 0; font-size: 20px; font-weight: 800; color: #111827;">📋 ${t('income')} - ${state.data.period || ''}</h3>
                </div>
                <div style="padding: 20px;">
                    <!-- Main Income Statement -->
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                        <tr style="background: #f9fafb; border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 16px; font-weight: 600;">الإيرادات (Revenue)</td>
                            <td style="padding: 16px; text-align: right; font-weight: 600; color: #059669;">${frappe.format(s.income, {fieldtype: 'Currency'})}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 16px; font-weight: 600;">المصروفات (Expenses)</td>
                            <td style="padding: 16px; text-align: right; font-weight: 600; color: #dc2626;">${frappe.format(s.expense, {fieldtype: 'Currency'})}</td>
                        </tr>
                        <tr style="background: #f3f4f6; border-top: 3px solid #667eea; border-bottom: 3px solid #667eea;">
                            <td style="padding: 16px; font-weight: 800;">صافي الربح/الخسارة (Net Profit/Loss)</td>
                            <td style="padding: 16px; text-align: right; font-weight: 800; color: ${s.profit >= 0 ? '#059669' : '#dc2626'};">${frappe.format(s.profit, {fieldtype: 'Currency'})}</td>
                        </tr>
                    </table>
                    
                    <!-- Analysis Insights -->
                    ${analysis.insights && analysis.insights.length > 0 ? `
                    <div style="margin-bottom: 30px;">
                        <h4 style="font-size: 16px; font-weight: 700; margin-bottom: 15px; color: #667eea;">📊 رؤى تحليلية</h4>
                        ${analysis.insights.map(insight => `
                            <div style="padding: 12px; background: ${insight.includes('⚠️') ? '#fffbeb' : '#f0fdf4'}; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid ${insight.includes('⚠️') ? '#f59e0b' : '#10b981'};">
                                ${insight}
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
                    
                    <!-- Key Ratios -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px;">
                        <div style="padding: 15px; background: #f0f4ff; border-radius: 10px; border-left: 4px solid #667eea;">
                            <div style="font-size: 12px; color: #6b7280; font-weight: 600;">هامش الربح الإجمالي</div>
                            <div style="font-size: 24px; font-weight: 900; color: #667eea; margin-top: 5px;">${(analysis.gross_margin || 0).toFixed(2)}%</div>
                            ${analysis.margin_change ? `<div style="font-size: 11px; color: ${analysis.margin_change > 0 ? '#059669' : '#dc2626'}; margin-top: 3px;">${analysis.margin_change > 0 ? '↑' : '↓'} ${Math.abs(analysis.margin_change).toFixed(2)}%</div>` : ''}
                        </div>
                        <div style="padding: 15px; background: #f0fdf4; border-radius: 10px; border-left: 4px solid #10b981;">
                            <div style="font-size: 12px; color: #6b7280; font-weight: 600;">نمو الإيرادات</div>
                            <div style="font-size: 24px; font-weight: 900; color: #10b981; margin-top: 5px;">${(analysis.revenue_growth || 0).toFixed(2)}%</div>
                        </div>
                        <div style="padding: 15px; background: #fffbeb; border-radius: 10px; border-left: 4px solid #f59e0b;">
                            <div style="font-size: 12px; color: #6b7280; font-weight: 600;">نسبة المصروفات</div>
                            <div style="font-size: 24px; font-weight: 900; color: #f59e0b; margin-top: 5px;">${(analysis.expense_ratio || 0).toFixed(2)}%</div>
                        </div>
                    </div>
                    
                    <!-- Period Breakdown -->
                    ${quarterly.length > 0 ? `
                    <div style="margin-bottom: 30px;">
                        <h4 style="font-size: 16px; font-weight: 700; margin-bottom: 15px; color: #667eea;">📅 التحليل الربعي</h4>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #f9fafb; border-bottom: 2px solid #e5e7eb;">
                                    <th style="padding: 12px; text-align: left; font-weight: 700;">الربع</th>
                                    <th style="padding: 12px; text-align: right; font-weight: 700;">الإيرادات</th>
                                    <th style="padding: 12px; text-align: right; font-weight: 700;">المصروفات</th>
                                    <th style="padding: 12px; text-align: right; font-weight: 700;">الربح</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${quarterly.map(q => `
                                    <tr style="border-bottom: 1px solid #e5e7eb;">
                                        <td style="padding: 12px; font-weight: 600;">Q${q.q}</td>
                                        <td style="padding: 12px; text-align: right; color: #059669;">${frappe.format(q.inc, {fieldtype: 'Currency'})}</td>
                                        <td style="padding: 12px; text-align: right; color: #dc2626;">${frappe.format(q.exp, {fieldtype: 'Currency'})}</td>
                                        <td style="padding: 12px; text-align: right; font-weight: 600; color: ${q.profit >= 0 ? '#059669' : '#dc2626'};">${frappe.format(q.profit, {fieldtype: 'Currency'})}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ` : ''}
                    
                    ${monthly.length > 0 ? `
                    <div>
                        <h4 style="font-size: 16px; font-weight: 700; margin-bottom: 15px; color: #667eea;">📅 التحليل الشهري</h4>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #f9fafb; border-bottom: 2px solid #e5e7eb;">
                                    <th style="padding: 12px; text-align: left; font-weight: 700;">الشهر</th>
                                    <th style="padding: 12px; text-align: right; font-weight: 700;">الإيرادات</th>
                                    <th style="padding: 12px; text-align: right; font-weight: 700;">المصروفات</th>
                                    <th style="padding: 12px; text-align: right; font-weight: 700;">الربح</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${monthly.map(m => `
                                    <tr style="border-bottom: 1px solid #e5e7eb;">
                                        <td style="padding: 12px; font-weight: 600;">${m.month_name}</td>
                                        <td style="padding: 12px; text-align: right; color: #059669;">${frappe.format(m.inc, {fieldtype: 'Currency'})}</td>
                                        <td style="padding: 12px; text-align: right; color: #dc2626;">${frappe.format(m.exp, {fieldtype: 'Currency'})}</td>
                                        <td style="padding: 12px; text-align: right; font-weight: 600; color: ${m.profit >= 0 ? '#059669' : '#dc2626'};">${frappe.format(m.profit, {fieldtype: 'Currency'})}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        $('#income-tab').html(html);
    }

    function renderBalanceSheet() {
        if (!state.data?.summary) return;
        const s = state.data.summary;
        const analysis = state.data.balance_sheet_analysis || {};
        
        let html = `
            <div class="fade-in" style="background: white; border-radius: 14px; box-shadow: 0 4px 25px rgba(0,0,0,0.08); overflow: hidden;">
                <div style="padding: 24px 28px; border-bottom: 1px solid #e5e7eb; background: linear-gradient(to right, #f9fafb, #ffffff);">
                    <h3 style="margin: 0; font-size: 20px; font-weight: 800; color: #111827;">⚖️ ${t('balance')} - ${state.data.period || ''}</h3>
                </div>
                <div style="padding: 20px;">
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                        <tr style="background: #e0e7ff; border-bottom: 1px solid #e5e7eb;"><td colspan="2" style="padding: 16px; font-weight: 700; color: #4338ca;">الأصول (ASSETS)</td></tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 16px;">إجمالي الأصول</td><td style="padding: 16px; text-align: right; font-weight: 600;">${frappe.format(s.assets, {fieldtype: 'Currency'})}</td></tr>
                        
                        <tr style="background: #e0e7ff; border-bottom: 1px solid #e5e7eb;"><td colspan="2" style="padding: 16px; font-weight: 700; color: #4338ca;">الالتزامات وحقوق الملكية (LIABILITIES & EQUITY)</td></tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 16px;">إجمالي الالتزامات</td><td style="padding: 16px; text-align: right; font-weight: 600;">${frappe.format(s.liabilities, {fieldtype: 'Currency'})}</td></tr>
                        <tr style="background: #f3f4f6; border-top: 3px solid #667eea; border-bottom: 3px solid #667eea;"><td style="padding: 16px; font-weight: 800;">إجمالي حقوق الملكية</td><td style="padding: 16px; text-align: right; font-weight: 800;">${frappe.format(s.equity, {fieldtype: 'Currency'})}</td></tr>
                    </table>
                    
                    <!-- Analysis Insights -->
                    ${analysis.insights && analysis.insights.length > 0 ? `
                    <div style="margin-bottom: 30px;">
                        <h4 style="font-size: 16px; font-weight: 700; margin-bottom: 15px; color: #667eea;">📊 رؤى تحليلية</h4>
                        ${analysis.insights.map(insight => `
                            <div style="padding: 12px; background: ${insight.includes('⚠️') ? '#fffbeb' : '#f0fdf4'}; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid ${insight.includes('⚠️') ? '#f59e0b' : '#10b981'};">
                                ${insight}
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
                    
                    <!-- Key Metrics -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div style="padding: 15px; background: #f0f4ff; border-radius: 10px; border-left: 4px solid #667eea;">
                            <div style="font-size: 12px; color: #6b7280; font-weight: 600;">نسبة الديون للأصول</div>
                            <div style="font-size: 24px; font-weight: 900; color: #667eea; margin-top: 5px;">${(analysis.debt_to_assets || 0).toFixed(2)}%</div>
                        </div>
                        <div style="padding: 15px; background: #f0fdf4; border-radius: 10px; border-left: 4px solid #10b981;">
                            <div style="font-size: 12px; color: #6b7280; font-weight: 600;">نسبة حقوق الملكية</div>
                            <div style="font-size: 24px; font-weight: 900; color: #10b981; margin-top: 5px;">${(analysis.equity_ratio || 0).toFixed(2)}%</div>
                        </div>
                        <div style="padding: 15px; background: #fffbeb; border-radius: 10px; border-left: 4px solid #f59e0b;">
                            <div style="font-size: 12px; color: #6b7280; font-weight: 600;">نمو الأصول</div>
                            <div style="font-size: 24px; font-weight: 900; color: #f59e0b; margin-top: 5px;">${(analysis.asset_growth || 0).toFixed(2)}%</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        $('#balance-tab').html(html);
    }

    function renderCashFlow() {
        if (!state.data?.cash_flow) return;
        const cf = state.data.cash_flow;
        const analysis = state.data.cashflow_analysis || {};
        
        let html = `
            <div class="fade-in" style="background: white; border-radius: 14px; box-shadow: 0 4px 25px rgba(0,0,0,0.08); overflow: hidden;">
                <div style="padding: 24px 28px; border-bottom: 1px solid #e5e7eb; background: linear-gradient(to right, #f9fafb, #ffffff);">
                    <h3 style="margin: 0; font-size: 20px; font-weight: 800; color: #111827;">💰 ${t('cash')} - ${state.data.period || ''}</h3>
                </div>
                <div style="padding: 20px;">
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 16px; font-weight: 600;">الأنشطة التشغيلية</td><td style="padding: 16px; text-align: right; font-weight: 600; color: #667eea;">${frappe.format(cf.operating, {fieldtype: 'Currency'})}</td></tr>
                        <tr style="background: #f9fafb; border-bottom: 1px solid #e5e7eb;"><td style="padding: 16px; font-weight: 600;">الأنشطة الاستثمارية</td><td style="padding: 16px; text-align: right; font-weight: 600; color: #f093fb;">${frappe.format(cf.investing, {fieldtype: 'Currency'})}</td></tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 16px; font-weight: 600;">الأنشطة التمويلية</td><td style="padding: 16px; text-align: right; font-weight: 600; color: #4facfe;">${frappe.format(cf.financing, {fieldtype: 'Currency'})}</td></tr>
                        <tr style="background: #f3f4f6; border-top: 3px solid #667eea; border-bottom: 3px solid #667eea;"><td style="padding: 16px; font-weight: 800;">صافي التدفقات النقدية</td><td style="padding: 16px; text-align: right; font-weight: 800; color: ${cf.net >= 0 ? '#059669' : '#dc2626'};">${frappe.format(cf.net, {fieldtype: 'Currency'})}</td></tr>
                    </table>
                    
                    <!-- Analysis Insights -->
                    ${analysis.insights && analysis.insights.length > 0 ? `
                    <div style="margin-bottom: 30px;">
                        <h4 style="font-size: 16px; font-weight: 700; margin-bottom: 15px; color: #667eea;">📊 رؤى تحليلية</h4>
                        ${analysis.insights.map(insight => `
                            <div style="padding: 12px; background: ${insight.includes('⚠️') ? '#fffbeb' : '#f0fdf4'}; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid ${insight.includes('⚠️') ? '#f59e0b' : '#10b981'};">
                                ${insight}
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
                    
                    <!-- Key Metrics -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div style="padding: 15px; background: #f0fdf4; border-radius: 10px; border-left: 4px solid #10b981;">
                            <div style="font-size: 12px; color: #6b7280; font-weight: 600;">التدفق النقدي الحر</div>
                            <div style="font-size: 24px; font-weight: 900; color: #10b981; margin-top: 5px;">${frappe.format(analysis.free_cash_flow || 0, {fieldtype: 'Currency'})}</div>
                        </div>
                        <div style="padding: 15px; background: #f0f4ff; border-radius: 10px; border-left: 4px solid #667eea;">
                            <div style="font-size: 12px; color: #6b7280; font-weight: 600;">هامش التشغيل النقدي</div>
                            <div style="font-size: 24px; font-weight: 900; color: #667eea; margin-top: 5px;">${(analysis.operating_margin || 0).toFixed(2)}%</div>
                        </div>
                        <div style="padding: 15px; background: #fffbeb; border-radius: 10px; border-left: 4px solid #f59e0b;">
                            <div style="font-size: 12px; color: #6b7280; font-weight: 600;">جودة التحويل النقدي</div>
                            <div style="font-size: 24px; font-weight: 900; color: #f59e0b; margin-top: 5px;">${(analysis.cash_conversion || 0).toFixed(2)}%</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        $('#cash-tab').html(html);
    }

    function renderRatios() {
        if (!state.data?.ratios) return;
        const r = state.data.ratios;
        const ratios = [
            { name: 'ROE', value: r.roe, format: '%', color: '#667eea' },
            { name: 'ROA', value: r.roa, format: '%', color: '#4facfe' },
            { name: 'Net Margin', value: r.net_margin, format: '%', color: '#10b981' },
            { name: 'Current Ratio', value: r.current_ratio, format: '', color: '#f59e0b' },
            { name: 'Debt Ratio', value: r.debt_ratio, format: '%', color: '#f5576c' },
            { name: 'Z-Score', value: r.z_score, format: '', color: '#764ba2' }
        ];
        
        let html = '<div class="fade-in" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">';
        ratios.forEach(ratio => {
            html += `
                <div style="background: white; padding: 24px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border-left: 5px solid ${ratio.color};">
                    <div style="font-size: 13px; color: #6b7280; font-weight: 700; text-transform: uppercase; margin-bottom: 12px;">${ratio.name}</div>
                    <div style="font-size: 32px; font-weight: 900; color: ${ratio.color}; font-family: monospace;">${(ratio.value || 0).toFixed(2)}${ratio.format}</div>
                </div>
            `;
        });
        html += '</div>';
        $('#ratios-tab').html(html);
    }

    function renderEquityChanges() {
        if (!state.data?.equity_changes) return;
        const eq = state.data.equity_changes;
        
        let html = `
            <div class="fade-in" style="background: white; border-radius: 14px; box-shadow: 0 4px 25px rgba(0,0,0,0.08); overflow: hidden;">
                <div style="padding: 24px 28px; border-bottom: 1px solid #e5e7eb; background: linear-gradient(to right, #f9fafb, #ffffff);">
                    <h3 style="margin: 0; font-size: 20px; font-weight: 800; color: #111827;">📋 ${t('equity_changes')} - ${state.data.period || ''}</h3>
                </div>
                <div style="padding: 20px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background: #f3f4f6; border-bottom: 2px solid #e5e7eb;">
                            <td style="padding: 16px; font-weight: 700; color: #374151;">البند</td>
                            <td style="padding: 16px; text-align: right; font-weight: 700; color: #374151;">المبلغ</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 16px;">رصيد حقوق الملكية في بداية الفترة</td>
                            <td style="padding: 16px; text-align: right; font-weight: 600;">${frappe.format(eq.opening_balance || 0, {fieldtype: 'Currency'})}</td>
                        </tr>
                        <tr style="background: #f0fdf4; border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 16px; padding-right: 32px;">+ صافي الربح للفترة</td>
                            <td style="padding: 16px; text-align: right; font-weight: 600; color: #10b981;">${frappe.format(eq.net_profit || 0, {fieldtype: 'Currency'})}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 16px; padding-right: 32px;">+ مساهمات رأس المال</td>
                            <td style="padding: 16px; text-align: right; font-weight: 600; color: #667eea;">${frappe.format(eq.contributions || 0, {fieldtype: 'Currency'})}</td>
                        </tr>
                        <tr style="background: #fef2f2; border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 16px; padding-right: 32px;">- مسحوبات المالك</td>
                            <td style="padding: 16px; text-align: right; font-weight: 600; color: #dc2626;">${frappe.format(eq.withdrawals || 0, {fieldtype: 'Currency'})}</td>
                        </tr>
                        <tr style="background: #fef2f2; border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 16px; padding-right: 32px;">- توزيعات الأرباح</td>
                            <td style="padding: 16px; text-align: right; font-weight: 600; color: #dc2626;">${frappe.format(eq.dividends || 0, {fieldtype: 'Currency'})}</td>
                        </tr>
                        <tr style="background: #dbeafe; border-top: 3px solid #667eea; border-bottom: 3px solid #667eea;">
                            <td style="padding: 16px; font-weight: 800;">رصيد حقوق الملكية في نهاية الفترة</td>
                            <td style="padding: 16px; text-align: right; font-weight: 800;">${frappe.format(eq.closing_balance || 0, {fieldtype: 'Currency'})}</td>
                        </tr>
                        <tr style="background: #f9fafb;">
                            <td style="padding: 16px; font-weight: 700; color: ${(eq.total_change || 0) >= 0 ? '#10b981' : '#dc2626'};">صافي التغير في حقوق الملكية</td>
                            <td style="padding: 16px; text-align: right; font-weight: 800; color: ${(eq.total_change || 0) >= 0 ? '#10b981' : '#dc2626'};">${frappe.format(eq.total_change || 0, {fieldtype: 'Currency'})}</td>
                        </tr>
                    </table>
                </div>
            </div>
        `;
        $('#equity-tab').html(html);
    }

    function renderAIAnalysis() {
        const aiReport = state.data?.ai_report;
        
        if (!aiReport) {
            let html = `
                <div class="fade-in" style="background: white; border-radius: 14px; box-shadow: 0 4px 25px rgba(0,0,0,0.08); padding: 40px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 20px;">🤖</div>
                    <h3 style="font-size: 18px; color: #6b7280; margin: 0;">لا يوجد تحليل AI متاح</h3>
                    <p style="color: #9ca3af; margin-top: 10px;">قم بتشغيل التحليل للحصول على رؤى AI مفصلة</p>
                </div>
            `;
            $('#ai-tab').html(html);
            return;
        }
        
        let html = `
            <div class="fade-in" style="background: white; border-radius: 14px; box-shadow: 0 4px 25px rgba(0,0,0,0.08); overflow: hidden;">
                <div style="padding: 24px 28px; border-bottom: 1px solid #e5e7eb; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    <h3 style="margin: 0; font-size: 20px; font-weight: 800; color: #ffffff;">🤖 ${t('ai_analysis')} - DeepSeek Reasoner</h3>
                </div>
                <div style="padding: 28px; line-height: 1.9; font-size: 15px; color: #374151;">
        `;
        
        // Format AI report with proper styling
        const lines = aiReport.split('\n');
        let inSection = false;
        
        lines.forEach(line => {
            line = line.trim();
            if (!line) {
                html += '<br>';
                return;
            }
            
            // Section headers (bold lines or numbered sections)
            if (line.match(/^[#\*]+\s+(.+)/) || line.match(/^\d+[\.\)]\s+(.+)/) || line.match(/^[أ-ي]+[\.\)]\s+(.+)/)) {
                html += `<h4 style="font-size: 17px; font-weight: 800; color: #667eea; margin-top: 25px; margin-bottom: 15px; border-right: 4px solid #667eea; padding-right: 12px;">${line}</h4>`;
                inSection = true;
            }
            // Bullet points
            else if (line.startsWith('-') || line.startsWith('•') || line.startsWith('*')) {
                html += `<div style="margin: 8px 0; padding-right: 20px; position: relative;">
                    <span style="position: absolute; right: 0; color: #667eea; font-weight: 900;">•</span>
                    ${line.substring(1).trim()}
                </div>`;
            }
            // Regular paragraphs
            else {
                html += `<p style="margin: 12px 0;">${line}</p>`;
            }
        });
        
        html += `
                </div>
            </div>
        `;
        $('#ai-tab').html(html);
    }
};
