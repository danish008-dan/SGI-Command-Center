# database/admin_queries.py
import uuid
from datetime import datetime, timedelta

from database.connection import get_connection
from utils.password import hash_password
from utils.grade import calculate_grade, get_grade_point, calculate_sgpa, determine_final_result



def get_dashboard_stats():
    """Fetches total counts for the admin dashboard cards."""
    conn = get_connection()
    if conn is None:
        return {"students": 0, "teachers": 0, "departments": 0, "users": 0}

    try:
        cursor = conn.cursor()
        # Count students
        cursor.execute("SELECT COUNT(*) as count FROM students")
        students = cursor.fetchone()["count"]

        # Count teachers
        cursor.execute("SELECT COUNT(*) as count FROM teachers")
        teachers = cursor.fetchone()["count"]

        # Count departments
        cursor.execute("SELECT COUNT(*) as count FROM departments")
        departments = cursor.fetchone()["count"]

        # Count active users
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE status = 'Active'")
        users = cursor.fetchone()["count"]

        return {"students": students, "teachers": teachers, "departments": departments, "users": users}
    except Exception as e:
        print("Error fetching stats:", e)
        return {"students": 0, "teachers": 0, "departments": 0, "users": 0}
    finally:
        conn.close()





def get_departments_for_dropdown():
    """Fetches departments for the HTML select dropdown."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT department_id, department_name FROM departments ORDER BY department_name")
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching departments:", e)
        return []
    finally:
        conn.close()


# ==========================================
# STUDENT MANAGEMENT (PHASE 1)
# ==========================================

def get_student_directory_stats():
    """Fetches KPI stats for the student directory."""
    conn = get_connection()
    if conn is None: return {"total": 0, "active": 0, "inactive": 0}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM students")
        total = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) as c FROM users u 
            INNER JOIN students s ON u.user_id = s.user_id 
            WHERE u.status = 'Active'
        """)
        active = cursor.fetchone()["c"]

        return {"total": total, "active": active, "inactive": total - active}
    except Exception as e:
        print("Student stats error:", e)
        return {"total": 0, "active": 0, "inactive": 0}
    finally:
        conn.close()


def get_all_students(search=None, department_id=None, semester=None):
    """Fetches students with optional search and filters."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT s.student_id, s.enrollment_no, u.full_name, u.email, u.status,
                   d.department_name, s.semester, s.section, s.cgpa
            FROM students s
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE 1=1
        """
        params = []
        if search:
            sql += " AND (u.full_name LIKE %s OR s.enrollment_no LIKE %s OR u.email LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        if department_id:
            sql += " AND u.department_id = %s"
            params.append(department_id)
        if semester:
            sql += " AND s.semester = %s"
            params.append(semester)

        sql += " ORDER BY s.student_id DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching students:", e)
        return []
    finally:
        conn.close()


def get_student_for_admin(student_id):
    """Fetches complete student profile for Admin view."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT s.student_id, s.user_id, s.enrollment_no, s.semester, s.section, s.cgpa,
                   u.full_name, u.email, u.mobile, u.status, u.profile_image,
                   d.department_name
            FROM students s
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE s.student_id = %s
        """
        cursor.execute(sql, (student_id,))
        return cursor.fetchone()
    except Exception as e:
        print("Error fetching student for admin:", e)
        return None
    finally:
        conn.close()


def add_student_to_db(form_data):
    """Safely inserts a student using a database transaction."""
    conn = get_connection()
    if conn is None: return False, "Database connection failed."

    try:
        # Turn off autocommit temporarily for manual transaction control
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Check duplicate email
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (form_data['email'],))
        if cursor.fetchone():
            return False, "This email is already registered."

        # 2. Check duplicate enrollment
        cursor.execute("SELECT student_id FROM students WHERE enrollment_no = %s", (form_data['enrollment'],))
        if cursor.fetchone():
            return False, "This enrollment number already exists."

        # 3. Insert into Users table
        encrypted_password = hash_password(form_data['password']).decode()
        cursor.execute("""
            INSERT INTO users (full_name, email, mobile, password, role, department_id, status)
            VALUES (%s, %s, %s, %s, 'Student', %s, 'Active')
        """, (
            form_data['name'], form_data['email'], form_data['mobile'],
            encrypted_password, form_data['department_id']
        ))

        user_id = cursor.lastrowid

        # 4. Insert into Students table
        cursor.execute("""
            INSERT INTO students (user_id, enrollment_no, semester, section, cgpa, skills, interests, preferred_domain, dream_salary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, form_data['enrollment'], int(form_data['semester']),
            form_data.get('section') or None, form_data.get('cgpa') or None,
            form_data.get('skills'), form_data.get('interests'),
            form_data.get('domain'), form_data.get('salary') or None
        ))

        # 5. Commit if everything succeeds
        conn.commit()
        return True, "Student account created successfully."

    except Exception as e:
        # Rollback if anything fails!
        conn.rollback()
        print("Transaction Error:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)  # Reset autocommit
        conn.close()


# ==========================================
# TEACHER MANAGEMENT (PHASE 1)
# ==========================================

def get_teacher_directory_stats():
    """Fetches KPI stats for the teacher directory."""
    conn = get_connection()
    if conn is None: return {"total": 0, "active": 0, "inactive": 0}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM teachers")
        total = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) as c FROM users u 
            INNER JOIN teachers t ON u.user_id = t.user_id 
            WHERE u.status = 'Active'
        """)
        active = cursor.fetchone()["c"]

        return {"total": total, "active": active, "inactive": total - active}
    except Exception as e:
        print("Teacher stats error:", e)
        return {"total": 0, "active": 0, "inactive": 0}
    finally:
        conn.close()


def get_all_teachers(search=None, department_id=None):
    """Fetches teachers with optional search and filters."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT t.teacher_id, u.full_name, u.email, u.status, u.mobile,
                   d.department_name, t.designation, t.qualification, t.experience
            FROM teachers t
            INNER JOIN users u ON t.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE 1=1
        """
        params = []
        if search:
            sql += " AND (u.full_name LIKE %s OR u.email LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        if department_id:
            sql += " AND u.department_id = %s"
            params.append(department_id)

        sql += " ORDER BY t.teacher_id DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching teachers:", e)
        return []
    finally:
        conn.close()


def get_teacher_for_admin(teacher_id):
    """Fetches complete teacher profile for Admin view."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT t.teacher_id, t.user_id, t.designation, t.qualification, t.experience,
                   u.full_name, u.email, u.mobile, u.status, u.profile_image,
                   d.department_name
            FROM teachers t
            INNER JOIN users u ON t.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE t.teacher_id = %s
        """
        cursor.execute(sql, (teacher_id,))
        return cursor.fetchone()
    except Exception as e:
        print("Error fetching teacher for admin:", e)
        return None
    finally:
        conn.close()


def update_teacher_in_db(teacher_id, form_data):
    """Updates teacher and user records safely."""
    conn = get_connection()
    if conn is None: return False, "DB Connection Failed"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # Check email duplicate
        cursor.execute("""
            SELECT user_id FROM users WHERE email = %s 
            AND user_id != (SELECT user_id FROM teachers WHERE teacher_id = %s)
        """, (form_data['email'], teacher_id))
        if cursor.fetchone(): return False, "Email already in use by another account."

        # Update users table
        cursor.execute("""
            UPDATE users 
            SET full_name = %s, email = %s, mobile = %s, department_id = %s
            WHERE user_id = (SELECT user_id FROM teachers WHERE teacher_id = %s)
        """, (
            form_data['name'], form_data['email'], form_data.get('mobile'),
            form_data['department_id'], teacher_id
        ))

        # Update teachers table
        cursor.execute("""
            UPDATE teachers 
            SET designation = %s, qualification = %s, experience = %s
            WHERE teacher_id = %s
        """, (
            form_data['designation'], form_data.get('qualification'),
            int(form_data.get('experience', 0)), teacher_id
        ))

        conn.commit()
        return True, "Teacher updated successfully."
    except Exception as e:
        conn.rollback()
        print("Error updating teacher:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

def add_teacher_to_db(form_data):
    """Safely inserts a teacher using a database transaction."""
    conn = get_connection()
    if conn is None: return False, "Database connection failed."

    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Check duplicate email
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (form_data['email'],))
        if cursor.fetchone():
            return False, "This email is already registered."

        # 2. Insert into Users table
        encrypted_password = hash_password(form_data['password']).decode()
        cursor.execute("""
            INSERT INTO users (full_name, email, mobile, password, role, department_id, status)
            VALUES (%s, %s, %s, %s, 'Teacher', %s, 'Active')
        """, (
            form_data['name'], form_data['email'], form_data['mobile'],
            encrypted_password, form_data['department_id']
        ))

        user_id = cursor.lastrowid

        # 3. Insert into Teachers table
        cursor.execute("""
            INSERT INTO teachers (user_id, designation, qualification, experience)
            VALUES (%s, %s, %s, %s)
        """, (
            user_id, form_data['designation'],
            form_data.get('qualification') or None,
            int(form_data.get('experience', 0))
        ))

        conn.commit()
        return True, "Teacher account created successfully."

    except Exception as e:
        conn.rollback()
        print("Transaction Error:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

# ==========================================
# SUBJECT MANAGEMENT
# ==========================================

def get_teachers_for_dropdown():
    """Fetches teacher_id and name for the dropdown."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # We join with users table to get the teacher's name
        cursor.execute("""
            SELECT t.teacher_id, u.full_name 
            FROM teachers t 
            INNER JOIN users u ON t.user_id = u.user_id
            ORDER BY u.full_name
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching teachers:", e)
        return []
    finally:
        conn.close()


# ==========================================
# SUBJECT MANAGEMENT (PHASE 1)
# ==========================================

def get_subject_directory_stats():
    """Fetches KPI stats for the subject directory."""
    conn = get_connection()
    if conn is None: return {"total": 0, "active": 0, "inactive": 0}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM subjects")
        total = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM subjects WHERE status = 'Active'")
        active = cursor.fetchone()["c"]

        return {"total": total, "active": active, "inactive": total - active}
    except Exception as e:
        print("Subject stats error:", e)
        return {"total": 0, "active": 0, "inactive": 0}
    finally:
        conn.close()


def get_all_subjects(search=None, department_id=None, semester=None, subject_type=None):
    """Fetches subjects with optional search and filters."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT s.subject_id, s.subject_name, s.subject_code, s.semester, 
                   s.credits, s.subject_type, s.status,
                   d.department_name, 
                   u.full_name AS teacher_name
            FROM subjects s
            LEFT JOIN departments d ON s.department_id = d.department_id
            LEFT JOIN teachers t ON s.teacher_id = t.teacher_id
            LEFT JOIN users u ON t.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        if search:
            sql += " AND (s.subject_name LIKE %s OR s.subject_code LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        if department_id:
            sql += " AND s.department_id = %s"
            params.append(department_id)
        if semester:
            sql += " AND s.semester = %s"
            params.append(semester)
        if subject_type:
            sql += " AND s.subject_type = %s"
            params.append(subject_type)

        sql += " ORDER BY s.subject_id DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching subjects:", e)
        return []
    finally:
        conn.close()


def get_subject_for_admin(subject_id):
    """Fetches complete subject profile for Admin view."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT s.subject_id, s.subject_name, s.subject_code, s.semester, 
                   s.credits, s.subject_type, s.status, s.classes_per_week,
                   d.department_name, 
                   t.teacher_id, u.full_name AS teacher_name
            FROM subjects s
            LEFT JOIN departments d ON s.department_id = d.department_id
            LEFT JOIN teachers t ON s.teacher_id = t.teacher_id
            LEFT JOIN users u ON t.user_id = u.user_id
            WHERE s.subject_id = %s
        """
        cursor.execute(sql, (subject_id,))
        return cursor.fetchone()
    except Exception as e:
        print("Error fetching subject for admin:", e)
        return None
    finally:
        conn.close()


def toggle_subject_status_db(subject_id, new_status):
    """Soft delete or reactivate subject by toggling status."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE subjects SET status = %s WHERE subject_id = %s", (new_status, subject_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error toggling subject status:", e)
        return False
    finally:
        conn.close()

def add_subject_to_db(form_data):
    """Inserts a new subject."""
    conn = get_connection()
    if conn is None: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT subject_id FROM subjects WHERE subject_code = %s", (form_data['subject_code'],))
        if cursor.fetchone():
            return False, "Subject Code already exists."

        cursor.execute("""
            INSERT INTO subjects 
            (subject_name, subject_code, semester, department_id, teacher_id, credits, subject_type, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            form_data['subject_name'], form_data['subject_code'], int(form_data['semester']),
            form_data['department_id'], form_data['teacher_id'] or None,
            int(form_data.get('credits', 4)), form_data.get('subject_type', 'Theory'),
            form_data.get('status', 'Active')
        ))
        conn.commit()
        return True, "Subject added successfully."
    except Exception as e:
        print("Error adding subject:", e)
        return False, str(e)
    finally:
        conn.close()



def update_subject_in_db(subject_id, form_data):
    """Updates an existing subject in the database."""
    conn = get_connection()
    if conn is None: return False, "Database connection failed."
    try:
        cursor = conn.cursor()

        # Check duplicate code for OTHER subjects
        cursor.execute("""
            SELECT subject_id FROM subjects 
            WHERE subject_code = %s AND subject_id != %s
        """, (form_data['subject_code'], subject_id))
        if cursor.fetchone():
            return False, "Another subject already uses this code."

        cursor.execute("""
            UPDATE subjects 
            SET subject_code = %s, subject_name = %s, department_id = %s, 
                semester = %s, teacher_id = %s, credits = %s, 
                subject_type = %s, status = %s
            WHERE subject_id = %s
        """, (
            form_data['subject_code'], form_data['subject_name'],
            form_data['department_id'], int(form_data['semester']),
            form_data['teacher_id'] or None, int(form_data.get('credits', 4)),
            form_data.get('subject_type', 'Theory'),
            form_data.get('status', 'Active'), subject_id
        ))
        conn.commit()
        return True, "Subject updated successfully."
    except Exception as e:
        print("Error updating subject:", e)
        return False, str(e)
    finally:
        conn.close()


# DEPARTMENT MANAGEMENT

def get_department_stats():
    """Fetches KPI stats for the department overview page."""
    conn = get_connection()
    if conn is None: return {"total": 0, "active": 0, "inactive": 0, "hod_assigned": 0}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM departments")
        total = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM departments WHERE status = 'Active'")
        active = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM departments WHERE status = 'Inactive'")
        inactive = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(DISTINCT d.department_id) as c 
            FROM departments d 
            INNER JOIN department_hod_assignments ha ON d.department_id = ha.department_id 
            WHERE ha.status = 'Active'
        """)
        hod_assigned = cursor.fetchone()["c"]

        return {"total": total, "active": active, "inactive": inactive, "hod_assigned": hod_assigned}
    except Exception as e:
        print("Dept stats error:", e)
        return {"total": 0, "active": 0, "inactive": 0, "hod_assigned": 0}
    finally:
        conn.close()


def add_department_to_db(form_data):
    """Inserts a new department with full details."""
    conn = get_connection()
    if conn is None: return False, "DB Connection Failed"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT department_id FROM departments WHERE department_code = %s",
                       (form_data['department_code'],))
        if cursor.fetchone(): return False, "Department Code already exists."

        cursor.execute("""
            INSERT INTO departments (department_name, department_code, short_name, description, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            form_data['department_name'], form_data['department_code'],
            form_data.get('short_name'), form_data.get('description'),
            form_data.get('status', 'Active')
        ))
        conn.commit()
        return True, "Department added successfully."
    except Exception as e:
        print("Error adding department:", e)
        return False, str(e)
    finally:
        conn.close()


def get_all_departments():
    """Fetches all departments with current active HOD."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT d.department_id, d.department_name, d.department_code, d.short_name, 
                   d.description, d.status, d.created_at,
                   u.full_name AS hod_name
            FROM departments d
            LEFT JOIN department_hod_assignments ha ON d.department_id = ha.department_id AND ha.status = 'Active'
            LEFT JOIN users u ON ha.user_id = u.user_id
            ORDER BY d.department_id DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching departments:", e)
        return []
    finally:
        conn.close()


def update_department_in_db(dept_id, form_data):
    """Updates department master data."""
    conn = get_connection()
    if conn is None: return False, "DB Connection Failed"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT department_id FROM departments WHERE department_code = %s AND department_id != %s",
                       (form_data['department_code'], dept_id))
        if cursor.fetchone(): return False, "Another department uses this code."

        cursor.execute("""
            UPDATE departments 
            SET department_name = %s, department_code = %s, short_name = %s, description = %s, status = %s
            WHERE department_id = %s
        """, (
            form_data['department_name'], form_data['department_code'],
            form_data.get('short_name'), form_data.get('description'),
            form_data.get('status', 'Active'), dept_id
        ))
        conn.commit()
        return True, "Department updated successfully."
    except Exception as e:
        print("Error updating department:", e)
        return False, str(e)
    finally:
        conn.close()

def get_department_details(dept_id):
    """Fetches full details for the Department Detail Page."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # 1. Basic Info + Current Active HOD (Explicit columns to avoid d.* collision)
        cursor.execute("""
            SELECT 
                d.department_id, d.department_name, d.department_code, 
                d.short_name, d.description, d.status, d.created_at, 
                u.full_name AS hod_name, ha.effective_from AS hod_since
            FROM departments d
            LEFT JOIN department_hod_assignments ha ON d.department_id = ha.department_id AND ha.status = 'Active'
            LEFT JOIN users u ON ha.user_id = u.user_id
            WHERE d.department_id = %s
        """, (dept_id,))
        details = cursor.fetchone()
        if not details: return None

        # 2. Counts (Students, Faculty, Subjects)
        cursor.execute(
            "SELECT COUNT(*) as c FROM users u INNER JOIN students s ON u.user_id = s.user_id WHERE u.department_id = %s",
            (dept_id,))
        details["student_count"] = cursor.fetchone()["c"]

        cursor.execute(
            "SELECT COUNT(*) as c FROM users u INNER JOIN teachers t ON u.user_id = t.user_id WHERE u.department_id = %s",
            (dept_id,))
        details["faculty_count"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM subjects WHERE department_id = %s", (dept_id,))
        details["subject_count"] = cursor.fetchone()["c"]

        return details
    except Exception as e:
        print("Error fetching dept details:", e)
        return None
    finally:
        conn.close()

def get_department_people(dept_id):
    """Fetches faculty and students for a department."""
    conn = get_connection()
    if conn is None: return {"faculty": [], "students": []}
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.teacher_id, u.full_name, t.designation, t.qualification, t.experience, u.status
            FROM teachers t INNER JOIN users u ON t.user_id = u.user_id
            WHERE u.department_id = %s ORDER BY u.full_name
        """, (dept_id,))
        faculty = cursor.fetchall()

        cursor.execute("""
            SELECT s.student_id, s.enrollment_no, u.full_name, s.semester, s.section, u.status
            FROM students s INNER JOIN users u ON s.user_id = u.user_id
            WHERE u.department_id = %s ORDER BY s.semester, u.full_name
        """, (dept_id,))
        students = cursor.fetchall()

        return {"faculty": faculty, "students": students}
    except Exception as e:
        print("Error fetching dept people:", e)
        return {"faculty": [], "students": []}
    finally:
        conn.close()


def get_department_hod_history(dept_id):
    """Fetches HOD assignment history."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ha.assignment_id, u.full_name AS hod_name, ha.effective_from, ha.effective_to, ha.status, ha.created_at
            FROM department_hod_assignments ha
            INNER JOIN users u ON ha.user_id = u.user_id
            WHERE ha.department_id = %s
            ORDER BY ha.created_at DESC
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching HOD history:", e)
        return []
    finally:
        conn.close()


def get_hod_candidates():
    """Fetches users eligible to be HOD (Teachers and existing HODs)."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.full_name, u.role 
            FROM users u 
            WHERE u.role IN ('Teacher', 'HOD') AND u.status = 'Active'
            ORDER BY u.full_name
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching HOD candidates:", e)
        return []
    finally:
        conn.close()


def assign_new_hod(dept_id, user_id, effective_from, admin_id):
    """Assigns a new HOD, expires the old one, and updates user role."""
    conn = get_connection()
    if conn is None: return False, "DB Connection Failed"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Expire current active HOD assignment
        cursor.execute("""
            UPDATE department_hod_assignments 
            SET status = 'Inactive', effective_to = %s 
            WHERE department_id = %s AND status = 'Active'
        """, (effective_from, dept_id))

        # 2. Insert new active HOD assignment
        cursor.execute("""
            INSERT INTO department_hod_assignments (department_id, user_id, effective_from, status, assigned_by)
            VALUES (%s, %s, %s, 'Active', %s)
        """, (dept_id, user_id, effective_from, admin_id))

        # 3. Update new user role to HOD
        cursor.execute("UPDATE users SET role = 'HOD' WHERE user_id = %s", (user_id,))

        conn.commit()
        return True, "New HOD assigned successfully."
    except Exception as e:
        conn.rollback()
        print("Error assigning HOD:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

def get_low_attendance_students():
    """Fetches students who have less than 75% attendance in any subject."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT u.full_name AS student_name, ast.subject_name, ast.percentage
            FROM attendance_summary ast
            INNER JOIN students s ON ast.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE ast.percentage < 75
            ORDER BY ast.percentage ASC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching low attendance:", e)
        return []
    finally:
        conn.close()



def generate_semester_results(semester):
    """Calculates and saves results for all students in a semester."""
    conn = get_connection()
    if conn is None: return False, "Database connection failed."
    try:
        cursor = conn.cursor()

        # 1. Get all students in this semester
        cursor.execute("SELECT student_id FROM students WHERE semester = %s", (semester,))
        students = cursor.fetchall()
        if not students:
            return False, f"No students found in Semester {semester}."

        for student in students:
            student_id = student["student_id"]

            # Prevent overwriting already Published results (Controlled Publication)
            cursor.execute("SELECT status FROM results WHERE student_id = %s AND semester = %s", (student_id, semester))
            existing_res = cursor.fetchone()
            if existing_res and existing_res["status"] == 'Published':
                continue  # Skip this student, result is already live

            # 2. Get all marks for this student for this semester
            cursor.execute("""
                SELECT s.subject_id, s.credits, m.maximum_marks, m.obtained_marks
                FROM marks m
                INNER JOIN subjects s ON m.subject_id = s.subject_id
                WHERE m.student_id = %s AND s.semester = %s AND m.submission_status = 'Verified'
            """, (student_id, semester))
            marks = cursor.fetchall()

            if not marks: continue  # Skip if no marks entered

            total_max = sum(m["maximum_marks"] for m in marks)
            total_obt = sum(m["obtained_marks"] for m in marks)
            overall_percentage = round((total_obt / total_max) * 100, 2) if total_max > 0 else 0

            # Calculate SGPA and track subject grades
            sgpa_data = []
            subject_grades = []
            for m in marks:
                sub_pct = (m["obtained_marks"] / m["maximum_marks"]) * 100 if m["maximum_marks"] > 0 else 0
                sub_grade = calculate_grade(sub_pct)
                subject_grades.append(sub_grade)
                sgpa_data.append({"credits": m["credits"], "grade_point": get_grade_point(sub_grade)})

            sgpa = calculate_sgpa(sgpa_data)

            # FIX: Use determine_final_result to enforce Fail if any subject is F
            final_grade = determine_final_result(subject_grades, overall_percentage)

            # 3. Upsert into results table
            # Note: For Phase 1, CGPA is kept equal to SGPA until a multi-semester historical table is built in Phase 3.
            cursor.execute("""
                INSERT INTO results (student_id, semester, total_marks, obtained_marks, percentage, sgpa, cgpa, grade, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Draft')
                ON DUPLICATE KEY UPDATE 
                total_marks=VALUES(total_marks), obtained_marks=VALUES(obtained_marks), 
                percentage=VALUES(percentage), sgpa=VALUES(sgpa), cgpa=VALUES(cgpa), grade=VALUES(grade)
            """, (student_id, semester, total_max, total_obt, overall_percentage, sgpa, sgpa, final_grade))

        conn.commit()
        return True, f"Results generated successfully for {len(students)} students in Semester {semester}."
    except Exception as e:
        print("Error generating results:", e)
        return False, str(e)
    finally:
        conn.close()


def get_result_analysis(semester):
    """Fetches published results for Admin analysis (Toppers, Failed)."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT u.full_name, r.percentage, r.sgpa, r.grade
            FROM results r
            INNER JOIN students s ON r.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE r.semester = %s AND r.status = 'Published'
            ORDER BY r.percentage DESC
        """
        cursor.execute(sql, (semester,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching analysis:", e)
        return []
    finally:
        conn.close()


# ==========================================
# TIMETABLE MANAGEMENT
# ==========================================

def get_all_rooms():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms ORDER BY room_number")
        return cursor.fetchall()
    except Exception as e:
        return []
    finally:
        conn.close()


def add_room_to_db(form_data):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT room_id FROM rooms WHERE room_number = %s", (form_data['room_number'],))
        if cursor.fetchone(): return False, "Room number already exists."

        cursor.execute("""
            INSERT INTO rooms (room_number, room_name, room_type, capacity, building, floor)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (form_data['room_number'], form_data['room_name'], form_data['room_type'],
              form_data['capacity'], form_data.get('building'), form_data.get('floor') or None))
        conn.commit()
        return True, "Room added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_all_time_slots():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM time_slots ORDER BY start_time")
        return cursor.fetchall()
    except Exception as e:
        return []
    finally:
        conn.close()


def add_time_slot_to_db(form_data):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        is_break = 1 if form_data.get('is_break') == 'on' else 0
        cursor.execute("""
            INSERT INTO time_slots (slot_name, start_time, end_time, is_break)
            VALUES (%s, %s, %s, %s)
        """, (form_data['slot_name'], form_data['start_time'], form_data['end_time'], is_break))
        conn.commit()
        return True, "Time Slot added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def add_timetable_entry(form_data):
    """Inserts timetable entry with Teacher, Room, and Class conflict checking."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()

        # 1. Teacher Conflict
        cursor.execute("SELECT timetable_id FROM timetable WHERE teacher_id = %s AND day_of_week = %s AND slot_id = %s",
                       (form_data['teacher_id'], form_data['day'], form_data['slot_id']))
        if cursor.fetchone(): return False, "Teacher Conflict: This teacher is already assigned at this time."

        # 2. Room Conflict
        cursor.execute("SELECT timetable_id FROM timetable WHERE room_id = %s AND day_of_week = %s AND slot_id = %s",
                       (form_data['room_id'], form_data['day'], form_data['slot_id']))
        if cursor.fetchone(): return False, "Room Conflict: This room is already booked at this time."

        # 3. Class Conflict
        cursor.execute("""
            SELECT timetable_id FROM timetable 
            WHERE department_id = %s AND semester = %s AND section = %s AND day_of_week = %s AND slot_id = %s
        """, (form_data['department_id'], form_data['semester'], form_data['section'], form_data['day'],
              form_data['slot_id']))
        if cursor.fetchone(): return False, "Class Conflict: This class already has a subject at this time."

        cursor.execute("""
            INSERT INTO timetable (department_id, semester, section, subject_id, teacher_id, room_id, slot_id, day_of_week)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (form_data['department_id'], form_data['semester'], form_data['section'], form_data['subject_id'],
              form_data['teacher_id'], form_data['room_id'], form_data['slot_id'], form_data['day']))
        conn.commit()
        return True, "Timetable entry added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_timetable_grid(department_id, semester, section):
    """Fetches timetable data joined with subject, teacher, room."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # FIX: Changed %H:%i to %%H:%%i to prevent PyMySQL format string error
        sql = """
            SELECT t.day_of_week, 
                   DATE_FORMAT(ts.start_time, '%%H:%%i') as start_time, 
                   DATE_FORMAT(ts.end_time, '%%H:%%i') as end_time, 
                   ts.is_break,
                   s.subject_name, u.full_name AS teacher_name, r.room_number
            FROM timetable t
            INNER JOIN time_slots ts ON t.slot_id = ts.slot_id
            INNER JOIN subjects s ON t.subject_id = s.subject_id
            INNER JOIN teachers th ON t.teacher_id = th.teacher_id
            INNER JOIN users u ON th.user_id = u.user_id
            INNER JOIN rooms r ON t.room_id = r.room_id
            WHERE t.department_id = %s AND t.semester = %s AND t.section = %s
            ORDER BY ts.start_time
        """
        cursor.execute(sql, (department_id, semester, section))
        return cursor.fetchall()
    except Exception as e:
        print("ERROR fetching timetable grid:", e)
        return []
    finally:
        conn.close()


# ==========================================
# TIMETABLE MANAGEMENT
# ==========================================

def preflight_timetable_check(department_id, semester, section):
    """Validates scheduling inputs before generation."""
    conn = get_connection()
    if conn is None: return {"valid": False, "issues": ["DB Connection Failed"]}
    try:
        cursor = conn.cursor()
        issues = []

        # 1. Check Subjects
        cursor.execute("""
            SELECT subject_id, subject_name, teacher_id, classes_per_week 
            FROM subjects 
            WHERE department_id = %s AND semester = %s AND status = 'Active'
        """, (department_id, semester))
        subjects = cursor.fetchall()

        if not subjects:
            issues.append("No active subjects found for this Department/Semester.")
        else:
            for sub in subjects:
                if not sub["teacher_id"]:
                    issues.append(f"Subject '{sub['subject_name']}' has no teacher assigned.")
                if not sub["classes_per_week"] or sub["classes_per_week"] == 0:
                    issues.append(f"Subject '{sub['subject_name']}' has 0 classes per week defined.")

        # 2. Check Rooms
        cursor.execute("SELECT COUNT(*) as c FROM rooms WHERE status = 'Active'")
        if cursor.fetchone()["c"] == 0:
            issues.append("No active rooms available in the system.")

        # 3. Check Time Slots
        cursor.execute("SELECT COUNT(*) as c FROM time_slots WHERE status = 'Active' AND is_break = FALSE")
        if cursor.fetchone()["c"] == 0:
            issues.append("No active (non-break) time slots available.")

        return {"valid": len(issues) == 0, "issues": issues}
    except Exception as e:
        return {"valid": False, "issues": [str(e)]}
    finally:
        conn.close()


def generate_auto_timetable(department_id, semester, section, academic_year="2024-25"):
    """Generates timetable with structured diagnostics and safe draft replacement."""
    conn = get_connection()
    if conn is None: return {"status": "ERROR", "message": "DB Connection failed."}

    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Preflight Check
        preflight = preflight_timetable_check(department_id, semester, section)
        if not preflight["valid"]:
            return {"status": "INVALID_INPUT", "message": "Preflight validation failed.", "issues": preflight["issues"]}

        # 2. Fetch active subjects
        cursor.execute("""
            SELECT subject_id, subject_name, teacher_id, classes_per_week 
            FROM subjects 
            WHERE department_id = %s AND semester = %s AND status = 'Active' AND classes_per_week > 0
        """, (department_id, semester))
        subjects = cursor.fetchall()

        # 3. Fetch active time slots (non-break)
        cursor.execute(
            "SELECT slot_id FROM time_slots WHERE status = 'Active' AND is_break = FALSE ORDER BY start_time")
        slots = cursor.fetchall()

        # 4. Fetch active rooms
        cursor.execute("SELECT room_id FROM rooms WHERE status = 'Active'")
        rooms = cursor.fetchall()

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        generated_entries = []  # Store entries in memory to preserve old draft until success
        unscheduled_sessions = []
        scheduled_count = 0

        # 5. Generation Algorithm
        for sub in subjects:
            required = sub["classes_per_week"]
            scheduled_for_sub = 0

            for day in days:
                if scheduled_for_sub >= required: break

                for slot in slots:
                    if scheduled_for_sub >= required: break

                    slot_id = slot["slot_id"]
                    teacher_id = sub["teacher_id"]

                    # Find an available room
                    room_found = False
                    for room in rooms:
                        room_id = room["room_id"]

                        # CHECK 1: Teacher Conflict (Published or in current generated_entries)
                        teacher_busy = False
                        # Check DB for Published entries
                        cursor.execute("""
                            SELECT 1 FROM timetable 
                            WHERE teacher_id = %s AND day_of_week = %s AND slot_id = %s AND status = 'Published'
                        """, (teacher_id, day, slot_id))
                        if cursor.fetchone(): teacher_busy = True

                        # Check generated_entries for Draft conflicts
                        if not teacher_busy:
                            for entry in generated_entries:
                                if entry["teacher_id"] == teacher_id and entry["day"] == day and entry[
                                    "slot_id"] == slot_id:
                                    teacher_busy = True
                                    break

                        if teacher_busy: continue

                        # CHECK 2: Room Conflict
                        room_busy = False
                        cursor.execute("""
                            SELECT 1 FROM timetable 
                            WHERE room_id = %s AND day_of_week = %s AND slot_id = %s AND status = 'Published'
                        """, (room_id, day, slot_id))
                        if cursor.fetchone(): room_busy = True

                        if not room_busy:
                            for entry in generated_entries:
                                if entry["room_id"] == room_id and entry["day"] == day and entry["slot_id"] == slot_id:
                                    room_busy = True
                                    break
                        if room_busy: continue

                        # CHECK 3: Class Conflict
                        class_busy = False
                        cursor.execute("""
                            SELECT 1 FROM timetable 
                            WHERE department_id = %s AND semester = %s AND section = %s 
                            AND day_of_week = %s AND slot_id = %s AND status = 'Published'
                        """, (department_id, semester, section, day, slot_id))
                        if cursor.fetchone(): class_busy = True

                        if not class_busy:
                            for entry in generated_entries:
                                if entry["dept_id"] == department_id and entry["sem"] == semester and entry[
                                    "sec"] == section and entry["day"] == day and entry["slot_id"] == slot_id:
                                    class_busy = True
                                    break
                        if class_busy: continue

                        # CHECK 4: Teacher Availability
                        cursor.execute("""
                            SELECT available FROM teacher_availability 
                            WHERE teacher_id = %s AND day_of_week = %s AND slot_id = %s
                        """, (teacher_id, day, slot_id))
                        avail = cursor.fetchone()
                        if avail and avail["available"] == False: continue

                        # ALL CHECKS PASSED -> Add to generated_entries
                        generated_entries.append({
                            "dept_id": department_id, "sem": semester, "sec": section,
                            "subject_id": sub["subject_id"], "teacher_id": teacher_id,
                            "room_id": room_id, "slot_id": slot_id, "day": day
                        })
                        scheduled_for_sub += 1
                        scheduled_count += 1
                        room_found = True
                        break  # Move to next slot/day

                    if not room_found and day == days[-1] and scheduled_for_sub < required:
                        # Could not schedule this subject fully
                        unscheduled_sessions.append({
                            "subject": sub["subject_name"],
                            "reason": f"Could not place {required - scheduled_for_sub} sessions. Check teacher availability or room conflicts."
                        })

        # 6. Determine Status
        status = "SUCCESS" if len(unscheduled_sessions) == 0 else "INCOMPLETE"

        # 7. Safe Draft Replacement (Only if SUCCESS or INCOMPLETE)
        # Delete old drafts for this scope
        cursor.execute("""
            DELETE FROM timetable 
            WHERE department_id = %s AND semester = %s AND section = %s AND status = 'Draft'
        """, (department_id, semester, section))

        # Insert new generated entries
        for entry in generated_entries:
            cursor.execute("""
                INSERT INTO timetable (department_id, semester, section, subject_id, teacher_id, room_id, slot_id, day_of_week, status, academic_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Draft', %s)
            """, (entry["dept_id"], entry["sem"], entry["sec"], entry["subject_id"], entry["teacher_id"],
                  entry["room_id"], entry["slot_id"], entry["day"], academic_year))

        conn.commit()

        return {
            "status": status,
            "scheduled_count": scheduled_count,
            "unscheduled_sessions": unscheduled_sessions,
            "message": "Generation complete." if status == "SUCCESS" else "Generation complete with incomplete sessions."
        }

    except Exception as e:
        conn.rollback()
        print("Error generating timetable:", e)
        return {"status": "ERROR", "message": str(e)}
    finally:
        conn.autocommit(True)
        conn.close()


# ==========================================
# NOTICES & EVENTS
# ==========================================

def add_notice_to_db(title, description, user_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notices (title, description, posted_by) VALUES (%s, %s, %s)", (title, description, user_id))
        conn.commit()
        return True, "Notice posted successfully."
    except Exception as e: return False, str(e)
    finally: conn.close()


def add_event_to_db(name, description, event_date, venue):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (event_name, description, event_date, venue) VALUES (%s, %s, %s, %s)", (name, description, event_date, venue))
        conn.commit()
        return True, "Event scheduled successfully."
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_all_events():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM events ORDER BY event_date DESC"
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print("ERROR fetching events for Admin:", e)
        return []
    finally:
        conn.close()


# database/admin_queries.py

def get_all_complaints():
    """Fetches ordinary (non-sensitive) complaints for the Grievance Coordinator (Admin)."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT c.complaint_id, c.category, c.complaint, c.status, c.created_at, 
                   u.full_name AS student_name, d.department_name,
                   c.assigned_to, au.full_name AS assignee_name
            FROM complaints c
            INNER JOIN students s ON c.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            LEFT JOIN users au ON c.assigned_to = au.user_id
            WHERE c.sensitivity = 'Normal'
            ORDER BY c.created_at DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching complaints:", e)
        return []
    finally:
        conn.close()

def get_sensitive_complaints():
    """Fetches sensitive complaints for the restricted queue (Principal)."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Sensitive complaints are only visible in this queue
        sql = """
            SELECT c.complaint_id, c.category, c.complaint, c.status, c.created_at, 
                   u.full_name AS student_name, d.department_name
            FROM complaints c
            INNER JOIN students s ON c.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE c.sensitivity = 'Sensitive'
            ORDER BY c.created_at DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching sensitive complaints:", e)
        return []
    finally:
        conn.close()

def update_complaint_status(complaint_id, new_status, admin_id, reason=None):
    """Updates status and logs history."""
    conn = get_connection()
    if conn is None: return False
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get current status
        cursor.execute("SELECT status FROM complaints WHERE complaint_id = %s", (complaint_id,))
        current = cursor.fetchone()
        if not current:
            conn.rollback()
            return False

        old_status = current["status"]

        # 2. Update Complaint
        resolved_at = "NOW()" if new_status == 'Resolved' else "NULL"
        cursor.execute(f"""
            UPDATE complaints 
            SET status = %s, resolved_at = {resolved_at}
            WHERE complaint_id = %s
        """, (new_status, complaint_id))

        # 3. Log History
        cursor.execute("""
            INSERT INTO complaint_history (complaint_id, changed_by, old_status, new_status, action, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (complaint_id, admin_id, old_status, new_status, "Status Change", reason or f"Status changed to {new_status}"))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.autocommit(True)
        conn.close()

def assign_complaint(complaint_id, assignee_id, assigned_by):
    """Assigns a complaint to a specific user and logs history."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        cursor.execute("SELECT assigned_to FROM complaints WHERE complaint_id = %s", (complaint_id,))
        current = cursor.fetchone()
        if not current:
            conn.rollback()
            return False, "Complaint not found."

        old_assignee = current["assigned_to"]

        cursor.execute("""
            UPDATE complaints 
            SET assigned_to = %s, status = 'Assigned'
            WHERE complaint_id = %s
        """, (assignee_id, complaint_id))

        cursor.execute("""
            INSERT INTO complaint_history (complaint_id, changed_by, old_assignee, new_assignee, old_status, new_status, action, reason)
            VALUES (%s, %s, %s, %s, NULL, 'Assigned', 'Assignment', 'Case assigned')
        """, (complaint_id, assigned_by, old_assignee, assignee_id))

        conn.commit()
        return True, "Complaint assigned successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

def escalate_complaint(complaint_id, reason, escalated_by):
    """Escalates a complaint manually."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        cursor.execute("SELECT status, assigned_to FROM complaints WHERE complaint_id = %s", (complaint_id,))
        current = cursor.fetchone()
        if not current:
            conn.rollback()
            return False, "Complaint not found."

        old_status = current["status"]
        old_assignee = current["assigned_to"]

        # In manual escalation, we change status to 'Escalated'.
        # The escalated_from column keeps track of the previous assignee.
        cursor.execute("""
            UPDATE complaints 
            SET status = 'Escalated', escalated_from = %s, escalation_reason = %s
            WHERE complaint_id = %s
        """, (old_assignee, reason, complaint_id))

        cursor.execute("""
            INSERT INTO complaint_history (complaint_id, changed_by, old_status, new_status, old_assignee, action, reason)
            VALUES (%s, %s, %s, 'Escalated', %s, 'Escalation', %s)
        """, (complaint_id, escalated_by, old_status, old_assignee, reason))

        conn.commit()
        return True, "Complaint escalated successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

def add_complaint_message(complaint_id, sender_id, message, is_internal=False):
    """Adds a message or internal note to a complaint."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO complaint_messages (complaint_id, sender_id, message_text, is_internal_note)
            VALUES (%s, %s, %s, %s)
        """, (complaint_id, sender_id, message, is_internal))
        conn.commit()
        return True, "Message added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ==========================================
# USER MANAGEMENT & REPORTS
# ==========================================

def get_all_system_users():
    """Fetches all users for the Admin management table."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT u.user_id, u.full_name, u.email, u.role, u.status, u.created_at, d.department_name
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.department_id
            ORDER BY u.user_id DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching all users:", e)
        return []
    finally:
        conn.close()


def toggle_user_status_db(user_id, new_status):
    """Activates or deactivates a user account."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = %s WHERE user_id = %s", (new_status, user_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def reset_user_password_db(user_id):
    """Resets password to 'reset@123' (hashed securely)."""
    conn = get_connection()
    if conn is None: return False
    try:
        from utils.password import hash_password
        default_pw = hash_password("reset@123").decode()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (default_pw, user_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_college_analytics():
    """Fetches aggregate data for the Reports Dashboard."""
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()
        data = {}

        cursor.execute("SELECT COUNT(*) as c FROM students")
        data["total_students"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM teachers")
        data["total_teachers"] = cursor.fetchone()["c"]

        cursor.execute("SELECT IFNULL(SUM(amount_paid), 0) as c FROM fee_payments")
        data["fees_collected"] = float(cursor.fetchone()["c"])

        cursor.execute("SELECT COUNT(*) as c FROM complaints WHERE status != 'Resolved'")
        data["pending_complaints"] = cursor.fetchone()["c"]

        # Calculate Pass/Fail based on published results
        cursor.execute("SELECT COUNT(*) as c FROM results WHERE status='Published' AND grade != 'F'")
        data["passed"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM results WHERE status='Published' AND grade = 'F'")
        data["failed"] = cursor.fetchone()["c"]

        return data
    except Exception as e:
        print("Error fetching analytics:", e)
        return {}
    finally:
        conn.close()


def get_admin_command_center_stats(academic_year=None, semester=None, department_id=None):
    """Fetches complex aggregated data for the Admin Command Center Dashboard."""
    conn = get_connection()
    if conn is None:
        return {}

    try:
        cursor = conn.cursor()
        data = {}

        # --- ZONE 1: INSTITUTIONAL (Year-Independent Master Counts) ---
        cursor.execute("SELECT COUNT(*) as c FROM students")
        data["total_students"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM teachers")
        data["total_teachers"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM departments")
        data["total_departments"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM users WHERE status = 'Active'")
        data["active_users"] = cursor.fetchone()["c"]

        # --- ZONE 2: FINANCE (Filtered by academic_year, dept) ---
        fin_query = """
            SELECT 
                IFNULL(SUM(sf.payable_fee), 0) as total_demand,
                IFNULL(SUM(fp.amount_paid), 0) as total_collected
            FROM student_fees sf
            LEFT JOIN fee_payments fp ON sf.student_fee_id = fp.student_fee_id
            LEFT JOIN fee_structure fs ON sf.fee_structure_id = fs.fee_structure_id
            WHERE 1=1
        """
        params = []
        if academic_year:
            fin_query += " AND fs.academic_year = %s"
            params.append(academic_year)
        if department_id:
            fin_query += " AND fs.department_id = %s"
            params.append(department_id)

        cursor.execute(fin_query, tuple(params))
        fin_data = cursor.fetchone()
        data["total_demand"] = float(fin_data["total_demand"])
        data["total_collected"] = float(fin_data["total_collected"])
        data["outstanding"] = data["total_demand"] - data["total_collected"]
        data["collection_percentage"] = round((data["total_collected"] / data["total_demand"] * 100), 2) if data[
                                                                                                                "total_demand"] > 0 else 0

        # --- ZONE 3: ADMIN & APPROVALS ---
        cursor.execute("SELECT status, COUNT(*) as c FROM complaints GROUP BY status")
        comp_data = {row["status"]: row["c"] for row in cursor.fetchall()}
        data["open_complaints"] = comp_data.get("Pending", 0) + comp_data.get("In Progress", 0)

        # SLA Breached
        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM complaints WHERE status != 'Resolved' AND sla_due_at IS NOT NULL AND sla_due_at < NOW()")
            data["sla_breached"] = cursor.fetchone()["c"]
        except:
            data["sla_breached"] = 0

        # Pending Approvals
        cursor.execute("SELECT COUNT(*) as c FROM leave_requests WHERE status = 'Pending'")
        data["pending_leaves"] = cursor.fetchone()["c"]

        # Pending Timetable Drafts
        tt_query = "SELECT COUNT(*) as c FROM timetable WHERE status = 'Draft'"
        tt_params = []
        if department_id:
            tt_query += " AND department_id = %s"
            tt_params.append(department_id)
        if semester:
            tt_query += " AND semester = %s"
            tt_params.append(semester)
        cursor.execute(tt_query, tuple(tt_params))
        data["pending_timetable"] = cursor.fetchone()["c"]

        # --- ZONE 4: ACADEMIC HEALTH ---
        att_query = """
            SELECT IFNULL(AVG(ast.percentage), 0) as avg 
            FROM attendance_summary ast
            JOIN students s ON ast.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            WHERE 1=1
        """
        att_params = []
        if department_id:
            att_query += " AND u.department_id = %s"
            att_params.append(department_id)
        if semester:
            att_query += " AND s.semester = %s"
            att_params.append(semester)
        cursor.execute(att_query, tuple(att_params))
        data["avg_attendance"] = round(float(cursor.fetchone()["avg"]), 2)

        # Results Status
        res_query = "SELECT status, COUNT(*) as c FROM results r JOIN students s ON r.student_id = s.student_id WHERE 1=1"
        res_params = []
        if semester:
            res_query += " AND r.semester = %s"
            res_params.append(semester)
        if department_id:
            res_query += " AND s.user_id IN (SELECT user_id FROM users WHERE department_id = %s)"
            res_params.append(department_id)
        res_query += " GROUP BY status"
        cursor.execute(res_query, tuple(res_params))
        res_data = {row["status"]: row["c"] for row in cursor.fetchall()}
        data["published_results"] = res_data.get("Published", 0)
        data["draft_results"] = res_data.get("Draft", 0)

        # Timetable Conflicts
        conflict_query = """
            SELECT COUNT(*) as c FROM (
                SELECT teacher_id, day_of_week, slot_id 
                FROM timetable WHERE 1=1
        """
        conf_params = []
        if department_id:
            conflict_query += " AND department_id = %s"
            conf_params.append(department_id)
        if semester:
            conflict_query += " AND semester = %s"
            conf_params.append(semester)
        conflict_query += """
                GROUP BY teacher_id, day_of_week, slot_id 
                HAVING COUNT(*) > 1
            ) as dup
        """
        cursor.execute(conflict_query, tuple(conf_params))
        data["tt_conflicts"] = cursor.fetchone()["c"]

        # --- ZONE 5: ANALYTICS (Dept Data) ---
        cursor.execute("""
            SELECT d.department_name, 
                   COUNT(s.student_id) as students,
                   COUNT(t.teacher_id) as teachers
            FROM departments d
            LEFT JOIN users u ON u.department_id = d.department_id
            LEFT JOIN students s ON s.user_id = u.user_id
            LEFT JOIN teachers t ON t.user_id = u.user_id
            GROUP BY d.department_id, d.department_name
        """)
        depts = cursor.fetchall()
        data["dept_labels"] = [d["department_name"] for d in depts]
        data["dept_student_counts"] = [d["students"] for d in depts]
        data["dept_teacher_counts"] = [d["teachers"] for d in depts]
        data["dept_health_table"] = depts

        # --- ZONE 6: SYSTEM & RECENT ACTIVITY ---
        cursor.execute("""
            SELECT al.action, al.log_time, u.full_name 
            FROM audit_logs al 
            LEFT JOIN users u ON al.user_id = u.user_id 
            ORDER BY al.log_time DESC 
            LIMIT 5
        """)
        data["recent_activity"] = cursor.fetchall()

        # Fee Collection Trend (Last 6 Months)
        cursor.execute("""
            SELECT DATE_FORMAT(payment_date, '%%b') as month, SUM(amount_paid) as total
            FROM fee_payments
            WHERE payment_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY YEAR(payment_date), MONTH(payment_date)
            ORDER BY YEAR(payment_date), MONTH(payment_date)
        """)
        trend_data = cursor.fetchall()
        data["fee_trend_labels"] = [t["month"] for t in trend_data]
        data["fee_trend_data"] = [float(t["total"]) for t in trend_data]

        # Department-wise Fee Collection %
        cursor.execute("""
            SELECT d.department_name, 
                   IFNULL(SUM(sf.payable_fee), 0) as demand,
                   IFNULL(SUM(fp.amount_paid), 0) as collected
            FROM departments d
            LEFT JOIN fee_structure fs ON fs.department_id = d.department_id
            LEFT JOIN student_fees sf ON sf.fee_structure_id = fs.fee_structure_id
            LEFT JOIN fee_payments fp ON fp.student_fee_id = sf.student_fee_id
            GROUP BY d.department_name
        """)
        dept_fees = cursor.fetchall()
        data["dept_fee_labels"] = [df["department_name"] for df in dept_fees]
        data["dept_fee_percentages"] = []
        for df in dept_fees:
            demand = float(df["demand"])
            collected = float(df["collected"])
            pct = round((collected / demand) * 100, 2) if demand > 0 else 0.0
            data["dept_fee_percentages"].append(float(pct))

        # --- NEW CHART DATA (Bulletproofed) ---

        # Attendance Brackets Data
        try:
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN avg_pct < 50 THEN 1 ELSE 0 END) as b50,
                    SUM(CASE WHEN avg_pct >= 50 AND avg_pct < 75 THEN 1 ELSE 0 END) as b75,
                    SUM(CASE WHEN avg_pct >= 75 AND avg_pct < 90 THEN 1 ELSE 0 END) as b90,
                    SUM(CASE WHEN avg_pct >= 90 THEN 1 ELSE 0 END) as a90
                FROM (
                    SELECT student_id, AVG(percentage) as avg_pct 
                    FROM attendance_summary 
                    GROUP BY student_id
                ) as student_avgs
            """)
            att_brackets = cursor.fetchone()
            data["att_brackets_labels"] = ["< 50%", "50-75%", "75-90%", "> 90%"]
            data["att_brackets_data"] = [
                int(att_brackets["b50"] or 0),
                int(att_brackets["b75"] or 0),
                int(att_brackets["b90"] or 0),
                int(att_brackets["a90"] or 0)
            ]
        except Exception as e:
            print("Attendance brackets error:", e)
            data["att_brackets_labels"] = ["< 50%", "50-75%", "75-90%", "> 90%"]
            data["att_brackets_data"] = [0, 0, 0, 0]

        # Grade Distribution Data
        try:
            cursor.execute(
                "SELECT grade, COUNT(*) as count FROM results WHERE status = 'Published' AND grade IS NOT NULL AND grade != '' GROUP BY grade")
            grade_data = cursor.fetchall()
            data["grade_labels"] = [g["grade"] for g in grade_data]
            data["grade_counts"] = [int(g["count"]) for g in grade_data]
        except Exception as e:
            print("Grade distribution error:", e)
            data["grade_labels"] = []
            data["grade_counts"] = []

        return data
    except Exception as e:
        print("Error fetching command center stats:", e)
        return {}
    finally:
        conn.close()


# ==========================================
# STUDENT MANAGEMENT (PHASE 2 - ENROLLMENT HISTORY)
# ==========================================

def get_academic_sessions():
    """Fetches academic sessions for dropdowns."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM academic_sessions ORDER BY start_date DESC")
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching sessions:", e)
        return []
    finally:
        conn.close()

def get_student_enrollment_history(student_id):
    """Fetches enrollment history for a student."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT se.enrollment_id, acs.session_name, d.department_name, 
                   se.semester, se.section, se.enrollment_status, se.effective_from, se.effective_to
            FROM student_enrollments se
            LEFT JOIN academic_sessions acs ON se.academic_session_id = acs.academic_session_id
            INNER JOIN departments d ON se.department_id = d.department_id
            WHERE se.student_id = %s
            ORDER BY se.effective_from DESC, se.enrollment_id DESC
        """, (student_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Enrollment history error:", e)
        return []
    finally:
        conn.close()

def promote_student_semester(student_id, new_semester, new_session_id, admin_id):
    """Promotes student to next semester and logs history."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get current active enrollment details
        cursor.execute("""
            SELECT department_id, section FROM student_enrollments 
            WHERE student_id = %s AND enrollment_status = 'Active' LIMIT 1
        """, (student_id,))
        current = cursor.fetchone()
        if not current: return False, "No active enrollment found."

        # 2. Expire current enrollment
        cursor.execute("""
            UPDATE student_enrollments 
            SET enrollment_status = 'Promoted', effective_to = CURDATE() 
            WHERE student_id = %s AND enrollment_status = 'Active'
        """, (student_id,))

        # 3. Insert new enrollment record
        cursor.execute("""
            INSERT INTO student_enrollments 
            (student_id, academic_session_id, department_id, semester, section, enrollment_status, effective_from)
            VALUES (%s, %s, %s, %s, %s, 'Active', CURDATE())
        """, (student_id, new_session_id, current["department_id"], new_semester, current["section"]))

        # 4. Update students table current pointer
        cursor.execute("UPDATE students SET semester = %s WHERE student_id = %s", (new_semester, student_id))

        conn.commit()
        return True, "Student promoted successfully."
    except Exception as e:
        conn.rollback()
        print("Promote error:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

def transfer_student_section(student_id, new_department_id, new_section, admin_id):
    """Transfers student to new dept/section and logs history."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get current active enrollment details
        cursor.execute("""
            SELECT semester, academic_session_id FROM student_enrollments 
            WHERE student_id = %s AND enrollment_status = 'Active' LIMIT 1
        """, (student_id,))
        current = cursor.fetchone()
        if not current: return False, "No active enrollment found."

        # 2. Expire current enrollment
        cursor.execute("""
            UPDATE student_enrollments 
            SET enrollment_status = 'Transferred', effective_to = CURDATE() 
            WHERE student_id = %s AND enrollment_status = 'Active'
        """, (student_id,))

        # 3. Insert new enrollment record
        cursor.execute("""
            INSERT INTO student_enrollments 
            (student_id, academic_session_id, department_id, semester, section, enrollment_status, effective_from)
            VALUES (%s, %s, %s, %s, %s, 'Active', CURDATE())
        """, (student_id, current["academic_session_id"], new_department_id, current["semester"], new_section))

        # 4. Update users & students table current pointers
        cursor.execute("""
            UPDATE users SET department_id = %s 
            WHERE user_id = (SELECT user_id FROM students WHERE student_id = %s)
        """, (new_department_id, student_id))
        cursor.execute("UPDATE students SET section = %s WHERE student_id = %s", (new_section, student_id))

        conn.commit()
        return True, "Student transferred successfully."
    except Exception as e:
        conn.rollback()
        print("Transfer error:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# ==========================================
# TEACHER MANAGEMENT (PHASE 2 - SERVICE HISTORY)
# ==========================================

def get_teacher_service_history(teacher_id):
    """Fetches service history for a teacher."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tsh.history_id, d.department_name, tsh.designation, 
                   tsh.service_status, tsh.effective_from, tsh.effective_to
            FROM teacher_service_history tsh
            INNER JOIN departments d ON tsh.department_id = d.department_id
            WHERE tsh.teacher_id = %s
            ORDER BY tsh.effective_from DESC, tsh.history_id DESC
        """, (teacher_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Teacher history error:", e)
        return []
    finally:
        conn.close()

def promote_teacher_designation(teacher_id, new_designation, effective_from, admin_id):
    """Promotes teacher designation and logs history."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get current active service details
        cursor.execute("""
            SELECT department_id FROM teacher_service_history 
            WHERE teacher_id = %s AND service_status = 'Active' LIMIT 1
        """, (teacher_id,))
        current = cursor.fetchone()
        if not current: return False, "No active service record found."

        # 2. Expire current service record
        cursor.execute("""
            UPDATE teacher_service_history 
            SET service_status = 'Promoted', effective_to = %s 
            WHERE teacher_id = %s AND service_status = 'Active'
        """, (effective_from, teacher_id))

        # 3. Insert new service record
        cursor.execute("""
            INSERT INTO teacher_service_history 
            (teacher_id, department_id, designation, effective_from, service_status)
            VALUES (%s, %s, %s, %s, 'Active')
        """, (teacher_id, current["department_id"], new_designation, effective_from))

        # 4. Update teachers table current pointer
        cursor.execute("UPDATE teachers SET designation = %s WHERE teacher_id = %s", (new_designation, teacher_id))

        conn.commit()
        return True, "Teacher promoted successfully."
    except Exception as e:
        conn.rollback()
        print("Teacher promote error:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

def transfer_teacher_department(teacher_id, new_department_id, effective_from, admin_id):
    """Transfers teacher to new department and logs history."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get current active service details
        cursor.execute("""
            SELECT designation FROM teacher_service_history 
            WHERE teacher_id = %s AND service_status = 'Active' LIMIT 1
        """, (teacher_id,))
        current = cursor.fetchone()
        if not current: return False, "No active service record found."

        # 2. Expire current service record
        cursor.execute("""
            UPDATE teacher_service_history 
            SET service_status = 'Transferred', effective_to = %s 
            WHERE teacher_id = %s AND service_status = 'Active'
        """, (effective_from, teacher_id))

        # 3. Insert new service record
        cursor.execute("""
            INSERT INTO teacher_service_history 
            (teacher_id, department_id, designation, effective_from, service_status)
            VALUES (%s, %s, %s, %s, 'Active')
        """, (teacher_id, new_department_id, current["designation"], effective_from))

        # 4. Update users & teachers table current pointers
        cursor.execute("""
            UPDATE users SET department_id = %s 
            WHERE user_id = (SELECT user_id FROM teachers WHERE teacher_id = %s)
        """, (new_department_id, teacher_id))

        conn.commit()
        return True, "Teacher transferred successfully."
    except Exception as e:
        conn.rollback()
        print("Teacher transfer error:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

# ==========================================
# SUBJECT MANAGEMENT (PHASE 2 - ASSIGNMENT HISTORY)
# ==========================================

def get_subject_assignment_history(subject_id):
    """Fetches faculty assignment history for a subject."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sa.assignment_id, u.full_name AS teacher_name, 
                   sa.effective_from, sa.effective_to, sa.assignment_status, sa.created_at
            FROM subject_assignments sa
            INNER JOIN teachers t ON sa.teacher_id = t.teacher_id
            INNER JOIN users u ON t.user_id = u.user_id
            WHERE sa.subject_id = %s
            ORDER BY sa.effective_from DESC, sa.assignment_id DESC
        """, (subject_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Subject assignment history error:", e)
        return []
    finally:
        conn.close()

def assign_teacher_to_subject(subject_id, new_teacher_id, effective_from, admin_id):
    """Assigns a new teacher, expires the old one, and updates the current pointer."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Expire current active assignment
        cursor.execute("""
            UPDATE subject_assignments 
            SET assignment_status = 'Replaced', effective_to = %s 
            WHERE subject_id = %s AND assignment_status = 'Active'
        """, (effective_from, subject_id))

        # 2. Insert new assignment record
        cursor.execute("""
            INSERT INTO subject_assignments 
            (subject_id, teacher_id, effective_from, assignment_status, assigned_by)
            VALUES (%s, %s, %s, 'Active', %s)
        """, (subject_id, new_teacher_id, effective_from, admin_id))

        # 3. Update subjects table current pointer (for backward compatibility)
        cursor.execute("UPDATE subjects SET teacher_id = %s WHERE subject_id = %s", (new_teacher_id, subject_id))

        conn.commit()
        return True, "Teacher assigned successfully."
    except Exception as e:
        conn.rollback()
        print("Error assigning teacher to subject:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# ==========================================
# TIMETABLE MANAGEMENT (PHASE 3 - LIFECYCLE & APPROVAL)
# ==========================================

def get_timetable_status(dept_id, sem, sec, year="2024-25"):
    """Fetches the current lifecycle status of a timetable for a specific scope."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # We fetch the status of the first entry, assuming all entries for a scope share the same status
        cursor.execute("""
            SELECT status FROM timetable 
            WHERE department_id = %s AND semester = %s AND section = %s AND academic_year = %s 
            LIMIT 1
        """, (dept_id, sem, sec, year))
        result = cursor.fetchone()
        return result["status"] if result else None
    except Exception as e:
        print("Error fetching timetable status:", e)
        return None
    finally:
        conn.close()


def update_timetable_status(dept_id, sem, sec, new_status, expected_current_status, year="2024-25"):
    """Updates the status of all timetable entries for a scope, only if they match the expected current status."""
    conn = get_connection()
    if conn is None: return False, "DB Connection failed."
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE timetable 
            SET status = %s 
            WHERE department_id = %s AND semester = %s AND section = %s AND academic_year = %s AND status = %s
        """, (new_status, dept_id, sem, sec, year, expected_current_status))

        if cursor.rowcount == 0:
            return False, f"No '{expected_current_status}' timetable found for this scope. Please refresh."

        conn.commit()
        return True, f"Timetable status updated to '{new_status}'."
    except Exception as e:
        print("Error updating timetable status:", e)
        return False, str(e)
    finally:
        conn.close()


# ==========================================
# RESULT MANAGEMENT (PHASE 3 - APPROVAL)
# ==========================================

def submit_results_for_principal(semester):
    """Submits draft results to Principal for approval."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE results 
            SET approval_status = 'Pending Principal' 
            WHERE semester = %s AND status = 'Draft' AND approval_status = 'Draft'
        """, (semester,))

        if cursor.rowcount == 0:
            return False, "No draft results found or already submitted."

        conn.commit()
        return True, "Results submitted to Principal for approval."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# MODIFY the existing publish_semester_results function
def publish_semester_results(semester):
    """Publishes APPROVED results so students can view them."""
    conn = get_connection()
    if conn is None: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        # FIX: Can only publish if Principal has Approved
        cursor.execute("""
            UPDATE results 
            SET status = 'Published', published_at = NOW() 
            WHERE semester = %s AND approval_status = 'Approved'
        """, (semester,))

        if cursor.rowcount == 0:
            return False, "Cannot publish. Ensure results are approved by Principal first."

        conn.commit()
        return True, f"Semester {semester} results are now Published."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ==========================================
# RESULT MANAGEMENT (PHASE 4 - CONTROLLED PUBLICATION)
# ==========================================

def retract_published_results(semester):
    """Retracts a published result back to Draft for controlled corrections."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE results 
            SET status = 'Draft', approval_status = 'Draft', published_at = NULL
            WHERE semester = %s AND status = 'Published'
        """, (semester,))

        if cursor.rowcount == 0:
            return False, "No published results found for this semester."

        conn.commit()
        return True, "Results retracted successfully. They are now back in Draft mode for correction."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_result_status_summary(semester):
    """Fetches the approval status for the UI."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT approval_status, COUNT(*) as c 
            FROM results 
            WHERE semester = %s 
            GROUP BY approval_status
        """, (semester,))
        return cursor.fetchall()
    except Exception as e:
        return None
    finally:
        conn.close()


# ==========================================
# PHASE 5: ADVANCED EXAMINATION OPERATIONS
# ==========================================

def get_revaluation_requests():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.request_id, r.semester, r.reason, r.status, r.requested_at,
                   u.full_name AS student_name, s.subject_name
            FROM revaluation_requests r
            INNER JOIN students st ON r.student_id = st.student_id
            INNER JOIN users u ON st.user_id = u.user_id
            INNER JOIN subjects s ON r.subject_id = s.subject_id
            ORDER BY r.requested_at DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Reval fetch error:", e)
        return []
    finally:
        conn.close()


def process_revaluation(request_id, new_marks, admin_id):
    """Processes revaluation, updates marks, preserves old result, and recalculates."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get request details
        cursor.execute("SELECT student_id, semester, subject_id FROM revaluation_requests WHERE request_id = %s",
                       (request_id,))
        req = cursor.fetchone()
        if not req: return False, "Request not found."

        # 2. Update marks in marks table
        cursor.execute("""
            UPDATE marks SET obtained_marks = %s, submission_status = 'Verified'
            WHERE student_id = %s AND subject_id = %s
        """, (new_marks, req["student_id"], req["subject_id"]))

        # 3. Fetch CURRENT result to save in history BEFORE recalculating
        cursor.execute("SELECT * FROM results WHERE student_id = %s AND semester = %s",
                       (req["student_id"], req["semester"]))
        old_res = cursor.fetchone()
        if old_res:
            cursor.execute("""
                INSERT INTO result_history (student_id, semester, total_marks, obtained_marks, percentage, sgpa, cgpa, grade, changed_by, change_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Revaluation Update')
            """, (
                old_res["student_id"], old_res["semester"], old_res["total_marks"], old_res["obtained_marks"],
                old_res["percentage"], old_res["sgpa"], old_res["cgpa"], old_res["grade"], admin_id
            ))

        # 4. Recalculate result (Fetch all verified marks for this student/sem)
        cursor.execute("""
            SELECT s.subject_id, s.credits, m.maximum_marks, m.obtained_marks
            FROM marks m
            INNER JOIN subjects s ON m.subject_id = s.subject_id
            WHERE m.student_id = %s AND s.semester = %s AND m.submission_status = 'Verified'
        """, (req["student_id"], req["semester"]))
        marks = cursor.fetchall()

        if not marks:
            conn.rollback()
            return False, "No verified marks found to recalculate."

        total_max = sum(m["maximum_marks"] for m in marks)
        total_obt = sum(m["obtained_marks"] for m in marks)
        overall_pct = round((total_obt / total_max) * 100, 2) if total_max > 0 else 0

        sgpa_data = []
        subject_grades = []
        for m in marks:
            sub_pct = (m["obtained_marks"] / m["maximum_marks"]) * 100 if m["maximum_marks"] > 0 else 0
            sub_grade = calculate_grade(sub_pct)
            subject_grades.append(sub_grade)
            sgpa_data.append({"credits": m["credits"], "grade_point": get_grade_point(sub_grade)})

        sgpa = calculate_sgpa(sgpa_data)
        final_grade = determine_final_result(subject_grades, overall_pct)

        # 5. Update the results table (Revert to Draft for re-approval)
        cursor.execute("""
            UPDATE results 
            SET total_marks=%s, obtained_marks=%s, percentage=%s, sgpa=%s, cgpa=%s, grade=%s, 
                status='Draft', approval_status='Draft', published_at=NULL
            WHERE student_id = %s AND semester = %s
        """, (total_max, total_obt, overall_pct, sgpa, sgpa, final_grade, req["student_id"], req["semester"]))

        # 6. Update request status
        cursor.execute("UPDATE revaluation_requests SET status = 'Completed' WHERE request_id = %s", (request_id,))

        conn.commit()
        return True, "Revaluation processed. Result updated and moved to Draft for re-approval."
    except Exception as e:
        conn.rollback()
        print("Reval process error:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# ==========================================
# NOTICES & EVENTS (PHASE 2 - WORKFLOW & TARGETING)
# ==========================================

# Category to Approver Role Mapping
CATEGORY_APPROVERS = {
    "Examination": "Principal",
    "Academic": "HOD",
    "Administrative": "Admin",  # Admin can self-approve/publish
    "General": "Admin",
    "Holiday": "Principal"
}


def create_notice(form_data, user_role, user_id, attachment_path=None):
    """Creates a notice with appropriate initial status based on category and handles attachments."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        category = form_data.get("category", "General")

        # Determine initial status based on approver config
        approver_role = CATEGORY_APPROVERS.get(category, "Admin")
        if approver_role == user_role:
            status = "Published"
            approved_by = user_id
        else:
            status = "Pending"
            approved_by = None

        cursor.execute("""
            INSERT INTO notices (title, description, posted_by, category, status, target_audience, target_department_id, publish_at, expire_at, approved_by, attachment_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            form_data.get("title"), form_data.get("description"), user_id, category, status,
            form_data.get("target_audience", "All"),
            form_data.get("target_department_id") or None,
            form_data.get("publish_at") or None,
            form_data.get("expire_at") or None,
            approved_by,
            attachment_path  # Save the path
        ))
        conn.commit()
        return True, f"Notice created successfully with status: {status}"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_notices_for_approval(approver_role):
    """Fetches pending notices for a specific approver role."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Fetch notices where the category matches the approver's role
        categories = [cat for cat, role in CATEGORY_APPROVERS.items() if role == approver_role]
        if not categories:
            return []

        placeholders = ",".join(["%s"] * len(categories))
        sql = f"""
            SELECT n.notice_id, n.title, n.category, n.description, n.posted_on, u.full_name AS creator_name
            FROM notices n
            INNER JOIN users u ON n.posted_by = u.user_id
            WHERE n.status = 'Pending' AND n.category IN ({placeholders})
            ORDER BY n.posted_on DESC
        """
        cursor.execute(sql, tuple(categories))
        return cursor.fetchall()
    except Exception as e:
        print("Approval fetch error:", e)
        return []
    finally:
        conn.close()


def process_notice_approval(notice_id, action, approver_id, remarks=None):
    """Approves or Rejects a notice."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()

        if action == "Approved":
            # Check if it should be auto-published or scheduled
            cursor.execute("SELECT publish_at FROM notices WHERE notice_id = %s", (notice_id,))
            n = cursor.fetchone()
            new_status = "Published" if (not n["publish_at"] or n["publish_at"] <= datetime.now()) else "Approved"

            cursor.execute("""
                UPDATE notices 
                SET status = %s, approved_by = %s, approval_remarks = %s 
                WHERE notice_id = %s AND status = 'Pending'
            """, (new_status, approver_id, "Approved", notice_id))

        elif action == "Rejected":
            cursor.execute("""
                UPDATE notices 
                SET status = 'Draft', approved_by = %s, approval_remarks = %s 
                WHERE notice_id = %s AND status = 'Pending'
            """, (approver_id, remarks, notice_id))
        else:
            return False, "Invalid action."

        if cursor.rowcount == 0:
            return False, "Notice not found or not pending."

        conn.commit()
        return True, f"Notice {action} successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_all_notices():
    """Fetches all notices for Admin view (all statuses)."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT n.*, u.full_name AS creator_name 
            FROM notices n 
            INNER JOIN users u ON n.posted_by = u.user_id
            ORDER BY n.posted_on DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_user_notices(user_role, user_dept_id):
    """Fetches published notices filtered by audience targeting and date validity."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT * FROM notices
            WHERE status = 'Published'
            AND (publish_at IS NULL OR publish_at <= NOW())
            AND (expire_at IS NULL OR expire_at > NOW())
            AND (
                target_audience = 'All' OR
                (target_audience = 'Students' AND %s = 'Student') OR
                (target_audience = 'Teachers' AND %s = 'Teacher') OR
                (target_audience = 'Department' AND target_department_id = %s)
            )
            ORDER BY posted_on DESC
        """
        cursor.execute(sql, (user_role, user_role, user_dept_id))
        return cursor.fetchall()
    except Exception as e:
        print("User notices error:", e)
        return []
    finally:
        conn.close()

# ==========================================
# EVENTS MANAGEMENT (PHASE 6)
# ==========================================

def create_event(form_data, user_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (event_name, description, event_date, venue, status, target_audience, target_department_id, organizer)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            form_data.get("event_name"), form_data.get("description"), form_data.get("event_date"),
            form_data.get("venue"), "Published", # Admin directly publishes events for now
            form_data.get("target_audience", "All"),
            form_data.get("target_department_id") or None,
            form_data.get("organizer")
        ))
        conn.commit()
        return True, "Event created successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_user_events(user_role, user_dept_id):
    """Fetches published upcoming events filtered by audience targeting."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT * FROM events
            WHERE status = 'Published' AND event_date >= CURDATE()
            AND (
                target_audience = 'All' OR
                (target_audience = 'Students' AND %s = 'Student') OR
                (target_audience = 'Teachers' AND %s = 'Teacher') OR
                (target_audience = 'Department' AND target_department_id = %s)
            )
            ORDER BY event_date ASC
        """
        cursor.execute(sql, (user_role, user_role, user_dept_id))
        return cursor.fetchall()
    except Exception as e:
        print("User events error:", e)
        return []
    finally:
        conn.close()

# ==========================================
# USER MANAGEMENT (PHASE 2 - SECURE RBAC)
# ==========================================


def _insert_security_audit(
    cursor,
    actor_id,
    target_user_id,
    action,
    old_value=None,
    new_value=None,
    reason=None,
):
    """Insert an audit event using the caller's transaction."""
    cursor.execute(
        """
        INSERT INTO security_audit
            (actor_id, target_user_id, action, old_value, new_value, reason)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (actor_id, target_user_id, action, old_value, new_value, reason),
    )


def toggle_user_status_secure(target_user_id, current_status, actor_id):
    """Toggle account status safely and audit it atomically."""
    conn = get_connection()
    if conn is None:
        return False, "Unable to update user status. Please try again."

    try:
        conn.begin()
        cursor = conn.cursor()

        # Serialize account-security changes by locking users rows.
        cursor.execute(
            "SELECT user_id, role, status FROM users ORDER BY user_id FOR UPDATE"
        )
        users = cursor.fetchall()
        users_by_id = {int(row["user_id"]): row for row in users}

        target_id = int(target_user_id)
        actor = int(actor_id)

        if target_id == actor:
            conn.rollback()
            return False, "You cannot change your own account status."

        target = users_by_id.get(target_id)
        if target is None:
            conn.rollback()
            return False, "User not found."

        old_status = target["status"]
        if old_status not in ("Active", "Inactive"):
            conn.rollback()
            return False, "Invalid account status in database."

        new_status = "Inactive" if old_status == "Active" else "Active"

        if old_status == "Active" and target["role"] == "Admin":
            active_admins = sum(
                1 for row in users
                if row["role"] == "Admin" and row["status"] == "Active"
            )
            if active_admins <= 1:
                conn.rollback()
                return False, "Cannot deactivate the last active Admin."

        cursor.execute(
            """
            UPDATE users
            SET status = %s, session_version = session_version + 1
            WHERE user_id = %s
            """,
            (new_status, target_id),
        )

        if cursor.rowcount != 1:
            raise RuntimeError("Expected exactly one user status update.")

        _insert_security_audit(
            cursor,
            actor,
            target_id,
            "Status Change",
            old_status,
            new_status,
            "Account status toggled",
        )

        conn.commit()
        return True, (
            f"User status updated to {new_status}. "
            "Existing sessions have been invalidated."
        )

    except Exception:
        conn.rollback()
        # Log technical details server-side if needed; don't expose them to clients.
        print("Secure user-status update failed.")
        return False, "Unable to update user status. Please try again."
    finally:
        conn.close()


def assign_role_secure(target_user_id, new_role, actor_id):
    """Assign an allowed role and audit it atomically."""
    allowed_roles = {"Student", "Teacher", "HOD", "Principal", "Admin", "Staff"}

    if not isinstance(new_role, str) or new_role not in allowed_roles:
        return False, "Invalid role."

    conn = get_connection()
    if conn is None:
        return False, "Unable to update user role. Please try again."

    try:
        conn.begin()
        cursor = conn.cursor()

        # Use the same locking order as status changes.
        cursor.execute(
            "SELECT user_id, role FROM users ORDER BY user_id FOR UPDATE"
        )
        users = cursor.fetchall()
        users_by_id = {int(row["user_id"]): row for row in users}

        target_id = int(target_user_id)
        actor = int(actor_id)

        if target_id == actor:
            conn.rollback()
            return False, "You cannot change your own role."

        target = users_by_id.get(target_id)
        if target is None:
            conn.rollback()
            return False, "User not found."

        old_role = target["role"]
        if old_role == new_role:
            conn.rollback()
            return False, "User already has this role."

        cursor.execute(
            """
            UPDATE users
            SET role = %s, session_version = session_version + 1
            WHERE user_id = %s
            """,
            (new_role, target_id),
        )

        if cursor.rowcount != 1:
            raise RuntimeError("Expected exactly one user role update.")

        _insert_security_audit(
            cursor,
            actor,
            target_id,
            "Role Assignment",
            old_role,
            new_role,
            "Role changed by authorized administrator",
        )

        conn.commit()
        return True, f"Role updated to {new_role}. Existing sessions invalidated."

    except Exception:
        conn.rollback()
        print("Secure user-role update failed.")
        return False, "Unable to update user role. Please try again."
    finally:
        conn.close()


def log_security_audit(
    actor_id,
    target_user_id,
    action,
    old_value=None,
    new_value=None,
    reason=None,
):
    """
    Standalone audit helper.
    Security-sensitive mutations should instead call _insert_security_audit()
    inside their own transaction.
    """
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Database unavailable; audit event was not recorded.")

    try:
        conn.begin()
        cursor = conn.cursor()
        _insert_security_audit(
            cursor,
            actor_id,
            target_user_id,
            action,
            old_value,
            new_value,
            reason,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



def initiate_password_reset(target_user_id, actor_id):
    """Initiates a secure password reset with a temporary token."""
    conn = get_connection()
    if conn is None: return False, "DB Error", None
    try:
        # Generate a secure temporary token (valid for 1 hour)
        temp_token = str(uuid.uuid4().hex)
        expiry = datetime.now() + timedelta(hours=1)

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET password_reset_token = %s, 
                reset_token_expiry = %s,
                force_password_change = TRUE,
                session_version = session_version + 1
            WHERE user_id = %s
        """, (temp_token, expiry, target_user_id))

        log_security_audit(actor_id, target_user_id, "Password Reset Initiated", None, None,
                           "Temporary token generated")
        conn.commit()

        # In a real system, this token would be sent via email.
        # For now, we return it to display to the Admin.
        return True, "Password reset token generated. User must change password on next login.", temp_token
    except Exception as e:
        return False, str(e), None
    finally:
        conn.close()



# ==========================================
# REPORTS (PHASE 2 - FACULTY & ACADEMIC)
# ==========================================

def get_faculty_directory_report(department_id=None):
    """Fetches faculty data for the directory report."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT t.teacher_id, u.full_name, u.email, d.department_name, 
                   t.designation, t.qualification, t.experience
            FROM teachers t
            INNER JOIN users u ON t.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE 1=1
        """
        params = []
        if department_id:
            sql += " AND u.department_id = %s"
            params.append(department_id)

        sql += " ORDER BY u.full_name"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        print("Faculty report error:", e)
        return []
    finally:
        conn.close()


def get_low_attendance_report(department_id=None, semester=None):
    """Fetches low attendance data for academic report."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT u.full_name AS student_name, ast.subject_name, ast.percentage, d.department_name, s.semester
            FROM attendance_summary ast
            INNER JOIN students s ON ast.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE ast.percentage < 75
        """
        params = []
        if department_id:
            sql += " AND u.department_id = %s"
            params.append(department_id)
        if semester:
            sql += " AND s.semester = %s"
            params.append(semester)

        sql += " ORDER BY ast.percentage ASC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        print("Low attendance report error:", e)
        return []
    finally:
        conn.close()


# ==========================================
# REPORTS (PHASE 4 - FINANCE & AUDIT)
# ==========================================

def get_fee_collection_summary():
    """Fetches fee collection summary grouped by date and mode."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DATE(payment_date) as date, payment_mode, COUNT(*) as count, SUM(amount_paid) as total
            FROM fee_payments
            WHERE amount_paid > 0
            GROUP BY DATE(payment_date), payment_mode
            ORDER BY DATE(payment_date) DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Fee collection summary error:", e)
        return []
    finally:
        conn.close()

def get_outstanding_fees_summary():
    """Fetches students with outstanding balances."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.full_name, s.enrollment_no, d.department_name, sf.payable_fee, 
                   (sf.payable_fee - IFNULL((SELECT SUM(amount_paid) FROM fee_payments WHERE student_fee_id = sf.student_fee_id), 0)) as balance
            FROM student_fees sf
            INNER JOIN students s ON sf.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            HAVING balance > 0
            ORDER BY balance DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Outstanding summary error:", e)
        return []
    finally:
        conn.close()

def get_login_history_report():
    """Fetches recent login history."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT lh.login_time, u.full_name, u.role, lh.ip_address, lh.device
            FROM login_history lh
            INNER JOIN users u ON lh.user_id = u.user_id
            ORDER BY lh.login_time DESC
            LIMIT 100
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Login history report error:", e)
        return []
    finally:
        conn.close()

def get_activity_log_report():
    """Fetches recent audit logs."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT al.log_time, u.full_name, al.action
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.user_id
            ORDER BY al.log_time DESC
            LIMIT 100
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Activity log report error:", e)
        return []
    finally:
        conn.close()


def get_refund_register():
    """Fetches the refund & reversal register for the Finance Reports page.

    Returns refunds with student names and original receipt numbers.
    Read-only — no mutations. Used by GET /admin/reports/finance.
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.refund_id, r.refund_amount, r.reason, r.processed_at,
                   u.full_name AS student_name,
                   fp.receipt_number AS original_receipt
            FROM refunds r
            INNER JOIN fee_payments fp ON r.payment_id = fp.payment_id
            INNER JOIN student_fees sf ON r.student_fee_id = sf.student_fee_id
            INNER JOIN students s ON sf.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            ORDER BY r.processed_at DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Refund register error:", e)
        return []
    finally:
        conn.close()