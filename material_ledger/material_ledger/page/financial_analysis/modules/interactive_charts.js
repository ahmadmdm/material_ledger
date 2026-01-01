/**
 * Interactive Charts Module
 * Enhanced charts with zoom, pan, drill-down capabilities
 */

const FinancialInteractiveCharts = {
    // Active charts registry
    charts: {},

    // Chart configurations
    defaultConfig: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 800,
            easing: 'easeOutQuart'
        },
        interaction: {
            mode: 'index',
            intersect: false
        }
    },

    // Initialize module
    init() {
        this.loadChartPlugins();
        this.setupGlobalDefaults();
    },

    // Load Chart.js plugins
    loadChartPlugins() {
        // Zoom plugin (if available)
        if (window.Chart && window.chartjsPluginZoom) {
            Chart.register(window.chartjsPluginZoom);
        }
    },

    // Setup global Chart.js defaults
    setupGlobalDefaults() {
        if (!window.Chart) return;

        const isArabic = frappe.boot.lang === 'ar';

        Chart.defaults.font.family = isArabic ? 
            "'Cairo', 'Segoe UI', sans-serif" : 
            "'Inter', 'Segoe UI', sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#6b7280';
        
        // RTL support
        if (isArabic) {
            Chart.defaults.rtl = true;
            Chart.defaults.textDirection = 'rtl';
        }
    },

    // Create interactive line chart
    createLineChart(containerId, data, options = {}) {
        const isArabic = frappe.boot.lang === 'ar';
        const ctx = this.getContext(containerId);
        if (!ctx) return null;

        // Destroy existing chart
        this.destroyChart(containerId);

        const config = {
            type: 'line',
            data: data,
            options: {
                ...this.defaultConfig,
                plugins: {
                    legend: {
                        position: 'top',
                        rtl: isArabic,
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                return `${context.dataset.label}: ${this.formatValue(value, options.valueFormat)}`;
                            }
                        }
                    },
                    zoom: this.getZoomConfig()
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: options.beginAtZero !== false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: (value) => this.formatValue(value, options.valueFormat)
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0 && options.onPointClick) {
                        const element = elements[0];
                        options.onPointClick(element.index, data.datasets[element.datasetIndex]);
                    }
                },
                ...options.chartOptions
            }
        };

        const chart = new Chart(ctx, config);
        this.charts[containerId] = chart;

        // Add control buttons
        this.addChartControls(containerId, chart, options);

        return chart;
    },

    // Create interactive bar chart
    createBarChart(containerId, data, options = {}) {
        const isArabic = frappe.boot.lang === 'ar';
        const ctx = this.getContext(containerId);
        if (!ctx) return null;

        this.destroyChart(containerId);

        const config = {
            type: options.horizontal ? 'bar' : 'bar',
            data: data,
            options: {
                ...this.defaultConfig,
                indexAxis: options.horizontal ? 'y' : 'x',
                plugins: {
                    legend: {
                        display: data.datasets.length > 1,
                        position: 'top',
                        rtl: isArabic
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {
                            label: (context) => {
                                return `${context.dataset.label}: ${this.formatValue(context.parsed.y || context.parsed.x, options.valueFormat)}`;
                            }
                        }
                    },
                    zoom: this.getZoomConfig()
                },
                scales: {
                    x: {
                        grid: { display: false },
                        stacked: options.stacked
                    },
                    y: {
                        beginAtZero: true,
                        stacked: options.stacked,
                        ticks: {
                            callback: (value) => this.formatValue(value, options.valueFormat)
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0 && options.onBarClick) {
                        const element = elements[0];
                        options.onBarClick(element.index, data.datasets[element.datasetIndex], data.labels[element.index]);
                    }
                },
                ...options.chartOptions
            }
        };

        // Apply gradient backgrounds
        if (options.gradient) {
            this.applyGradients(ctx, data);
        }

        const chart = new Chart(ctx, config);
        this.charts[containerId] = chart;
        this.addChartControls(containerId, chart, options);

        return chart;
    },

    // Create doughnut/pie chart
    createDoughnutChart(containerId, data, options = {}) {
        const isArabic = frappe.boot.lang === 'ar';
        const ctx = this.getContext(containerId);
        if (!ctx) return null;

        this.destroyChart(containerId);

        const config = {
            type: options.pie ? 'pie' : 'doughnut',
            data: data,
            options: {
                ...this.defaultConfig,
                cutout: options.pie ? 0 : '60%',
                plugins: {
                    legend: {
                        position: isArabic ? 'right' : 'left',
                        rtl: isArabic,
                        labels: {
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${this.formatValue(context.parsed, options.valueFormat)} (${percentage}%)`;
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0 && options.onSliceClick) {
                        const element = elements[0];
                        options.onSliceClick(element.index, data.labels[element.index], data.datasets[0].data[element.index]);
                    }
                },
                ...options.chartOptions
            }
        };

        // Add center text for doughnut
        if (!options.pie && options.centerText) {
            config.plugins = [{
                id: 'centerText',
                afterDraw: (chart) => {
                    const ctx = chart.ctx;
                    const centerX = chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2;
                    const centerY = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2;
                    
                    ctx.save();
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    
                    // Main value
                    ctx.font = 'bold 24px Inter';
                    ctx.fillStyle = '#1f2937';
                    ctx.fillText(options.centerText.value, centerX, centerY - 10);
                    
                    // Label
                    ctx.font = '12px Inter';
                    ctx.fillStyle = '#6b7280';
                    ctx.fillText(options.centerText.label, centerX, centerY + 15);
                    
                    ctx.restore();
                }
            }];
        }

        const chart = new Chart(ctx, config);
        this.charts[containerId] = chart;

        return chart;
    },

    // Create area chart (filled line)
    createAreaChart(containerId, data, options = {}) {
        // Modify datasets to have fill
        data.datasets = data.datasets.map((dataset, index) => ({
            ...dataset,
            fill: options.stacked ? (index === 0 ? 'origin' : '-1') : 'origin',
            tension: 0.4
        }));

        return this.createLineChart(containerId, data, {
            ...options,
            chartOptions: {
                scales: {
                    y: {
                        stacked: options.stacked
                    }
                }
            }
        });
    },

    // Create radar chart
    createRadarChart(containerId, data, options = {}) {
        const ctx = this.getContext(containerId);
        if (!ctx) return null;

        this.destroyChart(containerId);

        const config = {
            type: 'radar',
            data: data,
            options: {
                ...this.defaultConfig,
                scales: {
                    r: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: options.stepSize || 20
                        },
                        pointLabels: {
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                ...options.chartOptions
            }
        };

        const chart = new Chart(ctx, config);
        this.charts[containerId] = chart;

        return chart;
    },

    // Get zoom configuration
    getZoomConfig() {
        return {
            pan: {
                enabled: true,
                mode: 'xy'
            },
            zoom: {
                wheel: {
                    enabled: true
                },
                pinch: {
                    enabled: true
                },
                mode: 'xy',
                onZoomComplete: ({chart}) => {
                    this.showResetButton(chart.canvas.id);
                }
            }
        };
    },

    // Add chart control buttons
    addChartControls(containerId, chart, options) {
        const isArabic = frappe.boot.lang === 'ar';
        const $container = $(`#${containerId}`).parent();
        
        // Remove existing controls
        $container.find('.chart-controls').remove();

        const controls = $(`
            <div class="chart-controls" style="
                display: flex;
                gap: 8px;
                margin-bottom: 10px;
                flex-wrap: wrap;
            ">
                <button class="chart-btn chart-zoom-in" title="${isArabic ? 'تكبير' : 'Zoom In'}" style="
                    background: #f3f4f6;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 6px 10px;
                    cursor: pointer;
                    font-size: 12px;
                ">
                    <i class="fa fa-search-plus"></i>
                </button>
                <button class="chart-btn chart-zoom-out" title="${isArabic ? 'تصغير' : 'Zoom Out'}" style="
                    background: #f3f4f6;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 6px 10px;
                    cursor: pointer;
                    font-size: 12px;
                ">
                    <i class="fa fa-search-minus"></i>
                </button>
                <button class="chart-btn chart-reset" title="${isArabic ? 'إعادة تعيين' : 'Reset'}" style="
                    background: #f3f4f6;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 6px 10px;
                    cursor: pointer;
                    font-size: 12px;
                    display: none;
                ">
                    <i class="fa fa-refresh"></i>
                </button>
                <button class="chart-btn chart-fullscreen" title="${isArabic ? 'ملء الشاشة' : 'Fullscreen'}" style="
                    background: #f3f4f6;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 6px 10px;
                    cursor: pointer;
                    font-size: 12px;
                ">
                    <i class="fa fa-expand"></i>
                </button>
                <button class="chart-btn chart-download" title="${isArabic ? 'تحميل الصورة' : 'Download Image'}" style="
                    background: #f3f4f6;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 6px 10px;
                    cursor: pointer;
                    font-size: 12px;
                ">
                    <i class="fa fa-download"></i>
                </button>
                ${options.showDataToggle ? `
                <button class="chart-btn chart-toggle-data" title="${isArabic ? 'إظهار/إخفاء البيانات' : 'Show/Hide Data'}" style="
                    background: #f3f4f6;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 6px 10px;
                    cursor: pointer;
                    font-size: 12px;
                ">
                    <i class="fa fa-table"></i>
                </button>
                ` : ''}
            </div>
        `);

        $container.prepend(controls);

        // Event handlers
        controls.find('.chart-zoom-in').on('click', () => {
            chart.zoom(1.2);
            controls.find('.chart-reset').show();
        });

        controls.find('.chart-zoom-out').on('click', () => {
            chart.zoom(0.8);
            controls.find('.chart-reset').show();
        });

        controls.find('.chart-reset').on('click', () => {
            chart.resetZoom();
            $(this).hide();
        });

        controls.find('.chart-fullscreen').on('click', () => {
            this.toggleFullscreen($container[0]);
        });

        controls.find('.chart-download').on('click', () => {
            this.downloadChart(chart, options.filename || 'chart');
        });

        controls.find('.chart-toggle-data').on('click', () => {
            this.toggleDataTable(containerId, chart);
        });
    },

    // Show reset button
    showResetButton(containerId) {
        $(`#${containerId}`).parent().find('.chart-reset').show();
    },

    // Toggle fullscreen
    toggleFullscreen(element) {
        if (!document.fullscreenElement) {
            element.requestFullscreen().catch(err => {
                console.error('Fullscreen error:', err);
            });
        } else {
            document.exitFullscreen();
        }
    },

    // Download chart as image
    downloadChart(chart, filename) {
        const link = document.createElement('a');
        link.download = `${filename}.png`;
        link.href = chart.toBase64Image();
        link.click();
    },

    // Toggle data table below chart
    toggleDataTable(containerId, chart) {
        const isArabic = frappe.boot.lang === 'ar';
        const $container = $(`#${containerId}`).parent();
        let $table = $container.find('.chart-data-table');

        if ($table.length) {
            $table.slideToggle();
            return;
        }

        // Create data table
        const data = chart.data;
        let html = `
            <div class="chart-data-table" style="margin-top: 15px; overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <thead>
                        <tr style="background: #f3f4f6;">
                            <th style="padding: 10px; text-align: ${isArabic ? 'right' : 'left'}; border: 1px solid #e5e7eb;">
                                ${isArabic ? 'التسمية' : 'Label'}
                            </th>
                            ${data.datasets.map(ds => `
                                <th style="padding: 10px; text-align: center; border: 1px solid #e5e7eb;">
                                    ${ds.label}
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.labels.map((label, i) => `
                            <tr>
                                <td style="padding: 8px 10px; border: 1px solid #e5e7eb; font-weight: 600;">
                                    ${label}
                                </td>
                                ${data.datasets.map(ds => `
                                    <td style="padding: 8px 10px; text-align: center; border: 1px solid #e5e7eb;">
                                        ${this.formatValue(ds.data[i], 'number')}
                                    </td>
                                `).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        $container.append(html);
    },

    // Apply gradient backgrounds to datasets
    applyGradients(ctx, data) {
        const gradients = [
            ['#667eea', '#764ba2'],
            ['#f093fb', '#f5576c'],
            ['#4facfe', '#00f2fe'],
            ['#43e97b', '#38f9d7'],
            ['#fa709a', '#fee140']
        ];

        data.datasets.forEach((dataset, index) => {
            const gradient = ctx.createLinearGradient(0, 0, 0, 300);
            const colors = gradients[index % gradients.length];
            gradient.addColorStop(0, colors[0]);
            gradient.addColorStop(1, colors[1]);
            dataset.backgroundColor = gradient;
        });
    },

    // Format value based on type
    formatValue(value, format) {
        if (value === null || value === undefined) return '-';
        
        const isArabic = frappe.boot.lang === 'ar';
        const locale = isArabic ? 'ar-SA' : 'en-US';

        switch (format) {
            case 'currency':
                return new Intl.NumberFormat(locale, {
                    style: 'currency',
                    currency: frappe.boot.sysdefaults.currency || 'SAR',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                }).format(value);
            
            case 'percent':
                return `${value.toFixed(1)}%`;
            
            case 'compact':
                if (Math.abs(value) >= 1000000) {
                    return (value / 1000000).toFixed(1) + (isArabic ? 'م' : 'M');
                } else if (Math.abs(value) >= 1000) {
                    return (value / 1000).toFixed(1) + (isArabic ? 'ك' : 'K');
                }
                return value.toFixed(0);
            
            default:
                return new Intl.NumberFormat(locale).format(value);
        }
    },

    // Get canvas context
    getContext(containerId) {
        let canvas = document.getElementById(containerId);
        
        if (!canvas) {
            const container = document.querySelector(`#${containerId}, .${containerId}`);
            if (container) {
                canvas = document.createElement('canvas');
                canvas.id = containerId;
                container.appendChild(canvas);
            }
        }
        
        return canvas ? canvas.getContext('2d') : null;
    },

    // Destroy chart
    destroyChart(containerId) {
        if (this.charts[containerId]) {
            this.charts[containerId].destroy();
            delete this.charts[containerId];
        }
    },

    // Update chart data
    updateChart(containerId, newData, animate = true) {
        const chart = this.charts[containerId];
        if (!chart) return;

        chart.data = newData;
        chart.update(animate ? 'default' : 'none');
    },

    // Add data point to chart
    addDataPoint(containerId, label, data, datasetIndex = 0) {
        const chart = this.charts[containerId];
        if (!chart) return;

        chart.data.labels.push(label);
        chart.data.datasets[datasetIndex].data.push(data);
        chart.update();
    },

    // Remove data point from chart
    removeDataPoint(containerId, index) {
        const chart = this.charts[containerId];
        if (!chart) return;

        chart.data.labels.splice(index, 1);
        chart.data.datasets.forEach(ds => ds.data.splice(index, 1));
        chart.update();
    },

    // Get all charts
    getAllCharts() {
        return this.charts;
    },

    // Destroy all charts
    destroyAllCharts() {
        Object.keys(this.charts).forEach(id => this.destroyChart(id));
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinancialInteractiveCharts;
}
