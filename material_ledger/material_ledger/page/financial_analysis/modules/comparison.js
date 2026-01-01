/**
 * Company Comparison Module
 * Compare financial metrics across multiple companies
 */

const FinancialComparison = {
    // Configuration
    config: {
        maxCompanies: 5,
        metrics: ['revenue', 'profit', 'assets', 'roe', 'roa', 'currentRatio', 'debtRatio']
    },

    // Comparison data
    data: {},
    companies: [],

    // Initialize comparison module
    init() {
        this.createComparisonUI();
    },

    // Create comparison UI
    createComparisonUI() {
        const isArabic = frappe.boot.lang === 'ar';
        
        const html = `
            <div id="company-comparison-section" style="display: none; margin-bottom: 25px;">
                <div style="background: white; border-radius: 16px; box-shadow: 0 4px 25px rgba(0,0,0,0.08); overflow: hidden;">
                    <div style="padding: 20px 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3 style="margin: 0; font-size: 18px; font-weight: 700;">
                                <i class="fa fa-columns" style="margin-${isArabic ? 'left' : 'right'}: 10px;"></i>
                                ${isArabic ? 'مقارنة الشركات' : 'Company Comparison'}
                            </h3>
                            <button id="close-comparison" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 8px 15px; border-radius: 8px; cursor: pointer; font-weight: 600;">
                                <i class="fa fa-times"></i> ${isArabic ? 'إغلاق' : 'Close'}
                            </button>
                        </div>
                    </div>
                    
                    <div style="padding: 25px;">
                        <div id="comparison-companies" style="display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 20px;">
                            <div class="comparison-add-btn" style="
                                width: 150px;
                                height: 80px;
                                border: 2px dashed #d1d5db;
                                border-radius: 12px;
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                justify-content: center;
                                cursor: pointer;
                                transition: all 0.3s;
                                color: #9ca3af;
                            ">
                                <i class="fa fa-plus" style="font-size: 24px; margin-bottom: 5px;"></i>
                                <span style="font-size: 12px; font-weight: 600;">${isArabic ? 'إضافة شركة' : 'Add Company'}</span>
                            </div>
                        </div>
                        
                        <div id="comparison-chart-container" style="height: 400px; display: none;"></div>
                        
                        <div id="comparison-table-container" style="display: none; margin-top: 20px;">
                            <table id="comparison-table" style="width: 100%; border-collapse: collapse;">
                                <thead></thead>
                                <tbody></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('#comparison-container').html(html);
        
        // Event handlers
        $('.comparison-add-btn').on('click', () => this.showAddCompanyDialog());
        $('#close-comparison').on('click', () => this.hide());
    },

    // Show comparison section
    show() {
        $('#company-comparison-section').slideDown(300);
    },

    // Hide comparison section
    hide() {
        $('#company-comparison-section').slideUp(300);
        this.clear();
    },

    // Show add company dialog
    showAddCompanyDialog() {
        const isArabic = frappe.boot.lang === 'ar';
        
        if (this.companies.length >= this.config.maxCompanies) {
            frappe.msgprint(isArabic ? 
                `الحد الأقصى ${this.config.maxCompanies} شركات` : 
                `Maximum ${this.config.maxCompanies} companies allowed`
            );
            return;
        }

        const d = new frappe.ui.Dialog({
            title: isArabic ? 'إضافة شركة للمقارنة' : 'Add Company to Compare',
            fields: [
                {
                    fieldname: 'company',
                    label: isArabic ? 'الشركة' : 'Company',
                    fieldtype: 'Link',
                    options: 'Company',
                    reqd: 1,
                    get_query: () => {
                        return {
                            filters: {
                                name: ['not in', this.companies]
                            }
                        };
                    }
                },
                {
                    fieldname: 'year',
                    label: isArabic ? 'السنة' : 'Year',
                    fieldtype: 'Int',
                    default: new Date().getFullYear(),
                    reqd: 1
                }
            ],
            primary_action_label: isArabic ? 'إضافة' : 'Add',
            primary_action: (values) => {
                this.addCompany(values.company, values.year);
                d.hide();
            }
        });
        
        d.show();
    },

    // Add company to comparison
    addCompany(company, year) {
        if (this.companies.includes(company)) return;
        
        this.companies.push(company);
        this.fetchCompanyData(company, year);
        this.renderCompanyCard(company);
    },

    // Remove company from comparison
    removeCompany(company) {
        this.companies = this.companies.filter(c => c !== company);
        delete this.data[company];
        $(`.comparison-company-card[data-company="${company}"]`).remove();
        this.updateCharts();
    },

    // Fetch company data
    fetchCompanyData(company, year) {
        const isArabic = frappe.boot.lang === 'ar';
        
        frappe.xcall('material_ledger.material_ledger.api.get_financial_analysis', {
            company: company,
            year: year,
            period: 'annual',
            sections: JSON.stringify(['ratios', 'dashboard'])
        }).then(data => {
            this.data[company] = {
                year: year,
                summary: data.summary || {},
                ratios: data.ratios || {}
            };
            this.updateCharts();
        }).catch(err => {
            console.error('Failed to fetch comparison data:', err);
            frappe.show_alert({
                message: isArabic ? 'فشل في جلب بيانات الشركة' : 'Failed to fetch company data',
                indicator: 'red'
            });
        });
    },

    // Render company card
    renderCompanyCard(company) {
        const isArabic = frappe.boot.lang === 'ar';
        
        const colors = ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a'];
        const colorIndex = this.companies.indexOf(company) % colors.length;
        
        const card = $(`
            <div class="comparison-company-card" data-company="${company}" style="
                background: linear-gradient(135deg, ${colors[colorIndex]} 0%, ${colors[(colorIndex + 1) % colors.length]} 100%);
                color: white;
                padding: 15px 20px;
                border-radius: 12px;
                min-width: 150px;
                position: relative;
            ">
                <button class="remove-company-btn" style="
                    position: absolute;
                    top: 5px;
                    ${isArabic ? 'left' : 'right'}: 5px;
                    background: rgba(255,255,255,0.3);
                    border: none;
                    color: white;
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    cursor: pointer;
                    font-size: 12px;
                ">
                    <i class="fa fa-times"></i>
                </button>
                <div style="font-weight: 700; font-size: 14px; margin-bottom: 5px;">${company}</div>
                <div style="font-size: 11px; opacity: 0.9;">
                    <i class="fa fa-spinner fa-spin"></i> ${isArabic ? 'جاري التحميل...' : 'Loading...'}
                </div>
            </div>
        `);
        
        card.find('.remove-company-btn').on('click', () => this.removeCompany(company));
        
        card.insertBefore('.comparison-add-btn');
    },

    // Update company card with data
    updateCompanyCard(company) {
        const data = this.data[company];
        if (!data) return;
        
        const isArabic = frappe.boot.lang === 'ar';
        const summary = data.summary;
        
        const $card = $(`.comparison-company-card[data-company="${company}"]`);
        $card.find('div:last').html(`
            <div style="font-size: 11px; opacity: 0.9;">
                ${isArabic ? 'الإيرادات:' : 'Revenue:'} ${frappe.format(summary.income || 0, {fieldtype: 'Currency'})}
            </div>
        `);
    },

    // Update comparison charts
    updateCharts() {
        if (this.companies.length < 2) {
            $('#comparison-chart-container, #comparison-table-container').hide();
            return;
        }
        
        $('#comparison-chart-container, #comparison-table-container').show();
        
        // Update cards
        this.companies.forEach(company => this.updateCompanyCard(company));
        
        // Render chart
        this.renderComparisonChart();
        
        // Render table
        this.renderComparisonTable();
    },

    // Render comparison chart
    renderComparisonChart() {
        const isArabic = frappe.boot.lang === 'ar';
        
        const ctx = document.getElementById('comparison-chart');
        if (!ctx) {
            $('#comparison-chart-container').html('<canvas id="comparison-chart"></canvas>');
        }
        
        const labels = this.companies;
        const metrics = {
            revenue: { label: isArabic ? 'الإيرادات' : 'Revenue', color: '#667eea' },
            profit: { label: isArabic ? 'الربح' : 'Profit', color: '#10b981' },
            roe: { label: 'ROE %', color: '#f59e0b' }
        };
        
        const datasets = [];
        
        // Revenue comparison
        datasets.push({
            label: metrics.revenue.label,
            data: this.companies.map(c => this.data[c]?.summary?.income || 0),
            backgroundColor: metrics.revenue.color,
            borderRadius: 8
        });
        
        // Profit comparison
        datasets.push({
            label: metrics.profit.label,
            data: this.companies.map(c => this.data[c]?.summary?.profit || 0),
            backgroundColor: metrics.profit.color,
            borderRadius: 8
        });
        
        if (window.Chart) {
            // Destroy existing chart
            if (this.chart) {
                this.chart.destroy();
            }
            
            this.chart = new Chart(document.getElementById('comparison-chart'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + 
                                           context.parsed.y.toLocaleString(isArabic ? 'ar-SA' : 'en-US');
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return value.toLocaleString(isArabic ? 'ar-SA' : 'en-US');
                                }
                            }
                        }
                    }
                }
            });
        }
    },

    // Render comparison table
    renderComparisonTable() {
        const isArabic = frappe.boot.lang === 'ar';
        
        const metrics = [
            { key: 'income', label: isArabic ? 'الإيرادات' : 'Revenue', format: 'Currency' },
            { key: 'expense', label: isArabic ? 'المصروفات' : 'Expenses', format: 'Currency' },
            { key: 'profit', label: isArabic ? 'صافي الربح' : 'Net Profit', format: 'Currency' },
            { key: 'assets', label: isArabic ? 'الأصول' : 'Assets', format: 'Currency' },
            { key: 'liabilities', label: isArabic ? 'الالتزامات' : 'Liabilities', format: 'Currency' },
            { key: 'equity', label: isArabic ? 'حقوق الملكية' : 'Equity', format: 'Currency' },
            { key: 'health_score', label: isArabic ? 'درجة الصحة' : 'Health Score', format: 'Score' }
        ];
        
        const ratioMetrics = [
            { key: 'roe', label: 'ROE', format: 'Percent' },
            { key: 'roa', label: 'ROA', format: 'Percent' },
            { key: 'current_ratio', label: isArabic ? 'نسبة التداول' : 'Current Ratio', format: 'Ratio' },
            { key: 'debt_ratio', label: isArabic ? 'نسبة الدين' : 'Debt Ratio', format: 'Percent' },
            { key: 'net_margin', label: isArabic ? 'هامش الربح' : 'Profit Margin', format: 'Percent' }
        ];
        
        let theadHTML = `<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <th style="padding: 15px; text-align: ${isArabic ? 'right' : 'left'}; font-weight: 700;">
                ${isArabic ? 'المقياس' : 'Metric'}
            </th>`;
        
        this.companies.forEach(company => {
            theadHTML += `<th style="padding: 15px; text-align: center; font-weight: 700;">${company}</th>`;
        });
        
        theadHTML += '</tr>';
        
        let tbodyHTML = '';
        
        // Summary metrics
        metrics.forEach((metric, index) => {
            tbodyHTML += `<tr style="background: ${index % 2 === 0 ? '#f9fafb' : 'white'};">
                <td style="padding: 12px 15px; font-weight: 600; color: #374151;">${metric.label}</td>`;
            
            this.companies.forEach(company => {
                const value = this.data[company]?.summary?.[metric.key] || 0;
                let formatted;
                
                switch (metric.format) {
                    case 'Currency':
                        formatted = frappe.format(value, {fieldtype: 'Currency'});
                        break;
                    case 'Score':
                        formatted = `<span style="font-weight: 700; color: ${value >= 60 ? '#10b981' : '#ef4444'};">${value}/100</span>`;
                        break;
                    default:
                        formatted = value.toLocaleString();
                }
                
                tbodyHTML += `<td style="padding: 12px 15px; text-align: center;">${formatted}</td>`;
            });
            
            tbodyHTML += '</tr>';
        });
        
        // Separator
        tbodyHTML += `<tr style="background: #e5e7eb;">
            <td colspan="${this.companies.length + 1}" style="padding: 10px 15px; font-weight: 700; color: #667eea;">
                ${isArabic ? 'النسب المالية' : 'Financial Ratios'}
            </td>
        </tr>`;
        
        // Ratio metrics
        ratioMetrics.forEach((metric, index) => {
            tbodyHTML += `<tr style="background: ${index % 2 === 0 ? '#f9fafb' : 'white'};">
                <td style="padding: 12px 15px; font-weight: 600; color: #374151;">${metric.label}</td>`;
            
            this.companies.forEach(company => {
                const value = this.data[company]?.ratios?.[metric.key] || 0;
                let formatted;
                
                switch (metric.format) {
                    case 'Percent':
                        formatted = `${value.toFixed(2)}%`;
                        break;
                    case 'Ratio':
                        formatted = value.toFixed(2);
                        break;
                    default:
                        formatted = value.toFixed(2);
                }
                
                tbodyHTML += `<td style="padding: 12px 15px; text-align: center; font-weight: 600;">${formatted}</td>`;
            });
            
            tbodyHTML += '</tr>';
        });
        
        $('#comparison-table thead').html(theadHTML);
        $('#comparison-table tbody').html(tbodyHTML);
    },

    // Clear comparison
    clear() {
        this.companies = [];
        this.data = {};
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        $('.comparison-company-card').remove();
        $('#comparison-chart-container, #comparison-table-container').hide();
    },

    // Export comparison
    exportComparison() {
        // TODO: Export to PDF/Excel
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinancialComparison;
}
