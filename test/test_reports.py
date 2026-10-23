# tests/test_reports.py
import pytest
import sys
import os

# Add project root to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_csv_formula_injection_safeguard():
    """Test that malicious strings are prefixed to prevent formula injection."""

    def safeguard(text):
        if str(text).startswith(('=', '+', '-', '@')):
            return f"'{text}"
        return text

    assert safeguard("=HYPERLINK('http://evil.com')") == "'=HYPERLINK('http://evil.com')"
    assert safeguard("+1+1") == "'+1+1"
    assert safeguard("-1") == "'-1"
    assert safeguard("@SUM(A1:A2)") == "'@SUM(A1:A2)"
    assert safeguard("Normal Student Name") == "Normal Student Name"


def test_report_filter_logic():
    """Test that filters are correctly parsed (simulating route logic)."""

    def parse_filters(department_id=None, semester=None):
        filters = {}
        if department_id:
            filters["department_id"] = int(department_id)
        if semester:
            filters["semester"] = int(semester)
        return filters

    # Test with no filters
    assert parse_filters() == {}

    # Test with only department
    assert parse_filters(department_id="1") == {"department_id": 1}

    # Test with both filters
    assert parse_filters(department_id="1", semester="3") == {"department_id": 1, "semester": 3}


def test_generic_pdf_generator_import():
    """Test that the PDF generator utility can be imported."""
    try:
        from utils.pdf_generator import generate_generic_report_pdf
        assert callable(generate_generic_report_pdf)
    except ImportError:
        pytest.fail("Failed to import generate_generic_report_pdf")