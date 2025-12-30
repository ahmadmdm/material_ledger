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
        groupByAccount: false
    };

    // Translations
    const t = (key) => {
        const trans = {
            en: {
                company: 'Company', from_date: 'From Date', to_date: 'To Date',
                account: 'Account', cost_center: 'Cost Center', project: 'Project',
                party_type: 'Party Type', party: 'Party', refresh: 'Refresh',
                print: 'Print', export: 'Export', total_debit: 'Total Debit',
                total_credit: 'Total Credit', balance: 'Closing Balance',
                posting_date: 'Date', remarks: 'Description', voucher_no: 'Voucher',
                debit: 'Debit', credit: 'Credit', no_data: 'No entries found',
                group_by_account: 'Group by Account', loading: 'Loading...',
                entries_count: 'Entries'
            },
            ar: {
                company: 'الشركة', from_date: 'من تاريخ', to_date: 'إلى تاريخ',
                account: 'الحساب', cost_center: 'مركز التكلفة', project: 'المشروع',
                party_type: 'نوع الطرف', party: 'الطرف', refresh: 'تحديث',
                print: 'طباعة', export: 'تصدير', total_debit: 'إجمالي المدين',
                total_credit: 'إجمالي الدائن', balance: 'رصيد الإغلاق',
                posting_date: 'التاريخ', remarks: 'البيان', voucher_no: 'رقم السند',
                debit: 'مدين', credit: 'دائن', no_data: 'لا توجد قيود',
                group_by_account: 'تجميع حسب الحساب', loading: 'جاري التحميل...',
                entries_count: 'قيد'
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
                            <button class="modern-btn export-btn" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; padding: 12px 22px; border-radius: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 10px; box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35); transition: all 0.3s; font-size: 14px;">
                                <i class="fa fa-file-excel-o" style="font-size: 16px;"></i> ${t('export')}
                            </button>
                            <button class="modern-btn print-btn" onclick="window.print()" style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; border: none; padding: 12px 22px; border-radius: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 10px; box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35); transition: all 0.3s; font-size: 14px;">
                                <i class="fa fa-print" style="font-size: 16px;"></i> ${t('print')}
                            </button>
                        </div>
                    </div>
                </div>
                <div style="overflow-x: auto;">
                    <table class="professional-ledger-table" style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                                <th style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('posting_date')}</th>
                                <th style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('account')}</th>
                                <th style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('remarks')}</th>
                                <th style="padding: 18px; text-align: ${isRtl ? 'right' : 'left'}; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('voucher_no')}</th>
                                <th style="padding: 18px; text-align: right; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('debit')}</th>
                                <th style="padding: 18px; text-align: right; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('credit')}</th>
                                <th style="padding: 18px; text-align: right; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">${t('balance')}</th>
                            </tr>
                        </thead>
                        <tbody id="ledger-tbody">
                            <tr>
                                <td colspan="7" style="padding: 80px; text-align: center; color: #9ca3af;">
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
        
        // Export button event
        $('.export-btn').on('click', exportToExcel);
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
        page.add_action_icon('printer', () => window.print(), t('print'));
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
                    <td colspan="7" style="padding: 80px; text-align: center; color: #9ca3af;">
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
    }

    function renderFlatTable(tbody) {
        state.entries.forEach(entry => {
            tbody.append(createTableRow(entry));
        });
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
                    <td colspan="7" style="font-size: 15px;">
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
                    <td colspan="4" style="text-align: ${isRtl ? 'left' : 'right'}; font-size: 14px;">${isRtl ? 'المجموع الفرعي' : 'Subtotal'}</td>
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
                <td>${frappe.datetime.str_to_user(e.posting_date) || ''}</td>
                <td style="font-weight: 500;">${e.account || ''}</td>
                <td style="color: #6b7280;">${e.remarks || ''}</td>
                <td>
                    ${e.voucher_type && e.voucher_no && !isOpening 
                        ? `<a href="#Form/${e.voucher_type}/${e.voucher_no}" class="voucher-link">${e.voucher_no}</a>`
                        : (e.voucher_no || '')
                    }
                </td>
                <td style="text-align: right; font-weight: 600; color: #667eea;">${frappe.format(e.debit || 0, {fieldtype: 'Currency'})}</td>
                <td style="text-align: right; font-weight: 600; color: #f5576c;">${frappe.format(e.credit || 0, {fieldtype: 'Currency'})}</td>
                <td style="text-align: right; font-weight: 700; color: ${e.balance < 0 ? '#dc2626' : '#059669'};">${frappe.format(e.balance || 0, {fieldtype: 'Currency'})}</td>
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
                <td colspan="7" style="padding: 60px; text-align: center;">
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
};
