# database/hod_queries.py
from database.connection import get_connection
from config import ATTENDANCE_THRESHOLD


# HOD DEPARTMENT INFORMATION
def get_hod_department_id(user_id):
    """Return the active department assigned to the HOD user."""

    conn = get_connection()

    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT department_id
            FROM department_hod_assignments
            WHERE user_id = %s
              AND status = 'Active'
            """,
            (user_id,)
        )

        result = cursor.fetchone()

        return result["department_id"] if result else None

    except Exception as e:
        print("Error getting HOD department:", e)
        return None

    finally:
        conn.close()


# DEPARTMENT STATISTICS
def get_department_stats(department_id):
    """Return basic student, teacher and subject statistics."""

    conn = get_connection()

    if conn is None:
        return {
            "students": 0,
            "teachers": 0,
            "subjects": 0
        }

    try:
        cursor = conn.cursor()

        # Student count
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM students s
            INNER JOIN users u
                ON s.user_id = u.user_id
            WHERE u.department_id = %s
            """,
            (department_id,)
        )

        students_result = cursor.fetchone()
        students = students_result["count"] if students_result else 0

        # Teacher count
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM teachers t
            INNER JOIN users u
                ON t.user_id = u.user_id
            WHERE u.department_id = %s
            """,
            (department_id,)
        )

        teachers_result = cursor.fetchone()
        teachers = teachers_result["count"] if teachers_result else 0

        # Subject count
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM subjects
            WHERE department_id = %s
            """,
            (department_id,)
        )

        subjects_result = cursor.fetchone()
        subjects = subjects_result["count"] if subjects_result else 0

        return {
            "students": students,
            "teachers": teachers,
            "subjects": subjects
        }

    except Exception as e:
        print("Error fetching department stats:", e)

        return {
            "students": 0,
            "teachers": 0,
            "subjects": 0
        }

    finally:
        conn.close()


# ATTENDANCE MANAGEMENT

def get_department_attendance_stats(dept_id):
    """
    Calculate department average attendance and
    number of students below the configured threshold.
    """

    conn = get_connection()

    if conn is None:
        return {
            "avg_attendance": 0,
            "low_attendance_count": 0
        }

    try:
        cursor = conn.cursor()

        # Calculate average attendance
        cursor.execute(
            """
            SELECT ROUND(AVG(att_perc), 2) AS avg_attendance
            FROM (
                SELECT
                    student_id,
                    ROUND(
                        (
                            SUM(
                                CASE
                                    WHEN status = 'Present' THEN 1
                                    ELSE 0
                                END
                            ) / COUNT(*)
                        ) * 100,
                        2
                    ) AS att_perc
                FROM attendance
                GROUP BY student_id
            ) AS sub
            WHERE student_id IN (
                SELECT s.student_id
                FROM students s
                INNER JOIN users u
                    ON s.user_id = u.user_id
                WHERE u.department_id = %s
            )
            """,
            (dept_id,)
        )

        avg_result = cursor.fetchone()

        if avg_result and avg_result["avg_attendance"] is not None:
            avg_attendance = avg_result["avg_attendance"]
        else:
            avg_attendance = 0

        # Count students below attendance threshold
        cursor.execute(
            """
            SELECT COUNT(DISTINCT s.student_id) AS count
            FROM students s
            INNER JOIN users u
                ON s.user_id = u.user_id
            INNER JOIN (
                SELECT
                    student_id,
                    ROUND(
                        (
                            SUM(
                                CASE
                                    WHEN status = 'Present' THEN 1
                                    ELSE 0
                                END
                            ) / COUNT(*)
                        ) * 100,
                        2
                    ) AS att_perc
                FROM attendance
                GROUP BY student_id
                HAVING att_perc < %s
            ) AS att
                ON s.student_id = att.student_id
            WHERE u.department_id = %s
            """,
            (ATTENDANCE_THRESHOLD, dept_id)
        )

        low_result = cursor.fetchone()
        low_count = low_result["count"] if low_result else 0

        return {
            "avg_attendance": avg_attendance,
            "low_attendance_count": low_count
        }

    except Exception as e:
        print("Error fetching optimized attendance stats:", e)

        return {
            "avg_attendance": 0,
            "low_attendance_count": 0
        }

    finally:
        conn.close()


def get_low_attendance_students(dept_id):
    """Return students whose attendance is below the configured threshold."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                u.full_name,
                s.enrollment_no,
                s.semester,
                ROUND(
                    (
                        SUM(
                            CASE
                                WHEN a.status = 'Present' THEN 1
                                ELSE 0
                            END
                        ) / COUNT(a.attendance_id)
                    ) * 100,
                    2
                ) AS percentage
            FROM attendance a
            INNER JOIN students s
                ON a.student_id = s.student_id
            INNER JOIN users u
                ON s.user_id = u.user_id
            WHERE u.department_id = %s
            GROUP BY
                s.student_id,
                u.full_name,
                s.enrollment_no,
                s.semester
            HAVING percentage < %s
            ORDER BY percentage ASC
            """,
            (dept_id, ATTENDANCE_THRESHOLD)
        )

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching low attendance list:", e)
        return []

    finally:
        conn.close()


# STUDENT ACADEMIC MANAGEMENT
def get_department_students(dept_id, search_query="", semester=None):
    """Fetch department students with optional search and semester filter."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        sql = """
            SELECT
                s.student_id,
                u.full_name,
                s.enrollment_no,
                s.semester,
                s.section,
                s.cgpa
            FROM students s
            INNER JOIN users u
                ON s.user_id = u.user_id
            WHERE u.department_id = %s
        """

        params = [dept_id]

        if search_query:
            sql += """
                AND (
                    u.full_name LIKE %s
                    OR s.enrollment_no LIKE %s
                )
            """

            search_value = f"%{search_query}%"

            params.extend([
                search_value,
                search_value
            ])

        if semester:
            sql += " AND s.semester = %s"
            params.append(semester)

        sql += """
            ORDER BY
                s.semester,
                u.full_name
        """

        cursor.execute(sql, tuple(params))

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching department students:", e)
        return []

    finally:
        conn.close()


def get_student_academic_profile(student_id):
    """Fetch consolidated read-only academic profile for a student."""

    conn = get_connection()

    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        # ----------------------------------------------------
        # Basic student information
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                u.full_name,
                u.email,
                s.enrollment_no,
                s.semester,
                s.section,
                s.cgpa,
                d.department_name
            FROM students s
            INNER JOIN users u
                ON s.user_id = u.user_id
            INNER JOIN departments d
                ON u.department_id = d.department_id
            WHERE s.student_id = %s
            """,
            (student_id,)
        )

        profile = cursor.fetchone()

        if not profile:
            return None

        # ----------------------------------------------------
        # Subject-wise attendance
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                sub.subject_name,
                COUNT(a.attendance_id) AS total_classes,
                SUM(
                    CASE
                        WHEN a.status = 'Present' THEN 1
                        ELSE 0
                    END
                ) AS present,
                ROUND(
                    (
                        SUM(
                            CASE
                                WHEN a.status = 'Present' THEN 1
                                ELSE 0
                            END
                        ) / COUNT(a.attendance_id)
                    ) * 100,
                    2
                ) AS percentage
            FROM attendance a
            INNER JOIN subjects sub
                ON a.subject_id = sub.subject_id
            WHERE a.student_id = %s
            GROUP BY
                sub.subject_id,
                sub.subject_name
            """,
            (student_id,)
        )

        profile["attendance"] = cursor.fetchall()

        # ----------------------------------------------------
        # Marks history
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                sub.subject_name,
                m.exam_type,
                m.maximum_marks,
                m.obtained_marks,
                m.submission_status
            FROM marks m
            INNER JOIN subjects sub
                ON m.subject_id = sub.subject_id
            WHERE m.student_id = %s
            ORDER BY
                sub.subject_name,
                m.exam_type
            """,
            (student_id,)
        )

        profile["marks"] = cursor.fetchall()

        return profile

    except Exception as e:
        print("Error fetching student academic profile:", e)
        return None

    finally:
        conn.close()


# PERFORMANCE MANAGEMENT
def get_department_top_performers(department_id, limit=5):
    """Return top performing students in a department."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        sql = """
            SELECT
                u.full_name,
                s.enrollment_no,
                ROUND(
                    (
                        SUM(m.obtained_marks)
                        / SUM(m.maximum_marks)
                    ) * 100,
                    2
                ) AS percentage
            FROM marks m
            INNER JOIN students s
                ON m.student_id = s.student_id
            INNER JOIN users u
                ON s.user_id = u.user_id
            WHERE u.department_id = %s
            GROUP BY
                s.student_id,
                u.full_name,
                s.enrollment_no
            ORDER BY percentage DESC
            LIMIT %s
        """

        cursor.execute(sql, (department_id, limit))

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching top performers:", e)
        return []

    finally:
        conn.close()


def get_department_weak_students(department_id, limit=5):
    """Return students with the lowest academic performance."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        sql = """
            SELECT
                u.full_name,
                s.enrollment_no,
                ROUND(
                    (
                        SUM(m.obtained_marks)
                        / SUM(m.maximum_marks)
                    ) * 100,
                    2
                ) AS percentage
            FROM marks m
            INNER JOIN students s
                ON m.student_id = s.student_id
            INNER JOIN users u
                ON s.user_id = u.user_id
            WHERE u.department_id = %s
            GROUP BY
                s.student_id,
                u.full_name,
                s.enrollment_no
            ORDER BY percentage ASC
            LIMIT %s
        """

        cursor.execute(sql, (department_id, limit))

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching weak students:", e)
        return []

    finally:
        conn.close()



# LEAVE MANAGEMENT
def get_department_leaves(department_id):
    """Return teacher leave requests for a department."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        sql = """
            SELECT
                lr.leave_id,
                lr.leave_type,
                lr.from_date,
                lr.to_date,
                lr.reason,
                lr.status,
                u.full_name AS teacher_name
            FROM leave_requests lr
            INNER JOIN teachers t
                ON lr.teacher_id = t.teacher_id
            INNER JOIN users u
                ON t.user_id = u.user_id
            WHERE u.department_id = %s
            ORDER BY lr.leave_id DESC
        """

        cursor.execute(sql, (department_id,))

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching department leaves:", e)
        return []

    finally:
        conn.close()


def update_leave_status(leave_id, status):
    """Update the status of a leave request."""

    conn = get_connection()

    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE leave_requests
            SET status = %s
            WHERE leave_id = %s
            """,
            (status, leave_id)
        )

        conn.commit()

        return True

    except Exception as e:
        print("Error updating leave status:", e)
        return False

    finally:
        conn.close()


# SUBJECT PERFORMANCE
def get_department_subject_performance(department_id):
    """Return average marks for each department subject."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        sql = """
            SELECT
                s.subject_name,
                s.subject_code,
                ROUND(
                    AVG(
                        (m.obtained_marks / m.maximum_marks) * 100
                    ),
                    2
                ) AS avg_marks
            FROM marks m
            INNER JOIN subjects s
                ON m.subject_id = s.subject_id
            WHERE s.department_id = %s
            GROUP BY
                s.subject_id,
                s.subject_name,
                s.subject_code
            ORDER BY avg_marks ASC
        """

        cursor.execute(sql, (department_id,))

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching subject performance:", e)
        return []

    finally:
        conn.close()


# FACULTY WORKLOAD
def get_department_faculty_workload(department_id):
    """
    Calculate faculty workload by summing classes_per_week
    from the subjects table.
    """

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                t.teacher_id,
                u.full_name,
                t.designation,
                COALESCE(SUM(s.classes_per_week), 0) AS total_hours,
                COALESCE(
                    SUM(
                        CASE
                            WHEN s.subject_type = 'Theory'
                            THEN s.classes_per_week
                            ELSE 0
                        END
                    ),
                    0
                ) AS theory_hours,
                COALESCE(
                    SUM(
                        CASE
                            WHEN s.subject_type = 'Practical'
                            THEN s.classes_per_week
                            ELSE 0
                        END
                    ),
                    0
                ) AS practical_hours,
                COALESCE(
                    SUM(
                        CASE
                            WHEN s.subject_type = 'Lab'
                            THEN s.classes_per_week
                            ELSE 0
                        END
                    ),
                    0
                ) AS lab_hours
            FROM teachers t
            INNER JOIN users u
                ON t.user_id = u.user_id
            LEFT JOIN subjects s
                ON t.teacher_id = s.teacher_id
               AND s.status = 'Active'
            WHERE u.department_id = %s
            GROUP BY
                t.teacher_id,
                u.full_name,
                t.designation
            ORDER BY total_hours DESC
            """,
            (department_id,)
        )

        return cursor.fetchall()

    except Exception as e:
        print("Error calculating faculty workload:", e)
        return []

    finally:
        conn.close()


# MARKS VERIFICATION
def get_submitted_marks_for_hod(department_id):
    """Return submitted marks waiting for HOD verification."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT
                m.subject_id,
                m.exam_type,
                s.subject_name,
                u.full_name AS teacher_name
            FROM marks m
            INNER JOIN subjects s
                ON m.subject_id = s.subject_id
            INNER JOIN teachers t
                ON m.teacher_id = t.teacher_id
            INNER JOIN users u
                ON t.user_id = u.user_id
            WHERE s.department_id = %s
              AND m.submission_status = 'Submitted'
            """,
            (department_id,)
        )

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching submitted marks:", e)
        return []

    finally:
        conn.close()


def update_marks_verification(subject_id, exam_type, new_status):
    """Update marks submission verification status."""

    conn = get_connection()

    if conn is None:
        return False, "Database connection error."

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE marks
            SET submission_status = %s
            WHERE subject_id = %s
              AND exam_type = %s
            """,
            (new_status, subject_id, exam_type)
        )

        conn.commit()

        return True, f"Marks {new_status} successfully."

    except Exception as e:
        print("Error updating marks verification:", e)

        return False, str(e)

    finally:
        conn.close()


# FACULTY ACADEMIC MANAGEMENT
def get_department_faculty(dept_id, search_query=""):
    """Fetch department faculty with optional search."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        sql = """
            SELECT
                t.teacher_id,
                u.full_name,
                u.email,
                t.designation,
                t.qualification,
                t.experience
            FROM teachers t
            INNER JOIN users u
                ON t.user_id = u.user_id
            WHERE u.department_id = %s
        """

        params = [dept_id]

        if search_query:
            sql += """
                AND (
                    u.full_name LIKE %s
                    OR t.designation LIKE %s
                )
            """

            search_value = f"%{search_query}%"

            params.extend([
                search_value,
                search_value
            ])

        sql += " ORDER BY u.full_name"

        cursor.execute(sql, tuple(params))

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching department faculty:", e)
        return []

    finally:
        conn.close()


def get_faculty_academic_profile(teacher_id):
    """Fetch read-only academic profile for a teacher."""

    conn = get_connection()

    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        # ----------------------------------------------------
        # Basic faculty information
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                u.full_name,
                u.email,
                t.designation,
                t.qualification,
                t.experience,
                d.department_name
            FROM teachers t
            INNER JOIN users u
                ON t.user_id = u.user_id
            INNER JOIN departments d
                ON u.department_id = d.department_id
            WHERE t.teacher_id = %s
            """,
            (teacher_id,)
        )

        profile = cursor.fetchone()

        if not profile:
            return None

        # ----------------------------------------------------
        # Assigned subjects
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                subject_name,
                subject_code,
                semester,
                subject_type,
                classes_per_week,
                credits
            FROM subjects
            WHERE teacher_id = %s
              AND status = 'Active'
            ORDER BY
                semester,
                subject_name
            """,
            (teacher_id,)
        )

        profile["subjects"] = cursor.fetchall()

        # ----------------------------------------------------
        # Leave history
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                leave_type,
                from_date,
                to_date,
                reason,
                status
            FROM leave_requests
            WHERE teacher_id = %s
            ORDER BY leave_id DESC
            LIMIT 10
            """,
            (teacher_id,)
        )

        profile["leaves"] = cursor.fetchall()

        return profile

    except Exception as e:
        print("Error fetching faculty academic profile:", e)
        return None

    finally:
        conn.close()


# SUBJECT & CURRICULUM MANAGEMENT
def get_department_subjects(
    dept_id,
    semester=None,
    subject_type=None
):
    """Fetch department subjects with allocated faculty information."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        sql = """
            SELECT
                s.subject_id,
                s.teacher_id,
                s.subject_name,
                s.subject_code,
                s.semester,
                s.subject_type,
                s.classes_per_week,
                s.credits,
                s.status,
                u.full_name AS faculty_name
            FROM subjects s
            LEFT JOIN teachers t
                ON s.teacher_id = t.teacher_id
            LEFT JOIN users u
                ON t.user_id = u.user_id
            WHERE s.department_id = %s
        """

        params = [dept_id]

        if semester:
            sql += " AND s.semester = %s"
            params.append(semester)

        if subject_type:
            sql += " AND s.subject_type = %s"
            params.append(subject_type)

        sql += """
            ORDER BY
                s.semester,
                s.subject_name
        """

        cursor.execute(sql, tuple(params))

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching department subjects:", e)
        return []

    finally:
        conn.close()


def get_department_unassigned_subjects(dept_id):
    """Return active subjects without an assigned faculty member."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                subject_name,
                subject_code,
                semester,
                classes_per_week
            FROM subjects
            WHERE department_id = %s
              AND teacher_id IS NULL
              AND status = 'Active'
            ORDER BY semester
            """,
            (dept_id,)
        )

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching unassigned subjects:", e)
        return []

    finally:
        conn.close()


# TIMETABLE MANAGEMENT
def get_department_timetable(
    dept_id,
    semester=None,
    section=None
):
    """Fetch timetable entries for a department."""

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        sql = """
            SELECT
                t.timetable_id,
                t.day_of_week,
                t.semester,
                t.section,
                t.academic_year,
                t.status,
                sub.subject_name,
                sub.subject_code,
                u.full_name AS teacher_name,
                r.room_number,
                r.room_name,
                ts.start_time,
                ts.end_time,
                ts.slot_name
            FROM timetable t
            INNER JOIN subjects sub
                ON t.subject_id = sub.subject_id
            LEFT JOIN teachers tea
                ON t.teacher_id = tea.teacher_id
            LEFT JOIN users u
                ON tea.user_id = u.user_id
            INNER JOIN rooms r
                ON t.room_id = r.room_id
            INNER JOIN time_slots ts
                ON t.slot_id = ts.slot_id
            WHERE t.department_id = %s
        """

        params = [dept_id]

        # Optional semester filter
        if semester:
            sql += " AND t.semester = %s"
            params.append(semester)

        # Optional section filter
        if section:
            sql += " AND t.section = %s"
            params.append(section)

        sql += """
            ORDER BY
                t.semester,
                t.section,
                t.day_of_week,
                ts.start_time
        """

        cursor.execute(sql, tuple(params))

        return cursor.fetchall()

    except Exception as e:
        print("Error fetching timetable:", e)
        return []

    finally:
        conn.close()


# TIMETABLE CONFLICT DETECTION
def get_department_timetable_conflicts(dept_id):
    """
    Detect timetable conflicts involving the HOD's department.

    A conflict exists when:
    1. The same teacher is assigned to two timetable entries
       at the same day and time slot.
    2. The same room is assigned to two timetable entries
       at the same day and time slot.
    """

    conn = get_connection()

    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                t1.timetable_id AS id1,
                t2.timetable_id AS id2,

                t1.day_of_week,

                t1.semester AS sem1,
                t1.section AS sec1,

                t2.semester AS sem2,
                t2.section AS sec2,

                sub1.subject_name AS sub1_name,
                sub2.subject_name AS sub2_name,

                u1.full_name AS teacher_name,

                r1.room_number AS room1,
                r2.room_number AS room2,

                ts.start_time,
                ts.end_time,
                ts.slot_name

            FROM timetable t1

            INNER JOIN timetable t2
                ON t1.day_of_week = t2.day_of_week
               AND t1.slot_id = t2.slot_id
               AND t1.timetable_id < t2.timetable_id

            INNER JOIN subjects sub1
                ON t1.subject_id = sub1.subject_id

            INNER JOIN subjects sub2
                ON t2.subject_id = sub2.subject_id

            LEFT JOIN teachers tea1
                ON t1.teacher_id = tea1.teacher_id

            LEFT JOIN users u1
                ON tea1.user_id = u1.user_id

            LEFT JOIN teachers tea2
                ON t2.teacher_id = tea2.teacher_id

            LEFT JOIN users u2
                ON tea2.user_id = u2.user_id

            INNER JOIN rooms r1
                ON t1.room_id = r1.room_id

            INNER JOIN rooms r2
                ON t2.room_id = r2.room_id

            INNER JOIN time_slots ts
                ON t1.slot_id = ts.slot_id

            WHERE (
                t1.teacher_id = t2.teacher_id
                OR t1.room_id = t2.room_id
            )
            AND (
                t1.department_id = %s
                OR t2.department_id = %s
            )

            ORDER BY
                t1.day_of_week,
                ts.start_time
            """,
            (dept_id, dept_id)
        )

        return cursor.fetchall()

    except Exception as e:
        print("Error detecting timetable conflicts:", e)
        return []

    finally:
        conn.close()

# ==========================================
# PHASE 3: EXAMINATIONS, RESULTS & STUDENT SUPPORT
# ==========================================

def get_department_marks_status(dept_id):
    """Aggregates marks submission status per subject for the department."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                sub.subject_name, 
                sub.subject_code,
                sub.semester,
                ut.full_name AS teacher_name,
                COUNT(m.marks_id) as total_records,
                SUM(CASE WHEN m.submission_status = 'Draft' THEN 1 ELSE 0 END) as draft_count,
                SUM(CASE WHEN m.submission_status = 'Submitted' THEN 1 ELSE 0 END) as submitted_count,
                SUM(CASE WHEN m.submission_status = 'Verified' THEN 1 ELSE 0 END) as verified_count,
                SUM(CASE WHEN m.submission_status = 'Returned' THEN 1 ELSE 0 END) as returned_count
            FROM subjects sub
            LEFT JOIN marks m ON sub.subject_id = m.subject_id
            LEFT JOIN teachers t ON sub.teacher_id = t.teacher_id
            LEFT JOIN users ut ON t.user_id = ut.user_id
            WHERE sub.department_id = %s AND sub.status = 'Active'
            GROUP BY sub.subject_id
            ORDER BY sub.semester, sub.subject_name
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching marks status:", e)
        return []
    finally:
        conn.close()

def get_department_results_status(dept_id):
    """Aggregates result approval statuses for the department."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.approval_status,
                r.status as publication_status,
                COUNT(*) as count
            FROM results r
            INNER JOIN students s ON r.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE u.department_id = %s
            GROUP BY r.approval_status, r.status
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching results status:", e)
        return []
    finally:
        conn.close()

def get_department_low_performers(dept_id, threshold=50.0):
    """Identifies students with average performance below a transparent threshold."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.full_name, 
                s.enrollment_no, 
                s.semester,
                ROUND(AVG((m.obtained_marks / m.maximum_marks) * 100), 2) as avg_percentage
            FROM marks m
            INNER JOIN students s ON m.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE u.department_id = %s
            GROUP BY s.student_id
            HAVING avg_percentage < %s
            ORDER BY avg_percentage ASC
        """, (dept_id, threshold))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching low performers:", e)
        return []
    finally:
        conn.close()

def get_department_normal_complaints(dept_id):
    """Fetches non-sensitive complaints for the department."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                c.complaint_id, 
                c.category, 
                c.complaint, 
                c.status, 
                c.created_at,
                u.full_name AS student_name
            FROM complaints c
            INNER JOIN students s ON c.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE u.department_id = %s AND c.sensitivity = 'Normal'
            ORDER BY c.created_at DESC
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching normal complaints:", e)
        return []
    finally:
        conn.close()

def get_department_academic_plan(dept_id):
    """Groups active subjects by semester to show curriculum structure."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                semester, 
                subject_name, 
                subject_code, 
                subject_type, 
                credits, 
                classes_per_week
            FROM subjects
            WHERE department_id = %s AND status = 'Active'
            ORDER BY semester, subject_name
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching academic plan:", e)
        return []
    finally:
        conn.close()

# ==========================================
# PHASE 4: DEPARTMENT ADMINISTRATION & OPERATIONS
# ==========================================

def get_department_notices(dept_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT notice_id, title, description, category, status, posted_on
            FROM notices
            WHERE target_department_id = %s OR target_audience = 'All'
            ORDER BY posted_on DESC
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching dept notices:", e)
        return []
    finally:
        conn.close()

def create_department_notice(dept_id, user_id, title, description, category):
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notices (title, description, category, status, target_audience, target_department_id, posted_by)
            VALUES (%s, %s, %s, 'Published', 'Department', %s, %s)
        """, (title, description, category, dept_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error creating notice:", e)
        return False
    finally:
        conn.close()

def get_department_events(dept_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_id, event_name, description, event_date, venue, status
            FROM events
            WHERE target_department_id = %s OR target_audience = 'All'
            ORDER BY event_date DESC
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching dept events:", e)
        return []
    finally:
        conn.close()

def create_department_event(dept_id, user_id, event_name, description, event_date, venue):
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (event_name, description, event_date, venue, status, target_audience, target_department_id, organizer)
            VALUES (%s, %s, %s, %s, 'Published', 'Department', %s, 'HOD')
        """, (event_name, description, event_date, venue, dept_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error creating event:", e)
        return False
    finally:
        conn.close()

def get_department_meetings(dept_id):
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
    except Exception as e:
        print("Error fetching dept meetings:", e)
        return []
    finally:
        conn.close()

def create_department_meeting(dept_id, user_id, title, meeting_date, venue, agenda):
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO meetings (title, meeting_date, venue, agenda, status, department_id, chairperson_id, organizer_id)
            VALUES (%s, %s, %s, %s, 'Scheduled', %s, %s, %s)
        """, (title, meeting_date, venue, agenda, dept_id, user_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error creating meeting:", e)
        return False
    finally:
        conn.close()

def get_department_assets(dept_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT asset_id, asset_code, name, condition_status, lifecycle_status
            FROM assets
            WHERE department_id = %s
            ORDER BY name
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching dept assets:", e)
        return []
    finally:
        conn.close()

def get_department_maintenance_requests(dept_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mr.request_id, mr.issue_description, mr.priority, mr.status, mr.created_at, a.name AS asset_name, a.asset_code
            FROM maintenance_requests mr
            INNER JOIN assets a ON mr.asset_id = a.asset_id
            WHERE a.department_id = %s
            ORDER BY mr.created_at DESC
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching maintenance requests:", e)
        return []
    finally:
        conn.close()

def create_maintenance_request(user_id, asset_id, issue_description, priority):
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_requests (asset_id, issue_description, priority, status, requested_by)
            VALUES (%s, %s, %s, 'Submitted', %s)
        """, (asset_id, issue_description, priority, user_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error creating maintenance request:", e)
        return False
    finally:
        conn.close()

def get_department_documents(dept_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT document_id, title, status, created_at
            FROM documents
            WHERE department_id = %s
            ORDER BY created_at DESC
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching dept documents:", e)
        return []
    finally:
        conn.close()

def get_department_placement_stats(dept_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pa.status, COUNT(*) as count
            FROM placement_applications pa
            INNER JOIN students s ON pa.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE u.department_id = %s
            GROUP BY pa.status
        """, (dept_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching placement stats:", e)
        return []
    finally:
        conn.close()


# ==========================================
# PHASE 5: INTELLIGENCE & GOVERNANCE QUERIES
# ==========================================

def get_hod_notifications(dept_id):
    """Dynamically generates department alerts from existing system states."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        alerts = []

        # 1. Pending Faculty Leaves
        cursor.execute(
            "SELECT COUNT(*) as count FROM leave_requests lr INNER JOIN teachers t ON lr.teacher_id = t.teacher_id INNER JOIN users u ON t.user_id = u.user_id WHERE u.department_id = %s AND lr.status = 'Pending'",
            (dept_id,))
        leave_count = cursor.fetchone()["count"]
        if leave_count > 0:
            alerts.append({"type": "Approval", "severity": "Medium",
                           "message": f"{leave_count} faculty leave requests pending approval.",
                           "link": "/hod/approvals"})

        # 2. Pending Marks Verification
        cursor.execute("""
            SELECT COUNT(DISTINCT m.subject_id) as count 
            FROM marks m 
            INNER JOIN subjects s ON m.subject_id = s.subject_id 
            WHERE s.department_id = %s AND m.submission_status = 'Submitted'
        """, (dept_id,))
        marks_count = cursor.fetchone()["count"]
        if marks_count > 0:
            alerts.append({"type": "Academic", "severity": "High",
                           "message": f"{marks_count} subjects have marks pending verification.",
                           "link": "/hod/approvals"})

        # 3. Low Attendance Alert
        att_stats = get_department_attendance_stats(dept_id)
        if att_stats["low_attendance_count"] > 0:
            alerts.append({"type": "Academic", "severity": "Critical",
                           "message": f"{att_stats['low_attendance_count']} students below 75% attendance.",
                           "link": "/hod/attendance"})

        # 4. Submitted Maintenance Requests
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM maintenance_requests mr 
            INNER JOIN assets a ON mr.asset_id = a.asset_id 
            WHERE a.department_id = %s AND mr.status = 'Submitted'
        """, (dept_id,))
        maint_count = cursor.fetchone()["count"]
        if maint_count > 0:
            alerts.append({"type": "Operations", "severity": "Medium",
                           "message": f"{maint_count} maintenance requests submitted, awaiting Admin/Campus action.",
                           "link": "/hod/maintenance"})

        return alerts
    except Exception as e:
        print("Error fetching HOD notifications:", e)
        return []
    finally:
        conn.close()


def get_hod_audit_trail(user_id, limit=20):
    """Fetches recent activity for the specific HOD."""
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
    except Exception as e:
        print("Error fetching HOD audit trail:", e)
        return []
    finally:
        conn.close()


def get_hod_report_data(dept_id):
    """Consolidates major KPIs for the Department Report."""
    stats = get_department_stats(dept_id)
    academic = get_department_attendance_stats(dept_id)
    marks_status = get_department_marks_status(dept_id)
    leaves = get_department_leaves(dept_id)

    pending_leaves = [l for l in leaves if l["status"] == 'Pending']
    pending_marks = [m for m in marks_status if m["submitted_count"] > 0]

    return {
        "stats": stats,
        "academic": academic,
        "pending_leaves_count": len(pending_leaves),
        "pending_marks_count": len(pending_marks),
        "total_subjects": len(marks_status)
    }


# =====================================================================
# HOD Executive Dashboard — additional aggregations
# Added in the HOD Dashboard Enhancement iteration to populate the
# Department Operations cards (Recent Notices, Upcoming Events,
# Maintenance) and the Academic Health & Risk card (Marks Completion).
# All functions reuse the existing department-scoping pattern:
# dept_id is always derived from the authenticated HOD's
# department_hod_assignments row (never trusted from the request).
# =====================================================================


def get_upcoming_department_events(dept_id, limit=5):
    """Return the next N upcoming events for the department.

    Business rule (HOD Dashboard blueprint §4.2, Q4 default):
      - Includes events targeted at this department OR audience='All'.
      - Only events with event_date >= today (future / today).
      - Only events with status='Published' (excludes Draft, Pending, Cancelled).
      - Ordered by event_date ASC (soonest first).
      - Capped at `limit` (default 5) to keep the dashboard card compact.

    Returns an empty list on connection failure or when no events match —
    the frontend's empty-state ("No events scheduled") handles this.
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT event_id, event_name, description, event_date, venue, status
            FROM events
            WHERE (target_department_id = %s OR target_audience = 'All')
              AND event_date >= CURDATE()
              AND status = 'Published'
            ORDER BY event_date ASC
            LIMIT %s
            """,
            (dept_id, limit),
        )
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching upcoming department events:", e)
        return []
    finally:
        conn.close()


def get_department_marks_completion_percentage(dept_id):
    """Percentage of marks records (for the department's subjects) that have
    been submitted/verified/returned (i.e. NOT in Draft status).

    Business rule (HOD Dashboard blueprint §5.3, Q6 default):
      - "Completed" = submission_status IN ('Submitted', 'Verified', 'Returned').
        (Returned marks ARE completed from the teacher's perspective — they
        submitted; the HOD returned them for correction. The percentage
        measures teacher-side submission completion, not HOD-side approval.)
      - Total = all marks records for subjects where s.department_id = dept_id.
      - Zero-denominator → 0 (no divide-by-zero).
      - Returns a float in the range [0.0, 100.0], rounded to 2 decimals.

    Used by the Academic Health & Risk "Marks Completion" progress bar on
    the HOD Executive Dashboard.
    """
    conn = get_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN m.submission_status != 'Draft' THEN 1 ELSE 0 END) AS completed
            FROM marks m
            INNER JOIN subjects s ON m.subject_id = s.subject_id
            WHERE s.department_id = %s
            """,
            (dept_id,),
        )
        result = cursor.fetchone()
        if not result or not result["total"] or result["total"] == 0:
            return 0
        completed = result["completed"] if result["completed"] is not None else 0
        return round((completed / result["total"]) * 100, 2)
    except Exception as e:
        print("Error fetching department marks completion percentage:", e)
        return 0
    finally:
        conn.close()