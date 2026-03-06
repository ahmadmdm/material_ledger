// AI Dashboard JavaScript
frappe.pages['ai-dashboard'].on_page_load = function(wrapper) {
    console.log("🤖 AI Financial Dashboard v1.0");
    
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('AI Financial Dashboard'),
        single_column: true
    });
    
    // Initialize dashboard
    let dashboard = new AIDashboard(page);
    dashboard.init();
};

class AIDashboard {
    constructor(page) {
        this.page = page;
        this.page_content = page.main;
        this.activeJobs = {};
        this.currentCompany = null;
        this.chatHistory = [];
    }
    
    init() {
        this.setupPage();
        this.bindEvents();
        this.loadCompanies();
        this.startJobMonitoring();
        this.checkNotifications();
        
        // Welcome message
        this.showWelcomeMessage();
    }
    
    setupPage() {
        // Load custom styles
        this.loadStyles();
        
        // Set up real-time updates
        this.setupRealTime();
        
        // Inject HTML directly since render_template might not find the file
        const html = `
<div class="ai-dashboard-container" dir="rtl">
    <!-- Header Section -->
    <div class="dashboard-header">
        <h1 class="dashboard-title">
            <span class="ai-icon">🤖</span>
            <span class="title-text">لوحة التحكم الذكية</span>
            <span class="subtitle">AI Financial Dashboard</span>
        </h1>
        
        <div class="dashboard-controls">
            <div class="company-selector">
                <label>الشركة:</label>
                <select class="form-control" id="company-select">
                    <option value="">اختر الشركة...</option>
                </select>
            </div>
            
            <button class="btn btn-primary" id="refresh-dashboard">
                <i class="fa fa-refresh"></i> تحديث البيانات
            </button>
        </div>
    </div>
    
    <!-- Quick Insights Cards -->
    <div class="quick-insights">
        <div class="insight-card" id="health-score-card">
            <div class="card-header">
                <h3>📊 درجة الصحة المالية</h3>
            </div>
            <div class="card-content">
                <div class="score-circle" id="health-score">
                    <span class="score-value">--</span>
                    <span class="score-label">من 100</span>
                </div>
                <div class="score-description" id="health-description">
                    جاري التحليل...
                </div>
            </div>
        </div>
        
        <div class="insight-card" id="ai-recommendations-card">
            <div class="card-header">
                <h3>💡 توصيات ذكية</h3>
            </div>
            <div class="card-content" id="ai-recommendations">
                <div class="loading-state">⏳ جاري تحليل البيانات...</div>
            </div>
        </div>
        
        <div class="insight-card" id="risk-alerts-card">
            <div class="card-header">
                <h3>⚠️ تنبيهات المخاطر</h3>
            </div>
            <div class="card-content" id="risk-alerts">
                <div class="loading-state">🔍 فحص المخاطر...</div>
            </div>
        </div>
    </div>
    
    <!-- AI Services Section -->
    <div class="ai-services-section">
        <h2 class="section-title">🎯 الخدمات الذكية</h2>
        
        <div class="services-grid">
            <!-- Financial Prediction -->
            <div class="service-card" data-service="prediction">
                <div class="service-icon">🔮</div>
                <h3>التنبؤ المالي</h3>
                <p>توقع الأداء والتدفق النقدي للأشهر القادمة</p>
                <button class="btn btn-primary service-btn">بدء التنبؤ</button>
                <div class="service-status" style="display: none;"></div>
            </div>
            
            <!-- Anomaly Detection -->
            <div class="service-card" data-service="anomaly">
                <div class="service-icon">🕵️</div>
                <h3>كشف الشذوذ</h3>
                <p>اكتشاف المعاملات المشبوهة والأنماط غير العادية</p>
                <button class="btn btn-warning service-btn">فحص الشذوذ</button>
                <div class="service-status" style="display: none;"></div>
            </div>
            
            <!-- Investment Analysis -->
            <div class="service-card" data-service="investment">
                <div class="service-icon">📈</div>
                <h3>تحليل الاستثمار</h3>
                <p>تقييم الفرص الاستثمارية وحساب العوائد</p>
                <button class="btn btn-success service-btn">تحليل الاستثمار</button>
                <div class="service-status" style="display: none;"></div>
            </div>
            
            <!-- Comprehensive Analysis -->
            <div class="service-card" data-service="comprehensive">
                <div class="service-icon">📋</div>
                <h3>التحليل الشامل</h3>
                <p>تحليل مالي شامل مدعوم بالذكاء الاصطناعي</p>
                <button class="btn btn-info service-btn">التحليل الشامل</button>
                <div class="service-status" style="display: none;"></div>
            </div>
        </div>
    </div>
    
    <!-- AI Assistant Chat -->
    <div class="ai-assistant-section">
        <h2 class="section-title">💬 المساعد الذكي</h2>
        
        <div class="chat-container">
            <div class="chat-messages" id="chat-messages">
                <div class="assistant-message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        <p>مرحباً! أنا مساعدك المالي الذكي. يمكنني مساعدتك في:</p>
                        <ul>
                            <li>تحليل البيانات المالية</li>
                            <li>الإجابة على الاستفسارات المحاسبية</li>
                            <li>تقديم التوصيات والنصائح</li>
                            <li>شرح التقارير والنسب المالية</li>
                        </ul>
                        <p>اسأل عن أي شيء تريد معرفته!</p>
                    </div>
                </div>
            </div>
            
            <div class="chat-input-container">
                <input type="text" class="form-control chat-input" id="chat-input" 
                       placeholder="اكتب سؤالك هنا... مثال: ما هو أداء الشركة هذا الربع؟">
                <button class="btn btn-primary chat-send" id="chat-send">
                    <i class="fa fa-paper-plane"></i>
                </button>
            </div>
            
            <div class="quick-questions">
                <h4>أسئلة سريعة:</h4>
                <div class="question-chips">
                    <span class="question-chip" data-question="ما هو صافي الربح هذا الشهر؟">💰 الربح الشهري</span>
                    <span class="question-chip" data-question="كيف أداء المبيعات مقارنة بالعام الماضي؟">📊 أداء المبيعات</span>
                    <span class="question-chip" data-question="ما هي أهم المخاطر المالية؟">⚠️ المخاطر</span>
                    <span class="question-chip" data-question="أين يمكنني تقليل التكاليف؟">💸 تقليل التكاليف</span>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Results Section -->
    <div class="results-section" style="display: none;">
        <h2 class="section-title">📊 نتائج التحليل</h2>
        <div class="results-container" id="results-container">
            <!-- Results will be loaded here -->
        </div>
    </div>
    
    <!-- Background Jobs Monitor -->
    <div class="jobs-monitor" id="jobs-monitor" style="display: none;">
        <h3>⏳ المهام قيد التنفيذ</h3>
        <div class="jobs-list" id="jobs-list">
            <!-- Active jobs will be shown here -->
        </div>
    </div>
</div>`;
        $(this.page.main).html(html);
    }
    
    loadStyles() {
        const style = `
            <style>
            .ai-dashboard-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .dashboard-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                color: white;
            }
            
            .dashboard-title {
                margin: 0;
                font-size: 28px;
                font-weight: bold;
            }
            
            .ai-icon {
                font-size: 36px;
                margin-right: 15px;
                animation: pulse 2s infinite;
            }
            
            .subtitle {
                display: block;
                font-size: 14px;
                opacity: 0.8;
                font-weight: normal;
            }
            
            .dashboard-controls {
                display: flex;
                gap: 15px;
                align-items: center;
            }
            
            .company-selector label {
                color: white;
                margin-right: 8px;
            }
            
            .quick-insights {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            
            .insight-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                border: 1px solid #f0f0f0;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .insight-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 30px rgba(0,0,0,0.12);
            }
            
            .card-header h3 {
                margin: 0 0 15px 0;
                color: #333;
                font-size: 18px;
            }
            
            .score-circle {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                width: 120px;
                height: 120px;
                border-radius: 50%;
                background: conic-gradient(#4ade80 0deg, #22c55e 180deg, #16a34a 360deg);
                margin: 0 auto 15px;
                position: relative;
            }
            
            .score-circle::before {
                content: '';
                position: absolute;
                width: 90px;
                height: 90px;
                background: white;
                border-radius: 50%;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
            }
            
            .score-value {
                font-size: 28px;
                font-weight: bold;
                color: #333;
                z-index: 1;
            }
            
            .score-label {
                font-size: 12px;
                color: #666;
                z-index: 1;
            }
            
            .score-description {
                text-align: center;
                color: #666;
                font-size: 14px;
            }
            
            .services-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            
            .service-card {
                background: white;
                border-radius: 12px;
                padding: 25px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                border: 1px solid #f0f0f0;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .service-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            }
            
            .service-icon {
                font-size: 48px;
                margin-bottom: 15px;
                display: block;
            }
            
            .service-card h3 {
                margin: 0 0 10px 0;
                color: #333;
                font-size: 20px;
            }
            
            .service-card p {
                color: #666;
                margin-bottom: 20px;
                line-height: 1.5;
            }
            
            .service-status {
                margin-top: 15px;
                padding: 10px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            
            .status-queued {
                background: #fef3c7;
                color: #92400e;
            }
            
            .status-processing {
                background: #dbeafe;
                color: #1e40af;
            }
            
            .status-completed {
                background: #d1fae5;
                color: #065f46;
            }
            
            .status-failed {
                background: #fee2e2;
                color: #991b1b;
            }
            
            .chat-container {
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                margin-bottom: 30px;
            }
            
            .chat-messages {
                height: 400px;
                overflow-y: auto;
                padding: 20px;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .message {
                margin-bottom: 15px;
                display: flex;
                align-items: flex-start;
                gap: 12px;
            }
            
            .assistant-message {
                margin-bottom: 20px;
            }
            
            .user-message {
                justify-content: flex-end;
                flex-direction: row-reverse;
            }
            
            .message-avatar {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background: #667eea;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                flex-shrink: 0;
            }
            
            .user-message .message-avatar {
                background: #22c55e;
            }
            
            .message-content {
                background: #f8fafc;
                padding: 12px 16px;
                border-radius: 12px;
                max-width: 70%;
                line-height: 1.5;
            }
            
            .user-message .message-content {
                background: #3b82f6;
                color: white;
            }
            
            .chat-input-container {
                display: flex;
                padding: 15px 20px;
                gap: 10px;
            }
            
            .chat-input {
                flex: 1;
                padding: 12px 16px;
                border: 1px solid #e2e8f0;
                border-radius: 25px;
                outline: none;
                font-size: 14px;
            }
            
            .chat-send {
                width: 45px;
                height: 45px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0;
            }
            
            .quick-questions {
                padding: 15px 20px 20px;
                background: #f8fafc;
            }
            
            .quick-questions h4 {
                margin: 0 0 12px 0;
                color: #374151;
                font-size: 14px;
            }
            
            .question-chips {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .question-chip {
                background: #e2e8f0;
                color: #475569;
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .question-chip:hover {
                background: #3b82f6;
                color: white;
            }
            
            .section-title {
                font-size: 24px;
                font-weight: bold;
                color: #1f2937;
                margin-bottom: 20px;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 10px;
            }
            
            .loading-state {
                text-align: center;
                color: #6b7280;
                padding: 20px;
                font-style: italic;
            }
            
            .jobs-monitor {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.15);
                padding: 15px;
                max-width: 300px;
                z-index: 1000;
            }
            
            .job-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .job-item:last-child {
                border-bottom: none;
            }
            
            .progress-bar {
                width: 100%;
                height: 4px;
                background: #f0f0f0;
                border-radius: 2px;
                overflow: hidden;
                margin-top: 5px;
            }
            
            .progress-fill {
                height: 100%;
                background: #3b82f6;
                transition: width 0.3s ease;
            }
            
            .notification-toast {
                position: fixed;
                top: 70px;
                right: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                padding: 15px 20px;
                z-index: 10000;
                border-left: 4px solid #22c55e;
                min-width: 300px;
            }
            
            .notification-toast.error {
                border-left-color: #ef4444;
            }
            
            .notification-toast.warning {
                border-left-color: #f59e0b;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            .notification-toast {
                animation: slideIn 0.3s ease;
            }
            
            /* RTL Support */
            [dir="rtl"] .quick-insights,
            [dir="rtl"] .services-grid {
                direction: rtl;
            }
            
            [dir="rtl"] .dashboard-controls {
                flex-direction: row-reverse;
            }
            
            /* Responsive Design */
            @media (max-width: 768px) {
                .ai-dashboard-container {
                    padding: 15px;
                }
                
                .dashboard-header {
                    flex-direction: column;
                    gap: 15px;
                    text-align: center;
                }
                
                .dashboard-controls {
                    flex-direction: column;
                    width: 100%;
                }
                
                .quick-insights {
                    grid-template-columns: 1fr;
                }
                
                .services-grid {
                    grid-template-columns: 1fr;
                }
                
                .message-content {
                    max-width: 85%;
                }
            }
            </style>
        `;
        $('head').append(style);
    }
    
    setupRealTime() {
        // Listen for AI job completion events
        frappe.realtime.on("ai_job_complete", (message) => {
            this.handleJobCompletion(message);
        });
        
        frappe.realtime.on("ai_job_error", (message) => {
            this.handleJobError(message);
        });
    }
    
    bindEvents() {
        const self = this;
        
        // Company selection
        $(document).on('change', '#company-select', function() {
            self.currentCompany = $(this).val();
            self.refreshDashboard();
        });
        
        // Dashboard refresh
        $(document).on('click', '#refresh-dashboard', function() {
            self.refreshDashboard();
        });
        
        // Service buttons
        $(document).on('click', '.service-btn', function() {
            const serviceCard = $(this).closest('.service-card');
            const serviceName = serviceCard.data('service');
            self.startAIService(serviceName, serviceCard);
        });
        
        // Chat functionality
        $(document).on('click', '#chat-send', function() {
            self.sendChatMessage();
        });
        
        $(document).on('keypress', '#chat-input', function(e) {
            if (e.which === 13) {
                self.sendChatMessage();
            }
        });
        
        // Quick questions
        $(document).on('click', '.question-chip', function() {
            const question = $(this).data('question');
            $('#chat-input').val(question);
            self.sendChatMessage();
        });
    }
    
    loadCompanies() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Company',
                fields: ['name', 'company_name']
            },
            callback: (r) => {
                if (r.message) {
                    let options = '<option value="">اختر الشركة...</option>';
                    r.message.forEach(company => {
                        options += `<option value="${company.name}">${company.company_name || company.name}</option>`;
                    });
                    $('#company-select').html(options);
                    
                    // Set default company if available
                    if (r.message.length === 1) {
                        $('#company-select').val(r.message[0].name);
                        this.currentCompany = r.message[0].name;
                        this.refreshDashboard();
                    }
                }
            }
        });
    }
    
    refreshDashboard() {
        if (!this.currentCompany) {
            this.showMessage('يرجى اختيار الشركة أولاً', 'warning');
            return;
        }
        
        this.updateHealthScore();
        this.updateRecommendations();
        this.updateRiskAlerts();
    }
    
    updateHealthScore() {
        $('#health-score .score-value').text('...');
        $('#health-description').text('جاري حساب درجة الصحة المالية...');
        
        frappe.call({
            method: 'material_ledger.material_ledger.api.get_financial_health_score',
            args: {
                company: this.currentCompany,
                year: new Date().getFullYear()
            },
            callback: (r) => {
                if (r.message) {
                    const score = r.message.score || 0;
                    const description = r.message.description || 'غير متاح';
                    
                    $('#health-score .score-value').text(score);
                    $('#health-description').text(description);
                    
                    // Update circle color based on score
                    const circle = $('#health-score .score-circle');
                    if (score >= 80) {
                        circle.css('background', 'conic-gradient(#22c55e 0deg, #16a34a 360deg)');
                    } else if (score >= 60) {
                        circle.css('background', 'conic-gradient(#f59e0b 0deg, #d97706 360deg)');
                    } else {
                        circle.css('background', 'conic-gradient(#ef4444 0deg, #dc2626 360deg)');
                    }
                }
            }
        });
    }
    
    updateRecommendations() {
        $('#ai-recommendations').html('<div class="loading-state">🧠 جاري تحليل البيانات وإنشاء التوصيات...</div>');
        
        frappe.call({
            method: 'material_ledger.material_ledger.api.get_ai_recommendations',
            args: {
                company: this.currentCompany
            },
            callback: (r) => {
                if (r.message && r.message.length > 0) {
                    let html = '<ul class="recommendations-list">';
                    r.message.slice(0, 3).forEach(rec => {
                        html += `<li class="recommendation-item">
                            <strong>${rec.type}</strong>: ${rec.description}
                        </li>`;
                    });
                    html += '</ul>';
                    $('#ai-recommendations').html(html);
                } else {
                    $('#ai-recommendations').html('<div class="loading-state">✅ لا توجد توصيات عاجلة</div>');
                }
            }
        });
    }
    
    updateRiskAlerts() {
        $('#risk-alerts').html('<div class="loading-state">🔍 فحص المخاطر المحتملة...</div>');
        
        frappe.call({
            method: 'material_ledger.material_ledger.api.get_risk_alerts',
            args: {
                company: this.currentCompany
            },
            callback: (r) => {
                if (r.message && r.message.length > 0) {
                    let html = '<ul class="risk-list">';
                    r.message.slice(0, 3).forEach(risk => {
                        const severityClass = risk.severity === 'high' ? 'text-danger' : 'text-warning';
                        html += `<li class="risk-item ${severityClass}">
                            <strong>${risk.type}</strong>: ${risk.description}
                        </li>`;
                    });
                    html += '</ul>';
                    $('#risk-alerts').html(html);
                } else {
                    $('#risk-alerts').html('<div class="loading-state">✅ لا توجد مخاطر مكتشفة</div>');
                }
            }
        });
    }
    
    startAIService(serviceName, serviceCard) {
        if (!this.currentCompany) {
            this.showMessage('يرجى اختيار الشركة أولاً', 'warning');
            return;
        }
        
        const serviceBtn = serviceCard.find('.service-btn');
        const statusDiv = serviceCard.find('.service-status');
        
        // Show loading state
        serviceBtn.prop('disabled', true).text('🔄 جاري البدء...');
        statusDiv.show().removeClass().addClass('service-status status-queued').text('⏳ في الطابور...');
        
        // API method mapping
        const serviceMethods = {
            'prediction': 'material_ledger.material_ledger.services.ai_prediction_service.start_financial_prediction',
            'anomaly': 'material_ledger.material_ledger.services.ai_anomaly_service.start_anomaly_detection',
            'investment': 'material_ledger.material_ledger.services.ai_investment_service.start_investment_analysis',
            'comprehensive': 'material_ledger.material_ledger.services.queue_service.queue_ai_analysis'
        };
        
        const method = serviceMethods[serviceName];
        const args = serviceName === 'comprehensive' ? 
            { job_type: 'comprehensive_analysis', company: this.currentCompany, filters: {} } :
            { company: this.currentCompany, filters: {} };
        
        frappe.call({
            method: method,
            args: args,
            callback: (r) => {
                if (r.message && r.message.job_id) {
                    const jobId = r.message.job_id;
                    
                    // Track this job
                    this.activeJobs[jobId] = {
                        service: serviceName,
                        card: serviceCard,
                        startTime: new Date()
                    };
                    
                    if (r.message.status === 'completed') {
                        // Job completed immediately (from cache)
                        this.handleJobCompletion({
                            job_id: jobId,
                            job_type: serviceName,
                            status: 'completed'
                        });
                        this.showResults(serviceName, r.message.data);
                    } else {
                        // Job queued for background processing
                        statusDiv.removeClass().addClass('service-status status-processing').text('⚙️ قيد المعالجة...');
                        this.showJobMonitor();
                        this.updateJobProgress(jobId);
                    }
                    
                    serviceBtn.prop('disabled', false).text('✅ تم البدء');
                } else {
                    serviceBtn.prop('disabled', false).text('❌ فشل');
                    statusDiv.removeClass().addClass('service-status status-failed').text('❌ فشل في البدء');
                    this.showMessage('فشل في بدء المهمة', 'error');
                }
            },
            error: () => {
                serviceBtn.prop('disabled', false).text('❌ خطأ');
                statusDiv.removeClass().addClass('service-status status-failed').text('❌ خطأ في الاتصال');
                this.showMessage('خطأ في الاتصال بالخدمة', 'error');
            }
        });
    }
    
    updateJobProgress(jobId) {
        if (!this.activeJobs[jobId]) return;
        
        frappe.call({
            method: 'material_ledger.material_ledger.services.queue_service.get_ai_job_status',
            args: { job_id: jobId },
            callback: (r) => {
                if (r.message) {
                    const job = this.activeJobs[jobId];
                    const status = r.message.status;
                    const progress = r.message.progress || 0;
                    
                    if (status === 'completed') {
                        this.handleJobCompletion({
                            job_id: jobId,
                            job_type: job.service,
                            status: 'completed'
                        });
                        if (r.message.result) {
                            this.showResults(job.service, r.message.result);
                        }
                    } else if (status === 'failed') {
                        this.handleJobError({
                            job_id: jobId,
                            job_type: job.service,
                            status: 'failed',
                            error: r.message.error
                        });
                    } else if (status === 'processing') {
                        // Update progress in UI
                        this.updateJobProgressUI(jobId, progress);
                        
                        // Continue polling
                        setTimeout(() => {
                            this.updateJobProgress(jobId);
                        }, 2000);
                    }
                }
            }
        });
    }
    
    updateJobProgressUI(jobId, progress) {
        const job = this.activeJobs[jobId];
        if (!job) return;
        
        const statusDiv = job.card.find('.service-status');
        statusDiv.removeClass().addClass('service-status status-processing')
               .html(`⚙️ معالجة... ${progress}%<div class="progress-bar"><div class="progress-fill" style="width: ${progress}%"></div></div>`);
        
        // Update jobs monitor
        const jobItem = $(`#job-${jobId}`);
        if (jobItem.length) {
            jobItem.find('.progress-fill').css('width', `${progress}%`);
        }
    }
    
    handleJobCompletion(message) {
        const jobId = message.job_id;
        const job = this.activeJobs[jobId];
        
        if (job) {
            const statusDiv = job.card.find('.service-status');
            const serviceBtn = job.card.find('.service-btn');
            
            statusDiv.removeClass().addClass('service-status status-completed').text('✅ تم بنجاح');
            serviceBtn.text('عرض النتائج').prop('disabled', false);
            
            // Remove from active jobs
            delete this.activeJobs[jobId];
            
            this.showMessage(`تم إكمال ${this.getServiceNameAr(message.job_type)} بنجاح!`, 'success');
            this.updateJobsMonitor();
        }
    }
    
    handleJobError(message) {
        const jobId = message.job_id;
        const job = this.activeJobs[jobId];
        
        if (job) {
            const statusDiv = job.card.find('.service-status');
            const serviceBtn = job.card.find('.service-btn');
            
            statusDiv.removeClass().addClass('service-status status-failed').text('❌ فشل');
            serviceBtn.text('إعادة المحاولة').prop('disabled', false);
            
            // Remove from active jobs
            delete this.activeJobs[jobId];
            
            this.showMessage(`فشل في ${this.getServiceNameAr(message.job_type)}: ${message.error || 'خطأ غير معروف'}`, 'error');
            this.updateJobsMonitor();
        }
    }
    
    getServiceNameAr(serviceType) {
        const names = {
            'financial_prediction': 'التنبؤ المالي',
            'anomaly_detection': 'كشف الشذوذ',
            'investment_analysis': 'تحليل الاستثمار',
            'comprehensive_analysis': 'التحليل الشامل'
        };
        return names[serviceType] || serviceType;
    }
    
    showJobMonitor() {
        $('#jobs-monitor').show();
        this.updateJobsMonitor();
    }
    
    updateJobsMonitor() {
        const jobsList = $('#jobs-list');
        const activeJobCount = Object.keys(this.activeJobs).length;
        
        if (activeJobCount === 0) {
            $('#jobs-monitor').hide();
            return;
        }
        
        let html = '';
        Object.entries(this.activeJobs).forEach(([jobId, job]) => {
            const elapsed = Math.floor((new Date() - job.startTime) / 1000);
            html += `
                <div class="job-item" id="job-${jobId}">
                    <div>
                        <strong>${this.getServiceNameAr(job.service)}</strong>
                        <small style="display: block; color: #666;">${elapsed}s مضى</small>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                </div>
            `;
        });
        
        jobsList.html(html);
    }
    
    sendChatMessage() {
        const input = $('#chat-input');
        const message = input.val().trim();
        
        if (!message) return;
        
        if (!this.currentCompany) {
            this.showMessage('يرجى اختيار الشركة أولاً للحصول على تحليل دقيق', 'warning');
            return;
        }
        
        // Add user message to chat
        this.addChatMessage(message, 'user');
        input.val('');
        
        // Add loading message
        const loadingId = this.addChatMessage('🤔 جاري التحليل والبحث عن الإجابة...', 'assistant', true);
        
        // Send to AI assistant
        frappe.call({
            method: 'material_ledger.material_ledger.api.chat_with_ai_assistant',
            args: {
                message: message,
                company: this.currentCompany,
                chat_history: this.chatHistory
            },
            callback: (r) => {
                // Remove loading message
                $(`#${loadingId}`).remove();
                
                if (r.message && r.message.response) {
                    this.addChatMessage(r.message.response, 'assistant');
                    
                    // Update chat history
                    this.chatHistory.push({
                        user: message,
                        assistant: r.message.response,
                        timestamp: new Date().toISOString()
                    });
                    
                    // Keep only last 10 exchanges
                    if (this.chatHistory.length > 10) {
                        this.chatHistory = this.chatHistory.slice(-10);
                    }
                } else {
                    this.addChatMessage('عذراً، لم أتمكن من معالجة طلبك حالياً. يرجى المحاولة مرة أخرى.', 'assistant');
                }
            },
            error: () => {
                $(`#${loadingId}`).remove();
                this.addChatMessage('عذراً، حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى.', 'assistant');
            }
        });
    }
    
    addChatMessage(message, sender, isLoading = false) {
        const messagesContainer = $('#chat-messages');
        const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        const avatar = sender === 'user' ? '👤' : '🤖';
        const messageClass = sender === 'user' ? 'user-message' : 'assistant-message';
        
        const messageHtml = `
            <div class="message ${messageClass}" id="${messageId}">
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    <p>${message}</p>
                </div>
            </div>
        `;
        
        messagesContainer.append(messageHtml);
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
        
        return messageId;
    }
    
    showResults(serviceName, data) {
        const resultsSection = $('.results-section');
        const resultsContainer = $('#results-container');
        
        resultsSection.show();
        
        let html = `<h3>نتائج ${this.getServiceNameAr(serviceName)}</h3>`;
        
        if (typeof data === 'string') {
            try {
                data = JSON.parse(data);
            } catch (e) {
                html += `<div class="alert alert-info"><pre>${data}</pre></div>`;
                resultsContainer.html(html);
                return;
            }
        }
        
        // Format results based on service type
        if (serviceName === 'prediction' && data.predictions) {
            html += this.formatPredictionResults(data);
        } else if (serviceName === 'anomaly' && data.anomalies) {
            html += this.formatAnomalyResults(data);
        } else if (serviceName === 'investment') {
            html += this.formatInvestmentResults(data);
        } else if (serviceName === 'comprehensive' || data.financial_data || data.summary) {
            html += this.formatComprehensiveResults(data);
        } else {
            html += `<div class="alert alert-info"><pre>${JSON.stringify(data, null, 2)}</pre></div>`;
        }
        
        resultsContainer.html(html);
        $('html, body').animate({ scrollTop: resultsSection.offset().top }, 1000);
    }
    
    formatPredictionResults(data) {
        let html = '<div class="prediction-results">';
        
        if (data.summary) {
            html += `<div class="alert alert-success">
                <h4>📊 ملخص التوقعات</h4>
                <p>متوسط الربح الشهري المتوقع: ${data.summary.avg_monthly_profit?.toLocaleString() || 'غير متاح'}</p>
                <p>الاتجاه العام: ${data.summary.growth_trend || 'غير محدد'}</p>
            </div>`;
        }
        
        if (data.predictions && data.predictions.length > 0) {
            html += '<h4>📈 التوقعات التفصيلية</h4>';
            html += '<div class="table-responsive"><table class="table table-striped">';
            html += '<thead><tr><th>الشهر</th><th>الإيرادات المتوقعة</th><th>المصروفات المتوقعة</th><th>الربح المتوقع</th></tr></thead><tbody>';
            
            data.predictions.slice(0, 12).forEach(pred => {
                const revenue = (pred.revenue || 0).toLocaleString();
                const expenses = (pred.expenses || 0).toLocaleString();
                const profit = (pred.profit || 0).toLocaleString();
                
                html += `<tr>
                    <td>${pred.date}</td>
                    <td class="text-success">${revenue}</td>
                    <td class="text-danger">${expenses}</td>
                    <td class="${pred.profit >= 0 ? 'text-success' : 'text-danger'}">${profit}</td>
                </tr>`;
            });
            
            html += '</tbody></table></div>';
        }
        
        html += '</div>';
        return html;
    }
    
    formatAnomalyResults(data) {
        let html = '<div class="anomaly-results">';
        
        html += `<div class="alert alert-${data.overall_risk === 'عالي' ? 'danger' : data.overall_risk === 'متوسط' ? 'warning' : 'info'}">
            <h4>🔍 تقييم المخاطر العام: ${data.overall_risk}</h4>
            <p>إجمالي الحالات المكتشفة: ${data.total_anomalies || 0}</p>
        </div>`;
        
        if (data.prioritized_anomalies && data.prioritized_anomalies.length > 0) {
            html += '<h4>⚠️ أهم الشذوذات المكتشفة</h4>';
            
            data.prioritized_anomalies.slice(0, 10).forEach(anomaly => {
                const severityClass = anomaly.severity === 'high' ? 'danger' : anomaly.severity === 'medium' ? 'warning' : 'info';
                html += `<div class="alert alert-${severityClass}">
                    <strong>${anomaly.type}</strong>: ${anomaly.description}
                </div>`;
            });
        }
        
        if (data.recommendations && data.recommendations.length > 0) {
            html += '<h4>💡 التوصيات</h4><ul>';
            data.recommendations.forEach(rec => {
                html += `<li>${rec}</li>`;
            });
            html += '</ul>';
        }
        
        html += '</div>';
        return html;
    }
    
    formatInvestmentResults(data) {
        let html = '<div class="investment-results">';
        
        if (data.roi_analysis && data.roi_analysis.summary) {
            const summary = data.roi_analysis.summary;
            html += `<div class="alert alert-info">
                <h4>📊 ملخص العوائد</h4>
                <p>متوسط العائد على الاستثمار: ${summary.average_roi?.toFixed(2) || 0}%</p>
                <p>إجمالي الاستثمارات: ${summary.total_investments || 0}</p>
            </div>`;
        }
        
        if (data.scenario_analysis) {
            html += '<h4>🎯 تحليل السيناريوهات</h4>';
            
            Object.entries(data.scenario_analysis).forEach(([scenario, details]) => {
                if (details.description) {
                    html += `<div class="alert alert-secondary">
                        <h5>${details.description}</h5>
                        <p>الربح المتوقع: ${details.projected_profit?.toLocaleString() || 'غير محدد'}</p>
                        <p>تحسن الربحية: ${details.profit_improvement?.toFixed(2) || 0}%</p>
                    </div>`;
                }
            });
        }
        
        html += '</div>';
        return html;
    }
    
    formatComprehensiveResults(data) {
        const fd = data.financial_data || data;
        const summary = fd.summary || data.summary || {};
        const ratios = fd.ratios || data.ratios || {};
        const trend = fd.trend || data.trend || {};
        const period = fd.period || data.period || '';
        
        const fmt = (v) => {
            if (v === undefined || v === null) return '--';
            const n = parseFloat(v);
            if (isNaN(n)) return v;
            return n.toLocaleString('ar-SA', {maximumFractionDigits: 2});
        };
        const pct = (v) => {
            if (v === undefined || v === null) return '--';
            return parseFloat(v).toFixed(2) + '%';
        };

        let html = '<div class="comprehensive-results">';

        // Period header
        html += `<div class="alert alert-primary" style="background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; border: none; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h4 style="margin:0 0 5px;font-size:20px;">📋 التحليل المالي الشامل</h4>
            <p style="margin:0;opacity:.85;">الفترة: ${period} | النوع: ${fd.period_type === 'annual' ? 'سنوي' : fd.period_type || '--'}</p>
        </div>`;

        // Summary cards
        const profit = parseFloat(summary.profit || 0);
        const healthScore = parseFloat(summary.health_score || 0);
        html += `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:25px;">
            <div class="comp-card" style="background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);border-right:4px solid #28a745;">
                <div style="font-size:13px;color:#888;margin-bottom:5px;">الإيرادات</div>
                <div style="font-size:22px;font-weight:700;color:#28a745;">${fmt(summary.income)}</div>
            </div>
            <div class="comp-card" style="background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);border-right:4px solid #dc3545;">
                <div style="font-size:13px;color:#888;margin-bottom:5px;">المصروفات</div>
                <div style="font-size:22px;font-weight:700;color:#dc3545;">${fmt(summary.expense)}</div>
            </div>
            <div class="comp-card" style="background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);border-right:4px solid ${profit >= 0 ? '#28a745' : '#dc3545'};">
                <div style="font-size:13px;color:#888;margin-bottom:5px;">صافي الربح</div>
                <div style="font-size:22px;font-weight:700;color:${profit >= 0 ? '#28a745' : '#dc3545'};">${fmt(summary.profit)}</div>
            </div>
            <div class="comp-card" style="background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);border-right:4px solid #667eea;">
                <div style="font-size:13px;color:#888;margin-bottom:5px;">درجة الصحة المالية</div>
                <div style="font-size:22px;font-weight:700;color:#667eea;">${fmt(healthScore)} <span style="font-size:14px;color:#aaa;">/ 100</span></div>
            </div>
        </div>`;

        // Balance sheet bar
        html += `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:25px;">
            <div style="background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);border-right:4px solid #17a2b8;">
                <div style="font-size:13px;color:#888;margin-bottom:5px;">إجمالي الأصول</div>
                <div style="font-size:20px;font-weight:700;color:#17a2b8;">${fmt(summary.assets)}</div>
            </div>
            <div style="background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);border-right:4px solid #ffc107;">
                <div style="font-size:13px;color:#888;margin-bottom:5px;">إجمالي الالتزامات</div>
                <div style="font-size:20px;font-weight:700;color:#e0a800;">${fmt(summary.liabilities)}</div>
            </div>
            <div style="background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);border-right:4px solid #6f42c1;">
                <div style="font-size:13px;color:#888;margin-bottom:5px;">حقوق الملكية</div>
                <div style="font-size:20px;font-weight:700;color:#6f42c1;">${fmt(summary.equity)}</div>
            </div>
        </div>`;

        // Ratios table
        if (Object.keys(ratios).length > 0) {
            const ratioLabels = {
                current_ratio: {name: 'نسبة السيولة الجارية', icon: '💧', good: v => v >= 1.5},
                quick_ratio: {name: 'نسبة السيولة السريعة', icon: '⚡', good: v => v >= 1},
                debt_ratio: {name: 'نسبة الديون %', icon: '🏦', good: v => v < 60},
                roe: {name: 'العائد على حقوق الملكية %', icon: '📈', good: v => v > 10},
                roa: {name: 'العائد على الأصول %', icon: '🏢', good: v => v > 5},
                net_margin: {name: 'هامش صافي الربح %', icon: '💰', good: v => v > 5},
                operating_margin: {name: 'هامش الربح التشغيلي %', icon: '⚙️', good: v => v > 10},
                asset_turnover: {name: 'معدل دوران الأصول', icon: '🔄', good: v => v >= 1},
                leverage: {name: 'الرافعة المالية', icon: '📊', good: v => v < 3},
                z_score: {name: 'مؤشر ألتمان Z-Score', icon: '🎯', good: v => v > 2.99},
                income_growth: {name: 'نمو الإيرادات %', icon: '📈', good: v => v > 0},
                profit_growth: {name: 'نمو الأرباح %', icon: '💹', good: v => v > 0},
                working_capital: {name: 'رأس المال العامل', icon: '🏗️', good: v => v > 0},
                dupont_roe: {name: 'تحليل دوبونت ROE', icon: '🔬', good: v => v > 10}
            };

            html += `<div style="background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 12px rgba(0,0,0,.08);margin-bottom:25px;">
                <h4 style="margin:0 0 15px;font-size:18px;color:#333;">📊 النسب المالية</h4>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;">`;

            for (const [key, val] of Object.entries(ratios)) {
                const info = ratioLabels[key] || {name: key, icon: '📌', good: () => true};
                const numVal = parseFloat(val);
                const isGood = !isNaN(numVal) && info.good(numVal);
                const color = isNaN(numVal) ? '#888' : isGood ? '#28a745' : '#dc3545';
                const bg = isNaN(numVal) ? '#f8f9fa' : isGood ? '#f0fff4' : '#fff5f5';

                html += `<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-radius:8px;background:${bg};">
                    <span style="font-size:14px;color:#555;">${info.icon} ${info.name}</span>
                    <span style="font-size:16px;font-weight:700;color:${color};">${fmt(val)}</span>
                </div>`;
            }
            html += '</div></div>';
        }

        // Trend comparison
        if (trend.current_year || trend.prev_year) {
            const cur = trend.current_year || {};
            const prev = trend.prev_year || {};

            html += `<div style="background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 12px rgba(0,0,0,.08);margin-bottom:25px;">
                <h4 style="margin:0 0 15px;font-size:18px;color:#333;">📈 مقارنة الأداء (السنة الحالية مقابل السابقة)</h4>
                <div class="table-responsive">
                <table class="table" style="margin:0;">
                    <thead><tr style="background:#f8f9fa;">
                        <th style="text-align:right;padding:12px;">البند</th>
                        <th style="text-align:center;padding:12px;">السنة الحالية</th>
                        <th style="text-align:center;padding:12px;">السنة السابقة</th>
                        <th style="text-align:center;padding:12px;">التغيّر</th>
                    </tr></thead><tbody>`;

            const items = [
                {label: 'الإيرادات', key: 'income'},
                {label: 'الربح', key: 'profit'},
                {label: 'الأصول', key: 'assets'}
            ];

            items.forEach(item => {
                const c = parseFloat(cur[item.key] || 0);
                const p = parseFloat(prev[item.key] || 0);
                const change = p !== 0 ? ((c - p) / Math.abs(p) * 100) : (c !== 0 ? 100 : 0);
                const changeColor = change >= 0 ? '#28a745' : '#dc3545';
                const arrow = change >= 0 ? '▲' : '▼';

                html += `<tr>
                    <td style="text-align:right;padding:12px;font-weight:600;">${item.label}</td>
                    <td style="text-align:center;padding:12px;">${fmt(c)}</td>
                    <td style="text-align:center;padding:12px;">${fmt(p)}</td>
                    <td style="text-align:center;padding:12px;color:${changeColor};font-weight:700;">${arrow} ${change.toFixed(1)}%</td>
                </tr>`;
            });

            html += '</tbody></table></div></div>';
        }

        html += '</div>';
        return html;
    }

    showMessage(message, type = 'info') {
        const toast = $(`
            <div class="notification-toast ${type}">
                <strong>${type === 'error' ? '❌' : type === 'warning' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️'}</strong>
                ${message}
            </div>
        `);
        
        $('body').append(toast);
        
        setTimeout(() => {
            toast.fadeOut(300, () => toast.remove());
        }, 5000);
    }
    
    showWelcomeMessage() {
        setTimeout(() => {
            this.showMessage('مرحباً بك في لوحة التحكم الذكية! اختر شركة لبدء التحليل المالي الذكي.', 'info');
        }, 1000);
    }
    
    startJobMonitoring() {
        // Poll for job updates every 5 seconds
        setInterval(() => {
            if (Object.keys(this.activeJobs).length > 0) {
                this.updateJobsMonitor();
            }
        }, 5000);
    }
    
    checkNotifications() {
        // Check for recent notifications
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Notification Log',
                filters: {
                    for_user: frappe.session.user,
                    read: 0,
                    subject: ['like', '%AI%']
                },
                fields: ['subject', 'email_content', 'creation'],
                limit: 5,
                order_by: 'creation desc'
            },
            callback: (r) => {
                if (r.message && r.message.length > 0) {
                    r.message.forEach(notif => {
                        this.showMessage(notif.subject, 'info');
                    });
                }
            }
        });
    }
}