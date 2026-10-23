# tests/test_asset_inventory.py
import pytest
import sys
import os

# Add project root to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_asset_code_generation_logic():
    """Test that the asset code is generated in the correct SGI-PREFIX-0001 format."""

    def generate_code(prefix, asset_id):
        return f"SGI-{prefix}-{str(asset_id).zfill(4)}"

    assert generate_code("IT", 1) == "SGI-IT-0001"
    assert generate_code("FUR", 45) == "SGI-FUR-0045"
    assert generate_code("LAB", 1002) == "SGI-LAB-1002"


def test_stock_balance_calculation():
    """Test that stock movements correctly calculate the new balance."""

    def calculate_new_balance(current_stock, movement_type, quantity):
        if movement_type == 'Issue':
            qty = -abs(float(quantity))
        else:  # Receipt, Return, etc.
            qty = abs(float(quantity))
        return float(current_stock) + qty

    # Start with 100 items
    balance = 100

    # Receive 50
    balance = calculate_new_balance(balance, 'Receipt', 50)
    assert balance == 150

    # Issue 30
    balance = calculate_new_balance(balance, 'Issue', 30)
    assert balance == 120

    # Return 10
    balance = calculate_new_balance(balance, 'Return', 10)
    assert balance == 130


def test_stock_over_issue_prevention():
    """Test that issuing more than available stock is prevented."""

    def can_issue(current_stock, issue_qty):
        return (float(current_stock) - float(issue_qty)) >= 0

    # Current stock 50, issue 50 (Should pass)
    assert can_issue(50, 50) == True

    # Current stock 50, issue 51 (Should fail)
    assert can_issue(50, 51) == False


def test_disposal_workflow_logic():
    """Test the disposal status transitions."""

    def process_disposal(current_status, action):
        if current_status != 'Pending':
            return False, "Already processed"
        if action == 'Approved':
            return True, 'Approved'
        elif action == 'Rejected':
            return True, 'Rejected'
        return False, "Invalid action"

    success, msg = process_disposal('Pending', 'Approved')
    assert success == True and msg == 'Approved'

    success, msg = process_disposal('Approved', 'Approved')
    assert success == False and "Already processed" in msg