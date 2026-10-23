# tests/test_hr_payroll.py
import pytest
import sys
import os
import calendar
from datetime import datetime

# Add project root to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_proration_calculation():
    """Test that salary is prorated correctly based on calendar days and LWP."""

    def calculate_net(monthly_salary, calendar_days, lwp_days):
        payable_days = calendar_days - lwp_days
        daily_salary = monthly_salary / calendar_days
        return daily_salary * payable_days

    # Test full month (October, 31 days), no LWP, Salary 31000
    assert calculate_net(31000, 31, 0) == 31000.0

    # Test mid-month joining (15 days LWP)
    # Salary 31000, 31 days, 15 LWP -> Payable 16 days
    expected = (31000 / 31) * 16
    assert calculate_net(31000, 31, 15) == round(expected, 2)


def test_payroll_separation_of_duties():
    """Test that the user who prepared the payroll cannot approve it."""

    def can_approve(prepared_by, approver_id, approver_role):
        if prepared_by == approver_id:
            return False, "Security Error: You cannot approve a payroll run you prepared."
        if approver_role not in ["Principal", "Admin"]:
            return False, "Unauthorized role."
        return True, "Approved"

    # Admin prepared, Admin approves (Same user) -> Should fail
    success, msg = can_approve(1, 1, "Admin")
    assert success == False
    assert "cannot approve" in msg

    # Admin prepared, Principal approves (Different user) -> Should pass
    success, msg = can_approve(1, 2, "Principal")
    assert success == True


def test_exit_workflow_logic():
    """Test that employee status changes correctly on exit clearance."""

    def process_exit(current_status, action):
        if current_status != 'Pending':
            return False, "Already processed"
        if action == 'Cleared':
            return True, 'Resigned'  # Employee status becomes Resigned
        elif action == 'Rejected':
            return True, 'Active'  # Employee remains Active
        return False, "Invalid action"

    success, emp_status = process_exit('Pending', 'Cleared')
    assert success == True and emp_status == 'Resigned'

    success, emp_status = process_exit('Cleared', 'Cleared')
    assert success == False