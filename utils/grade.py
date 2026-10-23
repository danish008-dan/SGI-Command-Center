# utils/grade.py

def calculate_grade(percentage):
    """Calculates letter grade based on percentage."""
    if percentage >= 90: return "A+"
    elif percentage >= 80: return "A"
    elif percentage >= 70: return "B+"
    elif percentage >= 60: return "B"
    elif percentage >= 50: return "C"
    elif percentage >= 40: return "D"
    return "F"

def get_grade_point(grade):
    """Returns the 10-point scale grade point."""
    points = {"A+": 10, "A": 9, "B+": 8, "B": 7, "C": 6, "D": 5, "F": 0}
    return points.get(grade, 0)

def calculate_sgpa(subjects_data):
    """
    Calculates SGPA.
    subjects_data: list of dicts [{'credits': 4, 'grade_point': 9}, ...]
    """
    total_credits = 0
    total_weighted_points = 0

    for sub in subjects_data:
        total_credits += sub["credits"]
        total_weighted_points += (sub["credits"] * sub["grade_point"])

    if total_credits == 0: return 0.0
    return round(total_weighted_points / total_credits, 2)

def determine_final_result(subject_grades, overall_percentage):
    """
    Determines the final semester grade.
    If any subject is 'F', the final result is 'F' (Fail), regardless of aggregate percentage.
    """
    if "F" in subject_grades:
        return "F"
    return calculate_grade(overall_percentage)