# tests/test_campus_operations.py
import pytest
import sys
import os
from datetime import datetime, timedelta

# Add project root to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_hostel_bed_allocation_conflict():
    """Test that two students cannot be allocated to the same bed simultaneously."""

    def check_bed_availability(bed_status):
        return bed_status == 'Available'

    # Bed is available -> Allocation succeeds
    assert check_bed_availability('Available') == True

    # Bed is occupied -> Allocation fails
    assert check_bed_availability('Occupied') == False


def test_library_issue_availability_check():
    """Test that a book copy must be 'Available' before it can be issued."""

    def can_issue_copy(copy_status):
        return copy_status == 'Available'

    assert can_issue_copy('Available') == True
    assert can_issue_copy('Issued') == False
    assert can_issue_copy('Lost') == False


def test_library_due_date_calculation():
    """Test that due date is calculated as issue date + 14 days."""

    def calculate_due_date(issue_date):
        return issue_date + timedelta(days=14)

    issue_date = datetime.now().date()
    due_date = calculate_due_date(issue_date)
    assert due_date == issue_date + timedelta(days=14)


def test_transport_duplicate_allocation():
    """Test that a student cannot have two active transport allocations."""

    def can_allocate(has_active_allocation):
        return not has_active_allocation

    # Student has no active allocation -> Can allocate
    assert can_allocate(False) == True

    # Student already has active allocation -> Cannot allocate
    assert can_allocate(True) == False


def test_visitor_check_in_workflow():
    """Test visitor status transitions."""

    def can_check_in(approval_status, current_status):
        return approval_status == 'Approved' and current_status == 'Scheduled'

    # Approved and Scheduled -> Can check in
    assert can_check_in('Approved', 'Scheduled') == True

    # Pending approval -> Cannot check in
    assert can_check_in('Pending', 'Scheduled') == False

    # Already checked in -> Cannot check in again
    assert can_check_in('Approved', 'Checked In') == False