frappe.pages['financial-analysis'].on_page_load = function(wrapper) {
    console.log("Financial Dashboard - Executive Elite Edition v9.1 (Final Fix)");
    
    const userLang = frappe.boot.lang || 'en';
    const isRtl = userLang === 'ar' || frappe.boot.sysdefaults.rtl === 1;

    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: isRtl ? 'غرفة العمليات المالية الاستراتيجية' : 'Strategic Financial Command Center',
        single_column: true
    });

    function load_scripts(scripts, callback) {
        if (!scripts || scripts.length === 0) { callback(); return; }
        const scriptSrc = scripts[0];
        if (document.querySelector(`script[src="${scriptSrc}"]`)) {
            load_scripts(scripts.slice(1), callback);
            return;
        }
        let el = document.createElement('script');
        el.src = scriptSrc;
        el.onload = () => load_scripts(scripts.slice(1), callback);
        el.onerror = () => load_scripts(scripts.slice(1), callback);
        document.head.appendChild(el);
    }

    function render_vue() {
        const template = `
        <div class="financial-analysis-wrapper">
            <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/@mdi/font@6.x/css/materialdesignicons.min.css" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/vuetify@2.x/dist/vuetify.min.css" rel="stylesheet">
            
            <style>
                .financial-analysis-wrapper, .v-application { 
                    font-family: 'Cairo', sans-serif !important; 
                    background-color: #f8fafc !important; 
                }

                .executive-card { 
                    border-radius: 20px !important; 
                    border: 1px solid rgba(226, 232, 240, 0.8) !important;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.03) !important;
                    background: white !important;
                }

                .accounting-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                .accounting-table th { background: #f1f5f9; padding: 14px; font-weight: 800; text-align: right; color: #1e3a8a; border-bottom: 2px solid #cbd5e1; }
                .accounting-table td { padding: 14px; border-bottom: 1px solid #f1f5f9; font-size: 0.95rem; font-weight: 500; }
                .val-cell { text-align: left !important; font-family: 'monospace'; font-weight: 800; font-size: 1.1rem; }
                .total-row { background: #f8fafc; font-weight: 900; border-top: 3px double #1e3a8a !important; }

                .ai-report-paper {
                    background: #ffffff !important;
                    border-right: 12px solid #1e3a8a !important;
                    padding: 40px !important;
                    box-shadow: 0 15px 40px rgba(0,0,0,0.05) !important;
                }

                /* هندسة الطباعة A4 المذهلة */
                @media print {
                    @page { size: A4; margin: 15mm; }
                    body { background: white !important; -webkit-print-color-adjust: exact; }
                    .no-print, .frappe-header, .navbar, .page-head, .v-tabs { display: none !important; }
                    .v-main { padding: 0 !important; margin: 0 !important; }
                    .print-report-container { width: 100%; padding: 0 !important; margin: 0 !important; background: white; }
                    .v-card { box-shadow: none !important; border: 1px solid #eee !important; border-radius: 0 !important; margin-bottom: 30px !important; break-inside: avoid; }
                    
                    /* إجبار كافة التبويبات على الظهور تحت بعضها في الطباعة */
                    .v-tabs-items { display: block !important; }
                    .v-window-item { display: block !important; opacity: 1 !important; transform: none !important; margin-bottom: 50px !important; }
                    
                    .luxury-print-header { 
                        display: flex !important; align-items: center; justify-content: space-between; 
                        border-bottom: 4px solid #1e3a8a; padding-bottom: 20px; margin-bottom: 40px;
                    }
                    .statement-title { font-size: 26px !important; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 25px; }
                }
                .luxury-print-header { display: none; }
                .statement-title { font-weight: 900; color: #1e3a8a; font-size: 20px; }
            </style>

            <div id="financial-analysis-app">
                <v-app>
                    <v-main>
                        <v-container fluid class="pa-4 pa-md-10 print-report-container">
                            
                            <!-- ترويسة الطباعة -->
                            <div class="luxury-print-header">
                                <div class="text-right">
                                    <div style="font-size: 32px; font-weight: 900; color: #1e3a8a;">تقرير الأداء والمركز المالي الاستراتيجي</div>
                                    <div class="text-h6 font-weight-bold grey--text text--darken-3">{{ filters.company }} | دورة {{ filters.year }}</div>
                                </div>
                                <div class="text-left">
                                    <div class="font-weight-black indigo--text text--darken-4" style="font-size: 18px;">Executive BI Suite</div>
                                    <div class="caption font-weight-bold">تاريخ التقرير: {{ new Date().toLocaleDateString('ar-EG') }}</div>
                                </div>
                            </div>

                            <!-- لوحة التحكم (مخفية عند الطباعة) -->
                            <v-row class="mb-8 align-center no-print">
                                <v-col cols="12" md="4">
                                    <div class="d-flex align-center">
                                        <v-icon x-large color="indigo darken-4" class="ml-4">mdi-shield-check</v-icon>
                                        <div>
                                            <h1 class="text-h4 font-weight-black indigo--text">CFO Elite Suite</h1>
                                            <div class="grey--text font-weight-bold">نظام تحليل القوائم المالية الذكي</div>
                                        </div>
                                    </div>
                                </v-col>
                                <v-col cols="12" md="8">
                                    <v-card class="pa-4 executive-card elevation-2">
                                        <v-row dense align="center">
                                            <v-col cols="12" md="3"><v-select v-model="filters.company" :items="companies" label="الشركة" outlined dense hide-details></v-select></v-col>
                                            <v-col cols="12" md="2"><v-select v-model="filters.year" :items="years" label="السنة" outlined dense hide-details></v-select></v-col>
                                            <v-col cols="12" md="3"><v-select v-model="filters.quarter" :items="quarters" label="الفترة المالية" outlined dense hide-details item-text="label" item-value="value"></v-select></v-col>
                                            <v-col cols="12" md="4" class="d-flex">
                                                <v-btn color="indigo darken-4" dark x-large depressed block @click="analyzeData" :loading="loading" class="ml-3">تحليل ذكي</v-btn>
                                                <v-btn color="blue-grey darken-3" dark x-large depressed @click="printReport" :disabled="!analysisData"><v-icon>mdi-printer</v-icon></v-btn>
                                            </v-col>
                                        </v-row>
                                    </v-card>
                                </v-col>
                            </v-row>

                            <div v-if="loading" class="text-center py-16"><v-progress-circular indeterminate color="indigo" size="64" width="6"></v-progress-circular></div>

                            <!-- المحتوى الرئيسي (يظهر فقط عند وجود البيانات) -->
                            <div v-if="!loading && analysisData">
                                
                                <!-- KPIs Section -->
                                <v-row class="mb-8">
                                    <v-col cols="12" sm="6" md="3" v-for="(kpi, i) in safeKpis" :key="'kpi-elite-'+i">
                                        <v-card class="executive-card pa-6 text-center">
                                            <div class="caption grey--text font-weight-black mb-1 text-uppercase">{{ kpi.label }}</div>
                                            <div class="text-h4 font-weight-black indigo--text">{{ kpi.value }}</div>
                                            <v-chip x-small class="mt-2 font-weight-bold" color="indigo lighten-5" text-color="indigo">
                                                {{ filters.quarter == 'all' ? 'سنوي' : 'الربع ' + filters.quarter }}
                                            </v-chip>
                                        </v-card>
                                    </v-col>
                                </v-row>

                                <!-- AI Strategic Summary -->
                                <v-row class="mb-10">
                                    <v-col cols="12">
                                        <v-card class="ai-report-paper executive-card">
                                            <div class="text-h4 font-weight-black indigo--text mb-6">التقرير الاستراتيجي الموحد</div>
                                            <div class="text-body-1 black--text" style="line-height: 2.2; text-align: justify;" v-html="formatAiText(analysisData.ai_report)"></div>
                                            <v-divider class="my-8"></v-divider>
                                            <div class="text-h5 font-weight-black indigo--text mb-4">توصيات تحسين الربحية والسيولة</div>
                                            <v-row>
                                                <v-col cols="12" md="6">
                                                    <v-alert colored-border border="right" color="green darken-1" icon="mdi-trending-up" elevation="1">
                                                        <div class="font-weight-bold indigo--text">كفاءة تشغيل الأصول</div>
                                                        <div class="caption grey--text text--darken-3 font-weight-bold">معدل الدوران الحالي هو ({{ analysisData.ratios.asset_turnover }}). يوصى بتقليل الأصول غير المستغلة لرفع ROE.</div>
                                                    </v-alert>
                                                </v-col>
                                                <v-col cols="12" md="6">
                                                    <v-alert colored-border border="right" color="orange darken-2" icon="mdi-shield-alert" elevation="1">
                                                        <div class="font-weight-bold indigo--text">إدارة الملاءة المالية</div>
                                                        <div class="caption grey--text text--darken-3 font-weight-bold">نسبة السيولة المتداولة ({{ analysisData.ratios.current_ratio }}). يجب تحسين دورة التحصيل النقدي لضمان التدفقات.</div>
                                                    </v-alert>
                                                </v-col>
                                            </v-row>
                                        </v-card>
                                    </v-col>
                                </v-row>

                                <!-- القوائم المالية الأربع (تبويبات في العرض، فردية في الطباعة) -->
                                <v-card class="executive-card overflow-hidden">
                                    <v-tabs v-model="activeTab" background-color="grey lighten-4" color="indigo darken-4" grow height="60" class="no-print">
                                        <v-tab class="font-weight-black">قائمة الدخل</v-tab>
                                        <v-tab class="font-weight-black">المركز المالي</v-tab>
                                        <v-tab class="font-weight-black">التدفق النقدي</v-tab>
                                        <v-tab class="font-weight-black">حقوق الملكية</v-tab>
                                    </v-tabs>

                                    <v-tabs-items v-model="activeTab">
                                        <!-- 1. قائمة الدخل -->
                                        <v-tab-item class="pa-8 pa-md-12">
                                            <div class="statement-title mb-6">قائمة الدخل (الأرباح والخسائر)</div>
                                            <table class="accounting-table">
                                                <thead><tr><th>البند المحاسبي</th><th class="val-cell">المبلغ</th></tr></thead>
                                                <tbody>
                                                    <tr><td>إجمالي الإيرادات والنشاط التشغيلي</td><td class="val-cell">{{ formatCurrency(safeCurrentData.income) }}</td></tr>
                                                    <tr><td>تكلفة المبيعات والمصاريف التشغيلية</td><td class="val-cell red--text">({{ formatCurrency(safeCurrentData.expense) }})</td></tr>
                                                    <tr class="total-row"><td>صافي الربح للفترة المحددة</td><td class="val-cell indigo--text">{{ formatCurrency(safeCurrentData.profit) }}</td></tr>
                                                </tbody>
                                            </table>
                                        </v-tab-item>

                                        <!-- 2. قائمة المركز المالي -->
                                        <v-tab-item class="pa-8 pa-md-12">
                                            <div class="statement-title mb-6">قائمة المركز المالي (الميزانية العمومية)</div>
                                            <table class="accounting-table">
                                                <thead><tr><th>الأصول والالتزامات</th><th class="val-cell">المبلغ</th></tr></thead>
                                                <tbody>
                                                    <tr><td>إجمالي الأصول (Assets)</td><td class="val-cell green--text">{{ formatCurrency(analysisData.summary.assets) }}</td></tr>
                                                    <tr><td>إجمالي الالتزامات (Liabilities)</td><td class="val-cell orange--text text--darken-3">{{ formatCurrency(analysisData.summary.liabilities) }}</td></tr>
                                                    <tr class="total-row"><td>صافي حقوق الملكية (Equity)</td><td class="val-cell indigo--text">{{ formatCurrency(analysisData.summary.equity) }}</td></tr>
                                                </tbody>
                                            </table>
                                        </v-tab-item>

                                        <!-- 3. قائمة التدفق النقدي -->
                                        <v-tab-item class="pa-8 pa-md-12">
                                            <div class="statement-title mb-6">قائمة التدفقات النقدية التقديرية</div>
                                            <table class="accounting-table">
                                                <thead><tr><th>النشاط</th><th class="val-cell">المبلغ</th></tr></thead>
                                                <tbody>
                                                    <tr><td>التدفقات من الأنشطة التشغيلية</td><td class="val-cell">{{ formatCurrency(safeCashFlow.operating) }}</td></tr>
                                                    <tr><td>التدفقات من الأنشطة الاستثمارية</td><td class="val-cell red--text">{{ formatCurrency(safeCashFlow.investing) }}</td></tr>
                                                    <tr><td>التدفقات من الأنشطة التمويلية</td><td class="val-cell">{{ formatCurrency(safeCashFlow.financing) }}</td></tr>
                                                    <tr class="total-row"><td>صافي التغير في النقد</td><td class="val-cell indigo--text">{{ formatCurrency(safeCashFlow.net) }}</td></tr>
                                                </tbody>
                                            </table>
                                        </v-tab-item>

                                        <!-- 4. حقوق الملكية -->
                                        <v-tab-item class="pa-8 pa-md-12">
                                            <div class="statement-title mb-6">قائمة التغير في حقوق الملكية</div>
                                            <table class="accounting-table">
                                                <thead><tr><th>الوصف</th><th class="val-cell">المبلغ</th></tr></thead>
                                                <tbody>
                                                    <tr><td>رصيد حقوق الملكية - بداية المدة</td><td class="val-cell">{{ formatCurrency(analysisData.summary.equity - analysisData.summary.profit) }}</td></tr>
                                                    <tr><td>صافي ربح العام المالي</td><td class="val-cell green--text">{{ formatCurrency(analysisData.summary.profit) }}</td></tr>
                                                    <tr><td>أرباح موزعة / تسويات</td><td class="val-cell red--text">(0.00)</td></tr>
                                                    <tr class="total-row"><td>رصيد حقوق الملكية - نهاية المدة</td><td class="val-cell indigo--text">{{ formatCurrency(analysisData.summary.equity) }}</td></tr>
                                                </tbody>
                                            </table>
                                        </v-tab-item>
                                    </v-tabs-items>
                                </v-card>

                                <!-- الرسوم البيانية (مخفية عند الطباعة لضمان جودة النص) -->
                                <v-row class="mt-12 no-print">
                                    <v-col cols="12" md="6">
                                        <v-card class="pa-6 executive-card">
                                            <div class="font-weight-black mb-4 indigo--text">تحليل الربحية الرباعي</div>
                                            <div id="chart-profit-main"></div>
                                        </v-card>
                                    </v-col>
                                    <v-col cols="12" md="6">
                                        <v-card class="pa-6 executive-card">
                                            <div class="font-weight-black mb-4 indigo--text">توزيع المركز المالي</div>
                                            <div id="chart-assets-pie"></div>
                                        </v-card>
                                    </v-col>
                                </v-row>

                                <!-- تذييل التقرير الرسمي -->
                                <div class="mt-16 d-none d-print-flex justify-space-between text-center px-10">
                                    <div style="width: 220px; border-top: 2px solid #333; padding-top: 10px; font-weight: 800;">إعداد / المحاسب المالي</div>
                                    <div style="width: 220px; border-top: 2px solid #333; padding-top: 10px; font-weight: 800;">اعتماد / المدير المالي</div>
                                    <div style="width: 220px; border-top: 2px solid #333; padding-top: 10px; font-weight: 800;">المصادقة / المدير العام</div>
                                </div>
                            </div>
                        </v-container>
                    </v-main>
                </v-app>
            </div>
        </div>
        `;

        let mainSection = $(wrapper).find(".layout-main-section");
        mainSection.html(template);

        new Vue({
            el: '#financial-analysis-app',
            vuetify: new Vuetify({ rtl: isRtl }),
            data: {
                loading: false,
                activeTab: 0,
                filters: { company: "", year: new Date().getFullYear(), quarter: "all" },
                companies: [],
                years: [2022, 2023, 2024, 2025],
                quarters: [
                    { label: 'العام المالي كاملاً', value: 'all' },
                    { label: 'الربع الأول (Q1)', value: '1' },
                    { label: 'الربع الثاني (Q2)', value: '2' },
                    { label: 'الربع الثالث (Q3)', value: '3' },
                    { label: 'الربع الرابع (Q4)', value: '4' }
                ],
                analysisData: null
            },
            computed: {
                // دالة آمنة لجلب بيانات التدفق النقدي لمنع أخطاء Undefined
                safeCashFlow() {
                    if (this.analysisData && this.analysisData.cash_flow) {
                        return this.analysisData.cash_flow;
                    }
                    return { operating: 0, investing: 0, financing: 0, net: 0 };
                },
                // دالة آمنة لفلترة البيانات بناءً على الربع المختار
                safeCurrentData() {
                    if (!this.analysisData) return { income: 0, expense: 0, profit: 0 };
                    if (this.filters.quarter === 'all') return this.analysisData.summary;
                    const qData = this.analysisData.quarterly.find(x => x.q == this.filters.quarter);
                    return qData ? { income: qData.inc, expense: qData.exp, profit: qData.inc - qData.exp } : this.analysisData.summary;
                },
                // بطاقات الـ KPIs العلوية
                safeKpis() {
                    const d = this.safeCurrentData;
                    const wc = (this.analysisData && this.analysisData.ratios) ? this.analysisData.ratios.working_capital : 0;
                    return [
                        { label: 'إجمالي الإيرادات', value: this.formatCurrency(d.income), color: 'green' },
                        { label: 'إجمالي المصاريف', value: this.formatCurrency(d.expense), color: 'red' },
                        { label: 'صافي الربح', value: this.formatCurrency(d.profit), color: 'indigo' },
                        { label: 'رأس المال العامل', value: this.formatCurrency(wc), color: 'blue' }
                    ];
                }
            },
            mounted() { this.fetchCompanies(); },
            methods: {
                fetchCompanies() {
                    frappe.call({
                        method: "frappe.client.get_list",
                        args: { doctype: "Company", fields: ["name"] },
                        callback: (r) => {
                            if (r.message) {
                                this.companies = r.message.map(c => c.name);
                                if (this.companies.length) this.filters.company = this.companies[0];
                            }
                        }
                    });
                },
                analyzeData() {
                    this.loading = true;
                    frappe.call({
                        method: "material_ledger.material_ledger.api.get_financial_analysis",
                        args: { company: this.filters.company, year: this.filters.year },
                        callback: (r) => {
                            this.loading = false;
                            if (r.message) {
                                this.analysisData = r.message;
                                this.$nextTick(() => { setTimeout(() => this.renderCharts(), 500); });
                            }
                        }
                    });
                },
                renderCharts() {
                    if (!this.analysisData) return;
                    
                    const lineEl = document.getElementById('chart-profit-main');
                    if (lineEl) {
                        lineEl.innerHTML = '';
                        new frappe.Chart("#chart-profit-main", {
                            data: {
                                labels: ["Q1", "Q2", "Q3", "Q4"],
                                datasets: [{ name: "Profit", values: this.analysisData.quarterly.map(x => flt(x.inc - x.exp)) }]
                            },
                            type: 'line', height: 250, colors: ['#1a237e'], lineOptions: { regionFill: 1 }
                        });
                    }

                    const pieEl = document.getElementById('chart-assets-pie');
                    if (pieEl) {
                        pieEl.innerHTML = '';
                        new frappe.Chart("#chart-assets-pie", {
                            data: {
                                labels: ["الأصول", "الخصوم", "حقوق الملكية"],
                                datasets: [{ values: [this.analysisData.summary.assets, this.analysisData.summary.liabilities, this.analysisData.summary.equity] }]
                            },
                            type: 'pie', height: 250, colors: ['#4caf50', '#f44336', '#1a237e']
                        });
                    }
                },
                formatAiText(text) {
                    if(!text) return "";
                    return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<b style="color:#1a237e">$1</b>');
                },
                formatCurrency(val) { return frappe.format(val, "Currency"); },
                printReport() { 
                    this.activeTab = 0; // العودة للتبويب الأول كمرجع شكلي فقط
                    setTimeout(() => { window.print(); }, 300);
                }
            }
        });
    }

    load_scripts([
        "https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.min.js",
        "https://cdn.jsdelivr.net/npm/vuetify@2.x/dist/vuetify.js"
    ], render_vue);
};