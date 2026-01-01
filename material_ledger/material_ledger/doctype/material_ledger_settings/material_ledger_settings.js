// Copyright (c) 2025, Ahmad
// For license information, please see license.txt

frappe.ui.form.on("Material Ledger Settings", {
    refresh(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Test AI Connection'), function() {
            frm.trigger('test_ai_connection');
        }, __('Actions'));
        
        frm.add_custom_button(__('Clear Cache'), function() {
            frappe.call({
                method: 'frappe.client.delete_keys',
                args: {
                    key: 'material_ledger*'
                },
                callback: function() {
                    frappe.show_alert({
                        message: __('Cache cleared successfully'),
                        indicator: 'green'
                    });
                }
            });
        }, __('Actions'));
        
        // Add help section
        frm.set_intro(__('Configure Material Ledger settings including AI analysis, security, and display options.'));
        
        // Style the form
        add_custom_styles();
    },
    
    test_ai_connection(frm) {
        frappe.call({
            method: 'material_ledger.material_ledger.doctype.material_ledger_settings.material_ledger_settings.test_ai_connection',
            freeze: true,
            freeze_message: __('Testing connection...'),
            callback: function(r) {
                if (r.message) {
                    if (r.message.success) {
                        frappe.msgprint({
                            title: __('Success'),
                            indicator: 'green',
                            message: r.message.message
                        });
                    } else {
                        frappe.msgprint({
                            title: __('Connection Failed'),
                            indicator: 'red',
                            message: r.message.message
                        });
                    }
                }
            }
        });
    },
    
    ai_provider(frm) {
        // Update default model based on provider
        if (frm.doc.ai_provider === 'DeepSeek') {
            frm.set_value('ai_model', 'deepseek-reasoner');
        } else if (frm.doc.ai_provider === 'OpenAI') {
            frm.set_value('ai_model', 'gpt-4');
        } else {
            frm.set_value('ai_model', 'local');
        }
    }
});

function add_custom_styles() {
    const styles = `
        <style>
            [data-doctype="Material Ledger Settings"] .form-section .section-head {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 15px;
                border-radius: 8px;
                margin-bottom: 15px;
            }
            
            [data-doctype="Material Ledger Settings"] .frappe-control[data-fieldtype="Check"] {
                background: #f8fafc;
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 10px;
            }
            
            [data-doctype="Material Ledger Settings"] .btn-primary-dark {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
        </style>
    `;
    $('head').append(styles);
}
