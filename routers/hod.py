# routers/hod.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from utils.auth import get_current_user, RoleChecker
from services.hod_services import HODService
from database.connection import get_connection

from database.hod_queries import (
    get_hod_department_id, get_department_stats,
    get_department_attendance_stats,
    get_low_attendance_students,
    get_department_students,
    get_student_academic_profile,
    get_department_top_performers,
    get_department_weak_students,
    get_department_leaves, update_leave_status,
    get_department_subject_performance,
    get_department_faculty_workload,
    get_submitted_marks_for_hod, update_marks_verification,
    get_department_faculty,
    get_faculty_academic_profile,
    get_department_subjects,
    get_department_unassigned_subjects,
    get_department_timetable,
    get_department_timetable_conflicts,
    get_department_marks_status,
    get_department_results_status,
    get_department_low_performers,
    get_department_normal_complaints,
    get_department_academic_plan,
    get_department_notices, create_department_notice,
    get_department_events, create_department_event,
    get_department_meetings, create_department_meeting,
    get_department_assets,
    get_department_maintenance_requests, create_maintenance_request,
    get_department_documents,
    get_department_placement_stats,
    get_hod_notifications,
    get_hod_audit_trail,
    get_hod_report_data,
    # HOD Executive Dashboard Enhancement — additional aggregations
    # for Department Operations cards + Academic Health & Risk card.
    get_upcoming_department_events,
    get_department_marks_completion_percentage,
)

# HOD AI imports
from ai.hod_graph import app_graph as hod_app_graph
from langgraph.types import Command
from langchain_core.messages import HumanMessage

router = APIRouter()
templates = Jinja2Templates(directory="templates")
hod_only = RoleChecker(["HOD"])


# ============================================================
# DASHBOARD ROUTES
# ============================================================

@router.get("/hod/dashboard", response_class=HTMLResponse)
async def hod_dashboard(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/dashboard.html")


@router.get("/hod/api/me")
async def api_get_me(user: dict = Depends(get_current_user)):
    conn = get_connection()
    if conn is None: return JSONResponse({"error": "DB Error"}, status_code=500)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, profile_image FROM users WHERE user_id = %s", (user["user_id"],))
        db_user = cursor.fetchone()
        if not db_user: return JSONResponse({"error": "User not found"}, status_code=404)

        hour = 12  # Default
        greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 17 else "Good Evening")
        return {
            "full_name": db_user["full_name"],
            "profile_image": db_user["profile_image"] or "default.png",
            "greeting": greeting,
            "current_date": "Today"
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


@router.get("/hod/api/dashboard")
async def api_get_dashboard(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id:
        return JSONResponse({"error": "Active department assignment not found"}, status_code=403)

    stats = get_department_stats(dept_id)
    top_performers = get_department_top_performers(dept_id)
    weak_students = get_department_weak_students(dept_id)
    subject_performance = get_department_subject_performance(dept_id)
    faculty_workload = get_department_faculty_workload(dept_id)
    attendance_stats = get_department_attendance_stats(dept_id)

    department_leaves = get_department_leaves(dept_id)
    pending_leaves = [leave for leave in department_leaves if leave["status"] == "Pending"]
    pending_marks = get_submitted_marks_for_hod(dept_id)

    # =====================================================================
    # HOD Executive Dashboard Enhancement — populate the 4 previously-missing
    # fields expected by dashboard.html JS:
    #   - recent_notices          (Department Operations > Recent Notices card)
    #   - upcoming_events         (Department Operations > Upcoming Events card)
    #   - pending_maintenance_count (Department Operations > Maintenance card
    #                                + Academic Health & Risk summary +
    #                                Today's Priorities alert)
    #   - marks_completion_percentage (Academic Health & Risk > Marks Completion)
    # All four reuse existing query functions or new helpers in hod_queries.py
    # that follow the same department-scoping pattern (dept_id from JWT, never
    # from the request). See blueprint §4-5 for business rules.
    # =====================================================================
    # Recent Notices: top 5 most recent, no status filter (matches the source
    # /hod/notices page's existing business logic per Q3 default).
    recent_notices = get_department_notices(dept_id)[:5]

    # Upcoming Events: top 5 future + Published events (Q4 default — stricter
    # than the source /hod/events page, which shows all events regardless of
    # status; an executive dashboard should show only confirmed upcoming events).
    upcoming_events = get_upcoming_department_events(dept_id, limit=5)

    # Pending Maintenance count: requests NOT yet Resolved/Closed (Q5 default).
    # Reuses the existing get_department_maintenance_requests array and filters
    # in Python to avoid an extra DB round-trip.
    all_maintenance = get_department_maintenance_requests(dept_id)
    pending_maintenance_count = sum(
        1 for m in all_maintenance
        if m.get("status") in ("Submitted", "Under Review", "In Progress")
    )

    # Marks Completion percentage: anything NOT Draft is "completed" (Q6 default).
    # Zero-denominator → 0 (handled in the query function).
    marks_completion_percentage = get_department_marks_completion_percentage(dept_id)

    return {
        "stats": stats,
        "top_performers": top_performers,
        "weak_students": weak_students,
        "subject_performance": subject_performance,
        "faculty_workload": faculty_workload,
        "avg_attendance": attendance_stats["avg_attendance"],
        "low_attendance_count": attendance_stats["low_attendance_count"],
        "pending_leaves_count": len(pending_leaves),
        "pending_marks_count": len(pending_marks),
        # New fields (HOD Dashboard Enhancement):
        "recent_notices": recent_notices,
        "upcoming_events": upcoming_events,
        "pending_maintenance_count": pending_maintenance_count,
        "marks_completion_percentage": marks_completion_percentage,
    }


# ============================================================
# ACADEMIC MANAGEMENT ROUTES
# ============================================================

@router.get("/hod/students", response_class=HTMLResponse)
async def hod_students_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/students.html")


@router.get("/hod/api/students")
async def api_get_students(request: Request, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    params = request.query_params
    search = params.get("search", "")
    semester = params.get("semester", None)
    students = get_department_students(dept_id, search, semester)
    return {"students": students}


@router.get("/hod/students/{student_id}", response_class=HTMLResponse)
async def hod_student_profile_page(request: Request, student_id: int, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id or not HODService.verify_student_in_department(student_id, dept_id):
        return HTMLResponse("Unauthorized", status_code=403)
    return templates.TemplateResponse(request=request, name="hod/student_profile.html",
                                      context={"student_id": student_id})


@router.get("/hod/api/students/{student_id}")
async def api_get_student_profile(student_id: int, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id or not HODService.verify_student_in_department(student_id, dept_id):
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
    profile = get_student_academic_profile(student_id)
    if not profile: return JSONResponse({"error": "Not found"}, status_code=404)
    return profile


@router.get("/hod/attendance", response_class=HTMLResponse)
async def hod_attendance_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/attendance.html")


@router.get("/hod/api/attendance")
async def api_get_attendance(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    stats = get_department_attendance_stats(dept_id)
    low_attendance = get_low_attendance_students(dept_id)
    return {"stats": stats, "low_attendance_students": low_attendance}


@router.get("/hod/marks-verification", response_class=HTMLResponse)
async def hod_marks_verification_page(request: Request, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    submitted_marks = []
    if dept_id: submitted_marks = get_submitted_marks_for_hod(dept_id)
    return templates.TemplateResponse(request=request, name="hod/marks_verification.html",
                                      context={"submitted_marks": submitted_marks})


@router.post("/hod/api/marks/verify")
async def api_verify_marks(request: Request, user: dict = Depends(hod_only)):
    form = await request.form()
    subject_id = int(form.get("subject_id"))
    exam_type = form.get("exam_type")
    action = form.get("action")
    success, msg = update_marks_verification(subject_id, exam_type, action)
    return JSONResponse({"success": success, "message": msg})


@router.get("/hod/leaves", response_class=HTMLResponse)
async def hod_leaves_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/leaves.html")


@router.get("/hod/api/leaves")
async def api_get_leaves(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return get_department_leaves(dept_id)


@router.post("/hod/api/leaves/update")
async def api_update_leave(leave_id: int = Form(...), status: str = Form(...), user: dict = Depends(hod_only)):
    success = update_leave_status(leave_id, status)
    return JSONResponse({"success": success, "message": "Status updated." if success else "Failed."})


# ============================================================
# FACULTY & TIMETABLE ROUTES
# ============================================================

@router.get("/hod/faculty", response_class=HTMLResponse)
async def hod_faculty_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/faculty.html")


@router.get("/hod/api/faculty")
async def api_get_faculty(request: Request, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    search = request.query_params.get("search", "")
    faculty_list = get_department_faculty(dept_id, search)
    return {"faculty": faculty_list}


@router.get("/hod/faculty/{teacher_id}", response_class=HTMLResponse)
async def hod_faculty_profile_page(request: Request, teacher_id: int, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id or not HODService.verify_faculty_in_department(teacher_id, dept_id):
        return HTMLResponse("Unauthorized", status_code=403)
    return templates.TemplateResponse(request=request, name="hod/faculty_profile.html",
                                      context={"teacher_id": teacher_id})


@router.get("/hod/api/faculty/{teacher_id}")
async def api_get_faculty_profile(teacher_id: int, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id or not HODService.verify_faculty_in_department(teacher_id, dept_id):
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
    profile = get_faculty_academic_profile(teacher_id)
    if not profile: return JSONResponse({"error": "Not found"}, status_code=404)
    return profile


@router.get("/hod/subjects", response_class=HTMLResponse)
async def hod_subjects_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/subjects.html")


@router.get("/hod/api/subjects")
async def api_get_subjects(request: Request, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    semester = request.query_params.get("semester", None)
    subject_type = request.query_params.get("subject_type", None)
    subjects = get_department_subjects(dept_id, semester, subject_type)
    unassigned = get_department_unassigned_subjects(dept_id)
    return {"subjects": subjects, "unassigned_subjects": unassigned}


@router.get("/hod/workload", response_class=HTMLResponse)
async def hod_workload_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/workload.html")


@router.get("/hod/api/workload")
async def api_get_workload(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    workload = get_department_faculty_workload(dept_id)
    return {"workload": workload}


@router.get("/hod/timetable", response_class=HTMLResponse)
async def hod_timetable_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/timetable.html")


@router.get("/hod/api/timetable")
async def api_get_timetable(request: Request, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    semester = request.query_params.get("semester", None)
    section = request.query_params.get("section", None)
    timetable = get_department_timetable(dept_id, semester, section)
    return {"timetable": timetable}


@router.get("/hod/timetable-conflicts", response_class=HTMLResponse)
async def hod_timetable_conflicts_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/timetable_conflicts.html")


@router.get("/hod/api/timetable/conflicts")
async def api_get_timetable_conflicts(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    conflicts = get_department_timetable_conflicts(dept_id)
    return {"conflicts": conflicts}


# ============================================================
# EXAMINATIONS, RESULTS & STUDENT SUPPORT
# ============================================================

@router.get("/hod/marks-monitoring", response_class=HTMLResponse)
async def hod_marks_monitoring_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/marks_monitoring.html")


@router.get("/hod/api/marks-monitoring")
async def api_get_marks_monitoring(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"subjects": get_department_marks_status(dept_id)}


@router.get("/hod/results-monitoring", response_class=HTMLResponse)
async def hod_results_monitoring_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/results_monitoring.html")


@router.get("/hod/api/results-monitoring")
async def api_get_results_monitoring(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"statuses": get_department_results_status(dept_id)}


@router.get("/hod/performance", response_class=HTMLResponse)
async def hod_performance_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/performance.html")


@router.get("/hod/api/performance")
async def api_get_performance(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"low_performers": get_department_low_performers(dept_id)}


@router.get("/hod/complaints", response_class=HTMLResponse)
async def hod_complaints_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/complaints.html")


@router.get("/hod/api/complaints")
async def api_get_complaints(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"complaints": get_department_normal_complaints(dept_id)}


@router.get("/hod/academic-plan", response_class=HTMLResponse)
async def hod_academic_plan_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/academic_plan.html")


@router.get("/hod/api/academic-plan")
async def api_get_academic_plan(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"subjects": get_department_academic_plan(dept_id)}


# ============================================================
# DEPARTMENT ADMINISTRATION & OPERATIONS
# ============================================================

@router.get("/hod/approvals", response_class=HTMLResponse)
async def hod_approvals_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/approvals.html")


@router.get("/hod/api/approvals")
async def api_get_hod_approvals(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    leaves = [l for l in get_department_leaves(dept_id) if l["status"] == 'Pending']
    marks = get_submitted_marks_for_hod(dept_id)
    maintenance = [m for m in get_department_maintenance_requests(dept_id) if m["status"] == 'Submitted']
    return {"leaves": leaves, "marks": marks, "maintenance": maintenance}


@router.get("/hod/notices", response_class=HTMLResponse)
async def hod_notices_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/notices.html")


@router.get("/hod/api/notices")
async def api_get_notices(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"notices": get_department_notices(dept_id)}


@router.post("/hod/api/notices/create")
async def api_create_notice(request: Request, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    form = await request.form()
    success = create_department_notice(dept_id, user["user_id"], form.get("title"), form.get("description"),
                                       form.get("category"))
    return JSONResponse({"success": success, "message": "Notice created." if success else "Failed."})


@router.get("/hod/events", response_class=HTMLResponse)
async def hod_events_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/events.html")


@router.get("/hod/api/events")
async def api_get_events(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"events": get_department_events(dept_id)}


@router.post("/hod/api/events/create")
async def api_create_event(request: Request, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    form = await request.form()
    success = create_department_event(dept_id, user["user_id"], form.get("event_name"), form.get("description"),
                                      form.get("event_date"), form.get("venue"))
    return JSONResponse({"success": success, "message": "Event created." if success else "Failed."})


@router.get("/hod/meetings", response_class=HTMLResponse)
async def hod_meetings_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/meetings.html")


@router.get("/hod/api/meetings")
async def api_get_meetings(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"meetings": get_department_meetings(dept_id)}


@router.post("/hod/api/meetings/create")
async def api_create_meeting(request: Request, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    form = await request.form()
    success = create_department_meeting(dept_id, user["user_id"], form.get("title"), form.get("meeting_date"),
                                        form.get("venue"), form.get("agenda"))
    return JSONResponse({"success": success, "message": "Meeting scheduled." if success else "Failed."})


@router.get("/hod/labs", response_class=HTMLResponse)
async def hod_labs_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/labs.html")


@router.get("/hod/api/assets")
async def api_get_assets(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"assets": get_department_assets(dept_id)}


@router.get("/hod/maintenance", response_class=HTMLResponse)
async def hod_maintenance_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/maintenance.html")


@router.get("/hod/api/maintenance")
async def api_get_maintenance(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"requests": get_department_maintenance_requests(dept_id)}


@router.post("/hod/api/maintenance/create")
async def api_create_maintenance(request: Request, user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    form = await request.form()
    asset_id = int(form.get("asset_id"))
    assets = get_department_assets(dept_id)
    if not any(a["asset_id"] == asset_id for a in assets):
        return JSONResponse({"error": "Unauthorized asset access"}, status_code=403)
    success = create_maintenance_request(user["user_id"], asset_id, form.get("issue_description"), form.get("priority"))
    return JSONResponse({"success": success, "message": "Request submitted." if success else "Failed."})


@router.get("/hod/documents", response_class=HTMLResponse)
async def hod_documents_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/documents.html")


@router.get("/hod/api/documents")
async def api_get_documents(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"documents": get_department_documents(dept_id)}


@router.get("/hod/placement", response_class=HTMLResponse)
async def hod_placement_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/placement.html")


@router.get("/hod/api/placement")
async def api_get_placement(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"stats": get_department_placement_stats(dept_id)}


# ============================================================
# INTELLIGENCE & GOVERNANCE LAYER
# ============================================================

@router.get("/hod/reports", response_class=HTMLResponse)
async def hod_reports_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/reports.html")


@router.get("/hod/api/reports")
async def api_get_hod_reports(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return get_hod_report_data(dept_id)


@router.get("/hod/notifications", response_class=HTMLResponse)
async def hod_notifications_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/notifications.html")


@router.get("/hod/api/notifications")
async def api_get_hod_notifications(user: dict = Depends(hod_only)):
    dept_id = HODService.get_hod_active_department_id(user["user_id"])
    if not dept_id: return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return {"notifications": get_hod_notifications(dept_id)}


@router.get("/hod/audit", response_class=HTMLResponse)
async def hod_audit_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/audit.html")


@router.get("/hod/api/audit")
async def api_get_hod_audit(user: dict = Depends(hod_only)):
    trail = get_hod_audit_trail(user["user_id"])
    return {"audit_trail": trail}


# ============================================================
# PHASE 5: HOD AI ASSISTANT
# ============================================================

@router.get("/hod/ai-assistant", response_class=HTMLResponse)
async def hod_ai_assistant_page(request: Request, user: dict = Depends(hod_only)):
    return templates.TemplateResponse(request=request, name="hod/ai_assistant.html")


@router.post("/hod/api/ai/ask")
async def api_ask_hod_assistant(request: Request, user: dict = Depends(hod_only)):
    form = await request.form()
    question = form.get("question")
    thread_id = f"hod_{user['user_id']}"
    config = {"configurable": {"thread_id": thread_id, "user_id": user['user_id']}}

    try:
        state = await hod_app_graph.aget_state(config)
        if state and state.next:
            is_confirmed = question.lower().strip() in ["yes", "y", "confirm", "haan", "okay"]
            output = await hod_app_graph.ainvoke(Command(resume={"confirmed": is_confirmed}), config=config)
        else:
            input_messages = [HumanMessage(content=question)]
            output = await hod_app_graph.ainvoke({"messages": input_messages}, config=config)

        current_state = await hod_app_graph.aget_state(config)
        is_paused = current_state and current_state.next and any(
            "interrupt" in str(task) for task in current_state.tasks)

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
        print("HOD AI Graph Error:", e)
        return JSONResponse({"success": False, "answer": "I encountered an error processing that request."})