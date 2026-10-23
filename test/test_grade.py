# tests/test_grade.py
import pytest
import sys
import os

# Add project root to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.grade import calculate_grade, get_grade_point, calculate_sgpa, determine_final_result

def test_grade_boundaries():
    assert calculate_grade(95) == "A+"
    assert calculate_grade(90) == "A+"
    assert calculate_grade(89.9) == "A"
    assert calculate_grade(80) == "A"
    assert calculate_grade(70) == "B+"
    assert calculate_grade(60) == "B"
    assert calculate_grade(50) == "C"
    assert calculate_grade(40) == "D"
    assert calculate_grade(39.9) == "F"
    assert calculate_grade(0) == "F"

def test_grade_points():
    assert get_grade_point("A+") == 10
    assert get_grade_point("F") == 0
    assert get_grade_point("Unknown") == 0

def test_sgpa_calculation():
    subjects = [
        {"credits": 4, "grade_point": 10}, # A+
        {"credits": 3, "grade_point": 9},  # A
        {"credits": 2, "grade_point": 0}   # F
    ]
    # (4*10 + 3*9 + 2*0) / 9 = 67 / 9 = 7.44
    assert calculate_sgpa(subjects) == 7.44

def test_determine_final_result_pass():
    # All subjects passed, aggregate is 85% -> Grade A
    grades = ["A", "B+", "A+"]
    assert determine_final_result(grades, 85) == "A"

def test_determine_final_result_fail():
    # One subject failed (F), aggregate is 60%, but final should be F
    grades = ["A", "B", "F"]
    assert determine_final_result(grades, 60) == "F"