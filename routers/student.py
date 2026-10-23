# routers/student.py
import os
import json
import random
import time
from datetime import datetime

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import StreamingResponse
from utils.auth import RoleChecker
from services.student_service import StudentService
from ai.career import generate_career_roadmap
from ai.resume import extract_text_from_pdf, analyze_resume
from database.connection import get_connection
from database.student_queries import apply_for_revaluation
from utils.pdf_generator import generate_fee_receipt_pdf, generate_resume_pdf, get_resume_renderer, ResumeRenderError
from utils.resume_validation import ResumeDraft
from database.admin_queries import get_user_notices, get_user_events
from ai.student_jarvis import student_jarvis_chat

from fastapi import (
    APIRouter, Request,
    Depends, File,
    Form, UploadFile
)

from database.student_queries import (
    get_student_attendance_report,
    get_student_overall_attendance,
    get_student_marks_report,
    get_student_overall_result,
    get_student_profile,
    can_student_complain,
    add_student_complaint,
    get_student_complaints,
    save_career_recommendation,
    get_saved_career_recommendation,
    get_student_id_from_user,
    get_student_published_results,
    get_student_attendance_log,
    get_semester_subject_marks,
    get_student_library_loans,
    get_student_hostel_allocation,
    get_student_transport_allocation,
    get_student_assignments,
    get_student_submission_status,
    save_student_submission,
    verify_assignment_scope,
    get_student_materials,
    get_student_cgpa,
    get_placement_drives,
    get_student_applications,
    check_existing_application,
    create_placement_application,
    save_resume_draft,
    get_resume_draft,
    get_resume_history,
    get_resume_history_by_id,
    get_latest_resume_analysis,
    save_resume_analysis_history,
    get_student_service_preferences,
    update_student_service_preference
)

from database.fee_queries import (
    get_student_fee_portal,
    create_payment_transaction,
    verify_and_save_transaction,
    get_payment_details_for_receipt
)

# Verified Navigation Registry
NAVIGATION_REGISTRY = {
    "dashboard": "/student/dashboard",
    "attendance": "/student/attendance",
    "marks": "/student/marks",
    "result": "/student/result",
    "fees": "/student/fees",
    "timetable": "/student/timetable",
    "assignments": "/student/assignments",
    "notices": "/student/notices",
    "library": "/student/library",
    "hostel": "/student/hostel",
    "transport": "/student/transport",
    "career": "/student/career",
    "resume_analyzer": "/student/placement",
    "resume_builder": "/student/resume-builder",
    "jarvis": "/student/jarvis"
}

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Standardized Authorization
student_only = RoleChecker(["Student"])


# ============================================================
# HTML PAGES (Secured)
# ============================================================

@router.get("/student/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/dashboard.html")


@router.get("/student/attendance", response_class=HTMLResponse)
async def student_attendance_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/attendance_report.html")


@router.get("/student/marks", response_class=HTMLResponse)
async def student_marks_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/marks.html")


@router.get("/student/result", response_class=HTMLResponse)
async def student_result_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/result.html")


@router.get("/student/fees", response_class=HTMLResponse)
async def student_fees_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/fees.html")


@router.get("/student/complaints", response_class=HTMLResponse)
async def student_complaints_page(request: Request, user: dict = Depends(student_only)):
    # FIXED: Fetch complaints and pass to template context
    student_id = get_student_id_from_user(user["user_id"])
    complaints = get_student_complaints(student_id) if student_id else []
    can_complain, next_date = can_student_complain(student_id) if student_id else (False, None)

    return templates.TemplateResponse(request=request, name="student/complaints.html",
                                      context={"complaints": complaints, "can_complain": can_complain,
                                               "next_date": next_date})


@router.get("/student/career", response_class=HTMLResponse)
async def career_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/career.html")


@router.get("/student/placement", response_class=HTMLResponse)
async def placement_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/placement.html")


@router.get("/student/notices", response_class=HTMLResponse)
async def student_notices_page(request: Request, user: dict = Depends(student_only)):
    conn = get_connection()
    dept_id = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT department_id FROM users WHERE user_id = %s", (user["user_id"],))
            u = cursor.fetchone()
            if u: dept_id = u["department_id"]
        finally:
            conn.close()

    notices = get_user_notices("Student", dept_id)
    events = get_user_events("Student", dept_id)
    return templates.TemplateResponse(request=request, name="student/notices.html",
                                      context={"notices": notices, "events": events})


@router.get("/student/timetable", response_class=HTMLResponse)
async def student_timetable_page(request: Request, user: dict = Depends(student_only)):
    conn = get_connection()
    timetable_rows = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT department_id FROM users WHERE user_id = %s", (user["user_id"],))
            u = cursor.fetchone()
            student_id = get_student_id_from_user(user["user_id"])
            cursor.execute("SELECT semester, section FROM students WHERE student_id = %s", (student_id,))
            s = cursor.fetchone()
            if u and s:
                from database.student_queries import get_student_timetable
                timetable_rows = get_student_timetable(u["department_id"], s["semester"], s["section"])
        finally:
            conn.close()

    grouped_timetable = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    for row in timetable_rows:
        time_key = f"{row['start_time']} - {row['end_time']}"
        if time_key not in grouped_timetable:
            grouped_timetable[time_key] = {day: None for day in days}
        grouped_timetable[time_key][row["day_of_week"]] = row

    return templates.TemplateResponse(
        request=request,
        name="student/timetable.html",
        context={"timetable": grouped_timetable, "days": days}
    )


# ============================================================
# SECURE API ROUTES
# ============================================================

@router.get("/student/api/dashboard")
async def api_get_dashboard(user: dict = Depends(student_only)):
    data, status_code = StudentService.get_dashboard_data(user["user_id"])
    return JSONResponse(content=data, status_code=status_code)


@router.get("/student/api/me")
async def api_get_me(user: dict = Depends(student_only)):
    conn = get_connection()
    if conn is None: return JSONResponse({"error": "DB Error"}, status_code=500)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, profile_image FROM users WHERE user_id = %s", (user["user_id"],))
        db_user = cursor.fetchone()
        if not db_user: return JSONResponse({"error": "User not found"}, status_code=404)

        hour = datetime.now().hour
        greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 17 else "Good Evening")
        return {
            "full_name": db_user["full_name"],
            "profile_image": db_user["profile_image"] or "default.png",
            "greeting": greeting,
            "current_date": datetime.now().strftime("%d %b, %Y")
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


@router.get("/student/api/profile")
async def api_get_profile(user: dict = Depends(student_only)):
    profile = get_student_profile(user["user_id"])
    return profile or {}


@router.get("/student/api/attendance")
async def api_get_attendance(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    report = get_student_attendance_report(student_id)
    overall = get_student_overall_attendance(student_id)
    log = get_student_attendance_log(student_id)
    return {"report": report, "overall": overall, "log": log}


@router.get("/student/api/result")
async def api_get_result(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"error": "Student profile not found"}, status_code=404)
    results = get_student_published_results(student_id)
    return {"results": results}


@router.get("/student/api/result/{semester}/subjects")
async def api_get_semester_subjects(semester: int, user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"error": "Student profile not found"}, status_code=404)
    subjects = get_semester_subject_marks(student_id, semester)
    return {"subjects": subjects}


@router.get("/student/api/marks")
async def api_get_marks(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    report = get_student_marks_report(student_id)
    overall_pct, overall_grade = get_student_overall_result(student_id)
    return {"report": report, "overall_percentage": overall_pct, "overall_grade": overall_grade}


@router.get("/student/api/fees")
async def api_get_fees(user: dict = Depends(student_only)):
    summary, history = get_student_fee_portal(user["user_id"])
    return {"summary": summary, "history": history}


@router.post("/student/api/payment/create")
async def api_create_payment(amount: float = Form(...), mode: str = Form(...), user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"success": False, "message": "Student profile not found"}, status_code=404)

    conn = get_connection()
    if conn is None: return JSONResponse({"success": False, "message": "DB Error"}, status_code=500)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT student_fee_id FROM student_fees WHERE student_id = %s", (student_id,))
        sf = cursor.fetchone()
    finally:
        conn.close()

    if not sf: return JSONResponse({"success": False, "message": "No fee assigned"}, status_code=400)

    txn_id = create_payment_transaction(sf["student_fee_id"], amount, mode, user["user_id"])
    if txn_id:
        gateway_txn_id = "SIMGW" + str(random.randint(100000, 999999))
        return JSONResponse({"success": True, "transaction_id": txn_id, "gateway_txn_id": gateway_txn_id})
    return JSONResponse({"success": False, "message": "Failed to create transaction"}, status_code=500)


@router.post("/student/api/payment/verify")
async def api_verify_payment(transaction_id: int = Form(...), gateway_txn_id: str = Form(...),
                             user: dict = Depends(student_only)):
    success, message = verify_and_save_transaction(transaction_id, gateway_txn_id, user["user_id"])
    if success: return JSONResponse({"success": True, "message": message})
    return JSONResponse({"success": False, "message": message}, status_code=400)


@router.get("/student/api/notices")
async def api_get_notices(user: dict = Depends(student_only)):
    conn = get_connection()
    dept_id = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT department_id FROM users WHERE user_id = %s", (user["user_id"],))
            u = cursor.fetchone()
            if u: dept_id = u["department_id"]
        finally:
            conn.close()
    notices = get_user_notices("Student", dept_id)
    events = get_user_events("Student", dept_id)
    return {"notices": notices, "events": events}


@router.get("/student/api/complaints")
async def api_get_complaints(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    can_complain, next_date = can_student_complain(student_id)
    complaints = get_student_complaints(student_id)
    return {"can_complain": can_complain, "next_date": next_date, "complaints": complaints}


@router.post("/student/api/complaints/add")
async def api_add_complaint(request: Request, user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    can_complain, _ = can_student_complain(student_id)
    if not can_complain:
        return JSONResponse({"success": False, "message": "You can only submit 1 complaint every 3 days."},
                            status_code=400)
    form = await request.form()
    success, msg = add_student_complaint(student_id, form["category"], form["complaint"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/student/api/career/saved")
async def api_get_saved_career(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    saved = get_saved_career_recommendation(student_id)
    return {"saved_report": saved}


@router.post("/student/api/career/generate")
async def api_generate_career(request: Request, user: dict = Depends(student_only)):
    form = await request.form()
    student_id = get_student_id_from_user(user["user_id"])
    ai_result = generate_career_roadmap(form.get("cgpa"), form.get("skills"), form.get("interests"), form.get("domain"),
                                        form.get("salary"))
    if ai_result:
        save_career_recommendation(student_id, ai_result)
        return JSONResponse({"success": True, "report": ai_result})
    return JSONResponse({"success": False, "message": "AI failed to generate a response."}, status_code=500)


@router.get("/student/api/placement/saved")
async def api_get_saved_placement(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    saved = get_latest_resume_analysis(student_id)
    return {"saved_report": saved}


@router.post("/student/api/placement/upload")
async def api_upload_resume(file: UploadFile = File(...), jd_text: str = Form(""), user: dict = Depends(student_only)):
    if file.content_type != "application/pdf":
        return JSONResponse({"success": False, "message": "Only PDF files are allowed."}, status_code=400)

    student_id = get_student_id_from_user(user["user_id"])
    upload_dir = "private_uploads/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    safe_filename = f"resume_{student_id}_{int(time.time())}.pdf"
    file_path = os.path.join(upload_dir, safe_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    resume_text = extract_text_from_pdf(file_path)
    if not resume_text:
        return JSONResponse({"success": False, "message": "Could not read text from PDF."}, status_code=400)

    has_jd = bool(jd_text and jd_text.strip())
    ai_result = analyze_resume(resume_text, jd_text if has_jd else "")

    if ai_result:
        save_resume_analysis_history(student_id, file_path, ai_result, has_jd)
        return JSONResponse({"success": True, "report": ai_result, "jd_used": has_jd})

    return JSONResponse({"success": False, "message": "AI failed to analyze resume."}, status_code=500)


# ==========================================
# PHASE 6: ADVANCED RESUME ANALYZER & BUILDER
# ==========================================

@router.get("/student/api/resume/history")
async def api_get_resume_history(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    history = get_resume_history(student_id)
    return {"history": history}


@router.get("/student/api/resume/history/{history_id}")
async def api_get_history_detail(history_id: int, user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    record = get_resume_history_by_id(history_id, student_id)
    if not record:
        return JSONResponse({"error": "Unauthorized or not found"}, status_code=404)
    return {"analysis": record["analysis_json"]}


@router.get("/student/api/resume/download/{history_id}")
async def api_download_resume_file(history_id: int, user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    record = get_resume_history_by_id(history_id, student_id)
    if not record:
        return HTMLResponse("Unauthorized", status_code=403)

    file_path = record["resume_file_path"]
    if not os.path.exists(file_path):
        return HTMLResponse("File not found", status_code=404)

    return StreamingResponse(
        open(file_path, "rb"),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resume_{history_id}.pdf"}
    )


@router.get("/student/resume-builder", response_class=HTMLResponse)
async def resume_builder_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/resume_builder.html")


# === Resume Builder payload size limit (blueprint v2 §6.5) ===
MAX_RESUME_PAYLOAD_BYTES = 256 * 1024  # 256 KB


def _sanitize_resume_filename(name: str) -> str:
    """Sanitize full_name into a safe filename component per blueprint §5.8."""
    import re as _re
    safe = _re.sub(r'[^A-Za-z0-9_-]+', '_', name or "").strip('_')
    return safe or "Resume"


@router.get("/student/api/resume/draft")
async def api_get_draft(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    draft = get_resume_draft(student_id)
    return {"draft": draft["content_json"] if draft else None}


@router.post("/student/api/resume/draft")
async def api_save_draft(request: Request, user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    form = await request.form()
    content_json = form.get("content_json") or ""

    # Payload size check (before json.loads to prevent memory exhaustion)
    if len(content_json.encode("utf-8")) > MAX_RESUME_PAYLOAD_BYTES:
        return JSONResponse(
            {"success": False, "message": "Resume data exceeds 256 KB limit."},
            status_code=413,
        )

    try:
        raw = json.loads(content_json)
        # Pydantic validation (also runs v1->v2 migration via model_validator)
        draft = ResumeDraft.model_validate(raw)
        success = save_resume_draft(student_id, draft.model_dump())
        return JSONResponse(
            {"success": success, "message": "Draft saved!" if success else "Failed."}
        )
    except ValueError:
        # Pydantic ValidationError (or json.loads) — return sanitized message
        return JSONResponse(
            {"success": False, "message": "Invalid resume data. Please check your entries."},
            status_code=400,
        )
    except Exception:
        # Log original exception server-side; return generic message to client
        import sys
        print(f"save_resume_draft error for student_id={student_id}", file=sys.stderr)
        return JSONResponse(
            {"success": False, "message": "Failed to save draft."},
            status_code=400,
        )


@router.post("/student/api/resume/export")
async def api_export_resume(request: Request, user: dict = Depends(student_only)):
    form = await request.form()
    content_json = form.get("content_json") or ""

    # Payload size check
    if len(content_json.encode("utf-8")) > MAX_RESUME_PAYLOAD_BYTES:
        return JSONResponse(
            {"success": False, "message": "Resume data exceeds 256 KB limit."},
            status_code=413,
        )

    try:
        raw = json.loads(content_json)
        draft = ResumeDraft.model_validate(raw)
        renderer = get_resume_renderer()
        buffer = renderer.render(draft.model_dump())

        # Sanitized filename (RFC 5987 for non-ASCII)
        from urllib.parse import quote
        base_name = _sanitize_resume_filename(draft.personal.full_name)
        filename = f"{base_name}_Resume.pdf"
        filename_ascii = filename.encode("ascii", "ignore").decode("ascii") or "Resume.pdf"
        filename_utf8 = quote(filename)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename_ascii}"; '
                    f"filename*=UTF-8''{filename_utf8}"
                )
            },
        )
    except ValueError:
        return JSONResponse(
            {"success": False, "message": "Invalid resume data. Please check your entries."},
            status_code=400,
        )
    except ResumeRenderError as e:
        return JSONResponse(
            {"success": False, "message": str(e)},
            status_code=500,
        )
    except Exception:
        import sys
        print("resume export error", file=sys.stderr)
        return JSONResponse(
            {"success": False, "message": "PDF generation failed."},
            status_code=500,
        )


@router.post("/student/api/revaluation/apply")
async def api_apply_reval(request: Request, user: dict = Depends(student_only)):
    form = await request.form()
    student_id = get_student_id_from_user(user["user_id"])
    success, msg = apply_for_revaluation(student_id, int(form.get("semester")), int(form.get("subject_id")),
                                         form.get("reason"))
    return JSONResponse({"success": success, "message": msg})


@router.get("/student/receipts/{payment_id}/pdf")
async def download_student_fee_receipt(payment_id: int, user: dict = Depends(student_only)):
    payment_data = get_payment_details_for_receipt(payment_id)
    student_id = get_student_id_from_user(user["user_id"])
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id FROM student_fees WHERE student_fee_id = %s",
                   (payment_data["student_fee_id"] if payment_data else 0,))
    sf = cursor.fetchone()
    conn.close()
    if not sf or sf["student_id"] != student_id:
        return HTMLResponse("Unauthorized access to receipt", status_code=403)
    if not payment_data: return HTMLResponse("Receipt not found", status_code=404)
    buffer = generate_fee_receipt_pdf(payment_data)
    return StreamingResponse(buffer, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=Receipt_{payment_data['receipt_number']}.pdf"})


# ==========================================
# PHASE 3: CAMPUS SERVICES
# ==========================================

@router.get("/student/library", response_class=HTMLResponse)
async def student_library_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/library.html")


@router.get("/student/api/library")
async def api_get_library(user: dict = Depends(student_only)):
    loans = get_student_library_loans(user["user_id"])
    return {"loans": loans}


@router.get("/student/hostel", response_class=HTMLResponse)
async def student_hostel_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/hostel.html")


@router.get("/student/transport", response_class=HTMLResponse)
async def student_transport_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/transport.html")


@router.get("/student/api/hostel")
async def api_get_hostel(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"error": "Student profile not found"}, status_code=404)

    allocation = get_student_hostel_allocation(student_id)
    prefs = get_student_service_preferences(student_id)

    return {
        "allocation": allocation,
        "service_enabled": prefs.get("hostel_service_enabled", True) if prefs else True
    }


@router.get("/student/api/transport")
async def api_get_transport(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"error": "Student profile not found"}, status_code=404)

    allocation = get_student_transport_allocation(student_id)
    prefs = get_student_service_preferences(student_id)

    return {
        "allocation": allocation,
        "service_enabled": prefs.get("transport_service_enabled", True) if prefs else True
    }


@router.post("/student/api/preferences/service")
async def api_update_preference(request: Request, user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id:
        return JSONResponse({"success": False, "message": "Student profile not found"}, status_code=404)

    try:
        body = await request.json()
        service_type = body.get("service_type")
        is_enabled = body.get("enabled")

        if service_type not in ["hostel", "transport"]:
            return JSONResponse({"success": False, "message": "Invalid service type."}, status_code=400)
        if not isinstance(is_enabled, bool):
            return JSONResponse({"success": False, "message": "Invalid enabled value."}, status_code=400)

        success, msg = update_student_service_preference(student_id, service_type, is_enabled)

        if success:
            return {"success": True, "message": msg}
        return JSONResponse({"success": False, "message": msg}, status_code=500)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)



# ==========================================
# PHASE 4: LEARNING & ACADEMIC ENGAGEMENT
# ==========================================

@router.get("/student/learning-center", response_class=HTMLResponse)
async def learning_center_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/learning_center.html")


@router.get("/student/assignments", response_class=HTMLResponse)
async def assignments_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/assignments.html")


@router.get("/student/api/assignments")
async def api_get_assignments(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"error": "Student profile not found"}, status_code=404)

    conn = get_connection()
    dept_id, sem, sec = None, None, None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT u.department_id, s.semester, s.section FROM students s INNER JOIN users u ON s.user_id = u.user_id WHERE s.student_id = %s",
                (student_id,))
            student_info = cursor.fetchone()
            if student_info:
                dept_id, sem, sec = student_info["department_id"], student_info["semester"], student_info["section"]
        finally:
            conn.close()

    if not dept_id: return {"assignments": []}

    assignments = get_student_assignments(student_id, dept_id, sem, sec)
    for a in assignments:
        sub = get_student_submission_status(student_id, a["assignment_id"])
        a["submission_status"] = "Submitted" if sub else "Pending"
        a["submission_date"] = sub["submission_date"] if sub else None

    return {"assignments": assignments}


@router.post("/student/api/assignments/{assignment_id}/submit")
async def api_submit_assignment(assignment_id: int, file: UploadFile = File(...), user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"success": False, "message": "Student profile not found"}, status_code=404)

    if not verify_assignment_scope(student_id, assignment_id):
        return JSONResponse({"success": False, "message": "Unauthorized: Assignment out of scope."}, status_code=403)

    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        return JSONResponse({"success": False, "message": "Invalid file type. Only PDF and DOCX allowed."},
                            status_code=400)

    upload_dir = "private_uploads/submissions"
    os.makedirs(upload_dir, exist_ok=True)
    ext = file.filename.split(".")[-1]
    safe_filename = f"sub_{student_id}_{assignment_id}.{ext}"
    file_path = os.path.join(upload_dir, safe_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    success, msg = save_student_submission(student_id, assignment_id, file_path)
    return JSONResponse({"success": success, "message": msg})


@router.get("/student/materials", response_class=HTMLResponse)
async def materials_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/materials.html")


@router.get("/student/api/materials")
async def api_get_materials(user: dict = Depends(student_only)):
    conn = get_connection()
    dept_id = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT department_id FROM users WHERE user_id = %s", (user["user_id"],))
            u = cursor.fetchone()
            if u: dept_id = u["department_id"]
        finally:
            conn.close()

    if not dept_id: return {"materials": []}
    return {"materials": get_student_materials(dept_id)}


# ==========================================
# PHASE 5: PLACEMENT DRIVES & APPLICATIONS
# ==========================================

@router.get("/student/api/companies")
async def api_get_companies(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"error": "Student profile not found"}, status_code=404)

    student_cgpa = get_student_cgpa(student_id)
    drives = get_placement_drives()

    for d in drives:
        req_cgpa = float(d.get("eligibility_cgpa") or 0)
        d["is_eligible"] = student_cgpa >= req_cgpa
        d["student_cgpa"] = student_cgpa

    return {"drives": drives}


@router.get("/student/api/applications")
async def api_get_applications(user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"error": "Student profile not found"}, status_code=404)

    applications = get_student_applications(student_id)
    return {"applications": applications}


@router.post("/student/api/applications/apply")
async def api_apply_to_company(request: Request, user: dict = Depends(student_only)):
    student_id = get_student_id_from_user(user["user_id"])
    if not student_id: return JSONResponse({"success": False, "message": "Student profile not found"}, status_code=404)

    form = await request.form()
    company_id = int(form.get("company_id"))

    if check_existing_application(student_id, company_id):
        return JSONResponse({"success": False, "message": "You have already applied to this company."}, status_code=400)

    student_cgpa = get_student_cgpa(student_id)
    drives = get_placement_drives()
    selected_drive = next((d for d in drives if d["company_id"] == company_id), None)

    if not selected_drive:
        return JSONResponse({"success": False, "message": "Invalid company."}, status_code=404)

    req_cgpa = float(selected_drive.get("eligibility_cgpa") or 0)
    if student_cgpa < req_cgpa:
        return JSONResponse({"success": False, "message": f"Ineligible. Minimum CGPA required is {req_cgpa}."},
                            status_code=403)

    success, msg = create_placement_application(student_id, company_id)
    return JSONResponse({"success": success, "message": msg})


# ==========================================
# PHASE 7: JARVIS AI ASSISTANT
# ==========================================

@router.get("/student/jarvis", response_class=HTMLResponse)
async def jarvis_page(request: Request, user: dict = Depends(student_only)):
    return templates.TemplateResponse(request=request, name="student/jarvis.html")


@router.post("/student/api/jarvis/chat")
async def api_jarvis_chat(request: Request, user: dict = Depends(student_only)):
    try:
        body = await request.json()
    except:
        return JSONResponse({"error": "Invalid request format."}, status_code=400)

    message = body.get("message", "").strip()
    history = body.get("history", [])

    if not message:
        return JSONResponse({"error": "Message cannot be empty."}, status_code=400)
    if len(message) > 500:
        return JSONResponse({"error": "Message too long (max 500 characters)."}, status_code=400)

    student_id = get_student_id_from_user(user["user_id"])
    if not student_id:
        return JSONResponse({"error": "Student profile not found."}, status_code=404)

    profile = get_student_profile(user["user_id"]) or {}
    attendance = get_student_overall_attendance(student_id)
    subject_attendance = get_student_attendance_report(student_id)
    subject_att_str = ", ".join(
        [f"{r['subject_name']}: {r['percentage']}%" for r in subject_attendance]) if subject_attendance else "None"

    from database.fee_queries import get_student_fee_portal
    fee_summary, _ = get_student_fee_portal(user["user_id"])
    pending_fee = 0.0
    total_fees = 0.0
    if fee_summary and fee_summary.get("payable_fee"):
        total_fees = float(fee_summary["payable_fee"])
        pending_fee = total_fees - float(fee_summary.get("paid", 0))

    # Fetch Full Week Timetable Data (Monday to Saturday)
    full_week_timetable = []
    conn = get_connection()
    dept_id, sem, sec = None, None, None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT department_id FROM users WHERE user_id = %s", (user["user_id"],))
            u = cursor.fetchone()
            cursor.execute("SELECT semester, section FROM students WHERE student_id = %s", (student_id,))
            s = cursor.fetchone()

            if u and s:
                dept_id = u["department_id"]
                sem = s["semester"]
                sec = s["section"]

                cursor.execute("""
                    SELECT sub.subject_name, u.full_name AS teacher_name, r.room_number, t.day_of_week,
                           DATE_FORMAT(ts.start_time, '%%H:%%i') as start_time, 
                           DATE_FORMAT(ts.end_time, '%%H:%%i') as end_time
                    FROM timetable t
                    INNER JOIN subjects sub ON t.subject_id = sub.subject_id
                    INNER JOIN teachers th ON t.teacher_id = th.teacher_id
                    INNER JOIN users u ON th.user_id = u.user_id
                    INNER JOIN rooms r ON t.room_id = r.room_id
                    INNER JOIN time_slots ts ON t.slot_id = ts.slot_id
                    WHERE t.department_id = %s AND t.semester = %s AND t.section = %s 
                      AND t.status = 'Published'
                    ORDER BY t.day_of_week, ts.start_time
                """, (dept_id, sem, sec))
                full_week_timetable = cursor.fetchall()
        except Exception as e:
            print("Error fetching timetable for JARVIS:", e)
        finally:
            conn.close()

    # Process timetable into a readable string for AI context
    today = datetime.today().strftime('%A')
    today_classes_count = 0
    today_classes_details = []
    weekly_timetable_str = "No timetable data available."

    if full_week_timetable:
        timetable_by_day = {}
        for row in full_week_timetable:
            day = row['day_of_week']
            if day not in timetable_by_day:
                timetable_by_day[day] = []
            timetable_by_day[day].append(
                f"{row['subject_name']} by {row['teacher_name']} in Room {row['room_number']} ({row['start_time']}-{row['end_time']})")

            if day == today:
                today_classes_count += 1
                today_classes_details.append(
                    f"{row['subject_name']} by {row['teacher_name']} in Room {row['room_number']} ({row['start_time']}-{row['end_time']})")

        # Build string like "Monday: Sub1 by Teacher1, Sub2 by Teacher2. Tuesday: ..."
        weekly_timetable_str = "\n".join([f"{day}: {', '.join(classes)}" for day, classes in timetable_by_day.items()])

    today_classes_str = "\n".join(today_classes_details) if today_classes_details else "No classes today."

    # Fetch Assignments Data
    pending_assignments_list = []
    submitted_assignments_count = 0
    if dept_id and sem is not None and sec:
        assignments = get_student_assignments(student_id, dept_id, sem, sec)
        for a in assignments:
            sub = get_student_submission_status(student_id, a["assignment_id"])
            if not sub:
                pending_assignments_list.append(a["title"])
            else:
                submitted_assignments_count += 1

    # Fetch Complaints Data
    complaints = get_student_complaints(student_id)
    pending_complaints_count = len([c for c in complaints if c['status'] not in ['Resolved', 'Closed']])
    resolved_complaints_count = len([c for c in complaints if c['status'] in ['Resolved', 'Closed']])

    # Fetch Library, Hostel, Transport
    lib_loans = get_student_library_loans(user["user_id"])
    issued_library_books_count = len(lib_loans)
    hostel = get_student_hostel_allocation(student_id)
    hostel_status = f"Active in {hostel['hostel_name']} Room {hostel['room_number']}" if hostel else "No active allocation"
    transport = get_student_transport_allocation(student_id)
    transport_status = f"Active on Route {transport['route_name']}" if transport else "No active allocation"

    # Fetch Notices
    notices = get_user_notices("Student", dept_id) if dept_id else []
    recent_notices = ", ".join([n['title'] for n in notices[:3]]) if notices else "None"

    pending_assignments_str = ", ".join(pending_assignments_list) if pending_assignments_list else "None"

    student_context = {
        "full_name": profile.get("full_name", "Student"),
        "department": profile.get("department_name", "Not available"),
        "semester": profile.get("semester", "Not available"),
        "section": profile.get("section", "Not available"),
        "cgpa": profile.get("cgpa", "Not available"),
        "overall_attendance": f"{attendance}%" if attendance else "Not available",
        "subject_attendance": subject_att_str,
        "total_fees": f"₹{total_fees:,.2f}" if fee_summary else "Not available",
        "pending_fees": f"₹{pending_fee:,.2f}" if fee_summary else "Not available",
        "today_classes_count": today_classes_count,
        "today_classes_details": today_classes_str,
        "weekly_timetable": weekly_timetable_str,  # Added Full Week Timetable
        "pending_assignments_list": pending_assignments_str,
        "submitted_assignments_count": submitted_assignments_count,
        "pending_complaints_count": pending_complaints_count,
        "resolved_complaints_count": resolved_complaints_count,
        "issued_library_books_count": issued_library_books_count,
        "hostel_status": hostel_status,
        "transport_status": transport_status,
        "recent_notices": recent_notices
    }

    # Call AI service
    ai_response = student_jarvis_chat(message, history, student_context)

    if not ai_response:
        return JSONResponse({"type": "text", "message": "I am having trouble processing your request right now."},
                            status_code=500)

    # Validate Navigation Action
    if ai_response.get("type") == "navigate":
        dest_id = ai_response.get("destination_id")
        if dest_id in NAVIGATION_REGISTRY:
            return JSONResponse({
                "type": "navigate",
                "message": ai_response.get("message", "Navigating..."),
                "url": NAVIGATION_REGISTRY[dest_id]
            })
        else:
            return JSONResponse({
                "type": "text",
                "message": "I cannot navigate to that page. It is either unauthorized or does not exist."
            })

    return JSONResponse({
        "type": "text",
        "message": ai_response.get("message", "I could not process that request.")
    })