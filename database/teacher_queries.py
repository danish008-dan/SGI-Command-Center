# database/teacher_queries.py
from datetime import datetime
from database.connection import get_connection
from config import ATTENDANCE_THRESHOLD


def get_teacher_id_from_user(user_id):
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT teacher_id FROM teachers WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result["teacher_id"] if result else None
    except Exception as e:
        print("Error getting teacher_id:", e)
        return None
    finally:
        conn.close()


# ==========================================
# PHASE 1: SCOPE & AUTHORIZATION
# ==========================================

def verify_teacher_subject_scope(teacher_id, subject_id):
    """Verifies that a subject is actually assigned to the teacher."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM subjects WHERE subject_id = %s AND teacher_id = %s AND status = 'Active'",
                       (subject_id, teacher_id))
        return cursor.fetchone() is not None
    except Exception:
        return False
    finally:
        conn.close()


def verify_student_in_teacher_scope(teacher_id, student_id):
    """Verifies that a student belongs to a class/section that the teacher is assigned to."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        # Checks if student's dept, semester, and section match ANY subject taught by this teacher
        cursor.execute("""
            SELECT 1 FROM students s
            INNER JOIN users u ON s.user_id = u.user_id
            INNER JOIN subjects sub ON u.department_id = sub.department_id AND s.semester = sub.semester AND (s.section = sub.section OR s.section IS NULL)
            WHERE sub.teacher_id = %s AND s.student_id = %s
        """, (teacher_id, student_id))
        return cursor.fetchone() is not None
    except Exception:
        return False
    finally:
        conn.close()


# ==========================================
# PHASE 1: ACADEMIC DIRECTORY
# ==========================================

def get_subjects_for_teacher(teacher_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT subject_id, subject_code, subject_name, semester, section, subject_type, credits, classes_per_week
            FROM subjects 
            WHERE teacher_id = %s AND status = 'Active'
            ORDER BY semester, subject_name
        """
        cursor.execute(sql, (teacher_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_sections_for_teacher_subject(teacher_id, subject_id):
    """Returns distinct sections the teacher handles for a specific subject."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT section 
            FROM subjects 
            WHERE teacher_id = %s AND subject_id = %s AND section IS NOT NULL
        """, (teacher_id, subject_id))
        return [row["section"] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def get_students_for_attendance(teacher_id, subject_id, section):
    """Gets students matching the subject's semester, dept, AND specific section."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT s.student_id, u.full_name AS student_name, s.enrollment_no, s.semester
            FROM students s
            INNER JOIN users u ON s.user_id = u.user_id
            INNER JOIN subjects sub ON u.department_id = sub.department_id AND s.semester = sub.semester
            WHERE sub.subject_id = %s AND sub.teacher_id = %s AND s.section = %s AND u.status = 'Active'
            ORDER BY u.full_name
        """
        cursor.execute(sql, (subject_id, teacher_id, section))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_student_academic_profile_for_teacher(teacher_id, student_id):
    """Fetches read-only academic profile strictly scoped to the teacher's subjects."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()

        # Basic student info
        cursor.execute("""
            SELECT u.full_name, u.email, s.enrollment_no, s.semester, s.section, d.department_name
            FROM students s
            INNER JOIN users u ON s.user_id = u.user_id
            INNER JOIN departments d ON u.department_id = d.department_id
            WHERE s.student_id = %s
        """, (student_id,))
        profile = cursor.fetchone()
        if not profile: return None

        # Attendance only for subjects taught by THIS teacher
        cursor.execute("""
            SELECT sub.subject_name, 
                   COUNT(a.attendance_id) as total_classes,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present,
                   ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.attendance_id)) * 100, 2) as percentage
            FROM attendance a
            INNER JOIN subjects sub ON a.subject_id = sub.subject_id
            WHERE a.student_id = %s AND sub.teacher_id = %s
            GROUP BY sub.subject_id
        """, (student_id, teacher_id))
        profile["attendance"] = cursor.fetchall()

        # Marks only for subjects taught by THIS teacher
        cursor.execute("""
            SELECT sub.subject_name, m.exam_type, m.maximum_marks, m.obtained_marks, m.submission_status
            FROM marks m
            INNER JOIN subjects sub ON m.subject_id = sub.subject_id
            WHERE m.student_id = %s AND sub.teacher_id = %s
            ORDER BY sub.subject_name
        """, (student_id, teacher_id))
        profile["marks"] = cursor.fetchall()

        return profile
    except Exception:
        return None
    finally:
        conn.close()


# ==========================================
# PHASE 1: ATTENDANCE & ANALYTICS
# ==========================================

def get_existing_attendance(subject_id, teacher_id, section, attendance_date):
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()
        sql = """
            SELECT a.student_id, a.status 
            FROM attendance a
            INNER JOIN students s ON a.student_id = s.student_id
            WHERE a.subject_id = %s AND a.teacher_id = %s AND s.section = %s AND a.attendance_date = %s
        """
        cursor.execute(sql, (subject_id, teacher_id, section, attendance_date))
        return {row["student_id"]: row["status"] for row in cursor.fetchall()}
    except Exception:
        return {}
    finally:
        conn.close()


def save_attendance_record(student_id, subject_id, teacher_id, attendance_date, status):
    conn = get_connection()
    if conn is None: return "Database connection failed."
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status = %s, teacher_id = %s
        """
        cursor.execute(sql, (student_id, subject_id, teacher_id, attendance_date, status, status, teacher_id))
        conn.commit()
        return None
    except Exception as e:
        return str(e)
    finally:
        conn.close()


def get_teacher_attendance_history(teacher_id, subject_id=None):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT a.attendance_date, sub.subject_name, s.section,
                   COUNT(a.attendance_id) as total,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present,
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent
            FROM attendance a
            INNER JOIN subjects sub ON a.subject_id = sub.subject_id
            INNER JOIN students s ON a.student_id = s.student_id
            WHERE sub.teacher_id = %s
        """
        params = [teacher_id]
        if subject_id:
            sql += " AND a.subject_id = %s"
            params.append(subject_id)

        sql += " GROUP BY a.attendance_date, a.subject_id, s.section ORDER BY a.attendance_date DESC LIMIT 30"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_teacher_low_attendance_students(teacher_id):
    """Finds students in teacher's classes below the centralized 75% threshold."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT u.full_name, s.enrollment_no, sub.subject_name, s.section,
                   ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.attendance_id)) * 100, 2) as percentage
            FROM attendance a
            INNER JOIN students s ON a.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            INNER JOIN subjects sub ON a.subject_id = sub.subject_id
            WHERE sub.teacher_id = %s
            GROUP BY a.student_id, a.subject_id
            HAVING percentage < %s
            ORDER BY percentage ASC
        """
        cursor.execute(sql, (teacher_id, ATTENDANCE_THRESHOLD))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


# ==========================================
# PHASE 1: MARKS & VALIDATION
# ==========================================

def get_existing_marks(subject_id, teacher_id, section, exam_type):
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()
        sql = """
            SELECT m.student_id, m.obtained_marks, m.remarks 
            FROM marks m
            INNER JOIN students s ON m.student_id = s.student_id
            WHERE m.subject_id = %s AND m.teacher_id = %s AND m.exam_type = %s AND s.section = %s
        """
        cursor.execute(sql, (subject_id, teacher_id, exam_type, section))
        return {row["student_id"]: row for row in cursor.fetchall()}
    except Exception:
        return {}
    finally:
        conn.close()


def save_marks_record(student_id, subject_id, teacher_id, exam_type, max_marks, obtained_marks, remarks):
    conn = get_connection()
    if conn is None: return "Database connection failed."
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO marks (student_id, subject_id, teacher_id, exam_type, maximum_marks, obtained_marks, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            obtained_marks = VALUES(obtained_marks), 
            remarks = VALUES(remarks),
            maximum_marks = VALUES(maximum_marks),
            teacher_id = VALUES(teacher_id)
        """
        cursor.execute(sql, (student_id, subject_id, teacher_id, exam_type, max_marks, obtained_marks,
                             remarks if remarks else None))
        conn.commit()
        return None
    except Exception as e:
        return str(e)
    finally:
        conn.close()


def submit_marks_for_verification(subject_id, exam_type, teacher_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE marks 
            SET submission_status = 'Submitted'
            WHERE subject_id = %s AND exam_type = %s AND teacher_id = %s AND submission_status = 'Draft'
        """, (subject_id, exam_type, teacher_id))
        conn.commit()
        return True, "Marks submitted for HOD verification."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ==========================================
# PHASE 1: DASHBOARD, NOTIFICATIONS, AUDIT
# ==========================================

def get_teacher_dashboard_stats(teacher_id):
    conn = get_connection()
    if conn is None: return {"subjects": 0, "classes_today": 0, "students": 0, "pending_marks": 0,
                             "low_attendance_count": 0}
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as c FROM subjects WHERE teacher_id = %s AND status = 'Active'", (teacher_id,))
        subjects = cursor.fetchone()["c"]

        today = datetime.today().strftime('%A')
        cursor.execute("SELECT COUNT(*) as c FROM timetable WHERE teacher_id = %s AND day_of_week = %s",
                       (teacher_id, today))
        classes_today = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(DISTINCT s.student_id) as c 
            FROM students s
            INNER JOIN users u ON s.user_id = u.user_id
            INNER JOIN subjects sub ON u.department_id = sub.department_id AND s.semester = sub.semester AND s.section = sub.section
            WHERE sub.teacher_id = %s
        """, (teacher_id,))
        students = cursor.fetchone()["c"]

        # Pending Marks (Drafts)
        cursor.execute("""
            SELECT COUNT(DISTINCT subject_id, exam_type) as c 
            FROM marks 
            WHERE teacher_id = %s AND submission_status = 'Draft'
        """, (teacher_id,))
        pending_marks = cursor.fetchone()["c"]

        # Low Attendance Count
        low_att = get_teacher_low_attendance_students(teacher_id)

        return {
            "subjects": subjects, "classes_today": classes_today, "students": students,
            "pending_marks": pending_marks, "low_attendance_count": len(low_att)
        }
    except Exception:
        return {"subjects": 0, "classes_today": 0, "students": 0, "pending_marks": 0, "low_attendance_count": 0}
    finally:
        conn.close()


def get_teacher_timetable(teacher_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT t.day_of_week, 
                   DATE_FORMAT(ts.start_time, '%%H:%%i') as start_time, 
                   DATE_FORMAT(ts.end_time, '%%H:%%i') as end_time, 
                   s.subject_name, r.room_number, t.semester, t.section
            FROM timetable t
            INNER JOIN time_slots ts ON t.slot_id = ts.slot_id
            INNER JOIN subjects s ON t.subject_id = s.subject_id
            INNER JOIN rooms r ON t.room_id = r.room_id
            WHERE t.teacher_id = %s AND t.status = 'Published'
            ORDER BY ts.start_time
        """
        cursor.execute(sql, (teacher_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_teacher_notifications(teacher_id):
    """Dynamically generates alerts for the teacher."""
    alerts = []
    stats = get_teacher_dashboard_stats(teacher_id)
    if stats["pending_marks"] > 0:
        alerts.append({"type": "Assessment", "severity": "High",
                       "message": f"You have {stats['pending_marks']} draft marks pending submission.",
                       "link": "/teacher/marks"})
    if stats["low_attendance_count"] > 0:
        alerts.append({"type": "Academic", "severity": "Medium",
                       "message": f"{stats['low_attendance_count']} students are below 75% attendance in your classes.",
                       "link": "/teacher/attendance/history"})
    if stats["classes_today"] == 0:
        alerts.append({"type": "General", "severity": "Low", "message": "No classes scheduled for today.",
                       "link": "/teacher/timetable"})
    return alerts


def get_teacher_audit_trail(user_id, limit=20):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT action, target_table, target_id, source_interface, log_time
            FROM audit_logs 
            WHERE user_id = %s 
            ORDER BY log_time DESC 
            LIMIT %s
        """, (user_id, limit))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


# ==========================================
# EXISTING LEAVE FUNCTIONS
# ==========================================
def apply_for_leave(teacher_id, leave_type, from_date, to_date, reason):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leave_requests (teacher_id, leave_type, from_date, to_date, reason, status)
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """, (teacher_id, leave_type, from_date, to_date, reason))
        conn.commit()
        return True, "Leave application submitted successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_my_leaves(teacher_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leave_requests WHERE teacher_id = %s ORDER BY leave_id DESC", (teacher_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


# ==========================================
# PHASE 2: TEACHING, ASSESSMENT & LEARNING
# ==========================================

# ASSESSMENT ANALYTICS
def get_assessment_analytics(teacher_id):
    """Aggregates marks data to provide assessment analytics."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sub.subject_name, sub.subject_code, m.exam_type, 
                   COUNT(m.student_id) as total_students,
                   MAX(m.obtained_marks) as highest,
                   MIN(m.obtained_marks) as lowest,
                   ROUND(AVG(m.obtained_marks), 2) as average,
                   MAX(m.maximum_marks) as max_marks
            FROM marks m
            INNER JOIN subjects sub ON m.subject_id = sub.subject_id
            WHERE m.teacher_id = %s
            GROUP BY m.subject_id, m.exam_type
            ORDER BY sub.subject_name, m.exam_type
        """, (teacher_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


# ASSIGNMENTS
def get_teacher_assignments(teacher_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.assignment_id, a.title, a.due_date, sub.subject_name, sub.semester, sub.section
            FROM assignments a
            INNER JOIN subjects sub ON a.subject_id = sub.subject_id
            WHERE a.teacher_id = %s
            ORDER BY a.due_date DESC
        """, (teacher_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def create_assignment(teacher_id, subject_id, title, description, due_date):
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assignments (subject_id, teacher_id, title, description, due_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (subject_id, teacher_id, title, description, due_date))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_assignment_submissions(assignment_id, teacher_id):
    """Fetches submissions for an assignment, verifying teacher scope."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Verify assignment belongs to teacher
        cursor.execute("SELECT 1 FROM assignments WHERE assignment_id = %s AND teacher_id = %s",
                       (assignment_id, teacher_id))
        if not cursor.fetchone(): return []

        cursor.execute("""
            SELECT s.student_id, u.full_name AS student_name, sub.submission_date, sub.marks, sub.remarks
            FROM assignment_submissions sub
            INNER JOIN students s ON sub.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE sub.assignment_id = %s
        """, (assignment_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


# LESSON PLANNER
def get_lesson_plans(teacher_id, subject_id=None):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT lp.plan_id, sub.subject_name, lp.section, lp.plan_date, lp.topic, lp.status
            FROM lesson_plans lp
            INNER JOIN subjects sub ON lp.subject_id = sub.subject_id
            WHERE lp.teacher_id = %s
        """
        params = [teacher_id]
        if subject_id:
            sql += " AND lp.subject_id = %s"
            params.append(subject_id)
        sql += " ORDER BY lp.plan_date DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def create_lesson_plan(teacher_id, subject_id, section, plan_date, topic, objective, method, duration):
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lesson_plans (teacher_id, subject_id, section, plan_date, topic, learning_objective, teaching_method, duration_minutes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (teacher_id, subject_id, section, plan_date, topic, objective, method, duration))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


# SYLLABUS COVERAGE
def get_syllabus_coverage(teacher_id, subject_id=None):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT sc.coverage_id, sub.subject_name, sc.section, sc.unit_name, sc.status, sc.coverage_date
            FROM syllabus_coverage sc
            INNER JOIN subjects sub ON sc.subject_id = sub.subject_id
            WHERE sc.teacher_id = %s
        """
        params = [teacher_id]
        if subject_id:
            sql += " AND sc.subject_id = %s"
            params.append(subject_id)
        sql += " ORDER BY sc.coverage_id DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def create_syllabus_topic(teacher_id, subject_id, section, unit_name):
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO syllabus_coverage (teacher_id, subject_id, section, unit_name)
            VALUES (%s, %s, %s, %s)
        """, (teacher_id, subject_id, section, unit_name))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


# QUESTION BANK
def get_question_bank(teacher_id, subject_id=None):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT q.question_id, sub.subject_name, q.topic, q.question_text, q.question_type, q.difficulty, q.marks
            FROM question_bank q
            INNER JOIN subjects sub ON q.subject_id = sub.subject_id
            WHERE q.teacher_id = %s
        """
        params = [teacher_id]
        if subject_id:
            sql += " AND q.subject_id = %s"
            params.append(subject_id)
        sql += " ORDER BY q.created_at DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def create_question(teacher_id, subject_id, topic, question_text, q_type, difficulty, marks):
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO question_bank (teacher_id, subject_id, topic, question_text, question_type, difficulty, marks)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (teacher_id, subject_id, topic, question_text, q_type, difficulty, marks))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


# ACADEMIC REPORTS
def get_teacher_academic_report(teacher_id):
    """Consolidates metrics for the teacher's academic report."""
    analytics = get_assessment_analytics(teacher_id)
    assignments = get_teacher_assignments(teacher_id)
    syllabus = get_syllabus_coverage(teacher_id)

    completed_units = len([s for s in syllabus if s["status"] == 'Completed'])
    total_units = len(syllabus)
    coverage = round((completed_units / total_units) * 100, 2) if total_units > 0 else 0

    return {
        "assessment_analytics": analytics,
        "total_assignments": len(assignments),
        "syllabus_coverage": coverage,
        "total_units": total_units
    }


# ==========================================
# PHASE 3: STUDENT SUCCESS & FACULTY OPERATIONS
# ==========================================

def get_teacher_workload(teacher_id):
    """Calculates total teaching hours per week from assigned subjects."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT subject_name, subject_code, classes_per_week, section
            FROM subjects 
            WHERE teacher_id = %s AND status = 'Active'
            ORDER BY subject_name
        """, (teacher_id,))
        subjects = cursor.fetchall()

        total_hours = sum(s["classes_per_week"] for s in subjects if s["classes_per_week"])
        return {"subjects": subjects, "total_hours": total_hours}
    except Exception:
        return {"subjects": [], "total_hours": 0}
    finally:
        conn.close()

def get_teacher_timetable_conflicts(teacher_id):
    """Detects time-based double-booking for the teacher using overlapping time ranges."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t1.day_of_week, 
                   DATE_FORMAT(ts1.start_time, '%%H:%%i') as start_time, 
                   DATE_FORMAT(ts1.end_time, '%%H:%%i') as end_time,
                   s1.subject_name AS sub1, t1.section AS sec1,
                   s2.subject_name AS sub2, t2.section AS sec2
            FROM timetable t1
            JOIN timetable t2 ON t1.teacher_id = t2.teacher_id 
                              AND t1.day_of_week = t2.day_of_week 
                              AND t1.timetable_id < t2.timetable_id
            JOIN time_slots ts1 ON t1.slot_id = ts1.slot_id
            JOIN time_slots ts2 ON t2.slot_id = ts2.slot_id
            JOIN subjects s1 ON t1.subject_id = s1.subject_id
            JOIN subjects s2 ON t2.subject_id = s2.subject_id
            WHERE t1.teacher_id = %s 
              AND ts1.start_time < ts2.end_time 
              AND ts1.end_time > ts2.start_time
        """, (teacher_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error detecting timetable conflicts:", e)
        return []
    finally:
        conn.close()


def get_teacher_department_meetings(dept_id):
    """Fetches department-level meetings for the teacher."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT meeting_id, title, meeting_date, venue, status, agenda
            FROM meetings 
            WHERE department_id = %s
            ORDER BY meeting_date DESC
        """, (dept_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_teacher_action_items(user_id):
    """Fetches action items assigned specifically to the teacher."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ai.action_id, m.title AS meeting_title, ai.description, ai.due_date, ai.status
            FROM action_items ai
            INNER JOIN meetings m ON ai.meeting_id = m.meeting_id
            WHERE ai.assigned_to = %s
            ORDER BY ai.due_date DESC
        """, (user_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_teacher_notices(dept_id):
    """Fetches institutional and department-specific notices for the teacher."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, description, category, posted_on, target_audience
            FROM notices 
            WHERE target_audience IN ('All', 'Teachers') OR target_department_id = %s
            ORDER BY posted_on DESC LIMIT 10
        """, (dept_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_student_risk_indicators(teacher_id):
    """Dynamically calculates risk indicators for authorized students."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Get students with low attendance in teacher's subjects
        cursor.execute("""
            SELECT u.full_name, s.enrollment_no, sub.subject_name,
                   ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.attendance_id)) * 100, 2) as att_perc
            FROM attendance a
            INNER JOIN students s ON a.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            INNER JOIN subjects sub ON a.subject_id = sub.subject_id
            WHERE sub.teacher_id = %s
            GROUP BY a.student_id, a.subject_id
            HAVING att_perc < 75.0
        """, (teacher_id,))
        low_att = cursor.fetchall()

        # Get students with missing draft marks
        cursor.execute("""
            SELECT u.full_name, s.enrollment_no, sub.subject_name, m.exam_type
            FROM marks m
            INNER JOIN students s ON m.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            INNER JOIN subjects sub ON m.subject_id = sub.subject_id
            WHERE sub.teacher_id = %s AND m.obtained_marks IS NULL OR m.submission_status = 'Draft'
        """, (teacher_id,))
        missing_marks = cursor.fetchall()

        return {
            "low_attendance": low_att,
            "missing_marks": missing_marks
        }
    except Exception:
        return {"low_attendance": [], "missing_marks": []}
    finally:
        conn.close()


def get_teacher_department_id(user_id):
    """Helper to get dept_id for meeting/notice scope."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT department_id FROM users WHERE user_id = %s", (user_id,))
        res = cursor.fetchone()
        return res["department_id"] if res else None
    except Exception:
        return None
    finally:
        conn.close()


# ==========================================
# PHASE 4: ANALYTICS, REPORTING & INTELLIGENCE
# ==========================================

def get_teaching_analytics(teacher_id):
    """Consolidates all teaching metrics into a single dashboard payload."""
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Academic Scope
        cursor.execute("SELECT COUNT(*) as c FROM subjects WHERE teacher_id = %s AND status = 'Active'", (teacher_id,))
        subjects = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(DISTINCT s.student_id) as c 
            FROM students s
            INNER JOIN users u ON s.user_id = u.user_id
            INNER JOIN subjects sub ON u.department_id = sub.department_id AND s.semester = sub.semester AND s.section = sub.section
            WHERE sub.teacher_id = %s
        """, (teacher_id,))
        students = cursor.fetchone()["c"]

        cursor.execute(
            "SELECT COUNT(DISTINCT section) as c FROM subjects WHERE teacher_id = %s AND section IS NOT NULL",
            (teacher_id,))
        classes = cursor.fetchone()["c"]

        # 2. Attendance & Assessment Ops
        cursor.execute("SELECT COUNT(DISTINCT attendance_date) as c FROM attendance WHERE teacher_id = %s",
                       (teacher_id,))
        att_sessions = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(DISTINCT subject_id, exam_type) as c 
            FROM marks WHERE teacher_id = %s AND submission_status = 'Draft'
        """, (teacher_id,))
        pending_marks = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM assignments WHERE teacher_id = %s", (teacher_id,))
        assignments = cursor.fetchone()["c"]

        # 3. Syllabus & Plans
        cursor.execute("SELECT COUNT(*) as c FROM lesson_plans WHERE teacher_id = %s", (teacher_id,))
        lesson_plans = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed,
                COUNT(*) as total
            FROM syllabus_coverage WHERE teacher_id = %s
        """, (teacher_id,))
        syllabus = cursor.fetchone()

        return {
            "subjects": subjects, "classes": classes, "students": students,
            "att_sessions": att_sessions, "pending_marks": pending_marks,
            "assignments": assignments, "lesson_plans": lesson_plans,
            "syllabus_completed": syllabus["completed"] if syllabus else 0,
            "syllabus_total": syllabus["total"] if syllabus else 0
        }
    except Exception:
        return {}
    finally:
        conn.close()


def get_attendance_intelligence(teacher_id):
    """Aggregates attendance data to show class-level intelligence."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sub.subject_name, sub.section,
                   COUNT(a.attendance_id) as total_records,
                   ROUND(AVG(CASE WHEN a.status = 'Present' THEN 100 ELSE 0 END), 2) as avg_attendance,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
            FROM attendance a
            INNER JOIN subjects sub ON a.subject_id = sub.subject_id
            WHERE sub.teacher_id = %s
            GROUP BY sub.subject_id
        """, (teacher_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_student_risk_dashboard(teacher_id):
    """Identifies students with transparent risk indicators based on existing data."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Complex join to find students, their attendance, and missing marks in teacher's scope
        cursor.execute("""
            SELECT u.full_name, s.enrollment_no, sub.subject_name,
                   ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.attendance_id)) * 100, 2) as att_perc,
                   COUNT(m.marks_id) as total_assessments,
                   SUM(CASE WHEN m.obtained_marks IS NULL OR m.submission_status = 'Draft' THEN 1 ELSE 0 END) as missing_marks
            FROM students s
            INNER JOIN users u ON s.user_id = u.user_id
            INNER JOIN subjects sub ON u.department_id = sub.department_id AND s.semester = sub.semester AND s.section = sub.section
            LEFT JOIN attendance a ON s.student_id = a.student_id AND a.subject_id = sub.subject_id
            LEFT JOIN marks m ON s.student_id = m.student_id AND m.subject_id = sub.subject_id
            WHERE sub.teacher_id = %s
            GROUP BY s.student_id, sub.subject_id
            HAVING att_perc < 75.0 OR missing_marks > 0
            ORDER BY att_perc ASC
        """, (teacher_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Risk Dashboard Error:", e)
        return []
    finally:
        conn.close()


def get_academic_report_data(teacher_id):
    """Consolidates data for the final academic report."""
    teaching = get_teaching_analytics(teacher_id)
    att_intel = get_attendance_intelligence(teacher_id)
    risks = get_student_risk_dashboard(teacher_id)

    return {
        "teaching_stats": teaching,
        "attendance_intel": att_intel,
        "risk_count": len(risks)
    }