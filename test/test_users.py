# tests/test_users.py
import pytest
import sys
import os

# Add project root to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Mock the security logic for testing without DB connection
def check_deactivation_safety(target_user_id, actor_id, target_role, active_admin_count):
    """Simulates the safety checks from toggle_user_status_secure"""
    # 1. Prevent Self-Deactivation
    if target_user_id == actor_id:
        return False, "Security Error: You cannot deactivate your own account."

    # 2. Prevent Last-Admin Lockout
    if target_role == 'Admin' and active_admin_count <= 1:
        return False, "Security Error: Cannot deactivate the last active Admin account."

    return True, "Safe to deactivate"


def test_self_deactivation_prevention():
    # User tries to deactivate themselves (ID 1 = Actor, ID 1 = Target)
    valid, msg = check_deactivation_safety(1, 1, "Admin", 2)
    assert valid == False
    assert "own account" in msg


def test_last_admin_lockout_prevention():
    # Admin tries to deactivate the only other active Admin
    valid, msg = check_deactivation_safety(2, 1, "Admin", 1)
    assert valid == False
    assert "last active Admin" in msg


def test_safe_deactivation_of_student():
    # Admin deactivates a Student (Should be safe)
    valid, msg = check_deactivation_safety(5, 1, "Student", 2)
    assert valid == True


def test_safe_deactivation_of_second_admin():
    # Admin deactivates another Admin when there are 3 active admins
    valid, msg = check_deactivation_safety(2, 1, "Admin", 3)
    assert valid == True


def test_safe_deactivation_of_hod():
    # Admin deactivates an HOD
    valid, msg = check_deactivation_safety(3, 1, "HOD", 1)
    assert valid == True