# Copyright (c) 2025, Ahmad
# For license information, please see license.txt

"""
Unit Tests for Material Ledger API
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch, MagicMock
import json


class TestMaterialLedgerAPI(FrappeTestCase):
    """Test cases for Material Ledger API endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        super().setUpClass()
        
        # Create test company if not exists
        if not frappe.db.exists("Company", "_Test Company"):
            company = frappe.get_doc({
                "doctype": "Company",
                "company_name": "_Test Company",
                "abbr": "_TC",
                "default_currency": "SAR",
                "country": "Saudi Arabia"
            })
            company.insert(ignore_permissions=True)
    
    def test_get_ledger_entries_requires_company(self):
        """Test that get_ledger_entries requires company parameter"""
        from material_ledger.material_ledger.api import get_ledger_entries
        
        with self.assertRaises(frappe.exceptions.ValidationError):
            get_ledger_entries(
                company="",
                from_date="2025-01-01",
                to_date="2025-12-31"
            )
    
    def test_get_ledger_entries_requires_date_range(self):
        """Test that get_ledger_entries requires date range"""
        from material_ledger.material_ledger.api import get_ledger_entries
        
        with self.assertRaises(frappe.exceptions.ValidationError):
            get_ledger_entries(
                company="_Test Company",
                from_date="",
                to_date=""
            )
    
    def test_get_ledger_entries_valid_params(self):
        """Test get_ledger_entries with valid parameters"""
        from material_ledger.material_ledger.api import get_ledger_entries
        
        result = get_ledger_entries(
            company="_Test Company",
            from_date="2025-01-01",
            to_date="2025-12-31"
        )
        
        self.assertIsInstance(result, list)
    
    def test_get_financial_analysis_requires_company(self):
        """Test that get_financial_analysis requires company"""
        from material_ledger.material_ledger.api import get_financial_analysis
        
        with self.assertRaises(frappe.exceptions.ValidationError):
            get_financial_analysis(
                company="",
                year=2025
            )
    
    def test_get_financial_analysis_requires_year(self):
        """Test that get_financial_analysis requires valid year"""
        from material_ledger.material_ledger.api import get_financial_analysis
        
        with self.assertRaises(frappe.exceptions.ValidationError):
            get_financial_analysis(
                company="_Test Company",
                year=0
            )
    
    def test_get_financial_analysis_returns_data(self):
        """Test that get_financial_analysis returns expected structure"""
        from material_ledger.material_ledger.api import get_financial_analysis
        
        result = get_financial_analysis(
            company="_Test Company",
            year=2025,
            period="annual"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("period", result)
    
    def test_generate_ledger_pdf(self):
        """Test PDF generation"""
        from material_ledger.material_ledger.api import generate_ledger_pdf
        
        html = "<html><body><h1>Test Report</h1></body></html>"
        result = generate_ledger_pdf(html)
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)


class TestFinancialCalculator(FrappeTestCase):
    """Test cases for Financial Calculator service"""
    
    def test_calculate_ratios(self):
        """Test financial ratios calculation"""
        from material_ledger.material_ledger.services.financial_calculator import FinancialCalculator
        
        ratios = FinancialCalculator.calculate_ratios(
            income=1000000,
            expense=800000,
            net_profit=200000,
            assets=5000000,
            liabilities=2000000,
            equity=3000000,
            current_assets=1500000,
            current_liabilities=800000
        )
        
        self.assertIsInstance(ratios, dict)
        self.assertIn("roe", ratios)
        self.assertIn("roa", ratios)
        self.assertIn("current_ratio", ratios)
        self.assertIn("z_score", ratios)
        
        # Check ROE calculation
        expected_roe = (200000 / 3000000) * 100
        self.assertAlmostEqual(ratios["roe"], expected_roe, places=2)
        
        # Check current ratio
        expected_current_ratio = 1500000 / 800000
        self.assertAlmostEqual(ratios["current_ratio"], expected_current_ratio, places=2)
    
    def test_calculate_health_score(self):
        """Test health score calculation"""
        from material_ledger.material_ledger.services.financial_calculator import FinancialCalculator
        
        # Good ratios
        good_ratios = {
            "roe": 15,
            "net_margin": 12,
            "current_ratio": 2.0,
            "leverage": 1.5,
            "income_growth": 8,
            "z_score": 3.5
        }
        
        score = FinancialCalculator.calculate_health_score(good_ratios)
        self.assertGreaterEqual(score, 60)
        self.assertLessEqual(score, 100)
        
        # Poor ratios
        poor_ratios = {
            "roe": -5,
            "net_margin": -10,
            "current_ratio": 0.5,
            "leverage": 5,
            "income_growth": -15,
            "z_score": 1.2
        }
        
        score = FinancialCalculator.calculate_health_score(poor_ratios)
        self.assertLess(score, 40)
    
    def test_detect_risk_flags(self):
        """Test risk flag detection"""
        from material_ledger.material_ledger.services.financial_calculator import FinancialCalculator
        
        # Test with loss
        flags = FinancialCalculator.detect_risk_flags(
            ratios={"net_margin": -5, "current_ratio": 0.8, "z_score": 1.5, "roa": -2},
            profit=-100000,
            income=500000,
            assets=1000000,
            liabilities=600000
        )
        
        self.assertIsInstance(flags, list)
        self.assertGreater(len(flags), 0)
        
        # Check for loss flag
        loss_flags = [f for f in flags if f["code"] == "LOSS"]
        self.assertEqual(len(loss_flags), 1)
        
        # Check for bankruptcy risk
        bankruptcy_flags = [f for f in flags if f["code"] == "BANKRUPTCY_RISK"]
        self.assertEqual(len(bankruptcy_flags), 1)


class TestValidators(FrappeTestCase):
    """Test cases for Input Validators"""
    
    def test_validate_company_required(self):
        """Test company validation when required"""
        from material_ledger.material_ledger.services.validators import InputValidator
        
        with self.assertRaises(frappe.exceptions.ValidationError):
            InputValidator.validate_company("", required=True)
    
    def test_validate_company_exists(self):
        """Test company existence validation"""
        from material_ledger.material_ledger.services.validators import InputValidator
        
        with self.assertRaises(frappe.exceptions.ValidationError):
            InputValidator.validate_company("Non Existent Company XYZ")
    
    def test_validate_date_range(self):
        """Test date range validation"""
        from material_ledger.material_ledger.services.validators import InputValidator
        
        # Valid range
        from_date, to_date = InputValidator.validate_date_range(
            "2025-01-01", "2025-12-31"
        )
        self.assertEqual(from_date, "2025-01-01")
        self.assertEqual(to_date, "2025-12-31")
        
        # Invalid range (from > to)
        with self.assertRaises(frappe.exceptions.ValidationError):
            InputValidator.validate_date_range("2025-12-31", "2025-01-01")
    
    def test_validate_year(self):
        """Test year validation"""
        from material_ledger.material_ledger.services.validators import InputValidator
        
        # Valid year
        year = InputValidator.validate_year(2025)
        self.assertEqual(year, 2025)
        
        # Invalid year (too old)
        with self.assertRaises(frappe.exceptions.ValidationError):
            InputValidator.validate_year(1800)
    
    def test_validate_period(self):
        """Test period validation"""
        from material_ledger.material_ledger.services.validators import InputValidator
        
        # Valid periods
        period, _ = InputValidator.validate_period("annual")
        self.assertEqual(period, "annual")
        
        period, _ = InputValidator.validate_period("quarterly", "Q1")
        self.assertEqual(period, "quarterly")
        
        # Invalid period
        with self.assertRaises(frappe.exceptions.ValidationError):
            InputValidator.validate_period("invalid_period")
    
    def test_sanitize_html(self):
        """Test HTML sanitization"""
        from material_ledger.material_ledger.services.validators import InputValidator
        
        # Test script removal
        html = '<div>Hello<script>alert("xss")</script></div>'
        sanitized = InputValidator.sanitize_html(html)
        self.assertNotIn("<script>", sanitized)
        self.assertIn("<div>Hello", sanitized)
        
        # Test iframe removal
        html = '<div><iframe src="http://evil.com"></iframe></div>'
        sanitized = InputValidator.sanitize_html(html)
        self.assertNotIn("<iframe", sanitized)


class TestAIService(FrappeTestCase):
    """Test cases for AI Service"""
    
    def test_ai_service_initialization(self):
        """Test AI service initialization"""
        from material_ledger.material_ledger.services.ai_service import AIService
        
        service = AIService()
        self.assertIsNotNone(service.settings)
    
    @patch('material_ledger.material_ledger.services.ai_service.requests.post')
    def test_generate_report_success(self, mock_post):
        """Test successful AI report generation"""
        from material_ledger.material_ledger.services.ai_service import AIService
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test analysis report"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        service = AIService()
        service.api_key = "test_key"  # Set test key
        
        result = service.generate_financial_report(
            company="Test Company",
            year=2025,
            data={"summary": {"income": 1000000}}
        )
        
        self.assertIsInstance(result, str)
    
    def test_ai_service_not_available_without_key(self):
        """Test AI service returns appropriate message without API key"""
        from material_ledger.material_ledger.services.ai_service import AIService
        
        service = AIService()
        service.api_key = None
        
        self.assertFalse(service.is_available())


class TestMaterialLedgerSettings(FrappeTestCase):
    """Test cases for Material Ledger Settings"""
    
    def test_get_settings(self):
        """Test getting settings"""
        from material_ledger.material_ledger.doctype.material_ledger_settings.material_ledger_settings import MaterialLedgerSettings
        
        settings = MaterialLedgerSettings.get_settings()
        
        self.assertIsInstance(settings, dict)
        self.assertIn("enable_ai_analysis", settings)
        self.assertIn("enable_rate_limiting", settings)
        self.assertIn("cache_timeout", settings)


def run_tests():
    """Run all tests"""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestMaterialLedgerAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestFinancialCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestValidators))
    suite.addTests(loader.loadTestsFromTestCase(TestAIService))
    suite.addTests(loader.loadTestsFromTestCase(TestMaterialLedgerSettings))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
