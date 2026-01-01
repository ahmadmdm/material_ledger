/**
 * State Management Module
 * Centralized state management for financial analysis
 */

const FinancialState = {
    // Application state
    state: {
        loading: false,
        data: null,
        filters: { 
            company: "", 
            year: new Date().getFullYear(), 
            period: "quarterly", 
            period_number: 'Q1' 
        },
        activeStatement: 'dashboard',
        tabData: {},
        tabLoading: {},
        // User preferences
        preferences: {
            darkMode: false,
            language: 'ar',
            dashboardWidgets: ['kpi', 'charts', 'risks', 'ratios'],
            notifications: true
        },
        // Comparison data
        comparison: {
            enabled: false,
            companies: [],
            data: {}
        },
        // Cached data
        cache: {
            key: 'financial_analysis_cache',
            ttl: 3600000 // 1 hour
        }
    },

    // Initialize state from localStorage
    init() {
        this.loadPreferences();
        this.loadCache();
        return this.state;
    },

    // Get current state
    get() {
        return this.state;
    },

    // Update state
    set(key, value) {
        if (key.includes('.')) {
            const keys = key.split('.');
            let obj = this.state;
            for (let i = 0; i < keys.length - 1; i++) {
                obj = obj[keys[i]];
            }
            obj[keys[keys.length - 1]] = value;
        } else {
            this.state[key] = value;
        }
        this.notifyListeners(key, value);
    },

    // State change listeners
    listeners: {},
    
    subscribe(key, callback) {
        if (!this.listeners[key]) {
            this.listeners[key] = [];
        }
        this.listeners[key].push(callback);
        return () => {
            this.listeners[key] = this.listeners[key].filter(cb => cb !== callback);
        };
    },

    notifyListeners(key, value) {
        if (this.listeners[key]) {
            this.listeners[key].forEach(cb => cb(value));
        }
        // Notify wildcard listeners
        if (this.listeners['*']) {
            this.listeners['*'].forEach(cb => cb(key, value));
        }
    },

    // Preferences management
    loadPreferences() {
        try {
            const saved = localStorage.getItem('financial_analysis_prefs');
            if (saved) {
                this.state.preferences = { ...this.state.preferences, ...JSON.parse(saved) };
            }
        } catch (e) {
            console.warn('Failed to load preferences:', e);
        }
    },

    savePreferences() {
        try {
            localStorage.setItem('financial_analysis_prefs', JSON.stringify(this.state.preferences));
        } catch (e) {
            console.warn('Failed to save preferences:', e);
        }
    },

    // Cache management
    loadCache() {
        try {
            const cache = JSON.parse(localStorage.getItem(this.state.cache.key) || '{}');
            const now = Date.now();
            // Clean expired entries
            Object.keys(cache).forEach(key => {
                if (now - cache[key].timestamp > this.state.cache.ttl) {
                    delete cache[key];
                }
            });
            localStorage.setItem(this.state.cache.key, JSON.stringify(cache));
        } catch (e) {
            console.warn('Failed to load cache:', e);
        }
    },

    getCached(key) {
        try {
            const cache = JSON.parse(localStorage.getItem(this.state.cache.key) || '{}');
            const entry = cache[key];
            if (entry && (Date.now() - entry.timestamp) < this.state.cache.ttl) {
                return entry.data;
            }
        } catch (e) {
            console.warn('Cache read error:', e);
        }
        return null;
    },

    setCache(key, data) {
        try {
            const cache = JSON.parse(localStorage.getItem(this.state.cache.key) || '{}');
            cache[key] = { data, timestamp: Date.now() };
            // Keep only last 20 entries
            const keys = Object.keys(cache);
            if (keys.length > 20) {
                const oldest = keys.sort((a, b) => cache[a].timestamp - cache[b].timestamp)[0];
                delete cache[oldest];
            }
            localStorage.setItem(this.state.cache.key, JSON.stringify(cache));
        } catch (e) {
            console.warn('Cache write error:', e);
        }
    },

    clearCache() {
        localStorage.removeItem(this.state.cache.key);
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinancialState;
}
