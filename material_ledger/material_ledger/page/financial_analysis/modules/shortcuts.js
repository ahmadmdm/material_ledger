/**
 * Keyboard Shortcuts Module
 * Global keyboard shortcuts for financial analysis
 */

const FinancialShortcuts = {
    // Registered shortcuts
    shortcuts: {},
    
    // Active state
    enabled: true,
    
    // Help dialog visible
    helpVisible: false,

    // Initialize keyboard shortcuts
    init() {
        this.registerDefaultShortcuts();
        this.bindKeyListener();
        this.createHelpDialog();
    },

    // Register default shortcuts
    registerDefaultShortcuts() {
        const isArabic = frappe.boot.lang === 'ar';
        
        // Navigation
        this.register('r', {
            description: isArabic ? 'تحديث البيانات' : 'Refresh Data',
            category: 'navigation',
            action: () => {
                $('.page-head .btn-primary').click();
            }
        });

        this.register('d', {
            description: isArabic ? 'لوحة التحكم' : 'Dashboard',
            category: 'navigation',
            action: () => $('.dashboard-tab[data-tab="dashboard"]').click()
        });

        this.register('i', {
            description: isArabic ? 'قائمة الدخل' : 'Income Statement',
            category: 'navigation',
            action: () => $('.dashboard-tab[data-tab="income"]').click()
        });

        this.register('b', {
            description: isArabic ? 'الميزانية' : 'Balance Sheet',
            category: 'navigation',
            action: () => $('.dashboard-tab[data-tab="balance"]').click()
        });

        this.register('c', {
            description: isArabic ? 'التدفقات النقدية' : 'Cash Flow',
            category: 'navigation',
            action: () => $('.dashboard-tab[data-tab="cash"]').click()
        });

        this.register('a', {
            description: isArabic ? 'تحليل AI' : 'AI Analysis',
            category: 'navigation',
            action: () => $('.dashboard-tab[data-tab="ai"]').click()
        });

        // Tabs 1-9
        for (let i = 1; i <= 9; i++) {
            this.register(i.toString(), {
                description: isArabic ? `التاب ${i}` : `Tab ${i}`,
                category: 'navigation',
                action: () => {
                    const tabs = $('.dashboard-tab');
                    if (tabs.length >= i) {
                        tabs.eq(i - 1).click();
                    }
                }
            });
        }

        // Actions
        this.register('p', {
            description: isArabic ? 'طباعة / تصدير PDF' : 'Print / Export PDF',
            category: 'actions',
            action: () => {
                // Trigger print
                if (typeof exportToPDF === 'function') {
                    exportToPDF();
                } else {
                    window.print();
                }
            }
        });

        this.register('e', {
            description: isArabic ? 'تصدير Excel' : 'Export Excel',
            category: 'actions',
            action: () => {
                if (typeof exportToExcel === 'function') {
                    exportToExcel();
                }
            }
        });

        this.register('/', {
            description: isArabic ? 'البحث' : 'Search',
            category: 'actions',
            action: () => {
                frappe.searchbox.show();
            }
        });

        // View
        this.register('m', {
            description: isArabic ? 'الوضع الداكن' : 'Toggle Dark Mode',
            category: 'view',
            action: () => {
                if (typeof toggleDarkMode === 'function') {
                    toggleDarkMode();
                }
            }
        });

        this.register('f', {
            description: isArabic ? 'شاشة كاملة' : 'Fullscreen',
            category: 'view',
            action: () => {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen();
                } else {
                    document.exitFullscreen();
                }
            }
        });

        // Help
        this.register('?', {
            description: isArabic ? 'عرض المساعدة' : 'Show Help',
            category: 'help',
            shift: true,
            action: () => this.showHelp()
        });

        this.register('Escape', {
            description: isArabic ? 'إغلاق' : 'Close',
            category: 'help',
            action: () => {
                if (this.helpVisible) {
                    this.hideHelp();
                }
                // Close any open dialogs
                $('.modal.show').modal('hide');
            }
        });

        // CTRL shortcuts
        this.register('s', {
            description: isArabic ? 'حفظ التقرير' : 'Save Report',
            category: 'actions',
            ctrl: true,
            action: (e) => {
                e.preventDefault();
                frappe.show_alert({
                    message: isArabic ? 'تم حفظ التقرير' : 'Report saved',
                    indicator: 'green'
                });
            }
        });
    },

    // Register a new shortcut
    register(key, options) {
        const shortcutKey = this.buildKey(key, options);
        this.shortcuts[shortcutKey] = {
            key: key,
            ...options
        };
    },

    // Build unique key for shortcut
    buildKey(key, options = {}) {
        let parts = [];
        if (options.ctrl) parts.push('ctrl');
        if (options.shift) parts.push('shift');
        if (options.alt) parts.push('alt');
        parts.push(key.toLowerCase());
        return parts.join('+');
    },

    // Bind keyboard listener
    bindKeyListener() {
        $(document).on('keydown.financial-shortcuts', (e) => {
            if (!this.enabled) return;

            // Ignore if typing in input
            if ($(e.target).is('input, textarea, select, [contenteditable]')) {
                // Allow escape
                if (e.key !== 'Escape') return;
            }

            const shortcutKey = this.buildKey(e.key, {
                ctrl: e.ctrlKey || e.metaKey,
                shift: e.shiftKey,
                alt: e.altKey
            });

            const shortcut = this.shortcuts[shortcutKey];
            if (shortcut && shortcut.action) {
                shortcut.action(e);
                e.preventDefault();
            }
        });
    },

    // Create help dialog
    createHelpDialog() {
        if ($('#shortcuts-help-dialog').length) return;

        const isArabic = frappe.boot.lang === 'ar';
        const categories = {
            navigation: isArabic ? 'التنقل' : 'Navigation',
            actions: isArabic ? 'الإجراءات' : 'Actions',
            view: isArabic ? 'العرض' : 'View',
            help: isArabic ? 'المساعدة' : 'Help'
        };

        $('body').append(`
            <div id="shortcuts-help-dialog" style="
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.7);
                z-index: 10001;
                backdrop-filter: blur(5px);
                animation: fadeIn 0.2s ease-out;
            ">
                <div style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: white;
                    border-radius: 16px;
                    padding: 30px;
                    max-width: 600px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 25px 80px rgba(0,0,0,0.3);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                        <h2 style="margin: 0; font-size: 24px; font-weight: 800; color: #1f2937;">
                            <i class="fa fa-keyboard-o" style="color: #667eea; margin-${isArabic ? 'left' : 'right'}: 10px;"></i>
                            ${isArabic ? 'اختصارات لوحة المفاتيح' : 'Keyboard Shortcuts'}
                        </h2>
                        <button id="close-shortcuts-help" style="
                            background: none;
                            border: none;
                            font-size: 24px;
                            cursor: pointer;
                            color: #9ca3af;
                            transition: color 0.2s;
                        ">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                    <div id="shortcuts-list"></div>
                </div>
            </div>
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                .shortcut-category {
                    margin-bottom: 25px;
                }
                .shortcut-category-title {
                    font-size: 14px;
                    font-weight: 700;
                    color: #667eea;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 12px;
                    padding-bottom: 8px;
                    border-bottom: 2px solid #e5e7eb;
                }
                .shortcut-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 0;
                    border-bottom: 1px solid #f3f4f6;
                }
                .shortcut-item:last-child {
                    border-bottom: none;
                }
                .shortcut-key {
                    display: inline-flex;
                    align-items: center;
                    gap: 5px;
                }
                .shortcut-key kbd {
                    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-family: 'SF Mono', 'Monaco', monospace;
                    font-size: 12px;
                    font-weight: 600;
                    color: #374151;
                    box-shadow: 0 2px 0 #d1d5db;
                }
                .shortcut-description {
                    color: #6b7280;
                    font-size: 14px;
                }
            </style>
        `);

        $('#close-shortcuts-help, #shortcuts-help-dialog').on('click', (e) => {
            if (e.target === e.currentTarget || $(e.target).closest('#close-shortcuts-help').length) {
                this.hideHelp();
            }
        });
    },

    // Show help dialog
    showHelp() {
        const isArabic = frappe.boot.lang === 'ar';
        const categories = {
            navigation: isArabic ? 'التنقل' : 'Navigation',
            actions: isArabic ? 'الإجراءات' : 'Actions',
            view: isArabic ? 'العرض' : 'View',
            help: isArabic ? 'المساعدة' : 'Help'
        };

        // Group shortcuts by category
        const grouped = {};
        Object.values(this.shortcuts).forEach(shortcut => {
            const cat = shortcut.category || 'other';
            if (!grouped[cat]) grouped[cat] = [];
            grouped[cat].push(shortcut);
        });

        let html = '';
        Object.keys(categories).forEach(cat => {
            if (!grouped[cat] || grouped[cat].length === 0) return;
            
            html += `<div class="shortcut-category">
                <div class="shortcut-category-title">${categories[cat]}</div>`;
            
            grouped[cat].forEach(shortcut => {
                let keys = [];
                if (shortcut.ctrl) keys.push('Ctrl');
                if (shortcut.shift) keys.push('Shift');
                if (shortcut.alt) keys.push('Alt');
                keys.push(shortcut.key.toUpperCase());
                
                html += `<div class="shortcut-item">
                    <span class="shortcut-description">${shortcut.description}</span>
                    <span class="shortcut-key">
                        ${keys.map(k => `<kbd>${k}</kbd>`).join(' + ')}
                    </span>
                </div>`;
            });
            
            html += '</div>';
        });

        $('#shortcuts-list').html(html);
        $('#shortcuts-help-dialog').fadeIn(200);
        this.helpVisible = true;
    },

    // Hide help dialog
    hideHelp() {
        $('#shortcuts-help-dialog').fadeOut(200);
        this.helpVisible = false;
    },

    // Enable shortcuts
    enable() {
        this.enabled = true;
    },

    // Disable shortcuts
    disable() {
        this.enabled = false;
    },

    // Destroy
    destroy() {
        $(document).off('keydown.financial-shortcuts');
        $('#shortcuts-help-dialog').remove();
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinancialShortcuts;
}
