frappe.pages['material-ledger-report'].on_page_load = function(wrapper) {
    console.log("🎨 Material Ledger - Ultra Professional Design v6.0");
    
    const userLang = frappe.boot.lang || 'en';
    const isRtl = userLang === 'ar';
    
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: isRtl ? '📊 دفتر الأستاذ العام' : '📊 Material Ledger',
        single_column: true
    });

    // Add Ultra Professional Styles
    addUltraProfessionalStyles();
    
    const VISIBLE_COL_KEY = 'material_ledger_visible_columns';

    // State
    let state = {
        loading: false,
        entries: [],
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
        groupByAccount: false,
        visibleColumns: {
            posting_date: true,
            transaction_date: false,
            due_date: false,
            account: true,
            remarks: true,
            voucher_type: false,
            voucher_no: true,
            party_type: false,
            party: false,
            cost_center: false,
            project: false,
            against: false,
            debit: true,
            credit: true,
            balance: true
        }
    };

    // Load saved column preferences
    state.visibleColumns = loadVisibleColumns(state.visibleColumns);

    // Translations
    const t = (key) => {
        const trans = {
            en: {
                company: 'Company', from_date: 'From Date', to_date: 'To Date',
                account: 'Account', cost_center: 'Cost Center', project: 'Project',
                party_type: 'Party Type', party: 'Party', refresh: 'Refresh',
                print: 'Print', export: 'Export', total_debit: 'Total Debit',
                total_credit: 'Total Credit', balance: 'Closing Balance',
                posting_date: 'Date', transaction_date: 'Transaction Date', due_date: 'Due Date',
                remarks: 'Description', voucher_no: 'Voucher', voucher_type: 'Voucher Type',
                debit: 'Debit', credit: 'Credit', no_data: 'No entries found',
                group_by_account: 'Group by Account', loading: 'Loading...',
                entries_count: 'Entries', against: 'Against'
            },
            ar: {
                company: 'الشركة', from_date: 'من تاريخ', to_date: 'إلى تاريخ',
                account: 'الحساب', cost_center: 'مركز التكلفة', project: 'المشروع',
                party_type: 'نوع الطرف', party: 'الطرف', refresh: 'تحديث',
                print: 'طباعة', export: 'تصدير', total_debit: 'إجمالي المدين',
                total_credit: 'إجمالي الدائن', balance: 'رصيد الإغلاق',
                posting_date: 'تاريخ القيد', transaction_date: 'تاريخ المعاملة', due_date: 'تاريخ الاستحقاق',
                remarks: 'البيان', voucher_no: 'رقم السند', voucher_type: 'نوع السند',
                debit: 'مدين', credit: 'دائن', no_data: 'لا توجد قيود',
                group_by_account: 'تجميع حسب الحساب', loading: 'جاري التحميل...',
                entries_count: 'قيد', against: 'مقابل'
            }
        };
        return trans[isRtl ? 'ar' : 'en'][key] || key;
    };

    // Build Ultra Professional UI
    buildUltraProfessionalUI();
    setupFilters();
    setupActions();
    fetchCompanies();

    function addUltraProfessionalStyles() {
        const styles = `
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
                
                .page-content { font-family: 'Inter', sans-serif !important; background: #f8fafc; }
                
                .stat-card:hover { transform: translateY(-5px); box-shadow: 0 20px 50px rgba(0,0,0,0.15) !important; }
                
                .modern-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.25) !important; }
                
                .professional-ledger-table tbody tr { transition: all 0.3s ease; }
                .professional-ledger-table tbody tr:hover { background: linear-gradient(to right, #f0f9ff, #ffffff); transform: scale(1.01); }
                
                .professional-ledger-table tbody td { 
                    padding: 14px 16px; 
                    border-bottom: 1px solid #e5e7eb; 
                    font-size: 14px;
                    color: #374151;
                }
                
                .professional-ledger-table tbody tr:nth-child(even) { background: #f9fafb; }
                
                .voucher-link { 
                    color: #667eea; 
                    font-weight: 600; 
                    text-decoration: none; 
                    transition: all 0.3s;
                    padding: 4px 10px;
                    background: #f0f4ff;
                    border-radius: 6px;
                    display: inline-block;
                }
                .voucher-link:hover { 
                    background: #667eea; 
                    color: white; 
                    transform: scale(1.05);
                }
                
                .opening-row { background: linear-gradient(to right, #fffbeb, #ffffff) !important; font-weight: 600; }
                
                .group-header-row { 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; 
                    color: white !important; 
                    font-weight: 700;
                    font-size: 15px;
                }
                .group-header-row td { color: white !important; padding: 16px !important; }
                
                .subtotal-row { 
                    background: #f3f4f6 !important; 
                    font-weight: 700; 
                    border-top: 2px solid #667eea !important;
                    border-bottom: 2px solid #667eea !important;
                }
                
                @keyframes fadeInUp { 
                    from { opacity: 0; transform: translateY(30px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                .fade-in-up { animation: fadeInUp 0.6s ease-out; }
                
                @media print {
                    .ledger-hero-section, .stats-grid, .no-print { display: none !important; }
                    .professional-table-wrapper { box-shadow: none !important; }
                    .professional-ledger-table tbody tr:hover { transform: none; }
                }
            </style>
        `;
        $('head').append(styles);
    }

    function loadVisibleColumns(defaults) {
        try {
            const saved = JSON.parse(localStorage.getItem(VISIBLE_COL_KEY) || '{}');
            return { ...defaults, ...saved };
        } catch (e) {
            console.warn('Visible columns load failed', e);
            return defaults;
        }
    }

    function saveVisibleColumns() {
        try {
            localStorage.setItem(VISIBLE_COL_KEY, JSON.stringify(state.visibleColumns));
        } catch (e) {
            console.warn('Visible columns save failed', e);
        }
    }

    function buildUltraProfessionalUI() {
        const heroHTML = `
            <div class="ledger-hero-section fade-in-up" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 15px 50px rgba(102, 126, 234, 0.4);">
                <div style="display: flex; align-items: center; justify-content: space-between; color: white; flex-wrap: wrap; gap: 20px;">
                    <div style="flex: 1; min-width: 250px;">
                        <h2 style="margin: 0; font-size: 32px; font-weight: 800; display: flex; align-items: center; gap: 12px;">
                            <i class="fa fa-book" style="font-size: 36px;"></i>
                            <span id="hero-company-name" style="opacity: 0.95;">--</span>
                        </h2>
                        <p style="margin: 12px 0 0 0; opacity: 0.9; font-size: 15px; display: flex; align-items: center; gap: 8px;">
                            <i class="fa fa-calendar"></i> 
                            <span id="hero-from-date">--</span> 
                            <i class="fa fa-arrow-right" style="font-size: 12px;"></i> 
                            <span id="hero-to-date">--</span>
                        </p>
                    </div>
                    <div style="text-align: center;">
                        <div style="background: rgba(255,255,255,0.25); padding: 18px 28px; border-radius: 12px; backdrop-filter: blur(10px); border: 2px solid rgba(255,255,255,0.3);">
                            <div style="font-size: 13px; opacity: 0.9; margin-bottom: 6px; font-weight: 600;">${t('entries_count')}</div>
                            <div style="font-size: 36px; font-weight: 900;" id="hero-entries-count">0</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const statsHTML = `
            <div class="stats-grid fade-in-up" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 25px;">
                <div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 28px; border-radius: 14px; color: white; box-shadow: 0 12px 35px rgba(102, 126, 234, 0.35); position: relative; overflow: hidden; transition: all 0.3s ease;">
                    <div style="position: absolute; top: -40px; right: -40px; width: 150px; height: 150px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
                    <div style="position: relative; z-index: 1;">
                        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 14px;">
                            <div style="background: rgba(255,255,255,0.25); padding: 14px; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                <i class="fa fa-arrow-up" style="font-size: 26px;"></i>
                            </div>
                            <span style="font-size: 14px; font-weight: 700; opacity: 0.95; text-transform: uppercase; letter-spacing: 1.2px;">${t('total_debit')}</span>
                        </div>
                        <div style="font-size: 36px; font-weight: 900; line-height: 1; font-family: 'Inter', monospace;" id="total-debit">0.00</div>
                    </div>
                </div>

                <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 28px; border-radius: 14px; color: white; box-shadow: 0 12px 35px rgba(240, 147, 251, 0.35); position: relative; overflow: hidden; transition: all 0.3s ease;">
                    <div style="position: absolute; top: -40px; right: -40px; width: 150px; height: 150px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
                    <div style="position: relative; z-index: 1;">
                        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 14px;">
                            <div style="background: rgba(255,255,255,0.25); padding: 14px; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                <i class="fa fa-arrow-down" style="font-size: 26px;"></i>
                            </div>
                            <span style="font-size: 14px; font-weight: 700; opacity: 0.95; text-transform: uppercase; letter-spacing: 1.2px;">${t('total_credit')}</span>
                        </div>
                        <div style="font-size: 36px; font-weight: 900; line-height: 1; font-family: 'Inter', monospace;" id="total-credit">0.00</div>
                    </div>
                </div>

                <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 28px; border-radius: 14px; color: white; box-shadow: 0 12px 35px rgba(79, 172, 254, 0.35); position: relative; overflow: hidden; transition: all 0.3s ease;">
                    <div style="position: absolute; top: -40px; right: -40px; width: 150px; height: 150px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
                    <div style="position: relative; z-index: 1;">
                        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 14px;">
                            <div style="background: rgba(255,255,255,0.25); padding: 14px; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                <i class="fa fa-balance-scale" style="font-size: 26px;"></i>
                            </div>
                            <span style="font-size: 14px; font-weight: 700; opacity: 0.95; text-transform: uppercase; letter-spacing: 1px;">${t('balance')}</span>
                        </div>
                        <div style="font-size: 36px; font-weight: 900; line-height: 1; font-family: 'Inter', monospace;" id="closing-balance">0.00</div>
                    </div>
                </div>
            </div>
        `;

        const tableHTML = `
            <div class="professional-table-wrapper fade-in-up" style="background: white; border-radius: 14px; box-shadow: 0 4px 25px rgba(0,0,0,0.08); overflow: hidden;">
                <div style="padding: 24px 28px; border-bottom: 1px solid #e5e7eb; background: linear-gradient(to right, #f9fafb, #ffffff);">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                        <h3 style="margin: 0; font-size: 22px; font-weight: 800; color: #111827; display: flex; align-items: center; gap: 12px;">
                            <i class="fa fa-table" style="color: #667eea; font-size: 24px;"></i>
                            ${isRtl ? 'سجل الحركات المالية' : 'Financial Transactions Register'}
                        </h3>
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; background: #f3f4f6; padding: 10px 18px; border-radius: 10px; font-size: 14px; font-weight: 600; transition: all 0.3s; border: 2px solid transparent;">
                                <input type="checkbox" id="group-toggle" style="width: 20px; height: 20px; cursor: pointer; accent-color: #667eea;">
                                <span>${t('group_by_account')}</span>
                            </label>
                            <button class="modern-btn columns-btn" style="background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); color: white; border: none; padding: 12px 22px; border-radius: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 10px; box-shadow: 0 6px 20px rgba(14, 165, 233, 0.35); transition: all 0.3s; font-size: 14px;">
                                <i class="fa fa-columns" style="font-size: 16px;"></i> ${isRtl ? 'تخصيص الأعمدة' : 'Customize Columns'}
                            </button>
                            <button class="modern-btn export-btn" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; padding: 12px 22px; border-radius: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 10px; box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35); transition: all 0.3s; font-size: 14px;">
                                <i class="fa fa-file-excel-o" style="font-size: 16px;"></i> ${t('export')}
                            </button>
                            <button class="modern-btn pdf-btn" style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; border: none; padding: 12px 22px; border-radius: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 10px; box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35); transition: all 0.3s; font-size: 14px;">
                                <i class="fa fa-file-pdf-o" style="font-size: 16px;"></i> PDF
                            </button>
                        </div>
                    </div>
                </div>
                <div style="overflow-x: auto;">
                    <table class="professional-ledger-table" style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                                <th class="col-posting_date" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('posting_date')}</th>
                                <th class="col-transaction_date" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('transaction_date')}</th>
                                <th class="col-due_date" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('due_date')}</th>
                                <th class="col-account" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('account')}</th>
                                <th class="col-remarks" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('remarks')}</th>
                                <th class="col-voucher_type" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('voucher_type')}</th>
                                <th class="col-voucher_no" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('voucher_no')}</th>
                                <th class="col-party_type" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('party_type')}</th>
                                <th class="col-party" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('party')}</th>
                                <th class="col-cost_center" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('cost_center')}</th>
                                <th class="col-project" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('project')}</th>
                                <th class="col-against" style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('against')}</th>
                                <th class="col-debit" style="padding: 18px; text-align: right; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('debit')}</th>
                                <th class="col-credit" style="padding: 18px; text-align: right; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('credit')}</th>
                                <th class="col-balance" style="padding: 18px; text-align: right; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('balance')}</th>
                            </tr>
                        </thead>
                        <tbody id="ledger-tbody">
                            <tr>
                                <td colspan="15" style="padding: 80px; text-align: center; color: #9ca3af;">
                                    <i class="fa fa-inbox" style="font-size: 56px; opacity: 0.25; display: block; margin-bottom: 18px;"></i>
                                    <div style="font-size: 18px; font-weight: 600; color: #6b7280;">${t('no_data')}</div>
                                    <div style="font-size: 14px; color: #9ca3af; margin-top: 8px;">${isRtl ? 'استخدم الفلاتر للبحث عن القيود' : 'Use filters to search for entries'}</div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        $(wrapper).find('.page-content').append(heroHTML + statsHTML + tableHTML);
        
        // Group toggle event
        $('#group-toggle').on('change', function() {
            state.groupByAccount = $(this).is(':checked');
            renderTable();
        });
        
        // Column customization
        $('.columns-btn').on('click', openColumnDialog);
        
        // Export button event
        $('.export-btn').on('click', exportToExcel);

        // PDF export
        $('.pdf-btn').on('click', exportToPDF);

        // Voucher click routing
        $(wrapper).on('click', '.voucher-link', function(e) {
            e.preventDefault();
            const rType = $(this).data('route-type');
            const rName = $(this).data('route-name');
            console.log('🔗 Voucher clicked', { rType, rName });
            if (rType && rName) {
                frappe.set_route('Form', rType, rName);
            }
        });

        applyColumnVisibility();
    }

    function setupFilters() {
        page.add_field({
            fieldname: 'company',
            label: t('company'),
            fieldtype: 'Link',
            options: 'Company',
            reqd: 1,
            change: function() {
                state.filters.company = this.get_value();
                $('#hero-company-name').text(state.filters.company);
            }
        });

        page.add_field({
            fieldname: 'from_date',
            label: t('from_date'),
            fieldtype: 'Date',
            default: state.filters.from_date,
            change: function() {
                state.filters.from_date = this.get_value();
                $('#hero-from-date').text(frappe.datetime.str_to_user(state.filters.from_date));
            }
        });

        page.add_field({
            fieldname: 'to_date',
            label: t('to_date'),
            fieldtype: 'Date',
            default: state.filters.to_date,
            change: function() {
                state.filters.to_date = this.get_value();
                $('#hero-to-date').text(frappe.datetime.str_to_user(state.filters.to_date));
            }
        });

        page.add_field({
            fieldname: 'account',
            label: t('account'),
            fieldtype: 'Link',
            options: 'Account',
            get_query: function() {
                return { filters: { company: state.filters.company, is_group: 0 } };
            },
            change: function() {
                state.filters.account = this.get_value();
            }
        });

        page.add_field({
            fieldname: 'cost_center',
            label: t('cost_center'),
            fieldtype: 'Link',
            options: 'Cost Center',
            change: function() {
                state.filters.cost_center = this.get_value();
            }
        });

        page.add_field({
            fieldname: 'project',
            label: t('project'),
            fieldtype: 'Link',
            options: 'Project',
            change: function() {
                state.filters.project = this.get_value();
            }
        });

        page.add_field({
            fieldname: 'party_type',
            label: t('party_type'),
            fieldtype: 'Select',
            options: ['', 'Customer', 'Supplier', 'Employee'],
            change: function() {
                state.filters.party_type = this.get_value();
            }
        });

        page.add_field({
            fieldname: 'party',
            label: t('party'),
            fieldtype: 'Dynamic Link',
            options: 'party_type',
            change: function() {
                state.filters.party = this.get_value();
            }
        });
    }

    function setupActions() {
        page.set_primary_action(t('refresh'), fetchEntries, 'refresh');
        page.add_action_icon('printer', () => exportToPDF(), t('print'));
    }

    function openColumnDialog() {
        const cols = [
            { key: 'posting_date', label: t('posting_date') },
            { key: 'transaction_date', label: t('transaction_date') },
            { key: 'due_date', label: t('due_date') },
            { key: 'account', label: t('account') },
            { key: 'remarks', label: t('remarks') },
            { key: 'voucher_type', label: t('voucher_type') },
            { key: 'voucher_no', label: t('voucher_no') },
            { key: 'party_type', label: t('party_type') },
            { key: 'party', label: t('party') },
            { key: 'cost_center', label: t('cost_center') },
            { key: 'project', label: t('project') },
            { key: 'against', label: t('against') },
            { key: 'debit', label: t('debit') },
            { key: 'credit', label: t('credit') },
            { key: 'balance', label: t('balance') }
        ];

        const d = new frappe.ui.Dialog({
            title: isRtl ? 'تخصيص الأعمدة' : 'Customize Columns',
            fields: cols.map(c => ({
                label: c.label,
                fieldname: c.key,
                fieldtype: 'Check',
                default: state.visibleColumns[c.key]
            })),
            primary_action_label: isRtl ? 'تطبيق' : 'Apply',
            primary_action: () => {
                cols.forEach(c => {
                    state.visibleColumns[c.key] = d.get_value(c.key);
                });
                applyColumnVisibility();
                saveVisibleColumns();
                d.hide();
            }
        });

        d.show();
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
                }
            }
        });
    }

    function fetchEntries() {
        if (!state.filters.company) return;
        
        state.loading = true;
        showLoading();

        frappe.call({
            method: 'material_ledger.material_ledger.api.get_ledger_entries',
            args: state.filters,
            callback: (r) => {
                state.loading = false;
                if (r.message) {
                    state.entries = r.message;
                    renderTable();
                    updateStats();
                    frappe.show_alert({ message: `✅ ${state.entries.length} ${t('entries_count')}`, indicator: 'green' });
                }
            }
        });
    }

    function renderTable() {
        const tbody = $('#ledger-tbody');
        tbody.empty();

        if (!state.entries.length) {
            tbody.html(`
                <tr>
                    <td colspan="15" style="padding: 80px; text-align: center; color: #9ca3af;">
                        <i class="fa fa-inbox" style="font-size: 56px; opacity: 0.25; display: block; margin-bottom: 18px;"></i>
                        <div style="font-size: 18px; font-weight: 600; color: #6b7280;">${t('no_data')}</div>
                    </td>
                </tr>
            `);
            return;
        }

        if (state.groupByAccount) {
            renderGroupedTable(tbody);
        } else {
            renderFlatTable(tbody);
        }
        applyColumnVisibility();
    }

    function renderFlatTable(tbody) {
        state.entries.forEach((entry, idx) => {
            if (idx < 3) {
                console.log('🧾 Row', idx + 1, {
                    name: entry.name,
                    voucher_type: entry.voucher_type,
                    voucher_no: entry.voucher_no,
                    account: entry.account,
                    is_opening: entry.is_opening,
                    debit: entry.debit,
                    credit: entry.credit
                });
            }
            tbody.append(createTableRow(entry));
        });
    }

    function applyColumnVisibility() {
        Object.keys(state.visibleColumns).forEach(key => {
            const visible = state.visibleColumns[key];
            const selector = '.col-' + key;
            $(selector).css('display', visible ? '' : 'none');
        });
        saveVisibleColumns();
    }

    function renderGroupedTable(tbody) {
        const grouped = {};
        state.entries.forEach(e => {
            const acc = e.account || 'Unknown';
            if (!grouped[acc]) grouped[acc] = [];
            grouped[acc].push(e);
        });

        Object.keys(grouped).forEach(acc => {
            tbody.append(`
                <tr class="group-header-row">
                    <td colspan="15" style="font-size: 15px;">
                        <i class="fa fa-folder-open" style="margin-right: 8px;"></i> ${acc}
                    </td>
                </tr>
            `);
            
            grouped[acc].forEach(e => tbody.append(createTableRow(e)));
            
            const subtotalD = grouped[acc].reduce((s, e) => s + (e.debit || 0), 0);
            const subtotalC = grouped[acc].reduce((s, e) => s + (e.credit || 0), 0);
            const subtotalB = grouped[acc][grouped[acc].length - 1].balance;
            
            tbody.append(`
                <tr class="subtotal-row">
                    <td colspan="12" style="text-align: ${isRtl ? 'left' : 'right'}; font-size: 14px;">${isRtl ? 'المجموع الفرعي' : 'Subtotal'}</td>
                    <td style="text-align: right;">${frappe.format(subtotalD, {fieldtype: 'Currency'})}</td>
                    <td style="text-align: right;">${frappe.format(subtotalC, {fieldtype: 'Currency'})}</td>
                    <td style="text-align: right;">${frappe.format(subtotalB, {fieldtype: 'Currency'})}</td>
                </tr>
            `);
        });
    }

    function createTableRow(e) {
        const isOpening = e.is_opening;
        return $(`
            <tr class="${isOpening ? 'opening-row' : ''}">
                <td class="col-posting_date">${frappe.datetime.str_to_user(e.posting_date) || ''}</td>
                <td class="col-transaction_date">${e.transaction_date ? frappe.datetime.str_to_user(e.transaction_date) : ''}</td>
                <td class="col-due_date">${e.due_date ? frappe.datetime.str_to_user(e.due_date) : ''}</td>
                <td class="col-account" style="font-weight: 500;">${e.account || ''}</td>
                <td class="col-remarks" style="color: #6b7280;">${e.remarks || ''}</td>
                <td class="col-voucher_type">${e.voucher_type || ''}</td>
                <td class="col-voucher_no">
                    ${(() => {
                        const label = e.voucher_no || e.name || '-';
                        if (isOpening && !e.voucher_no) return label;
                        const routeType = e.voucher_type || 'GL Entry';
                        const routeName = e.voucher_no || e.name || '';
                        const dataAttrs = `data-route-type="${routeType}" data-route-name="${routeName}" title="${routeType} / ${routeName}"`;
                        return `<a href="#" class="voucher-link" ${dataAttrs}>${label}</a>`;
                    })()}
                </td>
                <td class="col-party_type">${e.party_type || ''}</td>
                <td class="col-party">${e.party || ''}</td>
                <td class="col-cost_center">${e.cost_center || ''}</td>
                <td class="col-project">${e.project || ''}</td>
                <td class="col-against">${e.against || ''}</td>
                <td class="col-debit" style="text-align: right; font-weight: 600; color: #667eea;">${frappe.format(e.debit || 0, {fieldtype: 'Currency'})}</td>
                <td class="col-credit" style="text-align: right; font-weight: 600; color: #f5576c;">${frappe.format(e.credit || 0, {fieldtype: 'Currency'})}</td>
                <td class="col-balance" style="text-align: right; font-weight: 700; color: ${e.balance < 0 ? '#dc2626' : '#059669'};">${frappe.format(e.balance || 0, {fieldtype: 'Currency'})}</td>
            </tr>
        `);
    }

    function updateStats() {
        const totalD = state.entries.reduce((s, e) => s + (e.debit || 0), 0);
        const totalC = state.entries.reduce((s, e) => s + (e.credit || 0), 0);
        const balance = state.entries.length ? state.entries[state.entries.length - 1].balance : 0;

        $('#total-debit').html(frappe.format(totalD, {fieldtype: 'Currency'}));
        $('#total-credit').html(frappe.format(totalC, {fieldtype: 'Currency'}));
        $('#closing-balance').html(frappe.format(balance, {fieldtype: 'Currency'}));
        $('#hero-entries-count').text(state.entries.length);
        $('#hero-from-date').text(frappe.datetime.str_to_user(state.filters.from_date));
        $('#hero-to-date').text(frappe.datetime.str_to_user(state.filters.to_date));
    }

    function showLoading() {
        $('#ledger-tbody').html(`
            <tr>
                <td colspan="15" style="padding: 60px; text-align: center;">
                    <div style="display: inline-block; width: 50px; height: 50px; border: 5px solid #f3f4f6; border-top-color: #667eea; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    <div style="margin-top: 15px; color: #6b7280; font-weight: 600;">${t('loading')}</div>
                </td>
            </tr>
        `);
        $('head').append('<style>@keyframes spin { to { transform: rotate(360deg); }}</style>');
    }

    function exportToExcel() {
        if (!state.entries.length) {
            frappe.msgprint(isRtl ? 'لا توجد بيانات للتصدير' : 'No data to export');
            return;
        }

        const data = state.entries.map(e => ({
            [t('posting_date')]: e.posting_date,
            [t('account')]: e.account,
            [t('remarks')]: e.remarks,
            [t('voucher_no')]: e.voucher_no,
            [t('debit')]: e.debit,
            [t('credit')]: e.credit,
            [t('balance')]: e.balance
        }));

        frappe.tools.downloadify(data, null, 'Material_Ledger_' + frappe.datetime.now_date());
        frappe.show_alert({ message: '✅ ' + t('export'), indicator: 'green' });
    }

    function exportToPDF() {
        if (!state.entries.length) {
            frappe.msgprint(isRtl ? 'لا توجد بيانات للتصدير' : 'No data to export');
            return;
        }

        const html = buildPdfHtml();

        frappe.call({
            method: 'frappe.utils.pdf.get_pdf',
            args: { html },
            callback: (r) => {
                if (!r.message) {
                    frappe.msgprint(isRtl ? 'تعذر إنشاء ملف PDF' : 'Unable to generate PDF');
                    return;
                }

                const blob = base64ToBlob(r.message, 'application/pdf');
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'General_Ledger_Report.pdf';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                frappe.show_alert({ message: '✅ PDF جاهز', indicator: 'green' });
            },
            error: () => {
                frappe.msgprint(isRtl ? 'حدث خطأ أثناء إنشاء PDF' : 'Error while generating PDF');
            }
        });
    }

    function base64ToBlob(base64, mime) {
        const byteChars = atob(base64);
        const byteArrays = [];
        const sliceSize = 1024;
        for (let offset = 0; offset < byteChars.length; offset += sliceSize) {
            const slice = byteChars.slice(offset, offset + sliceSize);
            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }
            byteArrays.push(new Uint8Array(byteNumbers));
        }
        return new Blob(byteArrays, { type: mime });
    }

    function buildPdfHtml() {
        const fmt = (v) => (v || 0).toLocaleString(isRtl ? 'ar-SA' : 'en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        const today = frappe.datetime.str_to_user(frappe.datetime.get_today());
        const periodLabel = `${frappe.datetime.str_to_user(state.filters.from_date)} - ${frappe.datetime.str_to_user(state.filters.to_date)}`;

        const totalDebit = state.entries.reduce((s, e) => s + (e.debit || 0), 0);
        const totalCredit = state.entries.reduce((s, e) => s + (e.credit || 0), 0);
        const closingBalance = state.entries.length ? state.entries[state.entries.length - 1].balance : 0;
        const revenue = totalCredit;
        const expenses = totalDebit;
        const netProfit = revenue - expenses;

        const assets = Math.max(totalDebit, 0);
        const liabilities = Math.max(totalCredit, 0);
        const equity = assets - liabilities;

        const operatingCF = netProfit;
        const investingCF = 0;
        const financingCF = closingBalance - operatingCF;
        const netCash = operatingCF + investingCF + financingCF;

        const safeDivide = (a, b) => b ? (a / b) : 0;

        const ratios = {
            grossMargin: safeDivide(revenue - expenses, revenue) * 100,
            operatingMargin: safeDivide(netProfit, revenue) * 100,
            netMargin: safeDivide(netProfit, revenue) * 100,
            currentRatio: safeDivide(assets, liabilities),
            quickRatio: safeDivide(assets * 0.8, liabilities),
            debtToEquity: safeDivide(liabilities, equity || 1) * 100,
            roa: safeDivide(netProfit, assets || 1) * 100,
            roe: safeDivide(netProfit, equity || 1) * 100
        };

        const topEntries = state.entries.slice(0, 40);

        return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    @page { size: A4; margin: 20mm 16mm 18mm 16mm; }
    body { font-family: Arial, Helvetica, 'DejaVu Sans', sans-serif; color: #1f2937; margin: 0; padding: 0; }
    header { position: fixed; top: 0; left: 0; right: 0; height: 40px; padding: 10px 16mm; font-size: 12px; color: #4b5563; border-bottom: 1px solid #e5e7eb; }
    footer { position: fixed; bottom: 0; left: 0; right: 0; height: 30px; padding: 8px 16mm; font-size: 12px; color: #4b5563; border-top: 1px solid #e5e7eb; }
    .page-number:after { content: "Page " counter(page) " of " counter(pages); }
    .container { padding: 60px 0 40px 0; }
    h1, h2, h3 { margin: 0 0 8px 0; color: #111827; }
    h1 { font-size: 28px; }
    h2 { font-size: 20px; margin-top: 24px; }
    h3 { font-size: 16px; margin-top: 12px; }
    p { margin: 6px 0; line-height: 1.5; }
    .card { padding: 18px; border: 1px solid #e5e7eb; border-radius: 10px; margin-bottom: 16px; }
    .grid-2 { display: table; width: 100%; table-layout: fixed; border-spacing: 12px 0; }
    .grid-2 > div { display: table-cell; vertical-align: top; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0; }
    th { background: #f3f4f6; padding: 10px; text-align: right; border: 1px solid #e5e7eb; font-weight: 700; }
    td { padding: 10px; text-align: right; border: 1px solid #e5e7eb; font-size: 13px; }
    tr:nth-child(even) td { background: #f9fafb; }
    .total-row td { background: #eef2ff; font-weight: 800; }
    .highlight { color: #0ea5e9; font-weight: 700; }
    .muted { color: #6b7280; }
    .page-break { page-break-before: always; }
    .toc li { margin: 6px 0; }
</style>
</head>
<body>
    <header>
        <div style="display:flex; justify-content: space-between;">
            <div>${state.filters.company || ''} | Financial Report</div>
            <div class="page-number"></div>
        </div>
    </header>
    <footer>
        <div style="display:flex; justify-content: space-between;">
            <div>Generated: ${today}</div>
            <div>${periodLabel}</div>
        </div>
    </footer>
    <div class="container">
        <section style="height: 100%; display: flex; flex-direction: column; justify-content: center; text-align: center; padding: 80px 30px;">
            <h1>${state.filters.company || ''}</h1>
            <h2>Financial Statements & Analysis</h2>
            <p class="muted">Reporting Period: ${periodLabel}</p>
            <p class="muted">Generated on: ${today}</p>
            <p style="margin-top: 30px; font-weight: 700;">Confidential - Internal Use Only</p>
        </section>

        <section class="page-break">
            <h2>Table of Contents</h2>
            <ol class="toc">
                <li>Executive Financial Summary</li>
                <li>Financial Statements</li>
                <li>Financial Analysis</li>
                <li>Financial Ratios</li>
                <li>Insights & Risk Assessment</li>
                <li>Conclusion & Recommendations</li>
            </ol>
        </section>

        <section class="page-break">
            <h2>Executive Financial Summary</h2>
            <div class="grid-2">
                <div class="card">
                    <h3>Performance Snapshot</h3>
                    <p>Total Revenue: <span class="highlight">${fmt(revenue)}</span></p>
                    <p>Total Expenses: <span class="highlight">${fmt(expenses)}</span></p>
                    <p>Net Profit: <span class="highlight">${fmt(netProfit)}</span></p>
                </div>
                <div class="card">
                    <h3>Balance Overview</h3>
                    <p>Total Assets: <span class="highlight">${fmt(assets)}</span></p>
                    <p>Total Liabilities: <span class="highlight">${fmt(liabilities)}</span></p>
                    <p>Equity: <span class="highlight">${fmt(equity)}</span></p>
                </div>
            </div>
            <div class="card">
                <h3>Key Observations</h3>
                <p>• Revenue driven by recorded credits; expenses represented by debits.</p>
                <p>• Net profit equals credits minus debits within the selected period.</p>
                <p>• Balance derived from closing ledger balance.</p>
            </div>
        </section>

        <section class="page-break">
            <h2>Financial Statements</h2>
            <h3>Income Statement</h3>
            <table>
                <tr><th>Description</th><th>Amount</th></tr>
                <tr><td>Revenue</td><td>${fmt(revenue)}</td></tr>
                <tr><td>Expenses</td><td>${fmt(expenses)}</td></tr>
                <tr class="total-row"><td>Net Profit</td><td>${fmt(netProfit)}</td></tr>
            </table>

            <h3>Balance Sheet</h3>
            <table>
                <tr><th>Description</th><th>Amount</th></tr>
                <tr><td>Assets</td><td>${fmt(assets)}</td></tr>
                <tr><td>Liabilities</td><td>${fmt(liabilities)}</td></tr>
                <tr class="total-row"><td>Equity</td><td>${fmt(equity)}</td></tr>
            </table>

            <h3>Cash Flow Statement</h3>
            <table>
                <tr><th>Activity</th><th>Amount</th></tr>
                <tr><td>Operating Cash Flow</td><td>${fmt(operatingCF)}</td></tr>
                <tr><td>Investing Cash Flow</td><td>${fmt(investingCF)}</td></tr>
                <tr><td>Financing Cash Flow</td><td>${fmt(financingCF)}</td></tr>
                <tr class="total-row"><td>Net Cash Flow</td><td>${fmt(netCash)}</td></tr>
            </table>
        </section>

        <section class="page-break">
            <h2>Financial Analysis</h2>
            <div class="card">
                <h3>Profitability</h3>
                <p>Margins are derived from ledger credits (as revenue) minus debits (as expenses). Net profit reflects the current period difference.</p>
            </div>
            <div class="card">
                <h3>Liquidity</h3>
                <p>Current ratio uses assets versus liabilities derived from ledger balances. Quick ratio is conservatively estimated at 80% of assets.</p>
            </div>
            <div class="card">
                <h3>Solvency & Cash Flow Quality</h3>
                <p>Debt to equity is computed on ledger-derived liabilities and equity. Operating cash flow is approximated to net profit for this ledger view.</p>
            </div>
        </section>

        <section class="page-break">
            <h2>Financial Ratios</h2>
            <table>
                <tr><th>Ratio</th><th>Formula</th><th>Result</th></tr>
                <tr><td>Gross Margin</td><td>(Revenue - Expenses) / Revenue</td><td>${fmt(ratios.grossMargin)}%</td></tr>
                <tr><td>Operating Margin</td><td>Net Profit / Revenue</td><td>${fmt(ratios.operatingMargin)}%</td></tr>
                <tr><td>Net Profit Margin</td><td>Net Profit / Revenue</td><td>${fmt(ratios.netMargin)}%</td></tr>
                <tr><td>Current Ratio</td><td>Assets / Liabilities</td><td>${fmt(ratios.currentRatio)}</td></tr>
                <tr><td>Quick Ratio</td><td>(Assets x 0.8) / Liabilities</td><td>${fmt(ratios.quickRatio)}</td></tr>
                <tr><td>Debt to Equity</td><td>Liabilities / Equity</td><td>${fmt(ratios.debtToEquity)}%</td></tr>
                <tr><td>Return on Assets</td><td>Net Profit / Assets</td><td>${fmt(ratios.roa)}%</td></tr>
                <tr><td>Return on Equity</td><td>Net Profit / Equity</td><td>${fmt(ratios.roe)}%</td></tr>
            </table>
        </section>

        <section class="page-break">
            <h2>Insights & Risk Assessment</h2>
            <p>• Liquidity sensitivity depends on liabilities pressure versus available assets.</p>
            <p>• Revenue stability follows credit entry consistency; monitor period-over-period shifts.</p>
            <p>• Cost concentration observed through debit-heavy accounts; consider review of major expense centers.</p>
            <p>• Sustainability assumes steady inflow of credits; stress-test scenarios with reduced revenues.</p>
        </section>

        <section class="page-break">
            <h2>Conclusion & Recommendations</h2>
            <p>• Maintain disciplined expense controls to preserve margins.</p>
            <p>• Strengthen liquidity buffers if current ratio trends downward.</p>
            <p>• Review financing structure to improve debt-to-equity where needed.</p>
            <p>• Expand revenue diversification to stabilize top line.</p>
        </section>

        <section class="page-break">
            <h2>Ledger Detail (Top 40 Rows)</h2>
            <table>
                <tr><th>Date</th><th>Account</th><th>Description</th><th>Voucher</th><th>Debit</th><th>Credit</th><th>Balance</th></tr>
                ${topEntries.map(e => `
                    <tr>
                        <td>${frappe.datetime.str_to_user(e.posting_date)}</td>
                        <td>${e.account || ''}</td>
                        <td>${e.remarks || ''}</td>
                        <td>${e.voucher_no || ''}</td>
                        <td>${fmt(e.debit || 0)}</td>
                        <td>${fmt(e.credit || 0)}</td>
                        <td>${fmt(e.balance || 0)}</td>
                    </tr>
                `).join('')}
            </table>
        </section>
    </div>
</body>
</html>`;
    }
};
