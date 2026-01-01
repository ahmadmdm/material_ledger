/**
 * Custom Dashboard Widgets Module
 * Customizable dashboard with drag-and-drop widgets
 */

const FinancialDashboardWidgets = {
    // Widget registry
    widgets: {},
    
    // Dashboard layout
    layout: [],
    
    // Available widget types
    widgetTypes: {
        kpi: {
            name: 'KPI Card',
            nameAr: 'بطاقة مؤشر',
            icon: 'fa-chart-line',
            defaultSize: { w: 1, h: 1 }
        },
        chart: {
            name: 'Chart',
            nameAr: 'رسم بياني',
            icon: 'fa-bar-chart',
            defaultSize: { w: 2, h: 2 }
        },
        table: {
            name: 'Data Table',
            nameAr: 'جدول بيانات',
            icon: 'fa-table',
            defaultSize: { w: 2, h: 2 }
        },
        alerts: {
            name: 'Alerts',
            nameAr: 'التنبيهات',
            icon: 'fa-bell',
            defaultSize: { w: 1, h: 2 }
        },
        summary: {
            name: 'Summary',
            nameAr: 'ملخص',
            icon: 'fa-list-ul',
            defaultSize: { w: 2, h: 1 }
        },
        comparison: {
            name: 'Period Comparison',
            nameAr: 'مقارنة الفترات',
            icon: 'fa-columns',
            defaultSize: { w: 2, h: 2 }
        },
        trend: {
            name: 'Trend Indicator',
            nameAr: 'مؤشر الاتجاه',
            icon: 'fa-line-chart',
            defaultSize: { w: 1, h: 1 }
        },
        gauge: {
            name: 'Gauge',
            nameAr: 'مقياس',
            icon: 'fa-tachometer',
            defaultSize: { w: 1, h: 1 }
        }
    },

    // Initialize dashboard
    init() {
        this.loadSavedLayout();
        this.render();
    },

    // Load saved layout from localStorage
    loadSavedLayout() {
        const saved = localStorage.getItem('financial_dashboard_layout');
        if (saved) {
            try {
                this.layout = JSON.parse(saved);
            } catch (e) {
                this.layout = this.getDefaultLayout();
            }
        } else {
            this.layout = this.getDefaultLayout();
        }
    },

    // Get default layout
    getDefaultLayout() {
        return [
            { id: 'revenue-kpi', type: 'kpi', config: { metric: 'revenue' }, x: 0, y: 0, w: 1, h: 1 },
            { id: 'profit-kpi', type: 'kpi', config: { metric: 'profit' }, x: 1, y: 0, w: 1, h: 1 },
            { id: 'assets-kpi', type: 'kpi', config: { metric: 'assets' }, x: 2, y: 0, w: 1, h: 1 },
            { id: 'health-gauge', type: 'gauge', config: { metric: 'health_score' }, x: 3, y: 0, w: 1, h: 1 },
            { id: 'revenue-chart', type: 'chart', config: { chartType: 'line', metric: 'revenue_trend' }, x: 0, y: 1, w: 2, h: 2 },
            { id: 'expense-chart', type: 'chart', config: { chartType: 'doughnut', metric: 'expense_breakdown' }, x: 2, y: 1, w: 2, h: 2 },
            { id: 'alerts-widget', type: 'alerts', config: {}, x: 0, y: 3, w: 1, h: 2 },
            { id: 'ratio-table', type: 'table', config: { data: 'ratios' }, x: 1, y: 3, w: 2, h: 2 }
        ];
    },

    // Save layout
    saveLayout() {
        localStorage.setItem('financial_dashboard_layout', JSON.stringify(this.layout));
    },

    // Render dashboard
    render(containerId = 'custom-dashboard') {
        const isArabic = frappe.boot.lang === 'ar';
        
        const $container = $(`#${containerId}`);
        if (!$container.length) return;

        const html = `
            <div class="dashboard-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="margin: 0; font-size: 18px; font-weight: 700; color: #1f2937;">
                    <i class="fa fa-th-large" style="margin-${isArabic ? 'left' : 'right'}: 10px; color: #667eea;"></i>
                    ${isArabic ? 'لوحة التحكم المخصصة' : 'Custom Dashboard'}
                </h3>
                <div class="dashboard-actions" style="display: flex; gap: 10px;">
                    <button class="btn-add-widget" style="
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        border: none;
                        padding: 8px 15px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 13px;
                    ">
                        <i class="fa fa-plus"></i> ${isArabic ? 'إضافة عنصر' : 'Add Widget'}
                    </button>
                    <button class="btn-edit-mode" style="
                        background: #f3f4f6;
                        color: #374151;
                        border: 1px solid #e5e7eb;
                        padding: 8px 15px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 13px;
                    ">
                        <i class="fa fa-edit"></i> ${isArabic ? 'تحرير' : 'Edit'}
                    </button>
                    <button class="btn-reset-layout" style="
                        background: #f3f4f6;
                        color: #374151;
                        border: 1px solid #e5e7eb;
                        padding: 8px 15px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 13px;
                    ">
                        <i class="fa fa-refresh"></i> ${isArabic ? 'إعادة تعيين' : 'Reset'}
                    </button>
                </div>
            </div>
            <div class="dashboard-grid" style="
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                grid-auto-rows: 120px;
                gap: 15px;
            ">
                ${this.layout.map(widget => this.renderWidget(widget)).join('')}
            </div>
        `;

        $container.html(html);

        // Event handlers
        $container.find('.btn-add-widget').on('click', () => this.showAddWidgetDialog());
        $container.find('.btn-edit-mode').on('click', () => this.toggleEditMode());
        $container.find('.btn-reset-layout').on('click', () => this.resetLayout());

        // Initialize widgets
        this.initializeWidgets();
    },

    // Render single widget
    renderWidget(widget) {
        const isArabic = frappe.boot.lang === 'ar';
        const type = this.widgetTypes[widget.type];

        return `
            <div class="dashboard-widget" 
                 data-widget-id="${widget.id}"
                 data-widget-type="${widget.type}"
                 style="
                    grid-column: span ${widget.w};
                    grid-row: span ${widget.h};
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 2px 15px rgba(0,0,0,0.06);
                    padding: 15px;
                    position: relative;
                    overflow: hidden;
                    transition: all 0.3s;
                 ">
                <div class="widget-header" style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                ">
                    <span style="font-size: 12px; font-weight: 600; color: #6b7280;">
                        <i class="fa ${type.icon}" style="margin-${isArabic ? 'left' : 'right'}: 5px;"></i>
                        ${isArabic ? type.nameAr : type.name}
                    </span>
                    <div class="widget-actions edit-mode-only" style="display: none;">
                        <button class="widget-btn widget-settings" style="
                            background: none;
                            border: none;
                            color: #9ca3af;
                            cursor: pointer;
                            padding: 5px;
                        ">
                            <i class="fa fa-cog"></i>
                        </button>
                        <button class="widget-btn widget-remove" style="
                            background: none;
                            border: none;
                            color: #ef4444;
                            cursor: pointer;
                            padding: 5px;
                        ">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                </div>
                <div class="widget-content" id="widget-content-${widget.id}">
                    <div style="text-align: center; padding: 20px; color: #9ca3af;">
                        <i class="fa fa-spinner fa-spin fa-2x"></i>
                    </div>
                </div>
            </div>
        `;
    },

    // Initialize widgets with data
    initializeWidgets() {
        this.layout.forEach(widget => {
            this.loadWidgetData(widget);
        });

        // Setup widget actions
        $('.widget-settings').on('click', function() {
            const widgetId = $(this).closest('.dashboard-widget').data('widget-id');
            FinancialDashboardWidgets.showWidgetSettings(widgetId);
        });

        $('.widget-remove').on('click', function() {
            const widgetId = $(this).closest('.dashboard-widget').data('widget-id');
            FinancialDashboardWidgets.removeWidget(widgetId);
        });
    },

    // Load widget data
    loadWidgetData(widget) {
        const $content = $(`#widget-content-${widget.id}`);
        
        switch (widget.type) {
            case 'kpi':
                this.renderKPIWidget($content, widget.config);
                break;
            case 'chart':
                this.renderChartWidget($content, widget);
                break;
            case 'table':
                this.renderTableWidget($content, widget.config);
                break;
            case 'alerts':
                this.renderAlertsWidget($content);
                break;
            case 'gauge':
                this.renderGaugeWidget($content, widget.config);
                break;
            case 'trend':
                this.renderTrendWidget($content, widget.config);
                break;
            case 'summary':
                this.renderSummaryWidget($content, widget.config);
                break;
            default:
                $content.html('<div style="text-align: center; color: #9ca3af;">Widget type not supported</div>');
        }
    },

    // Render KPI widget
    renderKPIWidget($content, config) {
        const isArabic = frappe.boot.lang === 'ar';
        const data = this.getFinancialData();
        
        const metrics = {
            revenue: { label: isArabic ? 'الإيرادات' : 'Revenue', value: data.income || 0, icon: 'fa-money', color: '#10b981' },
            profit: { label: isArabic ? 'صافي الربح' : 'Net Profit', value: data.profit || 0, icon: 'fa-trending-up', color: '#667eea' },
            assets: { label: isArabic ? 'الأصول' : 'Assets', value: data.assets || 0, icon: 'fa-building', color: '#f59e0b' },
            expenses: { label: isArabic ? 'المصروفات' : 'Expenses', value: data.expense || 0, icon: 'fa-credit-card', color: '#ef4444' }
        };

        const metric = metrics[config.metric] || metrics.revenue;
        const change = this.calculateChange(config.metric);

        $content.html(`
            <div style="text-align: center;">
                <div style="
                    width: 50px;
                    height: 50px;
                    background: ${metric.color}15;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 10px;
                ">
                    <i class="fa ${metric.icon}" style="font-size: 20px; color: ${metric.color};"></i>
                </div>
                <div style="font-size: 20px; font-weight: 700; color: #1f2937; margin-bottom: 5px;">
                    ${frappe.format(metric.value, {fieldtype: 'Currency'})}
                </div>
                <div style="font-size: 12px; color: #6b7280;">${metric.label}</div>
                ${change !== null ? `
                <div style="
                    font-size: 11px;
                    color: ${change >= 0 ? '#10b981' : '#ef4444'};
                    margin-top: 5px;
                ">
                    <i class="fa fa-${change >= 0 ? 'arrow-up' : 'arrow-down'}"></i>
                    ${Math.abs(change).toFixed(1)}%
                </div>
                ` : ''}
            </div>
        `);
    },

    // Render chart widget
    renderChartWidget($content, widget) {
        const chartId = `chart-${widget.id}`;
        $content.html(`<canvas id="${chartId}" style="max-height: 100%;"></canvas>`);

        // Sample chart data
        const ctx = document.getElementById(chartId);
        if (ctx && window.Chart) {
            new Chart(ctx, {
                type: widget.config.chartType || 'line',
                data: {
                    labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
                    datasets: [{
                        label: 'الإيرادات',
                        data: [65000, 72000, 68000, 85000, 90000, 95000],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    },

    // Render table widget
    renderTableWidget($content, config) {
        const isArabic = frappe.boot.lang === 'ar';
        const data = this.getFinancialData();
        const ratios = data.ratios || {};

        const rows = [
            { label: isArabic ? 'العائد على حقوق الملكية' : 'ROE', value: `${(ratios.roe || 0).toFixed(2)}%` },
            { label: isArabic ? 'العائد على الأصول' : 'ROA', value: `${(ratios.roa || 0).toFixed(2)}%` },
            { label: isArabic ? 'نسبة التداول' : 'Current Ratio', value: (ratios.current_ratio || 0).toFixed(2) },
            { label: isArabic ? 'نسبة الدين' : 'Debt Ratio', value: `${(ratios.debt_ratio || 0).toFixed(2)}%` }
        ];

        $content.html(`
            <table style="width: 100%; font-size: 12px;">
                ${rows.map(row => `
                    <tr style="border-bottom: 1px solid #f3f4f6;">
                        <td style="padding: 8px 0; color: #6b7280;">${row.label}</td>
                        <td style="padding: 8px 0; text-align: ${isArabic ? 'left' : 'right'}; font-weight: 600; color: #1f2937;">
                            ${row.value}
                        </td>
                    </tr>
                `).join('')}
            </table>
        `);
    },

    // Render alerts widget
    renderAlertsWidget($content) {
        const isArabic = frappe.boot.lang === 'ar';
        const alerts = this.getAlerts();

        if (alerts.length === 0) {
            $content.html(`
                <div style="text-align: center; padding: 20px; color: #10b981;">
                    <i class="fa fa-check-circle fa-2x"></i>
                    <div style="margin-top: 10px; font-size: 13px;">
                        ${isArabic ? 'لا توجد تنبيهات' : 'No alerts'}
                    </div>
                </div>
            `);
            return;
        }

        $content.html(`
            <div style="max-height: 150px; overflow-y: auto;">
                ${alerts.slice(0, 5).map(alert => `
                    <div style="
                        padding: 8px 10px;
                        margin-bottom: 8px;
                        background: ${alert.type === 'critical' ? '#fef2f2' : '#fefce8'};
                        border-radius: 8px;
                        border-right: 3px solid ${alert.type === 'critical' ? '#ef4444' : '#f59e0b'};
                        font-size: 11px;
                    ">
                        <i class="fa fa-${alert.type === 'critical' ? 'exclamation-circle' : 'warning'}" 
                           style="color: ${alert.type === 'critical' ? '#ef4444' : '#f59e0b'};"></i>
                        ${alert.message}
                    </div>
                `).join('')}
            </div>
        `);
    },

    // Render gauge widget
    renderGaugeWidget($content, config) {
        const data = this.getFinancialData();
        const score = data.health_score || 75;
        const color = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444';

        $content.html(`
            <div style="text-align: center;">
                <div style="
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    background: conic-gradient(${color} ${score * 3.6}deg, #e5e7eb ${score * 3.6}deg);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto;
                ">
                    <div style="
                        width: 60px;
                        height: 60px;
                        background: white;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 18px;
                        font-weight: 700;
                        color: ${color};
                    ">
                        ${score}
                    </div>
                </div>
                <div style="font-size: 11px; color: #6b7280; margin-top: 8px;">
                    ${frappe.boot.lang === 'ar' ? 'درجة الصحة' : 'Health Score'}
                </div>
            </div>
        `);
    },

    // Render trend widget
    renderTrendWidget($content, config) {
        const isArabic = frappe.boot.lang === 'ar';
        const trend = 12.5; // Sample trend
        const isPositive = trend >= 0;

        $content.html(`
            <div style="text-align: center;">
                <div style="
                    font-size: 32px;
                    font-weight: 700;
                    color: ${isPositive ? '#10b981' : '#ef4444'};
                ">
                    <i class="fa fa-${isPositive ? 'arrow-up' : 'arrow-down'}"></i>
                    ${Math.abs(trend).toFixed(1)}%
                </div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">
                    ${isArabic ? 'التغير الشهري' : 'Monthly Change'}
                </div>
            </div>
        `);
    },

    // Render summary widget
    renderSummaryWidget($content, config) {
        const isArabic = frappe.boot.lang === 'ar';
        const data = this.getFinancialData();

        $content.html(`
            <div style="display: flex; justify-content: space-around; align-items: center; height: 100%;">
                <div style="text-align: center;">
                    <div style="font-size: 16px; font-weight: 700; color: #10b981;">
                        ${frappe.format(data.income || 0, {fieldtype: 'Currency'})}
                    </div>
                    <div style="font-size: 11px; color: #6b7280;">${isArabic ? 'إيرادات' : 'Revenue'}</div>
                </div>
                <div style="width: 1px; height: 40px; background: #e5e7eb;"></div>
                <div style="text-align: center;">
                    <div style="font-size: 16px; font-weight: 700; color: #ef4444;">
                        ${frappe.format(data.expense || 0, {fieldtype: 'Currency'})}
                    </div>
                    <div style="font-size: 11px; color: #6b7280;">${isArabic ? 'مصروفات' : 'Expenses'}</div>
                </div>
                <div style="width: 1px; height: 40px; background: #e5e7eb;"></div>
                <div style="text-align: center;">
                    <div style="font-size: 16px; font-weight: 700; color: #667eea;">
                        ${frappe.format(data.profit || 0, {fieldtype: 'Currency'})}
                    </div>
                    <div style="font-size: 11px; color: #6b7280;">${isArabic ? 'ربح' : 'Profit'}</div>
                </div>
            </div>
        `);
    },

    // Show add widget dialog
    showAddWidgetDialog() {
        const isArabic = frappe.boot.lang === 'ar';

        const d = new frappe.ui.Dialog({
            title: isArabic ? 'إضافة عنصر' : 'Add Widget',
            fields: [
                {
                    fieldname: 'widget_type',
                    label: isArabic ? 'نوع العنصر' : 'Widget Type',
                    fieldtype: 'Select',
                    options: Object.entries(this.widgetTypes).map(([key, val]) => ({
                        value: key,
                        label: isArabic ? val.nameAr : val.name
                    })),
                    reqd: 1
                }
            ],
            primary_action_label: isArabic ? 'إضافة' : 'Add',
            primary_action: (values) => {
                this.addWidget(values.widget_type);
                d.hide();
            }
        });

        d.show();
    },

    // Add widget
    addWidget(type) {
        const widgetType = this.widgetTypes[type];
        const newWidget = {
            id: `widget-${Date.now()}`,
            type: type,
            config: {},
            x: 0,
            y: this.layout.length,
            w: widgetType.defaultSize.w,
            h: widgetType.defaultSize.h
        };

        this.layout.push(newWidget);
        this.saveLayout();
        this.render();
    },

    // Remove widget
    removeWidget(widgetId) {
        this.layout = this.layout.filter(w => w.id !== widgetId);
        this.saveLayout();
        $(`.dashboard-widget[data-widget-id="${widgetId}"]`).fadeOut(300, function() {
            $(this).remove();
        });
    },

    // Toggle edit mode
    toggleEditMode() {
        const $dashboard = $('.dashboard-grid');
        const isEditing = $dashboard.hasClass('edit-mode');

        if (isEditing) {
            $dashboard.removeClass('edit-mode');
            $('.edit-mode-only').hide();
            $('.btn-edit-mode').html(`<i class="fa fa-edit"></i> ${frappe.boot.lang === 'ar' ? 'تحرير' : 'Edit'}`);
        } else {
            $dashboard.addClass('edit-mode');
            $('.edit-mode-only').show();
            $('.btn-edit-mode').html(`<i class="fa fa-check"></i> ${frappe.boot.lang === 'ar' ? 'حفظ' : 'Save'}`);
        }
    },

    // Reset layout
    resetLayout() {
        const isArabic = frappe.boot.lang === 'ar';
        
        frappe.confirm(
            isArabic ? 'هل أنت متأكد من إعادة تعيين التخطيط؟' : 'Are you sure you want to reset the layout?',
            () => {
                this.layout = this.getDefaultLayout();
                this.saveLayout();
                this.render();
            }
        );
    },

    // Get financial data (from global state or cache)
    getFinancialData() {
        return window.financialData || {};
    },

    // Calculate change percentage
    calculateChange(metric) {
        // This would compare with previous period
        return Math.random() * 20 - 10; // Sample random change
    },

    // Get alerts
    getAlerts() {
        const data = this.getFinancialData();
        const alerts = [];
        const isArabic = frappe.boot.lang === 'ar';

        if (data.profit < 0) {
            alerts.push({
                type: 'critical',
                message: isArabic ? 'صافي الربح سالب' : 'Net profit is negative'
            });
        }

        if ((data.ratios?.current_ratio || 0) < 1) {
            alerts.push({
                type: 'warning',
                message: isArabic ? 'نسبة التداول منخفضة' : 'Low current ratio'
            });
        }

        return alerts;
    },

    // Show widget settings
    showWidgetSettings(widgetId) {
        const widget = this.layout.find(w => w.id === widgetId);
        if (!widget) return;

        const isArabic = frappe.boot.lang === 'ar';

        const d = new frappe.ui.Dialog({
            title: isArabic ? 'إعدادات العنصر' : 'Widget Settings',
            fields: [
                {
                    fieldname: 'size',
                    label: isArabic ? 'الحجم' : 'Size',
                    fieldtype: 'Select',
                    options: [
                        { value: '1x1', label: '1x1' },
                        { value: '2x1', label: '2x1' },
                        { value: '2x2', label: '2x2' },
                        { value: '1x2', label: '1x2' }
                    ],
                    default: `${widget.w}x${widget.h}`
                }
            ],
            primary_action_label: isArabic ? 'حفظ' : 'Save',
            primary_action: (values) => {
                const [w, h] = values.size.split('x').map(Number);
                widget.w = w;
                widget.h = h;
                this.saveLayout();
                this.render();
                d.hide();
            }
        });

        d.show();
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinancialDashboardWidgets;
}
