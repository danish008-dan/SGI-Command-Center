# services/hod_service.py
from database.connection import get_connection

class HODService:
    """Service layer for HOD-specific authorization and department scoping."""

    @staticmethod
    def get_hod_active_department_id(user_id):
        """
        Resolves the active department ID for the authenticated HOD
        using the authoritative department_hod_assignments table.
        """
        conn = get_connection()
        if conn is None: return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT department_id FROM department_hod_assignments 
                WHERE user_id = %s AND status = 'Active'
                LIMIT 1
            """, (user_id,))
            result = cursor.fetchone()
            return result["department_id"] if result else None
        except Exception as e:
            print("Error resolving HOD department:", e)
            return None
        finally:
            conn.close()

    @staticmethod
    def verify_student_in_department(student_id, dept_id):
        """IDOR Protection: Verifies that a student belongs to the HOD's active department."""
        conn = get_connection()
        if conn is None: return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM students s 
                INNER JOIN users u ON s.user_id = u.user_id 
                WHERE s.student_id = %s AND u.department_id = %s
            """, (student_id, dept_id))
            return cursor.fetchone() is not None
        except Exception as e:
            print("Error verifying student department scope:", e)
            return False
        finally:
            conn.close()

    @staticmethod
    def verify_faculty_in_department(teacher_id, dept_id):
        """IDOR Protection: Verifies that a faculty member belongs to the HOD's active department."""
        conn = get_connection()
        if conn is None: return False
        try:
            cursor = conn.cursor()
            # Faculty can be linked via subjects table or direct users.department_id.
            # Using direct department_id is safest for read-only view.
            cursor.execute("""
                SELECT 1 FROM teachers t 
                INNER JOIN users u ON t.user_id = u.user_id 
                WHERE t.teacher_id = %s AND u.department_id = %s
            """, (teacher_id, dept_id))
            return cursor.fetchone() is not None
        except Exception as e:
            print("Error verifying faculty department scope:", e)
            return False
        finally:
            conn.close()

    @staticmethod
    def verify_subject_in_department(subject_id, dept_id):
        """IDOR Protection: Verifies that a subject belongs to the HOD's active department."""
        conn = get_connection()
        assigned_teacher_id = None
        conn = get_connection()
        if conn is None: return False, None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT department_id, teacher_id FROM subjects WHERE subject_id = %s", (subject_id,))
            result = cursor.fetchone()
            if result and result["department_id"] == dept_id:
                return True, result["teacher_id"]
            return False, None
        except Exception as e:
            print("Error verifying subject department scope:", e)
            return False, None
        finally:
            if conn: conn.close()