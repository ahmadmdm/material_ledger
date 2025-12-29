
frappe.pages['material-ledger-report'].on_page_load = function(wrapper) {
    console.log("Material Ledger Report Loaded - v3.2");
    frappe.show_alert({message: 'Material Ledger Loaded v3.2', indicator: 'green'});
    
    // Determine Language and Direction
    const userLang = frappe.boot.lang || 'en';
    const isRtl = userLang === 'ar' || frappe.boot.sysdefaults.rtl === 1;
    
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: isRtl ? 'دفتر الأستاذ العام' : 'Material Ledger',
        single_column: true
    });

    // Main wrapper logic
    var me = {};
    me.wrapper = $(wrapper);
    
    // Load external scripts sequentially
    function load_scripts(scripts, callback) {
        if (!scripts || scripts.length === 0) {
            callback();
            return;
        }

        const scriptSrc = scripts[0];
        // Check if script is already loaded
        if (document.querySelector(`script[src="${scriptSrc}"]`)) {
             load_scripts(scripts.slice(1), callback);
             return;
        }

        let el = document.createElement('script');
        el.src = scriptSrc;
        el.onload = () => {
            load_scripts(scripts.slice(1), callback);
        };
        document.head.appendChild(el);
    }

    function render_vue() {
        const template = `
<div class="material-ledger-wrapper">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@200;300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/@mdi/font@6.x/css/materialdesignicons.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/vuetify@2.x/dist/vuetify.min.css" rel="stylesheet">
    <style>
        .material-ledger-wrapper, .v-application {
            font-family: 'Cairo', sans-serif !important;
        }
        @media print {
            .no-print {
                display: none !important;
            }
            .v-main {
                padding: 0 !important;
            }
            .v-card {
                box-shadow: none !important;
            }
        }
    </style>

    <div id="material-ledger-app">
        <v-app>
            <v-main>
                <v-container fluid>
                    <v-card class="mb-4 no-print" elevation="2">
                        <v-card-title>
                            <span class="text-h5 primary--text font-weight-bold">{{ t('title') }}</span>
                            <v-spacer></v-spacer>
                            
                            <!-- Group By Account Switch -->
                            <v-switch
                                v-model="groupByAccount"
                                :label="t('group_by_account')"
                                class="mt-0 pt-0 mx-4"
                                hide-details
                            ></v-switch>

                            <v-btn icon @click="showSettings = true" class="mx-2">
                                <v-icon>mdi-cog</v-icon>
                            </v-btn>
                            <v-btn color="secondary" @click="printPage" class="mx-2" outlined>
                                <v-icon left>mdi-printer</v-icon> {{ t('print') }}
                            </v-btn>
                            <v-btn color="primary" @click="fetchEntries" :loading="loading" class="mx-2">
                                <v-icon left>mdi-refresh</v-icon> {{ t('refresh') }}
                            </v-btn>
                        </v-card-title>
                        <v-card-text>
                            <v-row>
                                <v-col cols="12" md="4">
                                    <v-card color="blue lighten-5" class="pa-4" outlined>
                                        <div class="text-subtitle-2 grey--text text--darken-2">{{ t('total_debit') }}</div>
                                        <div class="text-h5 blue--text text--darken-3 font-weight-bold">{{ formatCurrency(totalDebit) }}</div>
                                    </v-card>
                                </v-col>
                                <v-col cols="12" md="4">
                                    <v-card color="red lighten-5" class="pa-4" outlined>
                                        <div class="text-subtitle-2 grey--text text--darken-2">{{ t('total_credit') }}</div>
                                        <div class="text-h5 red--text text--darken-3 font-weight-bold">{{ formatCurrency(totalCredit) }}</div>
                                    </v-card>
                                </v-col>
                                <v-col cols="12" md="4">
                                    <v-card color="green lighten-5" class="pa-4" outlined>
                                        <div class="text-subtitle-2 grey--text text--darken-2">{{ t('closing_balance') }}</div>
                                        <div class="text-h5 green--text text--darken-3 font-weight-bold">{{ formatCurrency(closingBalance) }}</div>
                                    </v-card>
                                </v-col>
                            </v-row>
                            <v-divider class="my-4"></v-divider>
                            <v-row>
                                <v-col cols="12" md="3">
                                    <v-select
                                        v-model="filters.company"
                                        :items="companies"
                                        :label="t('company')"
                                        outlined
                                        dense
                                        hide-details="auto"
                                    ></v-select>
                                </v-col>
                                <v-col cols="12" md="3">
                                    <v-text-field
                                        v-model="filters.from_date"
                                        :label="t('from_date')"
                                        type="date"
                                        outlined
                                        dense
                                        hide-details="auto"
                                    ></v-text-field>
                                </v-col>
                                <v-col cols="12" md="3">
                                    <v-text-field
                                        v-model="filters.to_date"
                                        :label="t('to_date')"
                                        type="date"
                                        outlined
                                        dense
                                        hide-details="auto"
                                    ></v-text-field>
                                </v-col>
                                <v-col cols="12" md="3">
                                    <v-autocomplete
                                        v-model="filters.account"
                                        :items="accounts"
                                        :label="t('account')"
                                        outlined
                                        dense
                                        clearable
                                        hide-details="auto"
                                    ></v-autocomplete>
                                </v-col>
                                <v-col cols="12" md="3">
                                    <v-autocomplete
                                        v-model="filters.cost_center"
                                        :items="cost_centers"
                                        :label="t('cost_center')"
                                        outlined
                                        dense
                                        clearable
                                        hide-details="auto"
                                    ></v-autocomplete>
                                </v-col>
                                <v-col cols="12" md="3">
                                    <v-autocomplete
                                        v-model="filters.project"
                                        :items="projects"
                                        :label="t('project')"
                                        outlined
                                        dense
                                        clearable
                                        hide-details="auto"
                                    ></v-autocomplete>
                                </v-col>
                                <!-- New Party Filters -->
                                <v-col cols="12" md="3">
                                    <v-select
                                        v-model="filters.party_type"
                                        :items="party_types"
                                        :label="t('party_type')"
                                        outlined
                                        dense
                                        clearable
                                        hide-details="auto"
                                        @change="fetchParties"
                                    ></v-select>
                                </v-col>
                                <v-col cols="12" md="3">
                                    <v-autocomplete
                                        v-model="filters.party"
                                        :items="parties"
                                        :label="t('party')"
                                        outlined
                                        dense
                                        clearable
                                        hide-details="auto"
                                        :disabled="!filters.party_type"
                                    ></v-autocomplete>
                                </v-col>
                            </v-row>
                        </v-card-text>
                    </v-card>

                    <v-card elevation="2">
                        <v-data-table
                            :headers="headers"
                            :items="entries"
                            :loading="loading"
                            class="elevation-1"
                            :items-per-page="20"
                            :footer-props="{'items-per-page-options': [20, 50, 100, -1]}"
                            dense
                            :group-by="groupByAccount ? 'account' : undefined"
                            :show-group-by="false"
                        >
                            <template v-slot:item.voucher_no="{ item }">
                                <a v-if="item.voucher_type && item.voucher_no" href="#" @click.prevent="openVoucher(item)" class="text-decoration-none font-weight-medium blue--text">
                                    {{ item.voucher_no }}
                                </a>
                                <span v-else>{{ item.voucher_no }}</span>
                            </template>
                            <template v-slot:item.debit="{ item }">
                                {{ formatCurrency(item.debit) }}
                            </template>
                            <template v-slot:item.credit="{ item }">
                                {{ formatCurrency(item.credit) }}
                            </template>
                            <template v-slot:item.balance="{ item }">
                                <span :class="{'red--text': item.balance < 0, 'green--text': item.balance > 0, 'font-weight-bold': true}">
                                    {{ formatCurrency(item.balance) }}
                                </span>
                            </template>
                            
                            <!-- Custom Group Header to calculate subtotals if needed -->
                            <!-- Vuetify default group header is fine for now, but we can customize -->
                        </v-data-table>
                    </v-card>

                    <!-- Settings Dialog -->
                    <v-dialog v-model="showSettings" max-width="600px">
                        <v-card>
                            <v-card-title>{{ t('column_settings') }}</v-card-title>
                            <v-card-text>
                                <v-row>
                                    <v-col cols="12" sm="6" v-for="col in availableColumns" :key="col.value">
                                        <v-checkbox
                                            v-model="selectedColumns"
                                            :label="col.text"
                                            :value="col.value"
                                            dense
                                        ></v-checkbox>
                                    </v-col>
                                </v-row>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="primary" text @click="showSettings = false">{{ t('close') }}</v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </v-container>
            </v-main>
        </v-app>
    </div>
</div>
`;
        
        // Append template to wrapper
        me.wrapper.find(".layout-main-section").html(template);

        // Initialize Vue after a short delay to ensure DOM is ready
        setTimeout(() => {
            if (!document.getElementById('material-ledger-app')) {
                console.error("Material Ledger App element not found!");
                return;
            }
            
            new Vue({
                el: '#material-ledger-app',
                vuetify: new Vuetify({
                    rtl: isRtl,
                    theme: {
                        themes: {
                            light: {
                                primary: '#1976D2',
                                secondary: '#424242',
                                accent: '#82B1FF',
                                error: '#FF5252',
                                info: '#2196F3',
                                success: '#4CAF50',
                                warning: '#FFC107',
                            },
                        },
                    },
                }),
                data: {
                    loading: false,
                    showSettings: false,
                    groupByAccount: false,
                    lang: userLang,
                    translations: {
                        en: {
                            title: 'Material Ledger',
                            total_debit: 'Total Debit',
                            total_credit: 'Total Credit',
                            closing_balance: 'Closing Balance',
                            company: 'Company',
                            from_date: 'From Date',
                            to_date: 'To Date',
                            account: 'Account',
                            cost_center: 'Cost Center',
                            project: 'Project',
                            party_type: 'Party Type',
                            party: 'Party',
                            group_by_account: 'Group by Account',
                            refresh: 'Refresh',
                            print: 'Print',
                            column_settings: 'Column Settings',
                            close: 'Close',
                            posting_date: 'Posting Date',
                            remarks: 'Remarks',
                            voucher_type: 'Voucher Type',
                            voucher_no: 'Voucher No',
                            debit: 'Debit',
                            credit: 'Credit',
                            balance: 'Balance',
                            transaction_date: 'Transaction Date',
                            due_date: 'Due Date',
                            party_type_col: 'Party Type',
                            party_col: 'Party',
                            against: 'Against'
                        },
                        ar: {
                            title: 'دفتر الأستاذ العام',
                            total_debit: 'مجموع المدين',
                            total_credit: 'مجموع الدائن',
                            closing_balance: 'رصيد الإغلاق',
                            company: 'الشركة',
                            from_date: 'من تاريخ',
                            to_date: 'إلى تاريخ',
                            account: 'الحساب',
                            cost_center: 'مركز التكلفة',
                            project: 'المشروع',
                            party_type: 'نوع الطرف',
                            party: 'الطرف',
                            group_by_account: 'تجميع حسب الحساب',
                            refresh: 'تحديث',
                            print: 'طباعة',
                            column_settings: 'إعدادات الأعمدة',
                            close: 'إغلاق',
                            posting_date: 'تاريخ القيد',
                            remarks: 'البيان',
                            voucher_type: 'نوع السند',
                            voucher_no: 'رقم السند',
                            debit: 'مدين',
                            credit: 'دائن',
                            balance: 'الرصيد',
                            transaction_date: 'تاريخ المعاملة',
                            due_date: 'تاريخ الاستحقاق',
                            party_type_col: 'نوع الطرف',
                            party_col: 'الطرف',
                            against: 'مقابل'
                        }
                    },
                    filters: {
                        company: "",
                        from_date: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
                        to_date: frappe.datetime.get_today(),
                        account: "",
                        cost_center: "",
                        project: "",
                        party_type: "",
                        party: ""
                    },
                    companies: [],
                    accounts: [],
                    cost_centers: [],
                    projects: [],
                    party_types: ["Customer", "Supplier", "Employee", "Student", "Member", "Shareholder"],
                    parties: [],
                    entries: [],
                    selectedColumns: ['posting_date', 'account', 'remarks', 'cost_center', 'project', 'voucher_type', 'voucher_no', 'debit', 'credit', 'balance']
                },
                computed: {
                    currentTranslations() {
                        return this.translations[this.lang === 'ar' ? 'ar' : 'en'];
                    },
                    availableColumns() {
                        const t = this.currentTranslations;
                        return [
                            { text: t.posting_date, value: 'posting_date' },
                            { text: t.account, value: 'account' },
                            { text: t.remarks, value: 'remarks' },
                            { text: t.cost_center, value: 'cost_center' },
                            { text: t.project, value: 'project' },
                            { text: t.voucher_type, value: 'voucher_type' },
                            { text: t.voucher_no, value: 'voucher_no' },
                            { text: t.debit, value: 'debit', align: 'end' },
                            { text: t.credit, value: 'credit', align: 'end' },
                            { text: t.balance, value: 'balance', align: 'end' },
                            { text: t.transaction_date, value: 'transaction_date' },
                            { text: t.due_date, value: 'due_date' },
                            { text: t.party_type_col, value: 'party_type' },
                            { text: t.party_col, value: 'party' },
                            { text: t.against, value: 'against' }
                        ];
                    },
                    headers() {
                        return this.availableColumns.filter(col => this.selectedColumns.includes(col.value));
                    },
                    totalDebit() {
                        return this.entries.reduce((acc, item) => acc + (parseFloat(item.debit) || 0), 0);
                    },
                    totalCredit() {
                        return this.entries.reduce((acc, item) => acc + (parseFloat(item.credit) || 0), 0);
                    },
                    closingBalance() {
                        if (this.entries.length === 0) return 0;
                        return this.entries[this.entries.length - 1].balance;
                    }
                },
                mounted() {
                    this.fetchCompanies();
                    this.fetchAccounts();
                    this.fetchCostCenters();
                    this.fetchProjects();
                },
                methods: {
                    t(key) {
                        return this.currentTranslations[key] || key;
                    },
                    openVoucher(item) {
                        if (item.voucher_type && item.voucher_no) {
                            frappe.set_route("Form", item.voucher_type, item.voucher_no);
                        }
                    },
                    printPage() {
                        window.print();
                    },
                    fetchCompanies() {
                        frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: "Company",
                                fields: ["name"]
                            },
                            callback: (r) => {
                                if (r.message) {
                                    this.companies = r.message.map(c => c.name);
                                    if (this.companies.length > 0) {
                                        this.filters.company = this.companies[0];
                                        this.fetchEntries();
                                    }
                                }
                            }
                        });
                    },
                    fetchAccounts() {
                        frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: "Account",
                                filters: { is_group: 0 },
                                fields: ["name"],
                                limit_page_length: 5000
                            },
                            callback: (r) => {
                                if (r.message) {
                                    this.accounts = r.message.map(a => a.name);
                                }
                            }
                        });
                    },
                    fetchCostCenters() {
                        frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: "Cost Center",
                                filters: { is_group: 0 },
                                fields: ["name"]
                            },
                            callback: (r) => {
                                if (r.message) {
                                    this.cost_centers = r.message.map(c => c.name);
                                }
                            }
                        });
                    },
                    fetchProjects() {
                        frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: "Project",
                                fields: ["name"]
                            },
                            callback: (r) => {
                                if (r.message) {
                                    this.projects = r.message.map(p => p.name);
                                }
                            }
                        });
                    },
                    fetchParties() {
                        this.filters.party = "";
                        this.parties = [];
                        if (!this.filters.party_type) return;

                        frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: this.filters.party_type,
                                fields: ["name"],
                                limit_page_length: 5000
                            },
                            callback: (r) => {
                                if (r.message) {
                                    this.parties = r.message.map(p => p.name);
                                }
                            }
                        });
                    },
                    fetchEntries() {
                        if (!this.filters.company) return;
                        
                        this.loading = true;
                        frappe.call({
                            method: "material_ledger.material_ledger.api.get_ledger_entries",
                            args: {
                                company: this.filters.company,
                                from_date: this.filters.from_date,
                                to_date: this.filters.to_date,
                                account: this.filters.account,
                                cost_center: this.filters.cost_center,
                                project: this.filters.project,
                                party_type: this.filters.party_type,
                                party: this.filters.party
                            },
                            callback: (r) => {
                                this.loading = false;
                                if (r.message) {
                                    this.entries = r.message;
                                }
                            }
                        });
                    },
                    formatCurrency(value) {
                        return format_currency(value);
                    }
                }
            });
        }, 100);
    }
    
    load_scripts([
        "https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js",
        "https://cdn.jsdelivr.net/npm/vuetify@2.x/dist/vuetify.js"
    ], render_vue);
};
