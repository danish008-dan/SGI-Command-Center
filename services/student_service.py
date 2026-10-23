# services/student_service.py
from database.student_queries import (
    get_student_id_from_user, get_student_overall_attendance,
    get_student_published_results, get_student_assignments,
    get_student_submission_status, get_student_applications,
    get_latest_resume_analysis
)
from database.admin_queries import get_user_notices
from database.fee_queries import get_student_fee_portal
from database.connection import get_connection
from datetime import datetime

class StudentService:
    @staticmethod
    def get_dashboard_data(user_id):
        student_id = get_student_id_from_user(user_id)
        if not student_id:
            return {"error": "Student profile not found"}, 404

        attendance = get_student_overall_attendance(student_id)
        attendance = float(attendance) if attendance is not None else 0.0

        fee_summary, _ = get_student_fee_portal(user_id)
        pending_fee = 0.0
        if fee_summary and fee_summary.get("payable_fee") is not None:
            pending_fee = float(fee_summary["payable_fee"]) - float(fee_summary.get("paid", 0))

        results = get_student_published_results(student_id)
        latest_result = results[0] if results else None
        latest_sgpa = float(latest_result["sgpa"]) if latest_result and latest_result.get("sgpa") else None

        today_schedule = []
        dept_id = None
        sem = None
        sec = None
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT department_id FROM users WHERE user_id = %s", (user_id,))
                u = cursor.fetchone()
                cursor.execute("SELECT semester, section FROM students WHERE user_id = %s", (user_id,))
                s = cursor.fetchone()

                if u and s:
                    dept_id = u["department_id"]
                    sem = s["semester"]
                    sec = s["section"]
                    today = datetime.today().strftime('%A')
                    cursor.execute("""
                        SELECT DATE_FORMAT(ts.start_time, '%%H:%%i') as start_time, 
                               DATE_FORMAT(ts.end_time, '%%H:%%i') as end_time, 
                               sub.subject_name, r.room_number, u.full_name AS teacher_name
                        FROM timetable t
                        INNER JOIN time_slots ts ON t.slot_id = ts.slot_id
                        INNER JOIN subjects sub ON t.subject_id = sub.subject_id
                        INNER JOIN teachers th ON t.teacher_id = th.teacher_id
                        INNER JOIN users u ON th.user_id = u.user_id
                        INNER JOIN rooms r ON t.room_id = r.room_id
                        WHERE t.department_id = %s AND t.semester = %s AND t.section = %s 
                          AND t.status = 'Published' AND t.day_of_week = %s
                        ORDER BY ts.start_time
                    """, (dept_id, sem, sec, today))
                    today_schedule = cursor.fetchall()
            except Exception as e:
                print("Error fetching student schedule:", e)
            finally:
                conn.close()

        pending_assignments = 0
        if dept_id and sem is not None and sec:
            assignments = get_student_assignments(student_id, dept_id, sem, sec)
            for a in assignments:
                if not get_student_submission_status(student_id, a["assignment_id"]):
                    pending_assignments += 1

        notices = get_user_notices("Student", dept_id) if dept_id else []
        recent_notices = len(notices)

        resume = get_latest_resume_analysis(student_id)
        resume_score = 0
        if resume and resume.get("analysis_json"):
            resume_score = resume["analysis_json"].get("ats_score", 0)

        applications = get_student_applications(student_id)
        active_applications = len(applications)

        return {
            "attendance_pct": attendance,
            "pending_fee": round(pending_fee, 2),
            "latest_sgpa": latest_sgpa,
            "today_schedule": today_schedule,
            "pending_assignments": pending_assignments,
            "recent_notices": recent_notices,
            "resume_score": resume_score,
            "active_applications": active_applications
        }, 200