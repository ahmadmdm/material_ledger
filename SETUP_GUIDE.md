# 🚀 Material Ledger - Quick Setup & Activation Guide

## النسخة الاحترافية 2.0 - Frappe UI Professional Edition

---

## ⚡ التفعيل السريع

### الخطوة 1: بناء الملفات

```bash
cd ~/frappe-bench
bench build --app material_ledger
bench restart
```

### الخطوة 2: مسح ذاكرة التخزين المؤقت

```bash
bench --site your-site-name clear-cache
bench --site your-site-name clear-website-cache
```

### الخطوة 3: الوصول إلى الصفحات

افتح المتصفح وانتقل إلى:

**📊 دفتر الأستاذ العام:**
```
https://your-site.com/app/material-ledger-report
```

**💼 التحليل المالي:**
```
https://your-site.com/app/financial-analysis
```

---

## 🔄 تفعيل النسخة الجديدة (Frappe UI)

إذا كنت تريد استخدام النسخة الجديدة المحسّنة:

### خيار A: التفعيل الكامل (موصى به)

```bash
cd ~/frappe-bench/apps/material_ledger/material_ledger/material_ledger/page

# Material Ledger Report
cd material_ledger_report
mv material_ledger_report.js material_ledger_report_vuetify_backup.js
mv material_ledger_report_new.js material_ledger_report.js

# Financial Analysis
cd ../financial_analysis
mv financial_analysis.js financial_analysis_vuetify_backup.js
mv financial_analysis_new.js financial_analysis.js

# بناء وإعادة التشغيل
cd ~/frappe-bench
bench build --app material_ledger
bench restart
```

### خيار B: اختبار النسخة الجديدة أولاً

النسخة الجديدة موجودة في ملفات منفصلة:
- `material_ledger_report_new.js`
- `financial_analysis_new.js`

يمكنك مراجعتها قبل التفعيل الكامل.

---

## 🎨 المميزات الجديدة

### ✅ دفتر الأستاذ العام (Material Ledger)

- واجهة احترافية متوافقة مع Frappe
- فلاتر متقدمة (شركة، تاريخ، حساب، مركز تكلفة، مشروع، طرف)
- تجميع حسب الحساب
- تصدير إلى Excel
- طباعة احترافية بجودة A4
- دعم RTL كامل للعربية
- سريع الاستجابة على الهواتف

### ✅ التحليل المالي (Financial Analysis)

- لوحة تحكم على مستوى CFO
- 4 قوائم مالية كاملة:
  - قائمة الدخل
  - قائمة المركز المالي
  - قائمة التدفقات النقدية
  - قائمة التغير في حقوق الملكية
- مؤشرات أداء رئيسية (KPIs)
- تحليل ربع سنوي
- مقارنة سنوية
- تقرير AI استراتيجي
- نسب مالية متقدمة
- Altman Z-Score

---

## 🔧 الإعدادات الإضافية (اختيارية)

### تفعيل تقرير AI (DeepSeek)

إذا كنت تريد تفعيل التحليل الذكي للتقارير:

```bash
bench --site your-site set-config deepseek_api_key "your-api-key"
```

أو أضف في `site_config.json`:

```json
{
  "deepseek_api_key": "sk-your-api-key-here"
}
```

---

## 📱 الوصول السريع

### إضافة إلى القائمة الرئيسية

1. انتقل إلى **Workspace**
2. اختر **Accounting Workspace**
3. أضف روابط مخصصة:
   - Material Ledger Report
   - Financial Analysis

### إنشاء اختصارات

```python
# في Frappe console
bench console

# إضافة إلى المفضلة
frappe.db.set_value("User", "user@example.com", "favorites", [
    {"type": "Page", "name": "material-ledger-report"},
    {"type": "Page", "name": "financial-analysis"}
])
```

---

## 🎯 اختبار التثبيت

### 1. اختبار دفتر الأستاذ

```python
bench console

from material_ledger.material_ledger.api import get_ledger_entries

result = get_ledger_entries(
    company="Your Company",
    from_date="2024-01-01",
    to_date="2024-12-31"
)

print(f"Found {len(result)} entries")
```

### 2. اختبار التحليل المالي

```python
from material_ledger.material_ledger.api import get_financial_analysis

analysis = get_financial_analysis(
    company="Your Company",
    year=2024
)

print(f"Net Profit: {analysis['summary']['profit']}")
print(f"ROE: {analysis['ratios']['roe']}%")
```

---

## 🐛 حل المشاكل الشائعة

### المشكلة: الصفحة لا تظهر

**الحل:**
```bash
bench --site your-site clear-cache
bench build --app material_ledger
bench restart
```

### المشكلة: خطأ في الصلاحيات

**الحل:**
تحقق من الأدوار في:
- `material_ledger_report.json`
- `financial_analysis.json`

أضف الدور المناسب للمستخدم.

### المشكلة: البيانات لا تظهر

**الحل:**
1. تأكد من وجود بيانات في `GL Entry`
2. تحقق من الشركة المختارة
3. تحقق من نطاق التاريخ

### المشكلة: أخطاء JavaScript

**الحل:**
1. افتح Developer Console (F12)
2. تحقق من الأخطاء
3. تأكد من تحميل جميع الملفات

---

## 📊 نصائح للأداء الأفضل

### 1. قاعدة البيانات

```sql
-- إضافة indexes للاستعلامات السريعة
ALTER TABLE `tabGL Entry` 
ADD INDEX idx_company_date (company, posting_date);

ALTER TABLE `tabGL Entry`
ADD INDEX idx_account (account);
```

### 2. Cache Configuration

في `site_config.json`:

```json
{
  "limits": {
    "max_page_length": 1000
  }
}
```

### 3. بناء Production

```bash
# للإنتاج
bench build --app material_ledger --production
```

---

## 📚 الموارد التعليمية

### الوثائق

- **README.md**: دليل المستخدم الكامل
- **DEVELOPMENT_GUIDE_NEW.md**: دليل المطورين
- **CHANGELOG.md**: سجل التغييرات

### الدعم الفني

- **Email**: trae@example.com
- **GitHub Issues**: [رابط المشروع]
- **Frappe Forum**: [رابط المنتدى]

---

## ✅ قائمة التحقق النهائية

- [ ] تثبيت التطبيق بنجاح
- [ ] بناء الملفات (build)
- [ ] مسح Cache
- [ ] إعادة تشغيل Bench
- [ ] الوصول إلى Material Ledger Report
- [ ] الوصول إلى Financial Analysis
- [ ] اختبار الفلاتر
- [ ] اختبار الطباعة
- [ ] اختبار التصدير (Excel)
- [ ] التحقق من البيانات

---

## 🎉 التهاني!

أنت الآن جاهز لاستخدام Material Ledger Professional Edition!

### الخطوات التالية:

1. **استكشف الميزات**: جرب جميع الفلاتر والخيارات
2. **خصص التقارير**: اضبط التواريخ والحسابات
3. **شارك مع الفريق**: دع فريقك يستفيد من التقارير
4. **قدم ملاحظاتك**: ساعدنا في التحسين

---

## 🚀 الميزات القادمة

- [ ] تصدير PDF
- [ ] تقارير مجدولة تلقائياً
- [ ] لوحة تحكم رئيسية
- [ ] تطبيق الهاتف
- [ ] تحليلات متقدمة

---

<div align="center">
  <h2>✨ شكراً لاستخدام Material Ledger! ✨</h2>
  <p><strong>النسخة 2.0.0 - Professional Edition</strong></p>
  <p>صُنع بحب ❤️ لمجتمع Frappe</p>
</div>

---

## 📞 تواصل معنا

لأي استفسارات أو مساعدة:
- **البريد الإلكتروني**: trae@example.com
- **الدعم الفني**: متاح عبر GitHub Issues

**وقت الاستجابة**: خلال 24-48 ساعة

---

<div align="center">
  <p><em>Happy Analyzing! 📊</em></p>
</div>
