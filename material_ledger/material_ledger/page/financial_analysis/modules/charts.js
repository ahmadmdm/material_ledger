/**
 * Financial Analysis - Charts Module
 * Handles all chart rendering using Chart.js
 */

const FinancialCharts = {
    // Chart instances cache
    instances: {},
    
    // Destroy existing chart if present
    destroy: function(chartId) {
        if (this.instances[chartId]) {
            this.instances[chartId].destroy();
            delete this.instances[chartId];
        }
    },
    
    // Create revenue vs expense chart
    createRevenueExpenseChart: function(ctx, data, isRtl) {
        this.destroy('revenueExpense');
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: isRtl ? 'الإيرادات' : 'Revenue',
                        data: data.revenue || [],
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: '#667eea',
                        borderWidth: 2,
                        borderRadius: 8
                    },
                    {
                        label: isRtl ? 'المصروفات' : 'Expenses',
                        data: data.expenses || [],
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: '#ef4444',
                        borderWidth: 2,
                        borderRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { font: { weight: '600' } }
                    },
                    title: {
                        display: true,
                        text: isRtl ? 'الإيرادات مقابل المصروفات' : 'Revenue vs Expenses',
                        font: { size: 16, weight: 'bold' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    }
                }
            }
        });
        
        this.instances['revenueExpense'] = chart;
        return chart;
    },
    
    // Create profit trend chart
    createProfitTrendChart: function(ctx, data, isRtl) {
        this.destroy('profitTrend');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: isRtl ? 'صافي الربح' : 'Net Profit',
                    data: data.profits || [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: isRtl ? 'اتجاه الأرباح' : 'Profit Trend',
                        font: { size: 16, weight: 'bold' }
                    }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    }
                }
            }
        });
        
        this.instances['profitTrend'] = chart;
        return chart;
    },
    
    // Create doughnut chart for asset/liability composition
    createCompositionChart: function(ctx, data, isRtl) {
        this.destroy('composition');
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: [
                        '#667eea', '#f093fb', '#4facfe', '#10b981',
                        '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { font: { size: 12 } }
                    }
                },
                cutout: '60%'
            }
        });
        
        this.instances['composition'] = chart;
        return chart;
    },
    
    // Create forecast chart
    createForecastChart: function(ctx, historical, forecasts, isRtl) {
        this.destroy('forecast');
        
        const histLabels = historical.map(h => h.year);
        const forecastLabels = forecasts.map(f => f.year);
        const allLabels = [...histLabels, ...forecastLabels];
        
        const histData = historical.map(h => h.income);
        const forecastData = forecasts.map(f => f.income.projected);
        const forecastLow = forecasts.map(f => f.income.low);
        const forecastHigh = forecasts.map(f => f.income.high);
        
        // Fill historical with nulls for forecast section and vice versa
        const histSeries = [...histData, ...new Array(forecastLabels.length).fill(null)];
        const forecastSeries = [...new Array(histLabels.length).fill(null), ...forecastData];
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: allLabels,
                datasets: [
                    {
                        label: isRtl ? 'الفعلي' : 'Actual',
                        data: histSeries,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 6
                    },
                    {
                        label: isRtl ? 'التوقعات' : 'Forecast',
                        data: forecastSeries,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderDash: [5, 5],
                        fill: true,
                        tension: 0.4,
                        pointRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: {
                        display: true,
                        text: isRtl ? 'التوقعات المالية' : 'Financial Forecast',
                        font: { size: 16, weight: 'bold' }
                    }
                }
            }
        });
        
        this.instances['forecast'] = chart;
        return chart;
    },
    
    // Destroy all charts
    destroyAll: function() {
        Object.keys(this.instances).forEach(key => this.destroy(key));
    }
};

// Export charts
if (typeof window !== 'undefined') {
    window.FinancialCharts = FinancialCharts;
}
