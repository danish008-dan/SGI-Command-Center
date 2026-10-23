# tests/test_fee_queries.py
import pytest

# Extracted validation logic for testing without DB connection
def check_payment_validity(amount, current_paid, payable_fee):
    if float(amount) <= 0:
        return False, "Amount must be greater than 0."
    if (current_paid + float(amount)) > payable_fee:
        return False, "Amount exceeds pending balance."
    return True, "Valid"

def test_valid_payment():
    valid, msg = check_payment_validity(5000, 0, 10000)
    assert valid == True

def test_zero_payment():
    valid, msg = check_payment_validity(0, 0, 10000)
    assert valid == False
    assert "greater than 0" in msg

def test_overpayment():
    valid, msg = check_payment_validity(5001, 5000, 10000)
    assert valid == False
    assert "exceeds pending balance" in msg

def test_exact_balance_payment():
    # Paying the exact remaining balance should be valid
    valid, msg = check_payment_validity(5000, 5000, 10000)
    assert valid == True