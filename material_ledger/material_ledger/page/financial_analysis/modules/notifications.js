/**
 * Notifications Module
 * Smart notifications and alerts system
 */

const FinancialNotifications = {
    // Configuration
    config: {
        enabled: true,
        sound: false,
        desktop: true,
        position: 'top-right', // top-right, top-left, bottom-right, bottom-left
        duration: 5000, // ms
        maxVisible: 5
    },

    // Active notifications
    active: [],
    queue: [],

    // Initialize notifications
    init(options = {}) {
        this.config = { ...this.config, ...options };
        this.createContainer();
        this.requestDesktopPermission();
    },

    // Create notification container
    createContainer() {
        if ($('#financial-notifications').length) return;
        
        const positions = {
            'top-right': 'top: 80px; right: 20px;',
            'top-left': 'top: 80px; left: 20px;',
            'bottom-right': 'bottom: 20px; right: 20px;',
            'bottom-left': 'bottom: 20px; left: 20px;'
        };

        $('body').append(`
            <div id="financial-notifications" style="
                position: fixed;
                ${positions[this.config.position]}
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 400px;
                pointer-events: none;
            "></div>
            <style>
                .fin-notification {
                    background: white;
                    border-radius: 12px;
                    padding: 16px 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
                    display: flex;
                    align-items: flex-start;
                    gap: 12px;
                    animation: slideInNotification 0.3s ease-out;
                    pointer-events: auto;
                    border-left: 4px solid;
                    transition: all 0.3s ease;
                }
                .fin-notification:hover {
                    transform: translateX(-5px);
                    box-shadow: 0 15px 50px rgba(0,0,0,0.2);
                }
                .fin-notification.info { border-left-color: #3b82f6; }
                .fin-notification.success { border-left-color: #10b981; }
                .fin-notification.warning { border-left-color: #f59e0b; }
                .fin-notification.error { border-left-color: #ef4444; }
                .fin-notification.critical { 
                    border-left-color: #dc2626; 
                    background: #fef2f2;
                    animation: shake 0.5s ease-out, slideInNotification 0.3s ease-out;
                }
                .fin-notification-icon {
                    font-size: 24px;
                    min-width: 30px;
                }
                .fin-notification.info .fin-notification-icon { color: #3b82f6; }
                .fin-notification.success .fin-notification-icon { color: #10b981; }
                .fin-notification.warning .fin-notification-icon { color: #f59e0b; }
                .fin-notification.error .fin-notification-icon { color: #ef4444; }
                .fin-notification.critical .fin-notification-icon { color: #dc2626; }
                .fin-notification-content { flex: 1; }
                .fin-notification-title { font-weight: 700; font-size: 14px; color: #1f2937; margin-bottom: 4px; }
                .fin-notification-message { font-size: 13px; color: #6b7280; line-height: 1.4; }
                .fin-notification-close {
                    cursor: pointer;
                    color: #9ca3af;
                    font-size: 18px;
                    transition: color 0.2s;
                }
                .fin-notification-close:hover { color: #374151; }
                .fin-notification-actions {
                    display: flex;
                    gap: 8px;
                    margin-top: 10px;
                }
                .fin-notification-btn {
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    border: none;
                    transition: all 0.2s;
                }
                .fin-notification-btn.primary {
                    background: #667eea;
                    color: white;
                }
                .fin-notification-btn.primary:hover {
                    background: #5a67d8;
                }
                .fin-notification-btn.secondary {
                    background: #f3f4f6;
                    color: #374151;
                }
                .fin-notification-btn.secondary:hover {
                    background: #e5e7eb;
                }
                @keyframes slideInNotification {
                    from { opacity: 0; transform: translateX(100px); }
                    to { opacity: 1; transform: translateX(0); }
                }
                @keyframes slideOutNotification {
                    from { opacity: 1; transform: translateX(0); }
                    to { opacity: 0; transform: translateX(100px); }
                }
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-10px); }
                    50% { transform: translateX(10px); }
                    75% { transform: translateX(-10px); }
                }
            </style>
        `);
    },

    // Request desktop notification permission
    requestDesktopPermission() {
        if (this.config.desktop && 'Notification' in window) {
            if (Notification.permission === 'default') {
                Notification.requestPermission();
            }
        }
    },

    // Show notification
    show(options) {
        if (!this.config.enabled) return;

        const notification = {
            id: Date.now() + Math.random(),
            type: options.type || 'info', // info, success, warning, error, critical
            title: options.title || '',
            message: options.message || '',
            duration: options.duration || this.config.duration,
            actions: options.actions || [],
            persistent: options.persistent || false,
            onClick: options.onClick || null
        };

        // Limit visible notifications
        if (this.active.length >= this.config.maxVisible) {
            this.queue.push(notification);
            return notification.id;
        }

        this.displayNotification(notification);
        return notification.id;
    },

    // Display notification in DOM
    displayNotification(notification) {
        const icons = {
            info: 'fa-info-circle',
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle',
            critical: 'fa-exclamation-circle'
        };

        let actionsHTML = '';
        if (notification.actions.length > 0) {
            actionsHTML = '<div class="fin-notification-actions">' +
                notification.actions.map(action => 
                    `<button class="fin-notification-btn ${action.primary ? 'primary' : 'secondary'}" 
                             data-action="${action.id}">${action.label}</button>`
                ).join('') +
            '</div>';
        }

        const $notification = $(`
            <div class="fin-notification ${notification.type}" data-id="${notification.id}">
                <div class="fin-notification-icon">
                    <i class="fa ${icons[notification.type]}"></i>
                </div>
                <div class="fin-notification-content">
                    <div class="fin-notification-title">${notification.title}</div>
                    <div class="fin-notification-message">${notification.message}</div>
                    ${actionsHTML}
                </div>
                <div class="fin-notification-close">
                    <i class="fa fa-times"></i>
                </div>
            </div>
        `);

        // Event handlers
        $notification.find('.fin-notification-close').on('click', () => {
            this.dismiss(notification.id);
        });

        if (notification.onClick) {
            $notification.css('cursor', 'pointer').on('click', (e) => {
                if (!$(e.target).closest('.fin-notification-close, .fin-notification-btn').length) {
                    notification.onClick();
                    this.dismiss(notification.id);
                }
            });
        }

        notification.actions.forEach(action => {
            $notification.find(`[data-action="${action.id}"]`).on('click', () => {
                if (action.callback) action.callback();
                if (action.dismiss !== false) this.dismiss(notification.id);
            });
        });

        $('#financial-notifications').append($notification);
        this.active.push(notification);

        // Auto-dismiss if not persistent
        if (!notification.persistent && notification.duration > 0) {
            setTimeout(() => {
                this.dismiss(notification.id);
            }, notification.duration);
        }

        // Show desktop notification for critical
        if (notification.type === 'critical' && this.config.desktop) {
            this.showDesktopNotification(notification);
        }

        // Play sound for critical
        if (notification.type === 'critical' && this.config.sound) {
            this.playSound();
        }
    },

    // Dismiss notification
    dismiss(id) {
        const $notification = $(`.fin-notification[data-id="${id}"]`);
        if ($notification.length) {
            $notification.css('animation', 'slideOutNotification 0.3s ease-out forwards');
            setTimeout(() => {
                $notification.remove();
                this.active = this.active.filter(n => n.id !== id);
                
                // Show queued notification
                if (this.queue.length > 0) {
                    const next = this.queue.shift();
                    this.displayNotification(next);
                }
            }, 300);
        }
    },

    // Dismiss all notifications
    dismissAll() {
        this.active.forEach(n => this.dismiss(n.id));
        this.queue = [];
    },

    // Show desktop notification
    showDesktopNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/assets/material_ledger/images/icon.png',
                tag: 'financial-' + notification.id
            });
        }
    },

    // Play notification sound
    playSound() {
        try {
            const audio = new Audio('/assets/material_ledger/sounds/alert.mp3');
            audio.volume = 0.3;
            audio.play();
        } catch (e) {
            console.warn('Failed to play notification sound');
        }
    },

    // Helper methods for common notifications
    info(title, message, options = {}) {
        return this.show({ type: 'info', title, message, ...options });
    },

    success(title, message, options = {}) {
        return this.show({ type: 'success', title, message, ...options });
    },

    warning(title, message, options = {}) {
        return this.show({ type: 'warning', title, message, ...options });
    },

    error(title, message, options = {}) {
        return this.show({ type: 'error', title, message, ...options });
    },

    critical(title, message, options = {}) {
        return this.show({ type: 'critical', title, message, persistent: true, ...options });
    },

    // Financial-specific notifications
    riskAlert(risk) {
        const isArabic = frappe.boot.lang === 'ar';
        return this.show({
            type: risk.level === 'critical' ? 'critical' : 'warning',
            title: risk.title,
            message: risk.message,
            persistent: risk.level === 'critical',
            actions: [
                {
                    id: 'view',
                    label: isArabic ? 'عرض التفاصيل' : 'View Details',
                    primary: true,
                    callback: () => {
                        // Navigate to risk details
                        $('.dashboard-tab[data-tab="ratios"]').click();
                    }
                },
                {
                    id: 'dismiss',
                    label: isArabic ? 'تجاهل' : 'Dismiss',
                    dismiss: true
                }
            ]
        });
    },

    // Show multiple risk alerts
    showRiskAlerts(risks) {
        if (!risks || risks.length === 0) return;
        
        const criticalRisks = risks.filter(r => r.level === 'critical');
        const warningRisks = risks.filter(r => r.level === 'warning');
        
        // Show critical risks first
        criticalRisks.forEach((risk, index) => {
            setTimeout(() => this.riskAlert(risk), index * 500);
        });
        
        // Then warnings
        warningRisks.forEach((risk, index) => {
            setTimeout(() => this.riskAlert(risk), (criticalRisks.length + index) * 500);
        });
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinancialNotifications;
}
