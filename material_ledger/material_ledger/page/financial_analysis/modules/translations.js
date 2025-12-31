/**
 * Financial Analysis - Translations Module
 * Handles all translation strings for multi-language support
 */

const FinancialTranslations = {
    en: {
        company: 'Company',
        year: 'Fiscal Year',
        refresh: 'Analyze',
        dashboard: 'Executive Dashboard',
        income: 'Income Statement',
        balance: 'Balance Sheet',
        cash: 'Cash Flow',
        ratios: 'Financial Ratios',
        health_score: 'Financial Health Score',
        risk_alerts: 'Risk Alerts',
        dupont: 'DuPont Analysis',
        working_capital: 'Working Capital',
        revenue: 'Revenue',
        expenses: 'Expenses',
        net_income: 'Net Income',
        no_data: 'No data',
        loading: 'Analyzing...',
        generate_ai: 'AI Insights',
        equity_changes: 'Changes in Equity',
        monthly: 'Monthly',
        quarterly: 'Quarterly',
        annual: 'Annual',
        period: 'Period',
        select_month: 'Select Month',
        select_quarter: 'Select Quarter',
        ai_analysis: 'AI Deep Analysis',
        forecast: 'Forecast',
        benchmark: 'Benchmark',
        forecast_title: 'Financial Forecasts',
        benchmark_title: 'Industry Benchmark',
        growth_rate: 'Growth Rate',
        projected: 'Projected',
        actual: 'Actual',
        confidence: 'Confidence',
        low: 'Low',
        avg: 'Average',
        high: 'High',
        excellent: 'Excellent',
        good: 'Good',
        fair: 'Fair',
        poor: 'Poor',
        needs_improvement: 'Needs Improvement',
        export_pdf: 'Export PDF',
        export_excel: 'Export Excel',
        schedule_report: 'Schedule Report',
        compare_periods: 'Compare Periods',
        retry: 'Retry',
        offline_mode: 'Offline Mode',
        cached_data: 'Showing cached data',
        no_internet: 'No internet connection',
        connection_error: 'Connection error',
        analysis_completed: 'Analysis completed'
    },
    ar: {
        company: 'الشركة',
        year: 'السنة المالية',
        refresh: 'تحليل',
        dashboard: 'لوحة التحكم التنفيذية',
        income: 'قائمة الدخل',
        balance: 'الميزانية العمومية',
        cash: 'التدفقات النقدية',
        ratios: 'النسب المالية',
        health_score: 'درجة الصحة المالية',
        risk_alerts: 'تنبيهات المخاطر',
        dupont: 'تحليل دوبونت',
        working_capital: 'رأس المال العامل',
        revenue: 'الإيرادات',
        expenses: 'المصروفات',
        net_income: 'صافي الدخل',
        no_data: 'لا توجد بيانات',
        loading: 'جاري التحليل...',
        generate_ai: 'رؤى AI',
        equity_changes: 'التغيرات في حقوق الملكية',
        monthly: 'شهري',
        quarterly: 'ربعي',
        annual: 'سنوي',
        period: 'الفترة',
        select_month: 'اختر الشهر',
        select_quarter: 'اختر الربع',
        ai_analysis: 'التحليل العميق بالذكاء الاصطناعي',
        forecast: 'التوقعات',
        benchmark: 'المقارنة',
        forecast_title: 'التوقعات المالية',
        benchmark_title: 'مقارنة الصناعة',
        growth_rate: 'معدل النمو',
        projected: 'المتوقع',
        actual: 'الفعلي',
        confidence: 'مستوى الثقة',
        low: 'منخفض',
        avg: 'متوسط',
        high: 'مرتفع',
        excellent: 'ممتاز',
        good: 'جيد',
        fair: 'مقبول',
        poor: 'ضعيف',
        needs_improvement: 'يحتاج تحسين',
        export_pdf: 'تصدير PDF',
        export_excel: 'تصدير Excel',
        schedule_report: 'جدولة التقرير',
        compare_periods: 'مقارنة الفترات',
        retry: 'إعادة المحاولة',
        offline_mode: 'وضع عدم الاتصال',
        cached_data: 'عرض البيانات المخزنة',
        no_internet: 'لا يوجد اتصال بالإنترنت',
        connection_error: 'خطأ في الاتصال',
        analysis_completed: 'تم التحليل بنجاح'
    }
};

// Create translator function
function createTranslator(lang) {
    const translations = FinancialTranslations[lang] || FinancialTranslations['en'];
    return function(key) {
        return translations[key] || key;
    };
}

// Export translations
if (typeof window !== 'undefined') {
    window.FinancialTranslations = FinancialTranslations;
    window.createFinancialTranslator = createTranslator;
}
