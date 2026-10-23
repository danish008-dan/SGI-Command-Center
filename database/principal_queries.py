# database/principal_queries.py
from database.connection import get_connection


def get_college_stats():
    """Fetches global stats for the Principal Executive Dashboard."""
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Academic Health (Active Students & Faculty)
        cursor.execute(
            "SELECT COUNT(*) as count FROM students s INNER JOIN users u ON s.user_id = u.user_id WHERE u.status = 'Active'")
        students = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT COUNT(*) as count FROM teachers t INNER JOIN users u ON t.user_id = u.user_id WHERE u.status = 'Active'")
        teachers = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM departments WHERE status = 'Active'")
        departments = cursor.fetchone()["count"]

        # 2. Financial Health (Collected vs Pending)
        cursor.execute("SELECT IFNULL(SUM(amount_paid), 0) as total FROM fee_payments")
        collected = float(cursor.fetchone()["total"])

        cursor.execute("""
            SELECT IFNULL(SUM(sf.payable_fee - IFNULL(p.paid, 0)), 0) as pending
            FROM student_fees sf
            LEFT JOIN (SELECT student_fee_id, SUM(amount_paid) as paid FROM fee_payments GROUP BY student_fee_id) p 
            ON sf.student_fee_id = p.student_fee_id
            WHERE sf.status != 'Paid'
        """)
        pending = float(cursor.fetchone()["pending"])

        # 3. Approval & Pending Actions
        cursor.execute("SELECT COUNT(*) as count FROM results WHERE approval_status = 'Pending Principal'")
        pending_results = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM concession_requests WHERE status = 'Pending'")
        pending_concessions = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM notices WHERE status = 'Pending'")
        pending_notices = cursor.fetchone()["count"]

        # 4. Compliance Health
        cursor.execute("""
            SELECT COUNT(*) as count FROM compliance_requirements 
            WHERE status NOT IN ('Verified', 'Submitted', 'Not Applicable') 
            AND (due_date IS NULL OR due_date >= CURDATE())
        """)
        pending_compliance = cursor.fetchone()["count"]

        return {
            "students": students, "teachers": teachers, "departments": departments,
            "collected": collected, "pending": pending,
            "pending_results": pending_results,
            "pending_concessions": pending_concessions,
            "pending_notices": pending_notices,
            "pending_compliance": pending_compliance
        }
    except Exception as e:
        print("Error fetching exec dashboard stats:", e)
        return {}
    finally:
        conn.close()

def get_department_wise_analysis():
    """Fetches student count and avg attendance per department."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT d.department_name, 
                   COUNT(DISTINCT s.student_id) as student_count,
                   COUNT(DISTINCT t.teacher_id) as teacher_count
            FROM departments d
            LEFT JOIN users u ON d.department_id = u.department_id AND u.status = 'Active'
            LEFT JOIN students s ON u.user_id = s.user_id
            LEFT JOIN teachers t ON u.user_id = t.user_id
            GROUP BY d.department_id, d.department_name
            ORDER BY d.department_name
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching dept analysis:", e)
        return []
    finally:
        conn.close()


def get_principal_ai_context():
    """Gathers live college data (records & stats) for the AI to analyze."""
    conn = get_connection()
    if conn is None: return "No data available."
    try:
        cursor = conn.cursor()
        context = "Live College Database Records:\n\n"

        # 1. Departments
        cursor.execute("SELECT department_name, hod_name FROM departments")
        depts = cursor.fetchall()
        context += "Departments:\n" + "\n".join(
            [f"- {d['department_name']} (HOD: {d['hod_name'] or 'N/A'})" for d in depts]) + "\n\n"

        # 2. Students (Fetching names and departments)
        cursor.execute("""
            SELECT u.full_name, d.department_name, s.semester 
            FROM students s 
            JOIN users u ON s.user_id = u.user_id 
            LEFT JOIN departments d ON u.department_id = d.department_id
        """)
        students = cursor.fetchall()
        context += "Students List:\n" + "\n".join(
            [f"- {s['full_name']} (Dept: {s['department_name'] or 'N/A'}, Sem: {s['semester']})" for s in
             students]) + "\n\n"

        # 3. Teachers
        cursor.execute("""
            SELECT u.full_name, d.department_name, t.designation 
            FROM teachers t 
            JOIN users u ON t.user_id = u.user_id 
            LEFT JOIN departments d ON u.department_id = d.department_id
        """)
        teachers = cursor.fetchall()
        context += "Teachers List:\n" + "\n".join(
            [f"- {t['full_name']} (Dept: {t['department_name'] or 'N/A'}, Role: {t['designation']})" for t in
             teachers]) + "\n\n"

        # 4. Complaints Summary
        cursor.execute("SELECT status, COUNT(*) as count FROM complaints GROUP BY status")
        comp_data = cursor.fetchall()
        context += "Complaints Summary: " + ", ".join([f"{r['status']} ({r['count']})" for r in comp_data]) + ".\n\n"

        # 5. Fees Summary
        cursor.execute("SELECT IFNULL(SUM(amount_paid), 0) as c FROM fee_payments")
        collected = cursor.fetchone()["c"]
        context += f"Total Fees Collected: Rs.{collected}.\n\n"

        return context
    except Exception as e:
        print("Error fetching principal context:", e)
        return "Error fetching data."
    finally:
        conn.close()


def get_pending_results_for_principal(semester=None):
    """Fetches results pending Principal approval."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT r.student_id, u.full_name, r.semester, r.percentage, r.sgpa, r.grade, r.approval_status
            FROM results r
            INNER JOIN students s ON r.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE r.approval_status = 'Pending Principal'
        """
        params = []
        if semester:
            sql += " AND r.semester = %s"
            params.append(semester)

        sql += " ORDER BY r.semester, u.full_name"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching pending results:", e)
        return []
    finally:
        conn.close()


def approve_results_by_principal(semester, principal_id):
    """Approves results for a semester."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE results 
            SET approval_status = 'Approved', approval_remarks = 'Approved by Principal'
            WHERE semester = %s AND approval_status = 'Pending Principal'
        """, (semester,))
        conn.commit()
        return True, f"Semester {semester} results approved successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def reject_results_by_principal(semester, reason, principal_id):
    """Rejects results and returns them to Admin with a reason."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE results 
            SET approval_status = 'Rejected', approval_remarks = %s
            WHERE semester = %s AND approval_status = 'Pending Principal'
        """, (reason, semester))
        conn.commit()
        return True, f"Semester {semester} results rejected and returned to Admin."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# database/principal_queries.py (Append to existing file)

def get_academic_oversight_stats():
    """Fetches institution-wide academic health metrics."""
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Overall Average Attendance (using the existing view)
        cursor.execute("SELECT IFNULL(AVG(percentage), 0) as avg_attendance FROM attendance_summary")
        avg_attendance = round(float(cursor.fetchone()["avg_attendance"]), 2)

        # 2. Result Performance (Average CGPA of Published Results)
        cursor.execute("SELECT IFNULL(AVG(cgpa), 0) as avg_cgpa FROM results WHERE status = 'Published'")
        avg_cgpa = round(float(cursor.fetchone()["avg_cgpa"]), 2)

        # 3. Pending Results (Draft / Pending Principal)
        cursor.execute("SELECT COUNT(*) as count FROM results WHERE approval_status IN ('Draft', 'Pending Principal')")
        pending_results = cursor.fetchone()["count"]

        # 4. Pending Marks Verification (Submitted but not Verified)
        cursor.execute("SELECT COUNT(*) as count FROM marks WHERE submission_status = 'Submitted'")
        pending_marks = cursor.fetchone()["count"]

        return {
            "avg_attendance": avg_attendance,
            "avg_cgpa": avg_cgpa,
            "pending_results": pending_results,
            "pending_marks": pending_marks
        }
    except Exception as e:
        print("Error fetching academic stats:", e)
        return {}
    finally:
        conn.close()


def get_department_wise_academics():
    """Fetches academic performance broken down by department."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT d.department_name, 
                   COUNT(DISTINCT s.student_id) as student_count,
                   IFNULL(AVG(att.percentage), 0) as avg_attendance,
                   IFNULL(AVG(r.cgpa), 0) as avg_cgpa
            FROM departments d
            LEFT JOIN users u ON d.department_id = u.department_id AND u.status = 'Active' AND u.role = 'Student'
            LEFT JOIN students s ON u.user_id = s.user_id
            LEFT JOIN attendance_summary att ON s.student_id = att.student_id
            LEFT JOIN results r ON s.student_id = r.student_id AND r.status = 'Published'
            GROUP BY d.department_id, d.department_name
            ORDER BY d.department_name
        """
        cursor.execute(sql)
        depts = cursor.fetchall()

        # Format numbers for UI
        for dept in depts:
            dept["avg_attendance"] = round(float(dept["avg_attendance"]), 2)
            dept["avg_cgpa"] = round(float(dept["avg_cgpa"]), 2)

        return depts
    except Exception as e:
        print("Error fetching dept academics:", e)
        return []
    finally:
        conn.close()


# database/principal_queries.py (Append to existing file)

# ==========================================
# FINANCE OVERSIGHT (Phase 6)
# ==========================================
def get_finance_oversight_stats():
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Total Demand & Collected
        cursor.execute("SELECT IFNULL(SUM(payable_fee), 0) as demand FROM student_fees")
        demand = float(cursor.fetchone()["demand"])

        cursor.execute("SELECT IFNULL(SUM(amount_paid), 0) as collected FROM fee_payments")
        collected = float(cursor.fetchone()["collected"])

        outstanding = demand - collected
        collection_rate = round((collected / demand) * 100, 2) if demand > 0 else 0

        # 2. Pending Concessions
        cursor.execute("SELECT COUNT(*) as count FROM concession_requests WHERE status = 'Pending'")
        pending_concessions = cursor.fetchone()["count"]

        return {
            "demand": demand, "collected": collected,
            "outstanding": outstanding, "collection_rate": collection_rate,
            "pending_concessions": pending_concessions
        }
    except Exception as e:
        print("Error fetching finance stats:", e)
        return {}
    finally:
        conn.close()


# ==========================================
# HR & PAYROLL OVERSIGHT (Phase 6)
# ==========================================
def get_hr_oversight_stats():
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Faculty vs Non-Teaching Staff
        cursor.execute(
            "SELECT COUNT(*) as count FROM teachers t INNER JOIN users u ON t.user_id = u.user_id WHERE u.status = 'Active'")
        faculty = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM employees WHERE status = 'Active'")
        staff = cursor.fetchone()["count"]
        total_workforce = faculty + staff

        # 2. Pending Salary Revisions (HR Approvals)
        cursor.execute("SELECT COUNT(*) as count FROM salary_revisions WHERE status = 'Pending'")
        pending_revisions = cursor.fetchone()["count"]

        # 3. Aggregate Payroll (Minimum Necessary Access - No Individual Breakdowns)
        # Summing the latest calculated/approved runs for the current active period
        cursor.execute("""
            SELECT IFNULL(SUM(gross_earnings), 0) as gross, IFNULL(SUM(net_payable), 0) as net 
            FROM payroll_runs 
            WHERE status IN ('Calculated', 'Under Review', 'Approved', 'Finalized')
        """)
        payroll = cursor.fetchone()

        return {
            "faculty": faculty, "staff": staff, "total_workforce": total_workforce,
            "pending_revisions": pending_revisions,
            "gross_payroll": float(payroll["gross"]),
            "net_payroll": float(payroll["net"])
        }
    except Exception as e:
        print("Error fetching HR stats:", e)
        return {}
    finally:
        conn.close()


# ==========================================
# CAMPUS OPERATIONS OVERSIGHT (Phase 6)
# ==========================================
def get_campus_oversight_stats():
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Assets & Inventory
        cursor.execute("SELECT COUNT(*) as count FROM assets WHERE lifecycle_status = 'Active'")
        active_assets = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT COUNT(*) as count FROM inventory_items WHERE current_stock <= reorder_level AND status='Active'")
        low_stock = cursor.fetchone()["count"]

        # 2. Hostel Occupancy
        cursor.execute("SELECT COUNT(*) as total FROM hostel_beds WHERE status != 'Maintenance'")
        total_beds = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as occ FROM hostel_beds WHERE status = 'Occupied'")
        occupied_beds = cursor.fetchone()["occ"]
        hostel_occupancy = round((occupied_beds / total_beds) * 100, 2) if total_beds > 0 else 0

        # 3. Library & Transport
        cursor.execute("SELECT COUNT(*) as count FROM library_copies WHERE status = 'Available'")
        books_avail = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM transport_routes WHERE status = 'Active'")
        transport_routes = cursor.fetchone()["count"]

        # 4. Pending Visitor Approvals
        cursor.execute("SELECT COUNT(*) as count FROM visitors WHERE approval_status = 'Pending'")
        pending_visitors = cursor.fetchone()["count"]

        return {
            "active_assets": active_assets, "low_stock": low_stock,
            "hostel_occupancy": hostel_occupancy, "total_beds": total_beds,
            "books_available": books_avail, "transport_routes": transport_routes,
            "pending_visitors": pending_visitors
        }
    except Exception as e:
        print("Error fetching campus stats:", e)
        return {}
    finally:
        conn.close()


# database/principal_queries.py (Append to existing file)

# ==========================================
# COMPLIANCE & DOCUMENTS OVERSIGHT (Phase 7)
# ==========================================
def get_compliance_oversight_stats():
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Pending Compliance Actions
        cursor.execute("""
            SELECT COUNT(*) as count FROM compliance_requirements 
            WHERE status NOT IN ('Verified', 'Not Applicable')
        """)
        pending_compliance = cursor.fetchone()["count"]

        # 2. Overdue Compliance
        cursor.execute("""
            SELECT COUNT(*) as count FROM compliance_requirements 
            WHERE status NOT IN ('Verified', 'Not Applicable') 
            AND due_date IS NOT NULL AND due_date < CURDATE()
        """)
        overdue_compliance = cursor.fetchone()["count"]

        # 3. Documents Pending Review
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE status = 'Pending Review'")
        pending_docs = cursor.fetchone()["count"]

        return {
            "pending_compliance": pending_compliance,
            "overdue_compliance": overdue_compliance,
            "pending_docs": pending_docs
        }
    except Exception as e:
        print("Error fetching compliance stats:", e)
        return {}
    finally:
        conn.close()


# ==========================================
# MEETINGS & ACTION ITEMS OVERSIGHT (Phase 7)
# ==========================================
def get_meetings_oversight_stats():
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Upcoming Meetings
        cursor.execute(
            "SELECT COUNT(*) as count FROM meetings WHERE meeting_date >= CURDATE() AND status IN ('Scheduled', 'Held', 'Minutes Draft')")
        upcoming_meetings = cursor.fetchone()["count"]

        # 2. Pending Action Items
        cursor.execute("SELECT COUNT(*) as count FROM action_items WHERE status IN ('Open', 'In Progress', 'On Hold')")
        pending_actions = cursor.fetchone()["count"]

        # 3. Overdue Action Items
        cursor.execute("""
            SELECT COUNT(*) as count FROM action_items 
            WHERE status IN ('Open', 'In Progress', 'On Hold') 
            AND due_date IS NOT NULL AND due_date < CURDATE()
        """)
        overdue_actions = cursor.fetchone()["count"]

        return {
            "upcoming_meetings": upcoming_meetings,
            "pending_actions": pending_actions,
            "overdue_actions": overdue_actions
        }
    except Exception as e:
        print("Error fetching meetings stats:", e)
        return {}
    finally:
        conn.close()


# ==========================================
# NOTICES & EVENTS OVERSIGHT (Phase 7)
# ==========================================
def get_notices_events_oversight_stats():
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Published Notices
        cursor.execute("SELECT COUNT(*) as count FROM notices WHERE status = 'Published'")
        published_notices = cursor.fetchone()["count"]

        # 2. Pending Notice Approvals
        cursor.execute("SELECT COUNT(*) as count FROM notices WHERE status = 'Pending'")
        pending_notices = cursor.fetchone()["count"]

        # 3. Upcoming Events
        cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_date >= CURDATE() AND status = 'Published'")
        upcoming_events = cursor.fetchone()["count"]

        return {
            "published_notices": published_notices,
            "pending_notices": pending_notices,
            "upcoming_events": upcoming_events
        }
    except Exception as e:
        print("Error fetching notices stats:", e)
        return {}
    finally:
        conn.close()


# ==========================================
# SENSITIVE COMPLAINTS OVERSIGHT (Phase 7)
# ==========================================
def get_sensitive_complaints_oversight():
    """Fetches aggregated sensitive complaint data. Minimum necessary access applied."""
    conn = get_connection()
    if conn is None: return {}
    try:
        cursor = conn.cursor()

        # 1. Counts by Status (Only Sensitive)
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM complaints 
            WHERE sensitivity = 'Sensitive' 
            GROUP BY status
        """)
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        # 2. Escalated Cases List (Limit to 5 recent, exclude explicit complaint text to protect student privacy on dashboard)
        cursor.execute("""
            SELECT c.complaint_id, c.category, c.priority, c.status, c.created_at, u.full_name as student_name
            FROM complaints c
            INNER JOIN students s ON c.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE c.sensitivity = 'Sensitive' AND c.status IN ('Escalated', 'Pending', 'Assigned')
            ORDER BY c.created_at DESC
            LIMIT 5
        """)
        escalated_list = cursor.fetchall()

        return {
            "status_counts": {
                "pending": status_counts.get("Pending", 0),
                "assigned": status_counts.get("Assigned", 0),
                "in_progress": status_counts.get("In Progress", 0),
                "escalated": status_counts.get("Escalated", 0),
                "resolved": status_counts.get("Resolved", 0)
            },
            "escalated_list": escalated_list
        }
    except Exception as e:
        print("Error fetching sensitive complaints oversight:", e)
        return {}
    finally:
        conn.close()

# ==========================================
# NOTIFICATIONS & ALERTS (Phase 8)
# ==========================================
def get_principal_notifications():
    """Dynamically generates institutional alerts from existing system states."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        alerts = []

        # 1. Pending Approvals
        cursor.execute("SELECT COUNT(*) as count FROM results WHERE approval_status = 'Pending Principal'")
        res_count = cursor.fetchone()["count"]
        if res_count > 0:
            alerts.append({"type": "Approval", "severity": "High",
                           "message": f"{res_count} semester results pending your approval.",
                           "link": "/principal/approvals"})

        cursor.execute("SELECT COUNT(*) as count FROM concession_requests WHERE status = 'Pending'")
        con_count = cursor.fetchone()["count"]
        if con_count > 0:
            alerts.append({"type": "Approval", "severity": "Medium",
                           "message": f"{con_count} fee concession requests pending approval.",
                           "link": "/principal/approvals"})

        # 2. Overdue Compliance
        cursor.execute("""
            SELECT COUNT(*) as count FROM compliance_requirements 
            WHERE status NOT IN ('Verified', 'Not Applicable') 
            AND due_date IS NOT NULL AND due_date < CURDATE()
        """)
        over_comp = cursor.fetchone()["count"]
        if over_comp > 0:
            alerts.append(
                {"type": "Compliance", "severity": "Critical", "message": f"{over_comp} compliance items are overdue.",
                 "link": "/principal/compliance"})

        # 3. Escalated Complaints
        cursor.execute(
            "SELECT COUNT(*) as count FROM complaints WHERE sensitivity = 'Sensitive' AND status = 'Escalated'")
        esc_comp = cursor.fetchone()["count"]
        if esc_comp > 0:
            alerts.append({"type": "Grievance", "severity": "Critical",
                           "message": f"{esc_comp} sensitive complaints have been escalated.",
                           "link": "/principal/complaints"})

        return alerts
    except Exception as e:
        print("Error fetching notifications:", e)
        return []
    finally:
        conn.close()


# ==========================================
# REPORTS & ANALYTICS (Phase 8)
# ==========================================
def get_executive_report_data():
    """Consolidates all major KPIs for the Executive Report."""
    # Reuse the functions we already built
    stats = get_college_stats()
    academic = get_academic_oversight_stats()
    finance = get_finance_oversight_stats()
    hr = get_hr_oversight_stats()
    campus = get_campus_oversight_stats()

    return {
        "stats": stats,
        "academic": academic,
        "finance": finance,
        "hr": hr,
        "campus": campus
    }


# ==========================================
# AUDIT & MY ACTIVITY (Phase 8)
# ==========================================
def get_principal_audit_trail(user_id, limit=20):
    """Fetches the recent activity log for the specific Principal."""
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
        print("Error fetching audit trail:", e)
        return []
    finally:
        conn.close()


# =====================================================================
# PRINCIPAL NOTICES & EVENTS OVERSIGHT — Admin-created records list
# Added in the Principal Panel Enhancement iteration to populate the
# new "Admin-Created Notices & Events" section on /principal/notices.
# Returns the actual list of records (not just numeric counts) so the
# Principal can see what Admin has created, similar to the Student
# Panel notice board but with institution-wide oversight visibility.
# =====================================================================


def get_all_admin_notices(limit=20):
    """Returns the most recent Admin-created notices (non-Draft only).

    Business rule (Principal Panel blueprint §6.3, Q3 default):
      - Includes notices where posted_by is a user with role='Admin'.
      - Excludes status='Draft' (drafts should not be visible on an
        executive oversight dashboard — only Published, Pending,
        Approved, Expired, Cancelled).
      - Ordered by posted_on DESC (most recent first).
      - Capped at `limit` (default 20) per Q4 default.
      - Returns the creator's full_name via JOIN with users.
      - Includes attachment_path so the Principal can access attachments
        if they exist (the existing authorization model applies — the
        Principal role has institution-wide oversight access).

    Returns an empty list on connection failure or when no Admin notices
    exist — the frontend's empty-state handles this.
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT n.notice_id, n.title, n.category, n.status, n.posted_on,
                   n.target_audience, n.target_department_id, n.attachment_path,
                   n.description, u.full_name AS creator_name,
                   d.department_name AS target_department_name
            FROM notices n
            INNER JOIN users u ON n.posted_by = u.user_id
            LEFT JOIN departments d ON n.target_department_id = d.department_id
            WHERE u.role = 'Admin'
              AND n.status != 'Draft'
            ORDER BY n.posted_on DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching admin notices for Principal:", e)
        return []
    finally:
        conn.close()


def get_all_admin_events(limit=20):
    """Returns the most recent events (Admin is the primary event creator).

    Business rule (Principal Panel blueprint §6.3):
      - All events are included (the events table has no explicit creator
        FK — the `organizer` column is a VARCHAR label, not a user_id FK.
        Admin creates events via create_event() in admin_queries.py which
        sets status='Published' directly. The Principal sees all events
        for institution-wide oversight.)
      - Ordered by event_date DESC (most recent first).
      - Capped at `limit` (default 20) per Q4 default.

    Returns an empty list on connection failure or when no events exist.
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT event_id, event_name, description, event_date, venue,
                   status, target_audience, target_department_id, organizer,
                   d.department_name AS target_department_name
            FROM events e
            LEFT JOIN departments d ON e.target_department_id = d.department_id
            ORDER BY e.event_date DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching admin events for Principal:", e)
        return []
    finally:
        conn.close()