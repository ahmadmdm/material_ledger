/**
 * Executive Dashboard - Material Ledger
 * Professional CFO-Level Financial Overview
 * Version 1.0.0
 */

frappe.pages['executive-dashboard'].on_page_load = function(wrapper) {
    console.log("🎯 Executive Dashboard v1.0 - Material Ledger");
    
    const userLang = frappe.boot.lang || 'en';
    const isRtl = userLang === 'ar';
    
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: isRtl ? '📊 لوحة التحكم التنفيذية' : '📊 Executive Dashboard',
        single_column: true
    });
    
    // Add professional styles
    addDashboardStyles();
    
    // State management
    let state = {
        loading: false,
        companies: [],
        selectedCompany: null,
        year: new Date().getFullYear(),
        data: null,
        refreshInterval: null
    };
    
    // Translations
    const t = (key) => {
        const trans = {
            en: {
                company: 'Company',
                year: 'Fiscal Year',
                refresh: 'Refresh',
                total_revenue: 'Total Revenue',
                net_profit: 'Net Profit',
                total_assets: 'Total Assets',
                health_score: 'Financial Health',
                roe: 'Return on Equity',
                roa: 'Return on Assets',
                current_ratio: 'Current Ratio',
                debt_ratio: 'Debt Ratio',
                loading: 'Loading...',
                no_data: 'No data available',
                risk_alerts: 'Risk Alerts',
                no_alerts: 'No alerts',
                quick_actions: 'Quick Actions',
                view_ledger: 'View Ledger',
                view_analysis: 'Financial Analysis',
                export_report: 'Export Report',
                settings: 'Settings',
                ai_insights: 'AI Insights',
                trend_up: 'Up',
                trend_down: 'Down',
                vs_last_year: 'vs Last Year',
                excellent: 'Excellent',
                good: 'Good',
                fair: 'Fair',
                poor: 'Poor'
            },
            ar: {
                company: 'الشركة',
                year: 'السنة المالية',
                refresh: 'تحديث',
                total_revenue: 'إجمالي الإيرادات',
                net_profit: 'صافي الربح',
                total_assets: 'إجمالي الأصول',
                health_score: 'الصحة المالية',
                roe: 'العائد على حقوق الملكية',
                roa: 'العائد على الأصول',
                current_ratio: 'نسبة التداول',
                debt_ratio: 'نسبة الديون',
                loading: 'جاري التحميل...',
                no_data: 'لا توجد بيانات',
                risk_alerts: 'تنبيهات المخاطر',
                no_alerts: 'لا توجد تنبيهات',
                quick_actions: 'إجراءات سريعة',
                view_ledger: 'عرض دفتر الأستاذ',
                view_analysis: 'التحليل المالي',
                export_report: 'تصدير التقرير',
                settings: 'الإعدادات',
                ai_insights: 'رؤى الذكاء الاصطناعي',
                trend_up: 'ارتفاع',
                trend_down: 'انخفاض',
                vs_last_year: 'مقارنة بالعام السابق',
                excellent: 'ممتاز',
                good: 'جيد',
                fair: 'متوسط',
                poor: 'ضعيف'
            }
        };
        return trans[isRtl ? 'ar' : 'en'][key] || key;
    };
    
    // Format currency
    const formatCurrency = (value) => {
        return frappe.format(value, { fieldtype: 'Currency' });
    };
    
    // Format percentage
    const formatPercent = (value) => {
        return (value || 0).toFixed(2) + '%';
    };
    
    // Build UI
    buildDashboardUI();
    setupFilters();
    fetchCompanies();
    
    function addDashboardStyles() {
        const styles = `
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
                
                .executive-dashboard {
                    font-family: 'Inter', sans-serif !important;
                    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .dashboard-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px;
                    border-radius: 20px;
                    color: white;
                    margin-bottom: 25px;
                    box-shadow: 0 15px 50px rgba(102, 126, 234, 0.4);
                }
                
                .dashboard-header h1 {
                    margin: 0;
                    font-size: 32px;
                    font-weight: 800;
                }
                
                .dashboard-header .subtitle {
                    opacity: 0.9;
                    margin-top: 8px;
                    font-size: 14px;
                }
                
                .kpi-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 20px;
                    margin-bottom: 25px;
                }
                
                .kpi-card {
                    background: white;
                    border-radius: 16px;
                    padding: 24px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }
                
                .kpi-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 15px 40px rgba(0,0,0,0.15);
                }
                
                .kpi-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 4px;
                    height: 100%;
                }
                
                .kpi-card.revenue::before { background: linear-gradient(180deg, #667eea, #764ba2); }
                .kpi-card.profit::before { background: linear-gradient(180deg, #10b981, #059669); }
                .kpi-card.assets::before { background: linear-gradient(180deg, #3b82f6, #2563eb); }
                .kpi-card.health::before { background: linear-gradient(180deg, #f59e0b, #d97706); }
                
                .kpi-card .icon {
                    width: 50px;
                    height: 50px;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    margin-bottom: 15px;
                }
                
                .kpi-card.revenue .icon { background: rgba(102, 126, 234, 0.1); color: #667eea; }
                .kpi-card.profit .icon { background: rgba(16, 185, 129, 0.1); color: #10b981; }
                .kpi-card.assets .icon { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
                .kpi-card.health .icon { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
                
                .kpi-card .label {
                    font-size: 13px;
                    color: #6b7280;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .kpi-card .value {
                    font-size: 28px;
                    font-weight: 800;
                    color: #1f2937;
                    margin: 8px 0;
                    font-family: 'JetBrains Mono', monospace;
                }
                
                .kpi-card .trend {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 13px;
                    font-weight: 600;
                }
                
                .kpi-card .trend.up { color: #10b981; }
                .kpi-card .trend.down { color: #ef4444; }
                
                .health-score-container {
                    background: white;
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    margin-bottom: 25px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    flex-wrap: wrap;
                    gap: 30px;
                }
                
                .health-score-circle {
                    width: 180px;
                    height: 180px;
                    border-radius: 50%;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }
                
                .health-score-circle.excellent { background: linear-gradient(135deg, #10b981, #059669); }
                .health-score-circle.good { background: linear-gradient(135deg, #3b82f6, #2563eb); }
                .health-score-circle.fair { background: linear-gradient(135deg, #f59e0b, #d97706); }
                .health-score-circle.poor { background: linear-gradient(135deg, #ef4444, #dc2626); }
                
                .health-score-circle .score {
                    font-size: 48px;
                    font-weight: 900;
                    color: white;
                }
                
                .health-score-circle .status {
                    font-size: 14px;
                    color: rgba(255,255,255,0.9);
                    font-weight: 600;
                    text-transform: uppercase;
                }
                
                .ratios-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 20px;
                    flex: 1;
                }
                
                .ratio-item {
                    text-align: center;
                    padding: 15px;
                    background: #f8fafc;
                    border-radius: 12px;
                }
                
                .ratio-item .label {
                    font-size: 12px;
                    color: #6b7280;
                    font-weight: 600;
                    margin-bottom: 8px;
                }
                
                .ratio-item .value {
                    font-size: 24px;
                    font-weight: 800;
                    color: #1f2937;
                }
                
                .alerts-container {
                    background: white;
                    border-radius: 20px;
                    padding: 25px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    margin-bottom: 25px;
                }
                
                .alerts-container h3 {
                    margin: 0 0 20px 0;
                    font-size: 18px;
                    font-weight: 700;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .alert-item {
                    padding: 15px;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    display: flex;
                    align-items: flex-start;
                    gap: 15px;
                }
                
                .alert-item.critical {
                    background: #fef2f2;
                    border-left: 4px solid #dc2626;
                }
                
                .alert-item.warning {
                    background: #fffbeb;
                    border-left: 4px solid #f59e0b;
                }
                
                .alert-item .alert-icon {
                    font-size: 20px;
                }
                
                .alert-item.critical .alert-icon { color: #dc2626; }
                .alert-item.warning .alert-icon { color: #f59e0b; }
                
                .alert-item .alert-content .title {
                    font-weight: 700;
                    font-size: 14px;
                    margin-bottom: 4px;
                }
                
                .alert-item .alert-content .message {
                    font-size: 13px;
                    color: #6b7280;
                }
                
                .quick-actions {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 25px;
                }
                
                .action-btn {
                    background: white;
                    border: 2px solid #e5e7eb;
                    border-radius: 12px;
                    padding: 20px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    color: #1f2937;
                }
                
                .action-btn:hover {
                    border-color: #667eea;
                    background: #f0f4ff;
                    transform: translateY(-2px);
                }
                
                .action-btn .icon {
                    width: 40px;
                    height: 40px;
                    border-radius: 10px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                }
                
                .action-btn .text {
                    font-weight: 600;
                    font-size: 14px;
                }
                
                .loading-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255,255,255,0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                }
                
                .loading-spinner {
                    width: 60px;
                    height: 60px;
                    border: 4px solid #e5e7eb;
                    border-top-color: #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                
                .no-data-message {
                    text-align: center;
                    padding: 60px;
                    color: #6b7280;
                }
                
                .no-data-message i {
                    font-size: 48px;
                    margin-bottom: 15px;
                    color: #d1d5db;
                }
            </style>
        `;
        $('head').append(styles);
    }
    
    function buildDashboardUI() {
        const content = `
            <div class="executive-dashboard">
                <div class="dashboard-header">
                    <h1><i class="fa fa-dashboard"></i> ${isRtl ? 'لوحة التحكم التنفيذية' : 'Executive Dashboard'}</h1>
                    <p class="subtitle">${isRtl ? 'نظرة شاملة على الأداء المالي' : 'Comprehensive Financial Performance Overview'}</p>
                </div>
                
                <div id="kpi-section"></div>
                <div id="health-section"></div>
                <div id="alerts-section"></div>
                <div id="actions-section"></div>
            </div>
        `;
        
        $(wrapper).find('.page-content').html(content);
    }
    
    function setupFilters() {
        page.add_field({
            fieldname: 'company',
            label: t('company'),
            fieldtype: 'Link',
            options: 'Company',
            reqd: 1,
            change: function() {
                const val = this.get_value();
                if (val && val !== state.selectedCompany) {
                    state.selectedCompany = val;
                    fetchData();
                }
            }
        });
        
        page.add_field({
            fieldname: 'year',
            label: t('year'),
            fieldtype: 'Int',
            default: state.year,
            change: function() {
                const val = this.get_value();
                if (val && val !== state.year) {
                    state.year = val;
                    fetchData();
                }
            }
        });
        
        page.set_primary_action(t('refresh'), () => fetchData(), 'fa fa-refresh');
    }
    
    function fetchCompanies() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Company',
                fields: ['name'],
                order_by: 'name asc'
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    state.companies = r.message;
                    if (!state.selectedCompany) {
                        state.selectedCompany = r.message[0].name;
                        page.fields_dict.company.set_value(state.selectedCompany);
                    }
                }
            }
        });
    }
    
    function fetchData() {
        if (!state.selectedCompany) return;
        
        state.loading = true;
        showLoading();
        
        frappe.call({
            method: 'material_ledger.material_ledger.api.get_financial_analysis',
            args: {
                company: state.selectedCompany,
                year: state.year,
                period: 'annual'
            },
            callback: function(r) {
                state.loading = false;
                hideLoading();
                
                if (r.message) {
                    state.data = r.message;
                    renderDashboard();
                } else {
                    renderNoData();
                }
            },
            error: function() {
                state.loading = false;
                hideLoading();
                renderNoData();
            }
        });
    }
    
    function showLoading() {
        if (!$('.loading-overlay').length) {
            $('body').append('<div class="loading-overlay"><div class="loading-spinner"></div></div>');
        }
    }
    
    function hideLoading() {
        $('.loading-overlay').remove();
    }
    
    function renderDashboard() {
        if (!state.data) {
            renderNoData();
            return;
        }
        
        renderKPIs();
        renderHealthScore();
        renderAlerts();
        renderQuickActions();
    }
    
    function renderKPIs() {
        const summary = state.data.summary || {};
        const ratios = state.data.ratios || {};
        const trend = state.data.trend || {};
        
        const income = summary.income || 0;
        const profit = summary.profit || 0;
        const assets = summary.assets || 0;
        const healthScore = summary.health_score || 0;
        
        const prevIncome = trend.prev_year?.income || 0;
        const prevProfit = trend.prev_year?.profit || 0;
        
        const incomeGrowth = prevIncome ? ((income - prevIncome) / prevIncome * 100) : 0;
        const profitGrowth = prevProfit ? ((profit - prevProfit) / Math.abs(prevProfit) * 100) : 0;
        
        const html = `
            <div class="kpi-grid">
                <div class="kpi-card revenue">
                    <div class="icon"><i class="fa fa-line-chart"></i></div>
                    <div class="label">${t('total_revenue')}</div>
                    <div class="value">${formatCurrency(income)}</div>
                    <div class="trend ${incomeGrowth >= 0 ? 'up' : 'down'}">
                        <i class="fa fa-${incomeGrowth >= 0 ? 'arrow-up' : 'arrow-down'}"></i>
                        ${Math.abs(incomeGrowth).toFixed(1)}% ${t('vs_last_year')}
                    </div>
                </div>
                
                <div class="kpi-card profit">
                    <div class="icon"><i class="fa fa-money"></i></div>
                    <div class="label">${t('net_profit')}</div>
                    <div class="value">${formatCurrency(profit)}</div>
                    <div class="trend ${profitGrowth >= 0 ? 'up' : 'down'}">
                        <i class="fa fa-${profitGrowth >= 0 ? 'arrow-up' : 'arrow-down'}"></i>
                        ${Math.abs(profitGrowth).toFixed(1)}% ${t('vs_last_year')}
                    </div>
                </div>
                
                <div class="kpi-card assets">
                    <div class="icon"><i class="fa fa-building"></i></div>
                    <div class="label">${t('total_assets')}</div>
                    <div class="value">${formatCurrency(assets)}</div>
                    <div class="trend up">
                        <i class="fa fa-check-circle"></i>
                        ${isRtl ? 'مستقر' : 'Stable'}
                    </div>
                </div>
                
                <div class="kpi-card health">
                    <div class="icon"><i class="fa fa-heartbeat"></i></div>
                    <div class="label">${t('health_score')}</div>
                    <div class="value">${healthScore}/100</div>
                    <div class="trend ${healthScore >= 60 ? 'up' : 'down'}">
                        <i class="fa fa-${healthScore >= 60 ? 'check-circle' : 'exclamation-circle'}"></i>
                        ${getHealthStatus(healthScore)}
                    </div>
                </div>
            </div>
        `;
        
        $('#kpi-section').html(html);
    }
    
    function renderHealthScore() {
        const summary = state.data.summary || {};
        const ratios = state.data.ratios || {};
        const healthScore = summary.health_score || 0;
        
        let statusClass = 'poor';
        let statusText = t('poor');
        
        if (healthScore >= 80) {
            statusClass = 'excellent';
            statusText = t('excellent');
        } else if (healthScore >= 60) {
            statusClass = 'good';
            statusText = t('good');
        } else if (healthScore >= 40) {
            statusClass = 'fair';
            statusText = t('fair');
        }
        
        const html = `
            <div class="health-score-container">
                <div class="health-score-circle ${statusClass}">
                    <div class="score">${healthScore}</div>
                    <div class="status">${statusText}</div>
                </div>
                
                <div class="ratios-grid">
                    <div class="ratio-item">
                        <div class="label">${t('roe')}</div>
                        <div class="value">${formatPercent(ratios.roe)}</div>
                    </div>
                    <div class="ratio-item">
                        <div class="label">${t('roa')}</div>
                        <div class="value">${formatPercent(ratios.roa)}</div>
                    </div>
                    <div class="ratio-item">
                        <div class="label">${t('current_ratio')}</div>
                        <div class="value">${(ratios.current_ratio || 0).toFixed(2)}</div>
                    </div>
                    <div class="ratio-item">
                        <div class="label">${t('debt_ratio')}</div>
                        <div class="value">${formatPercent(ratios.debt_ratio)}</div>
                    </div>
                    <div class="ratio-item">
                        <div class="label">Z-Score</div>
                        <div class="value">${(ratios.z_score || 0).toFixed(2)}</div>
                    </div>
                    <div class="ratio-item">
                        <div class="label">DuPont ROE</div>
                        <div class="value">${formatPercent(ratios.dupont_roe)}</div>
                    </div>
                </div>
            </div>
        `;
        
        $('#health-section').html(html);
    }
    
    function renderAlerts() {
        const riskFlags = state.data.risk_flags || [];
        
        let alertsHtml = '';
        
        if (riskFlags.length === 0) {
            alertsHtml = `
                <div style="text-align: center; padding: 30px; color: #10b981;">
                    <i class="fa fa-check-circle" style="font-size: 32px; margin-bottom: 10px;"></i>
                    <p style="margin: 0; font-weight: 600;">${t('no_alerts')}</p>
                </div>
            `;
        } else {
            alertsHtml = riskFlags.map(flag => `
                <div class="alert-item ${flag.level}">
                    <div class="alert-icon">
                        <i class="fa fa-${flag.level === 'critical' ? 'exclamation-circle' : 'exclamation-triangle'}"></i>
                    </div>
                    <div class="alert-content">
                        <div class="title">${flag.title}</div>
                        <div class="message">${flag.message}</div>
                    </div>
                </div>
            `).join('');
        }
        
        const html = `
            <div class="alerts-container">
                <h3>
                    <i class="fa fa-bell"></i>
                    ${t('risk_alerts')}
                    ${riskFlags.length > 0 ? `<span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">${riskFlags.length}</span>` : ''}
                </h3>
                ${alertsHtml}
            </div>
        `;
        
        $('#alerts-section').html(html);
    }
    
    function renderQuickActions() {
        const html = `
            <div class="quick-actions">
                <a href="/app/material-ledger-report" class="action-btn">
                    <div class="icon"><i class="fa fa-book"></i></div>
                    <div class="text">${t('view_ledger')}</div>
                </a>
                <a href="/app/financial-analysis" class="action-btn">
                    <div class="icon"><i class="fa fa-line-chart"></i></div>
                    <div class="text">${t('view_analysis')}</div>
                </a>
                <a href="#" class="action-btn" onclick="frappe.set_route('Form', 'Material Ledger Settings'); return false;">
                    <div class="icon"><i class="fa fa-cog"></i></div>
                    <div class="text">${t('settings')}</div>
                </a>
            </div>
        `;
        
        $('#actions-section').html(html);
    }
    
    function renderNoData() {
        const html = `
            <div class="no-data-message">
                <i class="fa fa-database"></i>
                <p>${t('no_data')}</p>
            </div>
        `;
        
        $('#kpi-section').html(html);
        $('#health-section').html('');
        $('#alerts-section').html('');
        $('#actions-section').html('');
    }
    
    function getHealthStatus(score) {
        if (score >= 80) return t('excellent');
        if (score >= 60) return t('good');
        if (score >= 40) return t('fair');
        return t('poor');
    }
};
