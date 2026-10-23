# routers/teacher.py
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request, Depends, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List

from utils.auth import get_current_user, RoleChecker
from database.teacher_queries import (
    get_teacher_id_from_user, get_subjects_for_teacher,
    get_students_for_attendance, get_existing_attendance,
    save_attendance_record, save_marks_record,
    get_existing_marks, apply_for_leave, get_my_leaves,
    get_teacher_dashboard_stats, get_teacher_timetable,
    submit_marks_for_verification,
    verify_teacher_subject_scope, verify_student_in_teacher_scope,
    get_sections_for_teacher_subject, get_student_academic_profile_for_teacher,
    get_teacher_attendance_history, get_teacher_low_attendance_students,
    get_teacher_notifications, get_teacher_audit_trail, get_teacher_workload,
    get_teacher_timetable_conflicts,
    get_teacher_department_meetings, get_teacher_action_items,
    get_teacher_notices, get_student_risk_indicators,
    get_teacher_department_id, get_teaching_analytics,
    get_attendance_intelligence,
    get_student_risk_dashboard, get_academic_report_data,
    # Phase 2 Imports
    get_assessment_analytics, get_teacher_assignments, create_assignment,
    get_assignment_submissions, get_lesson_plans, create_lesson_plan,
    get_syllabus_coverage, create_syllabus_topic,
    get_question_bank, create_question
)

from database.connection import get_connection
from ai.teacher import generate_assignment, generate_question_paper

# Phase 5 AI Imports
from ai.teacher_graph import app_graph as teacher_app_graph
from langgraph.types import Command
from langchain_core.messages import HumanMessage

router = APIRouter()
templates = Jinja2Templates(directory="templates")
teacher_only = RoleChecker(["Teacher"])


# --- HTML PAGES ---
@router.get("/teacher/dashboard", response_class=HTMLResponse)
async def teacher_dashboard(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/dashboard.html")


@router.get("/teacher/attendance", response_class=HTMLResponse)
async def attendance_page(request: Request, user: dict = Depends(teacher_only)):
    # Q11: Pass demo_mode flag to template so the date input can conditionally
    # allow future dates. ATTENDANCE_DEMO_MODE=1 enables the narrowly-scoped
    # demo exception (production default = unset = future dates blocked).
    demo_mode = os.getenv("ATTENDANCE_DEMO_MODE") == "1"
    today_kolkata = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
    return templates.TemplateResponse(
        request=request,
        name="teacher/attendance.html",
        context={"demo_mode": demo_mode, "today_date": today_kolkata},
    )


@router.get("/teacher/attendance/history", response_class=HTMLResponse)
async def attendance_history_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/attendance_history.html")


@router.get("/teacher/subjects", response_class=HTMLResponse)
async def subjects_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/subjects.html")


@router.get("/teacher/students", response_class=HTMLResponse)
async def students_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/students.html")


@router.get("/teacher/students/{student_id}", response_class=HTMLResponse)
async def student_profile_page(request: Request, student_id: int, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    if not teacher_id or not verify_student_in_teacher_scope(teacher_id, student_id):
        return HTMLResponse("Unauthorized: Student not in your academic scope", status_code=403)
    return templates.TemplateResponse(request=request, name="teacher/student_profile.html",
                                      context={"student_id": student_id})


@router.get("/teacher/marks", response_class=HTMLResponse)
async def marks_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/marks.html")


@router.get("/teacher/ai-tools", response_class=HTMLResponse)
async def ai_tools_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/ai_tools.html")


@router.get("/teacher/leaves", response_class=HTMLResponse)
async def teacher_leaves_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/leaves.html")


@router.get("/teacher/timetable", response_class=HTMLResponse)
async def teacher_timetable_page(request: Request, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    timetable_rows = get_teacher_timetable(teacher_id) if teacher_id else []
    grouped_timetable = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    for row in timetable_rows:
        time_key = f"{row['start_time']} - {row['end_time']}"
        if time_key not in grouped_timetable:
            grouped_timetable[time_key] = {day: None for day in days}
        grouped_timetable[time_key][row["day_of_week"]] = row
    return templates.TemplateResponse(request=request, name="teacher/timetable.html",
                                      context={"timetable": grouped_timetable, "days": days})


@router.get("/teacher/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/notifications.html")


@router.get("/teacher/audit", response_class=HTMLResponse)
async def audit_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/audit.html")


# --- SECURE API ROUTES ---
@router.get("/teacher/api/me")
async def api_get_me(user: dict = Depends(get_current_user)):
    conn = get_connection()
    if conn is None: return JSONResponse({"error": "DB Error"}, status_code=500)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, profile_image FROM users WHERE user_id = %s", (user["user_id"],))
        db_user = cursor.fetchone()
        if not db_user: return JSONResponse({"error": "User not found"}, status_code=404)
        hour = datetime.now().hour
        greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 17 else "Good Evening")
        return {"full_name": db_user["full_name"], "profile_image": db_user["profile_image"] or "default.png",
                "greeting": greeting, "current_date": datetime.now().strftime("%d %b, %Y")}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


@router.get("/teacher/api/dashboard")
async def api_get_teacher_dashboard(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    stats = get_teacher_dashboard_stats(teacher_id)
    timetable = get_teacher_timetable(teacher_id)
    today = datetime.today().strftime('%A')
    today_classes = [t for t in timetable if t["day_of_week"] == today]
    return {"stats": stats, "today_classes": today_classes}


@router.get("/teacher/api/subjects")
async def api_get_subjects(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return get_subjects_for_teacher(teacher_id)


# =====================================================================
# Bug 1 fix (Phase 3): /teacher/api/sections endpoint
# Was missing — frontend (students.html, attendance.html, marks.html)
# calls it but the backend never defined it. The query function
# `get_sections_for_teacher_subject` exists in teacher_queries.py:84
# but was dead code until this route was added.
# =====================================================================
@router.get("/teacher/api/sections")
async def api_get_sections(subject_id: int = Query(...), user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    if not teacher_id:
        return JSONResponse({"success": False, "message": "Teacher profile not found."}, status_code=400)
    sections = get_sections_for_teacher_subject(teacher_id, subject_id)
    return {"sections": sections}


# =====================================================================
# Bug 2 fix (Phase 4): /teacher/api/attendance/status endpoint
# Was missing — frontend (attendance.html:112) calls it to load existing
# attendance for a date so radio buttons reflect saved state.
# The query function `get_existing_attendance` exists in teacher_queries.py:176.
# =====================================================================
@router.get("/teacher/api/attendance/status")
async def api_get_attendance_status(
    subject_id: int = Query(...),
    section: str = Query(...),
    date: str = Query(...),
    user: dict = Depends(teacher_only),
):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    if not teacher_id:
        return JSONResponse({"success": False, "message": "Teacher profile not found."}, status_code=400)
    if not verify_teacher_subject_scope(teacher_id, subject_id):
        return JSONResponse({"success": False, "message": "Unauthorized subject access"}, status_code=403)
    attendance = get_existing_attendance(subject_id, teacher_id, section, date)
    return {"attendance": attendance}


@router.get("/teacher/api/students")
async def api_get_students(subject_id: int = Query(...), section: str = Query(...), user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    if not verify_teacher_subject_scope(teacher_id, subject_id):
        return JSONResponse({"error": "Unauthorized: Subject not assigned to you"}, status_code=403)
    students = get_students_for_attendance(teacher_id, subject_id, section)
    return {"students": students}


class AttendanceRecord(BaseModel):
    student_id: int
    status: str


class SaveAttendancePayload(BaseModel):
    subject_id: int
    section: str
    date: str
    # Q35: max 200 attendance records per save request (server-side cap)
    attendance: List[AttendanceRecord] = Field(default_factory=list, max_length=200)


@router.post("/teacher/api/save-attendance")
async def api_save_attendance(payload: SaveAttendancePayload, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    if not teacher_id:
        return JSONResponse({"success": False, "message": "Teacher profile not found."}, status_code=400)
    if not verify_teacher_subject_scope(teacher_id, payload.subject_id):
        return JSONResponse({"success": False, "message": "Unauthorized subject access"}, status_code=403)
    # Q11 + Q24: Date validation with Asia/Kolkata timezone.
    # Future dates blocked unless ATTENDANCE_DEMO_MODE=1 (narrowly-scoped demo exception).
    # Past dates are unlimited (teachers can mark retroactively).
    try:
        parsed_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return JSONResponse(
            {"success": False, "message": "Invalid date format. Expected YYYY-MM-DD."},
            status_code=400,
        )
    today_kolkata = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    if parsed_date > today_kolkata:
        if os.getenv("ATTENDANCE_DEMO_MODE") == "1":
            print(
                "ATTENDANCE_DEMO_MODE is enabled — future dates allowed for demonstration. "
                "Disable in production.",
                file=sys.stderr,
            )
        else:
            return JSONResponse(
                {
                    "success": False,
                    "message": "Future dates not allowed in production mode. "
                               "Set ATTENDANCE_DEMO_MODE=1 for demonstration.",
                },
                status_code=400,
            )
    for record in payload.attendance:
        error_msg = save_attendance_record(record.student_id, payload.subject_id, teacher_id, payload.date,
                                           record.status)
        if error_msg:
            return JSONResponse({"success": False, "message": f"DB Error for Student {record.student_id}: {error_msg}"},
                                status_code=500)
    return JSONResponse(
        {"success": True, "message": f"Successfully saved attendance for {len(payload.attendance)} students."})


@router.get("/teacher/api/marks")
async def api_get_marks(subject_id: int, section: str, exam_type: str, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    if not verify_teacher_subject_scope(teacher_id, subject_id):
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
    marks = get_existing_marks(subject_id, teacher_id, section, exam_type)
    return {"marks": marks}


class MarksRecord(BaseModel):
    student_id: int
    obtained_marks: float
    remarks: str


class SaveMarksPayload(BaseModel):
    subject_id: int
    section: str
    exam_type: str
    max_marks: int
    # Q36: max 200 marks records per save request (server-side cap)
    marks: List[MarksRecord] = Field(default_factory=list, max_length=200)


@router.post("/teacher/api/save-marks")
async def api_save_marks(payload: SaveMarksPayload, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    if not teacher_id:
        return JSONResponse({"success": False, "message": "Teacher profile not found."}, status_code=400)
    if not verify_teacher_subject_scope(teacher_id, payload.subject_id):
        return JSONResponse({"success": False, "message": "Unauthorized subject access"}, status_code=403)
    for record in payload.marks:
        if record.obtained_marks < 0 or record.obtained_marks > payload.max_marks:
            return JSONResponse({"success": False,
                                 "message": f"Invalid marks for Student {record.student_id}. Must be between 0 and {payload.max_marks}."},
                                status_code=400)
    for record in payload.marks:
        error_msg = save_marks_record(record.student_id, payload.subject_id, teacher_id, payload.exam_type,
                                      payload.max_marks, record.obtained_marks, record.remarks)
        if error_msg:
            return JSONResponse({"success": False, "message": f"DB Error for Student {record.student_id}: {error_msg}"},
                                status_code=500)
    return JSONResponse({"success": True, "message": f"Successfully saved marks for {len(payload.marks)} students."})


@router.post("/teacher/api/marks/submit")
async def api_submit_marks(request: Request, user: dict = Depends(teacher_only)):
    form = await request.form()
    subject_id = int(form.get("subject_id"))
    exam_type = form.get("exam_type")
    teacher_id = get_teacher_id_from_user(user["user_id"])
    if not verify_teacher_subject_scope(teacher_id, subject_id):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)
    success, msg = submit_marks_for_verification(subject_id, exam_type, teacher_id)
    return JSONResponse({"success": success, "message": msg})


@router.get("/teacher/api/attendance/history")
async def api_get_att_history(subject_id: int = None, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    history = get_teacher_attendance_history(teacher_id, subject_id)
    low_att = get_teacher_low_attendance_students(teacher_id)
    return {"history": history, "low_attendance_students": low_att}


@router.get("/teacher/api/students/{student_id}")
async def api_get_student_profile(student_id: int, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    if not verify_student_in_teacher_scope(teacher_id, student_id):
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
    profile = get_student_academic_profile_for_teacher(teacher_id, student_id)
    if not profile: return JSONResponse({"error": "Not found"}, status_code=404)
    return profile


@router.get("/teacher/api/notifications")
async def api_get_notifications(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return {"notifications": get_teacher_notifications(teacher_id)}


@router.get("/teacher/api/audit")
async def api_get_audit(user: dict = Depends(teacher_only)):
    trail = get_teacher_audit_trail(user["user_id"])
    return {"audit_trail": trail}


# --- AI & LEAVES ---
@router.post("/teacher/api/ai/question-paper")
async def api_generate_qp(subject: str = Form(...), unit: str = Form(...), difficulty: str = Form(...),
                          marks: int = Form(...), user: dict = Depends(teacher_only)):
    result = generate_question_paper(subject, unit, difficulty, marks)
    if result: return JSONResponse({"success": True, "report": result})
    return JSONResponse({"success": False, "message": "AI failed to generate question paper."}, status_code=500)


@router.post("/teacher/api/ai/assignment")
async def api_generate_assignment(subject: str = Form(...), topic: str = Form(...), user: dict = Depends(teacher_only)):
    result = generate_assignment(subject, topic)
    if result: return JSONResponse({"success": True, "report": result})
    return JSONResponse({"success": False, "message": "AI failed to generate assignment."}, status_code=500)


@router.get("/teacher/api/leaves")
async def api_get_leaves(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return get_my_leaves(teacher_id)


@router.post("/teacher/api/leaves/add")
async def api_add_leave(request: Request, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    form = await request.form()
    success, msg = apply_for_leave(teacher_id, form['leave_type'], form['from_date'], form['to_date'], form['reason'])
    return JSONResponse({"success": success, "message": msg})


# ==========================================
# PHASE 2: TEACHING, ASSESSMENT & LEARNING
# ==========================================

@router.get("/teacher/assessment-analytics", response_class=HTMLResponse)
async def assessment_analytics_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/assessment_analytics.html")


@router.get("/teacher/api/marks/analytics")
async def api_get_analytics(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return {"analytics": get_assessment_analytics(teacher_id)}


@router.get("/teacher/assignments", response_class=HTMLResponse)
async def assignments_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/assignments.html")


@router.get("/teacher/api/assignments")
async def api_get_assignments(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return {"assignments": get_teacher_assignments(teacher_id)}


@router.post("/teacher/api/assignments/create")
async def api_create_assignment(request: Request, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    form = await request.form()
    subject_id = int(form.get("subject_id"))
    if not verify_teacher_subject_scope(teacher_id, subject_id):
        return JSONResponse({"success": False, "message": "Unauthorized subject access"}, status_code=403)
    success = create_assignment(teacher_id, subject_id, form.get("title"), form.get("description"),
                                form.get("due_date"))
    return JSONResponse({"success": success, "message": "Assignment created." if success else "Failed."})


@router.get("/teacher/api/assignments/{assignment_id}/submissions")
async def api_get_submissions(assignment_id: int, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    submissions = get_assignment_submissions(assignment_id, teacher_id)
    if not submissions and assignment_id != 0:
        return JSONResponse({"error": "Unauthorized or no submissions"}, status_code=403)
    return {"submissions": submissions}


@router.get("/teacher/lesson-planner", response_class=HTMLResponse)
async def lesson_planner_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/lesson_planner.html")


@router.get("/teacher/api/lesson-plans")
async def api_get_lesson_plans(subject_id: int = None, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return {"plans": get_lesson_plans(teacher_id, subject_id)}


@router.post("/teacher/api/lesson-plans/create")
async def api_create_lesson_plan(request: Request, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    form = await request.form()
    subject_id = int(form.get("subject_id"))
    if not verify_teacher_subject_scope(teacher_id, subject_id):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)
    success = create_lesson_plan(teacher_id, subject_id, form.get("section"), form.get("plan_date"), form.get("topic"),
                                 form.get("objective"), form.get("method"), form.get("duration"))
    return JSONResponse({"success": success, "message": "Lesson plan created." if success else "Failed."})


@router.get("/teacher/syllabus", response_class=HTMLResponse)
async def syllabus_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/syllabus.html")


@router.get("/teacher/api/syllabus")
async def api_get_syllabus(subject_id: int = None, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return {"topics": get_syllabus_coverage(teacher_id, subject_id)}


@router.post("/teacher/api/syllabus/create")
async def api_create_syllabus_topic(request: Request, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    form = await request.form()
    subject_id = int(form.get("subject_id"))
    if not verify_teacher_subject_scope(teacher_id, subject_id):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)
    success = create_syllabus_topic(teacher_id, subject_id, form.get("section"), form.get("unit_name"))
    return JSONResponse({"success": success, "message": "Topic added." if success else "Failed."})


@router.get("/teacher/question-bank", response_class=HTMLResponse)
async def question_bank_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/question_bank.html")


@router.get("/teacher/api/questions")
async def api_get_questions(subject_id: int = None, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return {"questions": get_question_bank(teacher_id, subject_id)}


@router.post("/teacher/api/questions/create")
async def api_create_question(request: Request, user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    form = await request.form()
    subject_id = int(form.get("subject_id"))
    if not verify_teacher_subject_scope(teacher_id, subject_id):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)
    success = create_question(teacher_id, subject_id, form.get("topic"), form.get("question_text"),
                              form.get("question_type"), form.get("difficulty"), int(form.get("marks")))
    return JSONResponse({"success": success, "message": "Question added." if success else "Failed."})


# ==========================================
# PHASE 3: STUDENT SUCCESS & FACULTY OPERATIONS
# ==========================================

@router.get("/teacher/risk-indicators", response_class=HTMLResponse)
async def risk_indicators_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/risk_indicators.html")


@router.get("/teacher/api/risk-indicators")
async def api_get_risks(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return get_student_risk_indicators(teacher_id)


@router.get("/teacher/workload", response_class=HTMLResponse)
async def workload_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/workload.html")


@router.get("/teacher/api/workload")
async def api_get_workload(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return get_teacher_workload(teacher_id)


@router.get("/teacher/timetable/conflicts", response_class=HTMLResponse)
async def timetable_conflicts_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/timetable_conflicts.html")


@router.get("/teacher/api/timetable/conflicts")
async def api_get_conflicts(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return {"conflicts": get_teacher_timetable_conflicts(teacher_id)}


@router.get("/teacher/notices", response_class=HTMLResponse)
async def notices_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/notices.html")


@router.get("/teacher/api/notices")
async def api_get_notices(user: dict = Depends(teacher_only)):
    dept_id = get_teacher_department_id(user["user_id"])
    return {"notices": get_teacher_notices(dept_id)}


@router.get("/teacher/meetings", response_class=HTMLResponse)
async def meetings_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/meetings.html")


@router.get("/teacher/api/meetings")
async def api_get_meetings(user: dict = Depends(teacher_only)):
    dept_id = get_teacher_department_id(user["user_id"])
    meetings = get_teacher_department_meetings(dept_id)
    actions = get_teacher_action_items(user["user_id"])
    return {"meetings": meetings, "action_items": actions}


# ==========================================
# PHASE 4: ANALYTICS & ACADEMIC INTELLIGENCE
# ==========================================

@router.get("/teacher/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/analytics.html")


@router.get("/teacher/api/analytics/teaching")
async def api_get_teaching_analytics(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return get_teaching_analytics(teacher_id)


@router.get("/teacher/api/analytics/attendance")
async def api_get_att_intel(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return {"subjects": get_attendance_intelligence(teacher_id)}


@router.get("/teacher/risk-dashboard", response_class=HTMLResponse)
async def risk_dashboard_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/risk_dashboard.html")


@router.get("/teacher/api/risk-dashboard")
async def api_get_risk_dashboard(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return {"students": get_student_risk_dashboard(teacher_id)}


@router.get("/teacher/academic-reports", response_class=HTMLResponse)
async def academic_reports_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/academic_reports.html")


@router.get("/teacher/api/reports/academic")
async def api_get_academic_reports(user: dict = Depends(teacher_only)):
    teacher_id = get_teacher_id_from_user(user["user_id"])
    return get_academic_report_data(teacher_id)


# ==========================================
# PHASE 5: AI TEACHING COMMAND CENTER
# ==========================================

@router.get("/teacher/ai-assistant", response_class=HTMLResponse)
async def teacher_ai_assistant_page(request: Request, user: dict = Depends(teacher_only)):
    return templates.TemplateResponse(request=request, name="teacher/ai_assistant.html")


@router.post("/teacher/api/ai/ask")
async def api_ask_teacher_assistant(request: Request, user: dict = Depends(teacher_only)):
    form = await request.form()
    question = form.get("question")

    thread_id = f"teacher_{user['user_id']}"
    config = {"configurable": {"thread_id": thread_id, "user_id": user['user_id']}}

    try:
        state = await teacher_app_graph.aget_state(config)

        if state and state.next:
            is_confirmed = question.lower().strip() in ["yes", "y", "confirm", "haan", "okay"]
            output = await teacher_app_graph.ainvoke(Command(resume={"confirmed": is_confirmed}), config=config)
        else:
            input_messages = [HumanMessage(content=question)]
            output = await teacher_app_graph.ainvoke({"messages": input_messages}, config=config)

        current_state = await teacher_app_graph.aget_state(config)
        is_paused = current_state and current_state.next and any(
            "interrupt" in str(task) for task in current_state.tasks
        )

        if is_paused:
            interrupt_data = current_state.tasks[0].interrupts[0].value
            return JSONResponse({
                "success": True,
                "answer": interrupt_data.get("message", "Action requires confirmation. Reply 'Yes' to confirm."),
                "requires_confirmation": True
            })

        last_msg = output["messages"][-1]
        return JSONResponse({"success": True, "answer": last_msg.content})

    except Exception as e:
        print("Teacher AI Graph Error:", e)
        return JSONResponse({"success": False, "answer": "I encountered an error processing that request."})