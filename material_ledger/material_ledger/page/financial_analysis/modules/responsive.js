/**
 * Responsive Design Module
 * Handles responsive layout and mobile optimizations
 */

const FinancialResponsive = {
    // Breakpoints
    breakpoints: {
        mobile: 480,
        tablet: 768,
        desktop: 1024,
        wide: 1440
    },

    // Current device type
    deviceType: 'desktop',

    // Initialize responsive module
    init() {
        this.detectDevice();
        this.setupResizeListener();
        this.applyResponsiveStyles();
        this.setupTouchHandlers();
    },

    // Detect device type
    detectDevice() {
        const width = window.innerWidth;
        
        if (width <= this.breakpoints.mobile) {
            this.deviceType = 'mobile';
        } else if (width <= this.breakpoints.tablet) {
            this.deviceType = 'tablet';
        } else if (width <= this.breakpoints.desktop) {
            this.deviceType = 'desktop';
        } else {
            this.deviceType = 'wide';
        }
        
        document.body.setAttribute('data-device', this.deviceType);
        return this.deviceType;
    },

    // Setup resize listener
    setupResizeListener() {
        let resizeTimeout;
        
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                const previousDevice = this.deviceType;
                this.detectDevice();
                
                if (previousDevice !== this.deviceType) {
                    this.applyResponsiveStyles();
                    this.onDeviceChange(previousDevice, this.deviceType);
                }
            }, 150);
        });
    },

    // Apply responsive styles
    applyResponsiveStyles() {
        const styles = `
            /* Base responsive styles */
            @media screen and (max-width: ${this.breakpoints.tablet}px) {
                /* Tab bar - horizontal scroll on tablet */
                .financial-tabs {
                    flex-wrap: nowrap !important;
                    overflow-x: auto !important;
                    -webkit-overflow-scrolling: touch;
                    scrollbar-width: none;
                    padding: 10px 15px !important;
                }
                
                .financial-tabs::-webkit-scrollbar {
                    display: none;
                }
                
                .financial-tab {
                    flex-shrink: 0 !important;
                    min-width: 120px !important;
                    padding: 10px 15px !important;
                    font-size: 13px !important;
                }
                
                /* Metrics grid */
                .metrics-grid {
                    grid-template-columns: repeat(2, 1fr) !important;
                    gap: 12px !important;
                }
                
                /* Filter section */
                .filter-section {
                    flex-direction: column !important;
                    gap: 12px !important;
                }
                
                .filter-section .frappe-control {
                    width: 100% !important;
                    min-width: unset !important;
                }
                
                /* Tables */
                .financial-table {
                    display: block !important;
                    overflow-x: auto !important;
                    -webkit-overflow-scrolling: touch;
                }
                
                .financial-table td,
                .financial-table th {
                    padding: 10px 12px !important;
                    font-size: 13px !important;
                    white-space: nowrap;
                }
                
                /* Charts */
                .chart-container {
                    height: 280px !important;
                }
                
                /* Cards */
                .metric-card {
                    padding: 15px !important;
                }
                
                .metric-card h4 {
                    font-size: 13px !important;
                }
                
                .metric-card .metric-value {
                    font-size: 20px !important;
                }
                
                /* Comparison section */
                #comparison-companies {
                    flex-direction: column !important;
                }
                
                .comparison-company-card {
                    width: 100% !important;
                }
            }
            
            @media screen and (max-width: ${this.breakpoints.mobile}px) {
                /* Tab bar - vertical on mobile */
                .financial-tabs {
                    flex-direction: column !important;
                    padding: 8px !important;
                }
                
                .financial-tab {
                    width: 100% !important;
                    text-align: center !important;
                    padding: 12px !important;
                }
                
                /* Metrics - single column */
                .metrics-grid {
                    grid-template-columns: 1fr !important;
                }
                
                /* Hide non-essential columns */
                .financial-table .hide-mobile {
                    display: none !important;
                }
                
                /* Charts */
                .chart-container {
                    height: 220px !important;
                }
                
                /* Page header */
                .page-header {
                    flex-direction: column !important;
                    gap: 15px !important;
                    text-align: center;
                }
                
                .page-header .actions {
                    justify-content: center !important;
                }
                
                /* Quick actions - bottom fixed */
                .quick-actions-mobile {
                    position: fixed !important;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: white;
                    padding: 12px 15px !important;
                    box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
                    z-index: 999;
                    display: flex !important;
                    justify-content: space-around;
                }
                
                /* Add bottom padding to main content */
                .page-container {
                    padding-bottom: 80px !important;
                }
                
                /* Dialog - full screen on mobile */
                .modal-dialog {
                    margin: 0 !important;
                    max-width: 100% !important;
                    height: 100vh !important;
                }
                
                .modal-content {
                    border-radius: 0 !important;
                    height: 100% !important;
                }
                
                /* Notifications */
                .financial-notification {
                    left: 10px !important;
                    right: 10px !important;
                    max-width: none !important;
                }
            }
            
            /* Touch-friendly enhancements */
            @media (pointer: coarse) {
                /* Larger touch targets */
                .btn, button, .financial-tab, .clickable {
                    min-height: 44px !important;
                    min-width: 44px !important;
                }
                
                /* Table rows */
                .financial-table tr {
                    min-height: 50px !important;
                }
                
                /* Checkbox/radio */
                input[type="checkbox"],
                input[type="radio"] {
                    transform: scale(1.2);
                    margin: 8px !important;
                }
                
                /* Dropdown items */
                .dropdown-menu li {
                    padding: 12px 15px !important;
                }
            }
            
            /* Print styles */
            @media print {
                .financial-tabs,
                .filter-section,
                .no-print,
                .quick-actions-mobile,
                .financial-notification {
                    display: none !important;
                }
                
                .page-container {
                    padding: 0 !important;
                }
                
                .chart-container {
                    page-break-inside: avoid;
                }
                
                .financial-table {
                    page-break-inside: auto;
                }
                
                .financial-table tr {
                    page-break-inside: avoid;
                }
            }
            
            /* Dark mode responsive */
            @media (prefers-color-scheme: dark) {
                body:not(.light-mode) {
                    --bg-primary: #1f2937;
                    --bg-secondary: #111827;
                    --text-primary: #f9fafb;
                    --text-secondary: #9ca3af;
                    --border-color: #374151;
                }
            }
            
            /* High contrast */
            @media (prefers-contrast: high) {
                .metric-card,
                .financial-tab,
                .btn {
                    border: 2px solid currentColor !important;
                }
                
                .financial-tab.active {
                    background: #000 !important;
                    color: #fff !important;
                }
            }
            
            /* Reduced motion */
            @media (prefers-reduced-motion: reduce) {
                *,
                *::before,
                *::after {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            }
        `;
        
        // Remove existing responsive styles
        $('#financial-responsive-styles').remove();
        
        // Add new styles
        $('head').append(`<style id="financial-responsive-styles">${styles}</style>`);
    },

    // Setup touch handlers
    setupTouchHandlers() {
        if (!this.isTouchDevice()) return;
        
        // Swipe detection for tabs
        let touchStartX = 0;
        let touchStartY = 0;
        
        $('.financial-tabs-container').on('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        });
        
        $('.financial-tabs-container').on('touchend', (e) => {
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            
            // Only if horizontal swipe
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    this.swipePreviousTab();
                } else {
                    this.swipeNextTab();
                }
            }
        });
        
        // Long press for context menu
        let longPressTimer;
        
        $('.financial-table tbody tr').on('touchstart', function(e) {
            longPressTimer = setTimeout(() => {
                FinancialResponsive.showRowContextMenu($(this), e);
            }, 500);
        });
        
        $('.financial-table tbody tr').on('touchend touchmove', () => {
            clearTimeout(longPressTimer);
        });
    },

    // Check if touch device
    isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    },

    // Swipe to next tab
    swipeNextTab() {
        const $activeTab = $('.financial-tab.active');
        const $nextTab = $activeTab.next('.financial-tab');
        
        if ($nextTab.length) {
            $nextTab.click();
        }
    },

    // Swipe to previous tab
    swipePreviousTab() {
        const $activeTab = $('.financial-tab.active');
        const $prevTab = $activeTab.prev('.financial-tab');
        
        if ($prevTab.length) {
            $prevTab.click();
        }
    },

    // Show row context menu
    showRowContextMenu($row, event) {
        const isArabic = frappe.boot.lang === 'ar';
        
        const menu = $(`
            <div class="row-context-menu" style="
                position: fixed;
                top: ${event.touches[0].clientY}px;
                left: ${event.touches[0].clientX}px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 25px rgba(0,0,0,0.15);
                z-index: 9999;
                overflow: hidden;
                min-width: 150px;
            ">
                <div class="context-item" data-action="view" style="padding: 12px 15px; cursor: pointer; display: flex; align-items: center; gap: 10px;">
                    <i class="fa fa-eye"></i> ${isArabic ? 'عرض التفاصيل' : 'View Details'}
                </div>
                <div class="context-item" data-action="copy" style="padding: 12px 15px; cursor: pointer; display: flex; align-items: center; gap: 10px; border-top: 1px solid #eee;">
                    <i class="fa fa-copy"></i> ${isArabic ? 'نسخ' : 'Copy'}
                </div>
            </div>
        `);
        
        $('body').append(menu);
        
        // Hide on click outside
        setTimeout(() => {
            $(document).one('click touchstart', () => {
                menu.remove();
            });
        }, 100);
        
        // Handle actions
        menu.find('.context-item').on('click', function() {
            const action = $(this).data('action');
            if (action === 'copy') {
                FinancialResponsive.copyRowData($row);
            }
            menu.remove();
        });
    },

    // Copy row data
    copyRowData($row) {
        const text = $row.find('td').map(function() {
            return $(this).text().trim();
        }).get().join('\t');
        
        navigator.clipboard.writeText(text).then(() => {
            frappe.show_alert({
                message: frappe.boot.lang === 'ar' ? 'تم النسخ' : 'Copied',
                indicator: 'green'
            });
        });
    },

    // On device change callback
    onDeviceChange(from, to) {
        console.log(`Device changed from ${from} to ${to}`);
        
        // Trigger resize event for charts
        window.dispatchEvent(new Event('resize'));
        
        // Show mobile actions on mobile
        if (to === 'mobile') {
            this.showMobileActions();
        } else {
            this.hideMobileActions();
        }
    },

    // Show mobile quick actions
    showMobileActions() {
        if ($('.quick-actions-mobile').length) return;
        
        const isArabic = frappe.boot.lang === 'ar';
        
        const actions = $(`
            <div class="quick-actions-mobile">
                <button class="mobile-action" data-action="refresh" style="
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 10px;
                    font-weight: 600;
                ">
                    <i class="fa fa-refresh"></i>
                </button>
                <button class="mobile-action" data-action="export" style="
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 10px;
                    font-weight: 600;
                ">
                    <i class="fa fa-download"></i>
                </button>
                <button class="mobile-action" data-action="print" style="
                    background: linear-gradient(135deg, #6366f1, #4f46e5);
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 10px;
                    font-weight: 600;
                ">
                    <i class="fa fa-print"></i>
                </button>
                <button class="mobile-action" data-action="filter" style="
                    background: linear-gradient(135deg, #f59e0b, #d97706);
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 10px;
                    font-weight: 600;
                ">
                    <i class="fa fa-filter"></i>
                </button>
            </div>
        `);
        
        $('body').append(actions);
        
        actions.find('.mobile-action').on('click', function() {
            const action = $(this).data('action');
            switch (action) {
                case 'refresh':
                    $('.btn-refresh').click();
                    break;
                case 'export':
                    $('.btn-export').click();
                    break;
                case 'print':
                    window.print();
                    break;
                case 'filter':
                    $('.filter-section').slideToggle();
                    break;
            }
        });
    },

    // Hide mobile quick actions
    hideMobileActions() {
        $('.quick-actions-mobile').remove();
    },

    // Check if mobile
    isMobile() {
        return this.deviceType === 'mobile';
    },

    // Check if tablet
    isTablet() {
        return this.deviceType === 'tablet';
    },

    // Get current breakpoint
    getCurrentBreakpoint() {
        return this.deviceType;
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinancialResponsive;
}
