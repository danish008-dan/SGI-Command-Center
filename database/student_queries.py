# database/student_queries.py
from utils.grade import calculate_grade
from database.connection import get_connection
from datetime import datetime, timedelta

def get_student_id_from_user(user_id):
    """Gets the student_id from the users table."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result["student_id"] if result else None
    except Exception as e:
        print("Error getting student_id:", e)
        return None
    finally:
        conn.close()


def get_student_profile(user_id):
    """Fetches the logged-in student's profile details."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT u.full_name, u.email, s.enrollment_no, 
                   d.department_name, s.semester, s.section, s.cgpa
            FROM students s
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE u.user_id = %s
        """
        cursor.execute(sql, (user_id,))
        return cursor.fetchone()
    except Exception as e:
        print("Error fetching student profile:", e)
        return None
    finally:
        conn.close()


def get_student_attendance_report(student_id):
    """Fetches subject-wise attendance for a student using the SQL view."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT subject_name, total_classes, present, absent, percentage
            FROM attendance_summary
            WHERE student_id = %s
            ORDER BY subject_name
        """
        cursor.execute(sql, (student_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching student attendance report:", e)
        return []
    finally:
        conn.close()


def get_student_overall_attendance(student_id):
    """Calculates overall attendance percentage across all subjects."""
    conn = get_connection()
    if conn is None: return 0
    try:
        cursor = conn.cursor()
        sql = """
            SELECT 
                SUM(total_classes) as grand_total, 
                SUM(present) as grand_present
            FROM attendance_summary
            WHERE student_id = %s
        """
        cursor.execute(sql, (student_id,))
        result = cursor.fetchone()
        if result and result["grand_total"] is not None and result["grand_total"] > 0:
            return round((result["grand_present"] / result["grand_total"]) * 100, 2)
        return 0
    except Exception as e:
        print("Error fetching overall attendance:", e)
        return 0
    finally:
        conn.close()



def get_student_overall_result(student_id):
    """Calculates overall percentage and grade across all marks."""
    conn = get_connection()
    if conn is None: return 0, 'N/A'
    try:
        cursor = conn.cursor()
        sql = """
            SELECT SUM(maximum_marks) as total_max, SUM(obtained_marks) as total_obt
            FROM marks
            WHERE student_id = %s
        """
        cursor.execute(sql, (student_id,))
        result = cursor.fetchone()
        if result and result["total_max"] is not None and result["total_max"] > 0:
            overall = round((float(result["total_obt"]) / float(result["total_max"])) * 100, 2)
            grade = calculate_grade(overall)
            return overall, grade
        return 0, 'N/A'
    except Exception as e:
        print("Error fetching overall result:", e)
        return 0, 'N/A'
    finally:
        conn.close()


def get_student_marks_report(student_id):
    """Fetches all VERIFIED marks for a student and calculates percentages/grades."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT s.subject_name, s.subject_code, m.exam_type, m.maximum_marks, m.obtained_marks
            FROM marks m
            INNER JOIN subjects s ON m.subject_id = s.subject_id
            WHERE m.student_id = %s AND m.submission_status = 'Verified'
            ORDER BY s.subject_name, m.exam_type
        """
        cursor.execute(sql, (student_id,))
        rows = cursor.fetchall()

        report = []
        for row in rows:
            max_m = float(row["maximum_marks"])
            obt_m = float(row["obtained_marks"])
            percentage = round((obt_m / max_m) * 100, 2) if max_m > 0 else 0
            grade = calculate_grade(percentage)

            report.append({
                "subject_name": row["subject_name"],
                "subject_code": row["subject_code"],
                "exam_type": row["exam_type"],
                "maximum_marks": max_m,
                "obtained_marks": obt_m,
                "percentage": percentage,
                "grade": grade
            })
        return report
    except Exception as e:
        print("Error fetching student marks:", e)
        return []
    finally:
        conn.close()

def get_student_published_results(student_id):
    """Fetches ALL published historical results for the student."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT semester, total_marks, obtained_marks, percentage, sgpa, cgpa, grade, status, published_at
            FROM results
            WHERE student_id = %s AND status = 'Published'
            ORDER BY semester DESC
        """
        cursor.execute(sql, (student_id,))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching student results:", e)
        return []
    finally:
        conn.close()

def get_semester_subject_marks(student_id, semester):
    """Fetches subject-wise VERIFIED marks for the result view."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT s.subject_name, s.subject_code, s.credits, m.maximum_marks, m.obtained_marks
            FROM marks m
            INNER JOIN subjects s ON m.subject_id = s.subject_id
            WHERE m.student_id = %s AND s.semester = %s AND m.submission_status = 'Verified'
        """
        cursor.execute(sql, (student_id, semester))
        rows = cursor.fetchall()

        for row in rows:
            pct = round((float(row["obtained_marks"]) / float(row["maximum_marks"])) * 100, 2) if row["maximum_marks"] > 0 else 0
            row["percentage"] = pct
            row["grade"] = calculate_grade(pct)
        return rows
    except Exception as e:
        print("Error fetching subject marks:", e)
        return []
    finally:
        conn.close()

def get_student_attendance_log(student_id):
    """Fetches date-wise attendance records for the detailed log view."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT a.attendance_date, sub.subject_name, sub.subject_code, a.status
            FROM attendance a
            INNER JOIN subjects sub ON a.subject_id = sub.subject_id
            WHERE a.student_id = %s
            ORDER BY a.attendance_date DESC, sub.subject_name
        """
        cursor.execute(sql, (student_id,))
        # Convert date objects to string for JSON serialization
        rows = cursor.fetchall()
        for row in rows:
            if row.get("attendance_date"):
                row["attendance_date"] = row["attendance_date"].strftime('%Y-%m-%d')
        return rows
    except Exception as e:
        print("Error fetching attendance log:", e)
        return []
    finally:
        conn.close()

def get_student_notices():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT n.title, n.description, n.posted_on, u.full_name 
            FROM notices n 
            INNER JOIN users u ON n.posted_by = u.user_id
            ORDER BY n.posted_on DESC LIMIT 10
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception: return []
    finally: conn.close()

def get_upcoming_events():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM events WHERE event_date >= CURDATE() ORDER BY event_date ASC"
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print("ERROR fetching events for Student:", e)
        return []
    finally:
        conn.close()

def can_student_complain(student_id):
    """Checks if 3 days have passed since the last complaint."""
    conn = get_connection()
    if conn is None: return True # Allow if DB fails
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM complaints WHERE student_id = %s ORDER BY created_at DESC LIMIT 1", (student_id,))
        last = cursor.fetchone()
        if last:
            # Add 3 days to the last complaint date
            allowed_date = last["created_at"] + timedelta(days=3)
            if datetime.now() < allowed_date:
                return False, allowed_date
        return True, None
    except Exception as e:
        print("Error checking complaint limit:", e)
        return True, None
    finally:
        conn.close()


# Category Routing Configuration
CATEGORY_ROUTING = {
    "Academic": "HOD",
    "Harassment": "Sensitive",
    "Ragging": "Sensitive",
    "Infrastructure": "Admin",
    "IT": "Admin",
    "Finance": "Admin",
    "General": "Admin"
}


def add_student_complaint(student_id, category, complaint_text):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get Student's Department and User ID
        cursor.execute("""
            SELECT u.department_id, s.user_id 
            FROM students s 
            INNER JOIN users u ON s.user_id = u.user_id 
            WHERE s.student_id = %s
        """, (student_id,))
        student_info = cursor.fetchone()
        if not student_info:
            conn.rollback()
            return False, "Student profile not found."

        # 2. Determine Routing and Sensitivity
        routing_rule = CATEGORY_ROUTING.get(category, "Admin")
        sensitivity = "Sensitive" if routing_rule == "Sensitive" else "Normal"
        assigned_to = None

        if routing_rule == "HOD":
            # Find HOD for the student's department
            cursor.execute("""
                SELECT user_id FROM users 
                WHERE role = 'HOD' AND department_id = %s AND status = 'Active' 
                LIMIT 1
            """, (student_info["department_id"],))
            hod = cursor.fetchone()
            if hod:
                assigned_to = hod["user_id"]

        # 3. Insert Complaint
        cursor.execute("""
            INSERT INTO complaints (student_id, category, complaint, status, sensitivity, assigned_to)
            VALUES (%s, %s, %s, 'Pending', %s, %s)
        """, (student_id, category, complaint_text, sensitivity, assigned_to))

        complaint_id = cursor.lastrowid

        # 4. Log in History
        action_desc = "Complaint submitted and routed to " + (
            f"HOD (User ID: {assigned_to})" if assigned_to else "Grievance Coordinator Queue" if routing_rule == "Admin" else "Restricted Sensitive Queue")
        cursor.execute("""
            INSERT INTO complaint_history (complaint_id, changed_by, new_status, new_assignee, action, reason)
            VALUES (%s, %s, 'Pending', %s, %s, %s)
        """, (complaint_id, student_info["user_id"], assigned_to, "Created", action_desc))

        conn.commit()
        return True, "Complaint registered successfully. Reference: CMP" + str(complaint_id).zfill(6)
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

def get_student_complaints(student_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT complaint_id, category, complaint, status, created_at, resolved_at FROM complaints WHERE student_id = %s ORDER BY created_at DESC", (student_id,))
        return cursor.fetchall()
    except Exception: return []
    finally: conn.close()


def get_student_profile_for_ai(user_id):
    """Fetches only the fields needed for the AI Career Counsellor."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT cgpa, skills, interests FROM students WHERE user_id = %s", (user_id,))
        return cursor.fetchone()
    except Exception:
        return None
    finally:
        conn.close()

def save_career_recommendation(student_id, full_response_text):
    """Saves the AI Markdown response to the database."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        # Check if student already has a recommendation
        cursor.execute("SELECT recommendation_id FROM career_recommendations WHERE student_id = %s", (student_id,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute(
                "UPDATE career_recommendations SET full_response = %s, generated_on = NOW() WHERE student_id = %s",
                (full_response_text, student_id))
        else:
            cursor.execute("INSERT INTO career_recommendations (student_id, full_response) VALUES (%s, %s)",
                           (student_id, full_response_text))
        conn.commit()
        return True
    except Exception as e:
        print("Error saving recommendation:", e)
        return False
    finally:
        conn.close()

def get_saved_career_recommendation(student_id):
    """Fetches the last saved AI recommendation as a string."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_response FROM career_recommendations WHERE student_id = %s ORDER BY generated_on DESC LIMIT 1",
            (student_id,))
        result = cursor.fetchone()
        if result and result["full_response"]:
            return result["full_response"] # Return the string directly
        return None
    except Exception:
        return None
    finally:
        conn.close()

def save_resume_analysis(student_id, file_path, ai_response_json):
    """Saves or updates the resume analysis in the database."""
    conn = get_connection()
    if conn is None: return False
    try:
        import json
        json_string = json.dumps(ai_response_json)
        cursor = conn.cursor()

        # Check if student already has an analysis
        cursor.execute("SELECT analysis_id FROM resume_analysis WHERE student_id = %s", (student_id,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute("""
                UPDATE resume_analysis 
                SET resume_file = %s, full_response = %s, analyzed_on = NOW() 
                WHERE student_id = %s
            """, (file_path, json_string, student_id))
        else:
            cursor.execute("""
                INSERT INTO resume_analysis (student_id, resume_file, full_response) 
                VALUES (%s, %s, %s)
            """, (student_id, file_path, json_string))
        conn.commit()
        return True
    except Exception as e:
        print("Error saving resume analysis:", e)
        return False
    finally:
        conn.close()


def get_saved_resume_analysis(student_id):
    """Fetches the last saved AI resume analysis."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_response, resume_file FROM resume_analysis WHERE student_id = %s ORDER BY analyzed_on DESC LIMIT 1",
            (student_id,))
        result = cursor.fetchone()
        if result and result["full_response"]:
            import json
            data = json.loads(result["full_response"])
            data["resume_file"] = result["resume_file"]
            return data
        return None
    except Exception:
        return None
    finally:
        conn.close()

def get_student_timetable(dept_id, sem, sec):
    """Fetches ONLY published timetable for a student's class."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
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
            WHERE t.department_id = %s AND t.semester = %s AND t.section = %s AND t.status = 'Published'
            ORDER BY ts.start_time
        """
        cursor.execute(sql, (dept_id, sem, sec))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching student timetable:", e)
        return []
    finally:
        conn.close()


def apply_for_revaluation(student_id, semester, subject_id, reason):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        # Check if result is published
        cursor.execute("SELECT status FROM results WHERE student_id = %s AND semester = %s", (student_id, semester))
        res = cursor.fetchone()
        if not res or res["status"] != 'Published':
            return False, "Can only apply for published results."

        cursor.execute("""
            INSERT INTO revaluation_requests (student_id, semester, subject_id, reason)
            VALUES (%s, %s, %s, %s)
        """, (student_id, semester, subject_id, reason))
        conn.commit()
        return True, "Revaluation request submitted successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_student_complaint_details(complaint_id, user_id):
    """Fetches complaint details, history, and student-visible messages for verification."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()

        # 1. Verify complaint belongs to the user
        cursor.execute("""
            SELECT c.* FROM complaints c
            INNER JOIN students s ON c.student_id = s.student_id
            WHERE c.complaint_id = %s AND s.user_id = %s
        """, (complaint_id, user_id))
        complaint = cursor.fetchone()
        if not complaint: return None

        # 2. Fetch Student-Visible Messages (is_internal_note = FALSE)
        cursor.execute("""
            SELECT message_text, created_at, sender_id
            FROM complaint_messages
            WHERE complaint_id = %s AND is_internal_note = FALSE
            ORDER BY created_at ASC
        """, (complaint_id,))
        messages = cursor.fetchall()

        # 3. Fetch Status History
        cursor.execute("""
            SELECT action, reason, created_at
            FROM complaint_history
            WHERE complaint_id = %s
            ORDER BY created_at ASC
        """, (complaint_id,))
        history = cursor.fetchall()

        complaint["messages"] = messages
        complaint["history"] = history
        return complaint
    except Exception as e:
        print("Error fetching details:", e)
        return None
    finally:
        conn.close()

# ==========================================
# PHASE 3: CAMPUS SERVICES (READ-ONLY)
# ==========================================

def get_student_library_loans(user_id):
    """Fetches library loan records for the authenticated student."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT lb.title, lb.author, lc.accession_number, 
                   ll.issue_date, ll.due_date, ll.return_date, ll.status, ll.fine_amount
            FROM library_loans ll
            INNER JOIN library_copies lc ON ll.copy_id = lc.copy_id
            INNER JOIN library_books lb ON lc.book_id = lb.book_id
            WHERE ll.user_id = %s
            ORDER BY ll.issue_date DESC
        """
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        for row in rows:
            if row.get("issue_date"): row["issue_date"] = row["issue_date"].strftime('%Y-%m-%d')
            if row.get("due_date"): row["due_date"] = row["due_date"].strftime('%Y-%m-%d')
            if row.get("return_date"): row["return_date"] = row["return_date"].strftime('%Y-%m-%d')
        return rows
    except Exception as e:
        print("Error fetching library loans:", e)
        return []
    finally:
        conn.close()


def get_student_hostel_allocation(student_id):
    """Fetches active hostel allocation for the authenticated student."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT hr.hostel_name, hr.room_number, hr.room_type, hb.bed_number, 
                   ha.check_in_date, ha.expected_check_out, ha.status
            FROM hostel_allocations ha
            INNER JOIN hostel_beds hb ON ha.bed_id = hb.bed_id
            INNER JOIN hostel_rooms hr ON hb.room_id = hr.room_id
            WHERE ha.student_id = %s AND ha.status = 'Active'
            LIMIT 1
        """
        cursor.execute(sql, (student_id,))
        result = cursor.fetchone()
        if result:
            if result.get("check_in_date"): result["check_in_date"] = result["check_in_date"].strftime('%Y-%m-%d')
            if result.get("expected_check_out"): result["expected_check_out"] = result["expected_check_out"].strftime('%Y-%m-%d')
        return result
    except Exception as e:
        print("Error fetching hostel allocation:", e)
        return None
    finally:
        conn.close()

def get_student_transport_allocation(student_id):
    """Fetches active transport allocation for the authenticated student."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT tr.route_name, tr.start_point, tr.end_point, 
                   ts.stop_name, ta.effective_from, ta.status
            FROM transport_allocations ta
            INNER JOIN transport_routes tr ON ta.route_id = tr.route_id
            LEFT JOIN transport_stops ts ON ta.stop_id = ts.stop_id
            WHERE ta.student_id = %s AND ta.status = 'Active'
            LIMIT 1
        """
        cursor.execute(sql, (student_id,))
        result = cursor.fetchone()
        if result:
            if result.get("effective_from"): result["effective_from"] = result["effective_from"].strftime('%Y-%m-%d')
        return result
    except Exception as e:
        print("Error fetching transport allocation:", e)
        return None
    finally:
        conn.close()


# ==========================================
# PHASE 4: LEARNING & ACADEMIC ENGAGEMENT
# ==========================================

def get_student_assignments(student_id, dept_id, sem, sec):
    """Fetches assignments matching the student's enrollment scope."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT a.assignment_id, a.title, a.description, a.due_date, 
                   s.subject_name, s.subject_code, u.full_name AS teacher_name
            FROM assignments a
            INNER JOIN subjects s ON a.subject_id = s.subject_id
            LEFT JOIN teachers t ON a.teacher_id = t.teacher_id
            LEFT JOIN users u ON t.user_id = u.user_id
            WHERE s.department_id = %s AND s.semester = %s AND (s.section = %s OR s.section IS NULL)
            ORDER BY a.due_date DESC
        """
        cursor.execute(sql, (dept_id, sem, sec))
        rows = cursor.fetchall()
        for row in rows:
            if row.get("due_date"): row["due_date"] = row["due_date"].strftime('%Y-%m-%d')
        return rows
    except Exception as e:
        print("Error fetching student assignments:", e)
        return []
    finally:
        conn.close()

def get_student_submission_status(student_id, assignment_id):
    """Checks if a student has already submitted a specific assignment."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT submission_id, file_path, submission_date, marks, remarks
            FROM assignment_submissions
            WHERE student_id = %s AND assignment_id = %s
        """
        cursor.execute(sql, (student_id, assignment_id))
        result = cursor.fetchone()
        if result and result.get("submission_date"):
            result["submission_date"] = result["submission_date"].strftime('%Y-%m-%d %H:%M')
        return result
    except Exception as e:
        print("Error checking submission status:", e)
        return None
    finally:
        conn.close()


def save_student_submission(student_id, assignment_id, file_path):
    """Saves or updates the student's submission record."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        # Check if already submitted (UPSERT logic)
        cursor.execute("SELECT submission_id FROM assignment_submissions WHERE student_id = %s AND assignment_id = %s",
                       (student_id, assignment_id))
        exists = cursor.fetchone()

        if exists:
            cursor.execute("""
                UPDATE assignment_submissions 
                SET file_path = %s, submission_date = NOW(), marks = NULL, remarks = NULL
                WHERE submission_id = %s
            """, (file_path, exists["submission_id"]))
        else:
            cursor.execute("""
                INSERT INTO assignment_submissions (assignment_id, student_id, file_path, submission_date)
                VALUES (%s, %s, %s, NOW())
            """, (assignment_id, student_id, file_path))

        conn.commit()
        return True, "Assignment submitted successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def verify_assignment_scope(student_id, assignment_id):
    """Verifies that the assignment belongs to the student's academic scope."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        # Join assignments -> subjects -> students to verify scope
        cursor.execute("""
            SELECT 1 FROM assignments a
            INNER JOIN subjects s ON a.subject_id = s.subject_id
            INNER JOIN students st ON s.department_id = st.department_id AND s.semester = st.semester AND (s.section = st.section OR s.section IS NULL)
            WHERE st.student_id = %s AND a.assignment_id = %s
        """, (student_id, assignment_id))
        return cursor.fetchone() is not None
    except Exception:
        return False
    finally:
        conn.close()


def get_student_materials(dept_id):
    """Fetches approved learning materials for the student's department."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT document_id, title, status, created_at
            FROM documents
            WHERE department_id = %s AND status = 'Approved'
            ORDER BY created_at DESC
        """
        cursor.execute(sql, (dept_id,))
        rows = cursor.fetchall()
        for row in rows:
            if row.get("created_at"): row["created_at"] = row["created_at"].strftime('%Y-%m-%d')
        return rows
    except Exception as e:
        print("Error fetching materials:", e)
        return []
    finally:
        conn.close()

# ==========================================
# PHASE 5: CAREER, TRAINING & PLACEMENT
# ==========================================

def get_student_cgpa(student_id):
    """Fetches the student's CGPA for placement eligibility checks."""
    conn = get_connection()
    if conn is None: return 0.0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT cgpa FROM students WHERE student_id = %s", (student_id,))
        result = cursor.fetchone()
        return float(result["cgpa"]) if result and result["cgpa"] else 0.0
    except Exception:
        return 0.0
    finally:
        conn.close()

def get_placement_drives():
    """Fetches all available placement drives (companies)."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Since there's no 'status' column, we treat all companies as active drives
        sql = """
            SELECT company_id, company_name, location, package, eligibility_cgpa, required_skills, website
            FROM companies
            ORDER BY company_name
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching placement drives:", e)
        return []
    finally:
        conn.close()

def get_student_applications(student_id):
    """Fetches a student's placement application history."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT pa.application_id, pa.status, pa.applied_on, c.company_name, c.package
            FROM placement_applications pa
            INNER JOIN companies c ON pa.company_id = c.company_id
            WHERE pa.student_id = %s
            ORDER BY pa.applied_on DESC
        """
        cursor.execute(sql, (student_id,))
        rows = cursor.fetchall()
        for row in rows:
            if row.get("applied_on"): row["applied_on"] = row["applied_on"].strftime('%Y-%m-%d')
        return rows
    except Exception as e:
        print("Error fetching student applications:", e)
        return []
    finally:
        conn.close()

def check_existing_application(student_id, company_id):
    """Checks if a student has already applied to a specific company."""
    conn = get_connection()
    if conn is None: return True # Safer to assume exists if DB fails
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM placement_applications WHERE student_id = %s AND company_id = %s", (student_id, company_id))
        return cursor.fetchone() is not None
    except Exception:
        return True
    finally:
        conn.close()

def create_placement_application(student_id, company_id):
    """Creates a new placement application with 'Applied' status."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO placement_applications (student_id, company_id, status, applied_on)
            VALUES (%s, %s, 'Applied', NOW())
        """, (student_id, company_id))
        conn.commit()
        return True, "Application submitted successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ==========================================
# PHASE 6: ADVANCED RESUME ANALYZER & BUILDER
# ==========================================

import json
from datetime import datetime


def save_resume_analysis_history(student_id, file_path, analysis_json, jd_used):
    """Saves a new resume analysis record to history."""
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resume_analysis_history (student_id, resume_file_path, analysis_json, jd_used)
            VALUES (%s, %s, %s, %s)
        """, (student_id, file_path, json.dumps(analysis_json), jd_used))
        conn.commit()
        return True
    except Exception as e:
        print("Error saving resume history:", e)
        return False
    finally:
        conn.close()


def get_latest_resume_analysis(student_id):
    """Fetches the most recent resume analysis."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT history_id, resume_file_path, analysis_json, jd_used, created_at
            FROM resume_analysis_history 
            WHERE student_id = %s 
            ORDER BY created_at DESC LIMIT 1
        """, (student_id,))
        result = cursor.fetchone()
        if result:
            if result.get("created_at"): result["created_at"] = result["created_at"].strftime('%Y-%m-%d %H:%M')
            result["analysis_json"] = json.loads(result["analysis_json"])
        return result
    except Exception as e:
        print("Error fetching latest analysis:", e)
        return None
    finally:
        conn.close()


def get_resume_history(student_id):
    """Fetches all historical resume analyses for the student."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT history_id, jd_used, created_at
            FROM resume_analysis_history 
            WHERE student_id = %s 
            ORDER BY created_at DESC
        """, (student_id,))
        rows = cursor.fetchall()
        for row in rows:
            if row.get("created_at"): row["created_at"] = row["created_at"].strftime('%Y-%m-%d %H:%M')
        return rows
    except Exception:
        return []
    finally:
        conn.close()


def get_resume_history_by_id(history_id, student_id):
    """Fetches a specific history record and validates ownership (IDOR protection)."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT resume_file_path, analysis_json
            FROM resume_analysis_history 
            WHERE history_id = %s AND student_id = %s
        """, (history_id, student_id))
        result = cursor.fetchone()
        if result:
            result["analysis_json"] = json.loads(result["analysis_json"])
        return result
    except Exception:
        return None
    finally:
        conn.close()


def get_resume_draft(student_id):
    """Fetches the student's resume builder draft, migrated to v2 in-memory.

    Per blueprint v2 §4.5, the stored draft is NOT modified by the load
    path; the migration runs in-memory and only the returned dict reflects
    the v2 shape. The v2 shape persists only on an explicit Save.
    """
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT draft_id, content_json FROM resume_drafts WHERE student_id = %s LIMIT 1", (student_id,))
        result = cursor.fetchone()
        if result:
            raw = result["content_json"]
            if isinstance(raw, str):
                raw = json.loads(raw)
            # In-memory migration: stored draft is NOT modified
            try:
                from utils.resume_migration import migrate_v1_to_v2
                migrated = migrate_v1_to_v2(raw)
            except Exception:
                # Defensive: if migration fails (e.g. corrupt JSON),
                # return a minimal v2 skeleton so the form still loads.
                from utils.resume_migration import _empty_v2
                migrated = _empty_v2()
            return {"draft_id": result["draft_id"], "content_json": migrated}
        return None
    except Exception:
        return None
    finally:
        conn.close()


def save_resume_draft(student_id, content_json):
    """Saves or updates the student's resume builder draft.

    Per blueprint v2 §4.5, this uses the UPDATE-first-then-INSERT pattern
    (1 query in the common case) that transparently handles duplicate rows
    for the same student_id (legacy race condition residue) without
    requiring a UNIQUE constraint at the schema level.

    Stamps schema_version=2 and template_id on every save so future loads
    can detect the stored shape.

    Optional dedup (off by default): set env var RESUME_DEDUP_ON_SAVE=1
    to enable cleanup of duplicate rows for the same student. Off by
    default to avoid surprise writes; intended for DBA opt-in use.
    """
    import os as _os
    conn = get_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        # Defensive: ensure schema_version is set, without mutating caller's dict
        stamped = dict(content_json) if isinstance(content_json, dict) else {}
        stamped["schema_version"] = 2
        if "template_id" not in stamped:
            stamped["template_id"] = "dnish_latex_a4"
        json_string = json.dumps(stamped)
        # UPDATE all existing rows for this student (handles duplicates transparently)
        cursor.execute(
            "UPDATE resume_drafts SET content_json = %s, template_id = %s WHERE student_id = %s",
            (json_string, stamped["template_id"], student_id)
        )
        if cursor.rowcount == 0:
            # No existing row — INSERT
            cursor.execute(
                "INSERT INTO resume_drafts (student_id, content_json, template_id) VALUES (%s, %s, %s)",
                (student_id, json_string, stamped["template_id"])
            )
        # Optional dedup (off by default; DBA opt-in via env var)
        if _os.getenv("RESUME_DEDUP_ON_SAVE") == "1":
            cursor.execute(
                "DELETE FROM resume_drafts WHERE student_id = %s "
                "AND draft_id NOT IN ("
                "  SELECT min_id FROM ("
                "    SELECT MIN(draft_id) AS min_id FROM resume_drafts WHERE student_id = %s"
                "  ) AS m"
                ")",
                (student_id, student_id)
            )
        conn.commit()
        return True
    except Exception as e:
        print("Error saving resume draft:", e)
        return False
    finally:
        conn.close()


def get_student_service_preferences(student_id):
    """Fetches the service preferences for the authenticated student."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT hostel_service_enabled, transport_service_enabled FROM students WHERE student_id = %s",
                       (student_id,))
        return cursor.fetchone()
    except Exception as e:
        print("Error fetching preferences:", e)
        return None
    finally:
        conn.close()


def update_student_service_preference(student_id, service_type, is_enabled):
    """Updates the student's service preference (hostel or transport)."""
    conn = get_connection()
    if conn is None: return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        col_name = "hostel_service_enabled" if service_type == "hostel" else "transport_service_enabled"

        # Execute the update. We do NOT check rowcount because PyMySQL
        # returns 0 rows if the value is unchanged, which causes false errors.
        sql = f"UPDATE students SET {col_name} = %s WHERE student_id = %s"
        cursor.execute(sql, (is_enabled, student_id))
        conn.commit()

        return True, "Preference updated successfully."
    except Exception as e:
        print("Error updating preference:", e)
        return False, str(e)
    finally:
        conn.close()