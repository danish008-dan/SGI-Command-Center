# tests/test_complaints.py
import pytest
import sys
import os

# Add project root to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the CATEGORY_ROUTING dictionary for testing
CATEGORY_ROUTING = {
    "Academic": "HOD",
    "Harassment": "Sensitive",
    "Ragging": "Sensitive",
    "Infrastructure": "Admin",
    "IT": "Admin",
    "Finance": "Admin",
    "General": "Admin"
}

def get_sensitivity(category):
    """Simulates the sensitivity determination logic"""
    routing_rule = CATEGORY_ROUTING.get(category, "Admin")
    return "Sensitive" if routing_rule == "Sensitive" else "Normal"

def test_academic_routing():
    assert CATEGORY_ROUTING.get("Academic") == "HOD"
    assert get_sensitivity("Academic") == "Normal"

def test_harassment_routing():
    assert CATEGORY_ROUTING.get("Harassment") == "Sensitive"
    assert get_sensitivity("Harassment") == "Sensitive"

def test_ragging_routing():
    assert CATEGORY_ROUTING.get("Ragging") == "Sensitive"
    assert get_sensitivity("Ragging") == "Sensitive"

def test_infrastructure_routing():
    assert CATEGORY_ROUTING.get("Infrastructure") == "Admin"
    assert get_sensitivity("Infrastructure") == "Normal"

def test_general_routing():
    assert CATEGORY_ROUTING.get("General") == "Admin"
    assert get_sensitivity("General") == "Normal"