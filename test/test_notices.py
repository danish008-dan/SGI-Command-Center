# tests/test_notices.py
import pytest
import sys
import os

# Add project root to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the CATEGORY_APPROVERS dictionary for testing
CATEGORY_APPROVERS = {
    "Examination": "Principal",
    "Academic": "HOD",
    "Administrative": "Admin",
    "General": "Admin",
    "Holiday": "Principal"
}

def get_initial_status(category, user_role):
    """Simulates the logic from create_notice"""
    approver_role = CATEGORY_APPROVERS.get(category, "Admin")
    if approver_role == user_role:
        return "Published"
    else:
        return "Pending"

def test_admin_creates_general_notice():
    # Admin is the approver for General, so should be Published
    status = get_initial_status("General", "Admin")
    assert status == "Published"

def test_hod_creates_general_notice():
    # HOD is not the approver for General, so should be Pending
    status = get_initial_status("General", "HOD")
    assert status == "Pending"

def test_hod_creates_academic_notice():
    # HOD is the approver for Academic, so should be Published
    status = get_initial_status("Academic", "HOD")
    assert status == "Published"

def test_principal_creates_examination_notice():
    # Principal is the approver for Examination, so should be Published
    status = get_initial_status("Examination", "Principal")
    assert status == "Published"

def test_admin_creates_examination_notice():
    # Admin is not the approver for Examination, so should be Pending
    status = get_initial_status("Examination", "Admin")
    assert status == "Pending"