/**
 * Financial Analysis - Utility Functions Module
 * Contains helper functions for API calls, caching, and common operations
 */

// Local cache for offline support
const FinancialCache = {
    key: 'financial_analysis_cache',
    
    get: function(company, year, period) {
        try {
            const cache = JSON.parse(localStorage.getItem(this.key) || '{}');
            const cacheKey = `${company}_${year}_${period}`;
            const entry = cache[cacheKey];
            if (entry && (Date.now() - entry.timestamp) < 3600000) { // 1 hour cache
                return entry.data;
            }
        } catch(e) { 
            console.warn('Cache read error:', e); 
        }
        return null;
    },
    
    set: function(company, year, period, data) {
        try {
            const cache = JSON.parse(localStorage.getItem(this.key) || '{}');
            const cacheKey = `${company}_${year}_${period}`;
            cache[cacheKey] = { data: data, timestamp: Date.now() };
            // Keep only last 10 entries
            const keys = Object.keys(cache);
            if (keys.length > 10) {
                const oldest = keys.sort((a, b) => cache[a].timestamp - cache[b].timestamp)[0];
                delete cache[oldest];
            }
            localStorage.setItem(this.key, JSON.stringify(cache));
        } catch(e) { 
            console.warn('Cache write error:', e); 
        }
    },
    
    clear: function() {
        localStorage.removeItem(this.key);
    }
};

// API call with retry logic
function apiCallWithRetry(options, retries = 3, delay = 1000, isRtl = false) {
    return new Promise((resolve, reject) => {
        const attempt = (attemptNum) => {
            // Check online status
            if (!navigator.onLine) {
                const offlineError = isRtl ? 'لا يوجد اتصال بالإنترنت' : 'No internet connection';
                reject({ message: offlineError, offline: true });
                return;
            }
            
            frappe.call({
                ...options,
                callback: (r) => {
                    if (r.message) {
                        resolve(r);
                    } else if (attemptNum < retries) {
                        console.warn(`API call failed, retrying... Attempt ${attemptNum + 1}/${retries}`);
                        setTimeout(() => attempt(attemptNum + 1), delay * attemptNum);
                    } else {
                        reject({ message: isRtl ? 'فشل الاتصال بالخادم' : 'Server connection failed' });
                    }
                },
                error: (err) => {
                    if (attemptNum < retries) {
                        console.warn(`API error, retrying... Attempt ${attemptNum + 1}/${retries}`);
                        setTimeout(() => attempt(attemptNum + 1), delay * attemptNum);
                    } else {
                        reject({ 
                            message: err.message || (isRtl ? 'خطأ في الاتصال' : 'Connection error'), 
                            error: err 
                        });
                    }
                }
            });
        };
        attempt(1);
    });
}

// Format currency helper
function formatCurrency(value, options = {}) {
    return frappe.format(value, { fieldtype: 'Currency', ...options });
}

// Format percentage helper
function formatPercent(value, decimals = 2) {
    return `${(value || 0).toFixed(decimals)}%`;
}

// Get color based on value and thresholds
function getValueColor(value, goodThreshold, badThreshold, inverse = false) {
    if (inverse) {
        if (value <= badThreshold) return '#10b981'; // Green
        if (value >= goodThreshold) return '#ef4444'; // Red
        return '#f59e0b'; // Yellow
    }
    if (value >= goodThreshold) return '#10b981'; // Green
    if (value <= badThreshold) return '#ef4444'; // Red
    return '#f59e0b'; // Yellow
}

// Export utilities
if (typeof window !== 'undefined') {
    window.FinancialUtils = {
        cache: FinancialCache,
        apiCallWithRetry,
        formatCurrency,
        formatPercent,
        getValueColor
    };
}
