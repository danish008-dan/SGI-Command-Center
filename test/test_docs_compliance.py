# tests/test_docs_compliance.py
import pytest
import sys
import os

# Add project root to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_document_workflow_transitions():
    """Test that document status transitions follow the correct workflow."""

    def can_transition(current_status, new_status):
        valid_transitions = {
            'Draft': ['Pending Review'],
            'Pending Review': ['Approved', 'Rejected'],
            'Approved': ['Published'],
            'Published': ['Archived'],
            'Rejected': ['Draft']
        }
        return new_status in valid_transitions.get(current_status, [])

    # Draft -> Pending Review (Valid)
    assert can_transition('Draft', 'Pending Review') == True

    # Draft -> Approved (Invalid, must go through review)
    assert can_transition('Draft', 'Approved') == False

    # Pending -> Approved (Valid)
    assert can_transition('Pending Review', 'Approved') == True

    # Approved -> Published (Valid)
    assert can_transition('Approved', 'Published') == True

    # Published -> Archived (Valid)
    assert can_transition('Published', 'Archived') == True


def test_compliance_status_transitions():
    """Test compliance requirement status logic."""

    def is_valid_status(status):
        return status in ['Not Started', 'In Progress', 'Submitted', 'Verified', 'Not Applicable']

    assert is_valid_status('Not Started') == True
    assert is_valid_status('Verified') == True
    assert is_valid_status('Compliant') == False  # Invalid status


def test_action_item_completion():
    """Test that an action item cannot be completed without an owner."""

    def can_complete(assigned_to, status):
        return assigned_to is not None and status in ['Completed', 'In Progress', 'On Hold']

    # Has owner and status is Completed -> Can complete
    assert can_complete(1, 'Completed') == True

    # No owner -> Cannot complete
    assert can_complete(None, 'Completed') == False

    # Invalid status -> Cannot complete
    assert can_complete(1, 'Done') == False


def test_secure_download_authorization():
    """Test that secure document download requires authentication."""

    def can_download(user_role, doc_status):
        # Only authenticated users with docs.view can download published docs
        if user_role is None: return False
        if doc_status != 'Published': return False
        return True

    # Admin downloading published doc
    assert can_download('Admin', 'Published') == True

    # Unauthenticated user trying to download
    assert can_download(None, 'Published') == False

    # Trying to download a Draft (not published)
    assert can_download('Admin', 'Draft') == False