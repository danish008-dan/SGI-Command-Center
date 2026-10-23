# database/profile_queries.py
from database.connection import get_connection


def get_full_profile(user_id):
    """Fetches user details along with role-specific details (Student/Teacher)."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT u.user_id, u.full_name, u.email, u.mobile, u.role, u.profile_image,
                   s.student_id, s.semester, s.section, s.cgpa, s.skills, s.interests, s.preferred_domain, s.dream_salary,
                   t.teacher_id, t.designation, t.qualification, t.experience
            FROM users u
            LEFT JOIN students s ON u.user_id = s.user_id
            LEFT JOIN teachers t ON u.user_id = t.user_id
            WHERE u.user_id = %s
        """
        cursor.execute(sql, (user_id,))
        return cursor.fetchone()
    except Exception as e:
        print("Error fetching full profile:", e)
        return None
    finally:
        conn.close()


def update_basic_info(user_id, full_name, mobile):
    """Updates the common user details."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET full_name = %s, mobile = %s WHERE user_id = %s", (full_name, mobile, user_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error updating basic info:", e)
        return False
    finally:
        conn.close()


def update_student_info(user_id, form_data):
    """Updates student-specific details."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        # Convert empty strings to None for DECIMAL/INT fields
        cgpa = float(form_data.get('cgpa')) if form_data.get('cgpa') else None
        salary = float(form_data.get('dream_salary')) if form_data.get('dream_salary') else None
        semester = int(form_data.get('semester')) if form_data.get('semester') else None

        cursor.execute("""
            UPDATE students 
            SET semester = %s, section = %s, cgpa = %s, skills = %s, interests = %s, 
                preferred_domain = %s, dream_salary = %s 
            WHERE user_id = %s
        """, (semester, form_data.get('section'), cgpa, form_data.get('skills'),
              form_data.get('interests'), form_data.get('preferred_domain'), salary, user_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error updating student info:", e)
        return False
    finally:
        conn.close()


def update_teacher_info(user_id, form_data):
    """Updates teacher-specific details."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        experience = int(form_data.get('experience')) if form_data.get('experience') else 0

        cursor.execute("""
            UPDATE teachers 
            SET designation = %s, qualification = %s, experience = %s 
            WHERE user_id = %s
        """, (form_data.get('designation'), form_data.get('qualification'), experience, user_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error updating teacher info:", e)
        return False
    finally:
        conn.close()