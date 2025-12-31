/**
 * Financial Analysis - Export Functions Module
 * Handles PDF and Excel exports
 */

const FinancialExports = {
    
    // Export to PDF
    exportToPDF: function(state, isRtl) {
        if (!state.data) {
            frappe.msgprint(isRtl ? 'لا توجد بيانات للتصدير' : 'No data to export');
            return;
        }
        
        frappe.call({
            method: 'material_ledger.material_ledger.api.export_analysis_to_pdf',
            args: {
                company: state.filters.company,
                year: state.filters.year,
                period: state.filters.period,
                period_number: state.filters.period_number,
                data: JSON.stringify(state.data)
            },
            callback: (r) => {
                if (r.message && r.message.pdf) {
                    const blob = new Blob([
                        new Uint8Array(r.message.pdf.match(/.{1,2}/g).map(byte => parseInt(byte, 16)))
                    ], { type: 'application/pdf' });
                    
                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = `Financial_Analysis_${state.filters.company}_${state.filters.year}.pdf`;
                    link.click();
                    
                    frappe.show_alert({
                        message: isRtl ? 'تم تصدير التقرير بنجاح' : 'Report exported successfully',
                        indicator: 'green'
                    });
                }
            },
            error: () => {
                frappe.msgprint(isRtl ? 'فشل تصدير التقرير' : 'Failed to export report');
            }
        });
    },
    
    // Export to Excel
    exportToExcel: function(state, isRtl) {
        if (!state.data) {
            frappe.msgprint(isRtl ? 'لا توجد بيانات للتصدير' : 'No data to export');
            return;
        }
        
        // Create workbook data
        const summary = state.data.summary || {};
        const ratios = state.data.ratios || {};
        
        let csvContent = "data:text/csv;charset=utf-8,";
        
        // Summary section
        csvContent += (isRtl ? "ملخص التحليل المالي\n" : "Financial Analysis Summary\n");
        csvContent += `${isRtl ? 'الشركة' : 'Company'},${state.filters.company}\n`;
        csvContent += `${isRtl ? 'السنة' : 'Year'},${state.filters.year}\n`;
        csvContent += `${isRtl ? 'الفترة' : 'Period'},${state.filters.period}\n\n`;
        
        // Financial Summary
        csvContent += (isRtl ? "الملخص المالي\n" : "Financial Summary\n");
        csvContent += `${isRtl ? 'الإيرادات' : 'Revenue'},${summary.income || 0}\n`;
        csvContent += `${isRtl ? 'المصروفات' : 'Expenses'},${summary.expense || 0}\n`;
        csvContent += `${isRtl ? 'صافي الربح' : 'Net Profit'},${summary.profit || 0}\n`;
        csvContent += `${isRtl ? 'الأصول' : 'Assets'},${summary.assets || 0}\n`;
        csvContent += `${isRtl ? 'الالتزامات' : 'Liabilities'},${summary.liabilities || 0}\n`;
        csvContent += `${isRtl ? 'حقوق الملكية' : 'Equity'},${summary.equity || 0}\n\n`;
        
        // Ratios
        csvContent += (isRtl ? "النسب المالية\n" : "Financial Ratios\n");
        csvContent += `${isRtl ? 'العائد على حقوق الملكية' : 'ROE'},${ratios.roe || 0}%\n`;
        csvContent += `${isRtl ? 'العائد على الأصول' : 'ROA'},${ratios.roa || 0}%\n`;
        csvContent += `${isRtl ? 'هامش الربح الصافي' : 'Net Margin'},${ratios.net_margin || 0}%\n`;
        csvContent += `${isRtl ? 'نسبة التداول' : 'Current Ratio'},${ratios.current_ratio || 0}\n`;
        csvContent += `${isRtl ? 'نسبة الديون' : 'Debt Ratio'},${ratios.debt_ratio || 0}%\n`;
        csvContent += `Z-Score,${ratios.z_score || 0}\n`;
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', `Financial_Analysis_${state.filters.company}_${state.filters.year}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        frappe.show_alert({
            message: isRtl ? 'تم تصدير البيانات بنجاح' : 'Data exported successfully',
            indicator: 'green'
        });
    },
    
    // Print report
    printReport: function(state, isRtl) {
        if (!state.data) {
            frappe.msgprint(isRtl ? 'لا توجد بيانات للطباعة' : 'No data to print');
            return;
        }
        
        window.print();
    },
    
    // Schedule report
    scheduleReport: function(state, isRtl) {
        const dialog = new frappe.ui.Dialog({
            title: isRtl ? 'جدولة التقرير' : 'Schedule Report',
            fields: [
                {
                    fieldname: 'report_type',
                    fieldtype: 'Select',
                    label: isRtl ? 'نوع التقرير' : 'Report Type',
                    options: 'Full Analysis\nSummary Only\nIncome Statement\nBalance Sheet',
                    reqd: 1
                },
                {
                    fieldname: 'frequency',
                    fieldtype: 'Select',
                    label: isRtl ? 'التكرار' : 'Frequency',
                    options: 'Daily\nWeekly\nMonthly\nQuarterly',
                    reqd: 1
                },
                {
                    fieldname: 'email_to',
                    fieldtype: 'Data',
                    label: isRtl ? 'إرسال إلى' : 'Send To',
                    reqd: 1,
                    default: frappe.session.user
                }
            ],
            primary_action_label: isRtl ? 'جدولة' : 'Schedule',
            primary_action: function(values) {
                frappe.call({
                    method: 'material_ledger.material_ledger.api.schedule_financial_report',
                    args: {
                        company: state.filters.company,
                        report_type: values.report_type.toLowerCase().replace(' ', '_'),
                        frequency: values.frequency.toLowerCase(),
                        email_to: values.email_to
                    },
                    callback: (r) => {
                        if (r.message && r.message.status) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'green'
                            });
                            dialog.hide();
                        }
                    }
                });
            }
        });
        
        dialog.show();
    }
};

// Export
if (typeof window !== 'undefined') {
    window.FinancialExports = FinancialExports;
}
