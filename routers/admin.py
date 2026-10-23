# routers/admin.py
# STANDARD LIBRARY IMPORTS
import csv
import io
import os
import uuid
from datetime import datetime

# THIRD-PARTY IMPORTS
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates


# DATABASE IMPORTS
# -------------------- Admin Queries --------------------

from database.admin_queries import (
    # Department Management
    get_all_departments,
    get_departments_for_dropdown,
    add_department_to_db,
    update_department_in_db,
    get_department_details,
    get_department_stats,
    get_department_people,
    get_department_hod_history,
    get_hod_candidates,
    assign_new_hod,

    # Student Management
    get_all_students,
    add_student_to_db,
    get_student_directory_stats,
    get_student_for_admin,
    get_academic_sessions,
    get_student_enrollment_history,
    promote_student_semester,
    transfer_student_section,

    # Teacher Management
    get_all_teachers,
    add_teacher_to_db,
    get_teachers_for_dropdown,
    get_teacher_directory_stats,
    get_teacher_for_admin,
    update_teacher_in_db,
    get_teacher_service_history,
    promote_teacher_designation,
    transfer_teacher_department,

    # Subject Management
    get_all_subjects,
    add_subject_to_db,
    update_subject_in_db,
    get_subject_directory_stats,
    get_subject_for_admin,
    toggle_subject_status_db,
    get_subject_assignment_history,
    assign_teacher_to_subject,

    # Attendance
    get_low_attendance_students,

    # Results
    generate_semester_results,
    publish_semester_results,
    get_result_analysis,
    submit_results_for_principal,
    retract_published_results,
    get_result_status_summary,
    get_revaluation_requests,
    process_revaluation,

    # Room & Timetable Management
    get_all_rooms,
    add_room_to_db,
    get_all_time_slots,
    add_time_slot_to_db,
    add_timetable_entry,
    get_timetable_grid,
    generate_auto_timetable,
    get_timetable_status,
    update_timetable_status,

    # Notices & Events
    add_event_to_db,
    add_notice_to_db,
    get_all_notices,
    get_all_events,
    create_notice,
    process_notice_approval,
    create_event,

    # Complaints
    get_all_complaints,
    update_complaint_status,
    assign_complaint,
    escalate_complaint,
    add_complaint_message,

    # System Users
    get_all_system_users,

    # Analytics
    get_college_analytics,
    get_admin_command_center_stats,

    # Roles and Authentication
    toggle_user_status_secure,
    initiate_password_reset,
    assign_role_secure,

    # PDF Generation
    get_faculty_directory_report,
    get_low_attendance_report,
    get_fee_collection_summary,
    get_outstanding_fees_summary,
    get_login_history_report,
    get_activity_log_report,
    get_refund_register
)

# -------------------- Student Queries --------------------
from database.student_queries import (
    get_student_attendance_report,
    get_student_overall_attendance,
    get_student_marks_report,
    get_student_published_results
)
# -------------------- Teacher Queries --------------------
from database.teacher_queries import (
    get_subjects_for_teacher,
    get_my_leaves,
)
# -------------------- Fee Queries --------------------
from database.fee_queries import (
    # Fee Dashboard & Structure
    get_fee_dashboard_stats,
    add_fee_structure,
    get_all_fee_structures,

    # Student Fees
    assign_fee_to_student,
    get_student_fee_details_for_admin,
    bulk_assign_fee_to_students,

    # Payments
    save_fee_payment,
    get_pending_fees,
    get_payment_details_for_receipt,

    # Concession & Refund
    request_concession,
    process_refund,

    # Reports
    get_daily_collection_report,
    get_refund_register,
)
# -------------------- Database Connection --------------------
from database.connection import get_connection
# UTILITY IMPORTS
# -------------------- Authentication --------------------
from utils.auth import (
    get_current_user,
    RoleChecker,
)
# -------------------- PDF Generation --------------------
from utils.pdf_generator import (
    generate_student_list_pdf,
    generate_fee_receipt_pdf,
    generate_attendance_report_pdf,
    generate_generic_report_pdf
)


from database.asset_queries import (
    get_inventory_items, add_inventory_item, add_stock_movement,
    get_stock_requests, create_stock_request, process_stock_request, issue_stock_from_request
)

from utils.auth import PermissionChecker


# Define Permission Dependencies
user_view_perm = PermissionChecker("user.view")
reports_view_perm = PermissionChecker("reports.view")
inventory_view_perm = PermissionChecker("inventory.view")
user_reset_perm = PermissionChecker("user.reset_password")
user_deactivate_perm = PermissionChecker("user.deactivate")

user_assign_role_perm = PermissionChecker("user.assign_role")
reports_export_perm = PermissionChecker("reports.export_pdf")
inventory_manage_perm = PermissionChecker("inventory.manage")

inventory_approve_perm = PermissionChecker("inventory.approve")
reports_export_csv_perm = PermissionChecker("reports.export_csv")
reports_audit_view_perm = PermissionChecker("reports.audit.view")

reports_faculty_view_perm = PermissionChecker("reports.faculty.view")
reports_finance_view_perm = PermissionChecker("reports.finance.view")

reports_students_view_perm = PermissionChecker("reports.students.view")
reports_academics_view_perm = PermissionChecker("reports.academics.view")
reports_administration_view_perm = PermissionChecker("reports.administration.view")


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Security gate: Only Admins can access these routes
admin_only = RoleChecker(["Admin"])


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
        request: Request,
        user: dict = Depends(admin_only),
        academic_year: str = None,
        semester: str = None,
        department_id: str = None
):
    # Safely parse filters
    filters = {
        "academic_year": academic_year if academic_year else None,
        "semester": int(semester) if semester else None,
        "department_id": int(department_id) if department_id else None
    }

    stats = get_admin_command_center_stats(**filters)
    departments = get_departments_for_dropdown()
    low_attendance_students = get_low_attendance_students()

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "stats": stats,
            "departments": departments,
            "filters": filters,
            "low_attendance_students": low_attendance_students,
            "low_attendance_count": len(low_attendance_students)
        }
    )


# ==========================================
# DEPARTMENT MANAGEMENT (ENTERPRISE LEVEL)
# ==========================================

@router.get("/admin/departments", response_class=HTMLResponse)
async def get_departments_page(request: Request, user: dict = Depends(admin_only)):
    departments = get_all_departments()
    stats = get_department_stats()
    return templates.TemplateResponse(
        request=request,
        name="admin/departments.html",
        context={"departments": departments, "stats": stats}
    )


@router.post("/admin/departments/add")
async def post_department(request: Request):
    form = await request.form()
    form_data = {
        "department_name": form.get("department_name"),
        "department_code": form.get("department_code"),
        "short_name": form.get("short_name"),
        "description": form.get("description"),
        "status": form.get("status", "Active")
    }
    success, msg = add_department_to_db(form_data)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/departments/update")
async def update_department(
        department_id: int = Form(...),
        department_name: str = Form(...),
        department_code: str = Form(...),
        short_name: str = Form(""),
        description: str = Form(""),
        status: str = Form("Active")
):
    form_data = {
        "department_name": department_name, "department_code": department_code,
        "short_name": short_name, "description": description, "status": status
    }
    success, message = update_department_in_db(department_id, form_data)
    return JSONResponse({"success": success, "message": message})


@router.get("/admin/departments/{dept_id}", response_class=HTMLResponse)
async def department_detail_page(request: Request, dept_id: int, user: dict = Depends(admin_only)):
    details = get_department_details(dept_id)
    if not details:
        return HTMLResponse("Department not found", status_code=404)

    people = get_department_people(dept_id)
    history = get_department_hod_history(dept_id)
    candidates = get_hod_candidates()

    return templates.TemplateResponse(
        request=request,
        name="admin/department_details.html",
        context={
            "details": details,
            "people": people,
            "history": history,
            "candidates": candidates
        }
    )


@router.post("/admin/departments/{dept_id}/assign-hod")
async def assign_hod(dept_id: int, request: Request, user: dict = Depends(admin_only)):
    form = await request.form()
    user_id = int(form.get("user_id"))
    effective_from = form.get("effective_from")

    success, msg = assign_new_hod(dept_id, user_id, effective_from, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


# ==========================================
# RESULTS MANAGEMENT
# ==========================================

@router.get("/admin/results", response_class=HTMLResponse)
async def results_page(request: Request, user: dict = Depends(admin_only)):
    if user["role"] != "Admin":
        return HTMLResponse("<script>alert('Unauthorized'); window.location.href='/login';</script>")
    return templates.TemplateResponse(
        request=request,
        name="admin/results.html"
    )


@router.get("/admin/api/results")
async def api_get_results(semester: int, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
    return get_result_analysis(semester)


@router.post("/admin/api/results/generate")
async def api_generate_results(semester: int = Form(...), user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)
    success, message = generate_semester_results(semester)
    if success:
        return JSONResponse({"success": True, "message": message})
    return JSONResponse({"success": False, "message": message}, status_code=400)


@router.post("/admin/api/results/publish")
async def api_publish_results(semester: int = Form(...), user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)
    success, message = publish_semester_results(semester)
    if success:
        return JSONResponse({"success": True, "message": message})
    return JSONResponse({"success": False, "message": message}, status_code=400)


@router.post("/admin/api/results/submit-approval")
async def api_submit_for_approval(semester: int = Form(...), user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)
    success, message = submit_results_for_principal(semester)
    return JSONResponse({"success": success, "message": message})

@router.post("/admin/api/results/retract")
async def api_retract_results(semester: int = Form(...), user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    # Removed click.confirm. Frontend will handle the confirmation dialog.
    success, message = retract_published_results(semester)
    return JSONResponse({"success": success, "message": message})


@router.get("/admin/revaluation", response_class=HTMLResponse)
async def admin_reval_page(request: Request, user: dict = Depends(admin_only)):
    requests = get_revaluation_requests()
    return templates.TemplateResponse(
        request=request,
        name="admin/revaluation.html",
        context={"requests": requests}
    )


@router.post("/admin/api/revaluation/process")
async def api_process_reval(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    request_id = int(form.get("request_id"))
    new_marks = float(form.get("new_marks"))

    success, msg = process_revaluation(request_id, new_marks, user["user_id"])
    return JSONResponse({"success": success, "message": msg})

# ==========================================
# NOTICES & EVENTS
# ==========================================

@router.get("/admin/notices", response_class=HTMLResponse)
async def notices_page(request: Request, user: dict = Depends(admin_only)):
    notices = get_all_notices()
    events = get_all_events()
    return templates.TemplateResponse(
        request=request,
        name="admin/notices.html",
        context={
            "request": request,
            "notices": notices,
            "events": events
        }
    )


@router.post("/admin/api/notices/add")
async def api_add_notice(
        request: Request,
        file: UploadFile = File(None),  # Accept optional file
        user: dict = Depends(get_current_user)
):
    if user["role"] not in ["Admin", "HOD", "Principal"]:
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    form_data = {
        "title": form.get("title"),
        "description": form.get("description"),
        "category": form.get("category", "General"),
        "target_audience": form.get("target_audience", "All"),
        "target_department_id": form.get("target_department_id") or None,
        "publish_at": form.get("publish_at") or None,
        "expire_at": form.get("expire_at") or None
    }

    attachment_path = None
    # Handle file upload if provided
    if file and file.filename:
        # Validate file type (basic check)
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "application/msword",
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            return JSONResponse(
                {"success": False, "message": "Invalid file type. Only PDF, JPG, PNG, DOC, DOCX allowed."},
                status_code=400)

        # Generate safe filename
        ext = file.filename.split(".")[-1]
        safe_filename = f"notice_{uuid.uuid4().hex}.{ext}"
        upload_dir = "static/uploads/notices"
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_dir, safe_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        attachment_path = f"/{file_path}"  # Store path for DB

    success, msg = create_notice(form_data, user["role"], user["user_id"], attachment_path)
    return JSONResponse({"success": success, "message": msg})

@router.post("/admin/api/events/add")
async def api_add_event(request: Request):
    form = await request.form()
    success, msg = add_event_to_db(form['name'], form.get('description'), form['date'], form['venue'])
    return JSONResponse({"success": success, "message": msg})


# ==========================================
# COMPLAINTS
# ==========================================

@router.get("/admin/complaints", response_class=HTMLResponse)
async def admin_complaints_page(request: Request, user: dict = Depends(admin_only)):
    complaints = get_all_complaints()
    users = get_all_system_users() # Fix: Fetch users for dropdown
    return templates.TemplateResponse(
        request=request,
        name="admin/complaints.html",
        context={
            "complaints": complaints,
            "users": users
        }
    )


@router.post("/admin/api/complaints/update")
async def api_update_complaint(complaint_id: int = Form(...), status: str = Form(...)):
    success = update_complaint_status(complaint_id, status)
    if success:
        return JSONResponse({"success": True, "message": "Status updated."})
    else:
        return JSONResponse({"success": False, "message": "Failed."}, status_code=400)


# --- STUDENTS ---
@router.get("/admin/students", response_class=HTMLResponse)
async def get_students_page(
        request: Request,
        user: dict = Depends(admin_only),
        search: str = None,
        department_id: str = None,  # Changed to str
        semester: str = None  # Changed to str
):
    # Parse strings to int safely
    dept_id = int(department_id) if department_id and department_id.isdigit() else None
    sem = int(semester) if semester and semester.isdigit() else None

    departments = get_departments_for_dropdown()
    students = get_all_students(search, dept_id, sem)
    stats = get_student_directory_stats()
    filters = {"search": search, "department_id": dept_id, "semester": sem}

    return templates.TemplateResponse(
        request=request,
        name="admin/students.html",
        context={
            "departments": departments,
            "students": students,
            "stats": stats,
            "filters": filters
        }
    )

@router.post("/admin/students")
async def post_student(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        mobile: str = Form(""),
        enrollment: str = Form(...),
        department_id: int = Form(...),
        semester: int = Form(...),
        section: str = Form(""),
        cgpa: str = Form(""),
        skills: str = Form(""),
        interests: str = Form(""),
        domain: str = Form(""),
        salary: str = Form(""),
        password: str = Form(...)
):
    form_data = {
        "name": name, "email": email, "mobile": mobile, "enrollment": enrollment,
        "department_id": department_id, "semester": semester, "section": section,
        "cgpa": cgpa, "skills": skills, "interests": interests, "domain": domain,
        "salary": salary, "password": password
    }
    success, message = add_student_to_db(form_data)
    if success:
        return JSONResponse({"success": True, "message": message})
    else:
        return JSONResponse({"success": False, "message": message}, status_code=400)


@router.get("/admin/students/{student_id}", response_class=HTMLResponse)
async def student_profile_page(request: Request, student_id: int, user: dict = Depends(admin_only)):
    profile = get_student_for_admin(student_id)
    if not profile:
        return HTMLResponse("Student not found", status_code=404)

    # Reuse existing student queries
    attendance = get_student_attendance_report(student_id)
    overall_att = get_student_overall_attendance(student_id)
    marks = get_student_marks_report(student_id)
    all_results = get_student_published_results(student_id)
    sem_result = all_results[0] if all_results else None
    fees = get_student_fee_details_for_admin(student_id) or {}

    # Phase 2 additions (YEH LINEIN ZAROOR HONI CHAHIYE)
    sessions = get_academic_sessions()
    history = get_student_enrollment_history(student_id)
    departments = get_departments_for_dropdown()

    return templates.TemplateResponse(
        request=request,
        name="admin/student_profile.html",
        context={
            "profile": profile,
            "attendance": attendance,
            "overall_attendance": overall_att,
            "marks": marks,
            "sem_result": sem_result,
            "fees": fees,
            "sessions": sessions,
            "history": history,
            "departments": departments
        }
    )

@router.post("/admin/students/{student_id}/promote")
async def promote_student(student_id: int, request: Request, user: dict = Depends(admin_only)):
    form = await request.form()
    new_semester = int(form.get("new_semester"))
    new_session_id = int(form.get("new_session_id"))

    success, msg = promote_student_semester(student_id, new_semester, new_session_id, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/students/{student_id}/transfer")
async def transfer_student(student_id: int, request: Request, user: dict = Depends(admin_only)):
    form = await request.form()
    new_department_id = int(form.get("new_department_id"))
    new_section = form.get("new_section")

    success, msg = transfer_student_section(student_id, new_department_id, new_section, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


# --- TEACHERS ---
@router.get("/admin/teachers", response_class=HTMLResponse)
async def get_teachers_page(
        request: Request,
        user: dict = Depends(admin_only),
        search: str = None,
        department_id: str = None  # Changed to str
):
    # Parse string to int safely
    dept_id = int(department_id) if department_id and department_id.isdigit() else None

    departments = get_departments_for_dropdown()
    teachers = get_all_teachers(search, dept_id)
    stats = get_teacher_directory_stats()
    filters = {"search": search, "department_id": dept_id}

    return templates.TemplateResponse(
        request=request,
        name="admin/teachers.html",
        context={
            "departments": departments,
            "teachers": teachers,
            "stats": stats,
            "filters": filters
        }
    )

@router.post("/admin/teachers")
async def post_teacher(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        mobile: str = Form(""),
        department_id: int = Form(...),
        designation: str = Form(...),
        qualification: str = Form(""),
        experience: int = Form(0),
        password: str = Form(...)
):
    form_data = {
        "name": name, "email": email, "mobile": mobile,
        "department_id": department_id, "designation": designation,
        "qualification": qualification, "experience": experience,
        "password": password
    }
    success, message = add_teacher_to_db(form_data)
    if success:
        return JSONResponse({"success": True, "message": message})
    else:
        return JSONResponse({"success": False, "message": message}, status_code=400)


@router.post("/admin/teachers/update")
async def update_teacher(
        request: Request,
        teacher_id: int = Form(...),
        name: str = Form(...),
        email: str = Form(...),
        mobile: str = Form(""),
        department_id: int = Form(...),
        designation: str = Form(...),
        qualification: str = Form(""),
        experience: int = Form(0)
):
    form_data = {
        "name": name, "email": email, "mobile": mobile,
        "department_id": department_id, "designation": designation,
        "qualification": qualification, "experience": experience
    }
    success, message = update_teacher_in_db(teacher_id, form_data)
    return JSONResponse({"success": success, "message": message})


@router.get("/admin/teachers/{teacher_id}", response_class=HTMLResponse)
async def teacher_profile_page(request: Request, teacher_id: int, user: dict = Depends(admin_only)):
    profile = get_teacher_for_admin(teacher_id)
    if not profile:
        return HTMLResponse("Teacher not found", status_code=404)

    # Reuse existing teacher queries
    subjects = get_subjects_for_teacher(teacher_id)
    leaves = get_my_leaves(teacher_id)

    # Phase 2 additions
    history = get_teacher_service_history(teacher_id)
    departments = get_departments_for_dropdown()

    return templates.TemplateResponse(
        request=request,
        name="admin/teacher_profile.html",
        context={
            "profile": profile,
            "subjects": subjects,
            "leaves": leaves,
            "history": history,  # New
            "departments": departments  # New
        }
    )


@router.post("/admin/teachers/{teacher_id}/promote")
async def promote_teacher(teacher_id: int, request: Request, user: dict = Depends(admin_only)):
    form = await request.form()
    new_designation = form.get("new_designation")
    effective_from = form.get("effective_from")

    success, msg = promote_teacher_designation(teacher_id, new_designation, effective_from, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/teachers/{teacher_id}/transfer")
async def transfer_teacher(teacher_id: int, request: Request, user: dict = Depends(admin_only)):
    form = await request.form()
    new_department_id = int(form.get("new_department_id"))
    effective_from = form.get("effective_from")

    success, msg = transfer_teacher_department(teacher_id, new_department_id, effective_from, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


# --- SUBJECTS ---

# --- SUBJECTS ---
@router.get("/admin/subjects", response_class=HTMLResponse)
async def get_subjects_page(
        request: Request,
        user: dict = Depends(admin_only),
        search: str = None,
        department_id: str = None,  # Changed to str
        semester: str = None,  # Changed to str
        subject_type: str = None
):
    # Parse strings to int safely
    dept_id = int(department_id) if department_id and department_id.isdigit() else None
    sem = int(semester) if semester and semester.isdigit() else None

    departments = get_departments_for_dropdown()
    teachers = get_teachers_for_dropdown()
    subjects = get_all_subjects(search, dept_id, sem, subject_type)
    stats = get_subject_directory_stats()
    filters = {"search": search, "department_id": dept_id, "semester": sem, "subject_type": subject_type}

    return templates.TemplateResponse(
        request=request,
        name="admin/subjects.html",
        context={
            "departments": departments,
            "teachers": teachers,
            "subjects": subjects,
            "stats": stats,
            "filters": filters
        }
    )



@router.post("/admin/subjects/add")
async def post_subject(
        request: Request,
        subject_name: str = Form(...),
        subject_code: str = Form(...),
        department_id: int = Form(...),
        teacher_id: str = Form(""),
        semester: int = Form(...),
        credits: int = Form(4),
        subject_type: str = Form("Theory"),
        status: str = Form("Active")
):
    form_data = {
        "subject_name": subject_name, "subject_code": subject_code,
        "department_id": department_id, "teacher_id": teacher_id,
        "semester": semester, "credits": credits,
        "subject_type": subject_type, "status": status
    }
    success, message = add_subject_to_db(form_data)
    if success:
        return JSONResponse({"success": True, "message": message})
    else:
        return JSONResponse({"success": False, "message": message}, status_code=400)


@router.post("/admin/subjects/update")
async def update_subject(
        request: Request,
        subject_id: int = Form(...),
        subject_code: str = Form(...),
        subject_name: str = Form(...),
        department_id: int = Form(...),
        teacher_id: str = Form(""),
        semester: int = Form(...),
        credits: int = Form(4),
        subject_type: str = Form("Theory"),
        status: str = Form("Active")
):
    form_data = {
        "subject_code": subject_code, "subject_name": subject_name,
        "department_id": department_id, "teacher_id": teacher_id,
        "semester": semester, "credits": credits,
        "subject_type": subject_type, "status": status
    }
    success, message = update_subject_in_db(subject_id, form_data)
    if success:
        return JSONResponse({"success": True, "message": message})
    else:
        return JSONResponse({"success": False, "message": message}, status_code=400)


@router.post("/admin/subjects/toggle")
async def toggle_subject_status(subject_id: int = Form(...), status: str = Form(...)):
    new_status = "Active" if status == "Inactive" else "Inactive"
    success = toggle_subject_status_db(subject_id, new_status)
    return JSONResponse({"success": success, "new_status": new_status})


@router.get("/admin/subjects/{subject_id}", response_class=HTMLResponse)
async def subject_profile_page(request: Request, subject_id: int, user: dict = Depends(admin_only)):
    profile = get_subject_for_admin(subject_id)
    if not profile:
        return HTMLResponse("Subject not found", status_code=404)

    # Phase 2 additions
    history = get_subject_assignment_history(subject_id)
    teachers = get_teachers_for_dropdown()

    return templates.TemplateResponse(
        request=request,
        name="admin/subject_profile.html",
        context={
            "profile": profile,
            "history": history,
            "teachers": teachers
        }
    )


@router.post("/admin/subjects/{subject_id}/assign")
async def assign_teacher(subject_id: int, request: Request, user: dict = Depends(admin_only)):
    form = await request.form()
    new_teacher_id = int(form.get("new_teacher_id"))
    effective_from = form.get("effective_from")

    success, msg = assign_teacher_to_subject(subject_id, new_teacher_id, effective_from, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


# ==========================================
# TIMETABLE
# ==========================================

@router.get("/admin/timetable", response_class=HTMLResponse)
async def timetable_page(request: Request, user: dict = Depends(admin_only)):
    departments = get_departments_for_dropdown()
    subjects = get_all_subjects()
    teachers = get_teachers_for_dropdown()
    rooms = get_all_rooms()
    slots = get_all_time_slots()
    return templates.TemplateResponse(
        request=request,
        name="admin/timetable.html",
        context={
            "request": request,
            "departments": departments,
            "subjects": subjects,
            "teachers": teachers,
            "rooms": rooms,
            "slots": slots
        }
    )


@router.post("/admin/api/timetable/room/add")
async def api_add_room(request: Request):
    form = await request.form()
    success, msg = add_room_to_db(dict(form))
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/timetable/slot/add")
async def api_add_slot(request: Request):
    form = await request.form()
    success, msg = add_time_slot_to_db(dict(form))
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/timetable/add")
async def api_add_tt(request: Request):
    form = await request.form()
    success, msg = add_timetable_entry(dict(form))
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/api/timetable/grid")
async def api_get_grid(dept: int, sem: int, sec: str):
    return get_timetable_grid(dept, sem, sec)


@router.post("/admin/api/timetable/generate")
async def api_generate_tt(
        request: Request,
        user: dict = Depends(admin_only)
):
    form = await request.form()
    department_id = int(form.get("department_id"))
    semester = int(form.get("semester"))
    section = form.get("section")
    academic_year = form.get("academic_year", "2024-25")

    result = generate_auto_timetable(department_id, semester, section, academic_year)
    return JSONResponse(result)


@router.get("/admin/api/timetable/status")
async def api_get_tt_status(dept: int, sem: int, sec: str, year: str = "2024-25"):
    status = get_timetable_status(dept, sem, sec, year)
    return {"status": status}


@router.post("/admin/api/timetable/submit")
async def api_submit_tt(request: Request, user: dict = Depends(admin_only)):
    form = await request.form()
    dept = int(form.get("department_id"))
    sem = int(form.get("semester"))
    sec = form.get("section")
    year = form.get("academic_year", "2024-25")

    # Check for INCOMPLETE status before submitting? For Phase 3, we assume Admin ensures it's complete.
    success, msg = update_timetable_status(dept, sem, sec, "Pending Approval", "Draft", year)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/timetable/approve")
async def api_approve_tt(request: Request, user: dict = Depends(admin_only)):
    form = await request.form()
    dept = int(form.get("department_id"))
    sem = int(form.get("semester"))
    sec = form.get("section")
    year = form.get("academic_year", "2024-25")

    success, msg = update_timetable_status(dept, sem, sec, "Approved", "Pending Approval", year)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/timetable/publish")
async def api_publish_tt(request: Request, user: dict = Depends(admin_only)):
    form = await request.form()
    dept = int(form.get("department_id"))
    sem = int(form.get("semester"))
    sec = form.get("section")
    year = form.get("academic_year", "2024-25")

    success, msg = update_timetable_status(dept, sem, sec, "Published", "Approved", year)
    return JSONResponse({"success": success, "message": msg})


# ==========================================
# FEES
# ==========================================

@router.get("/admin/fees", response_class=HTMLResponse)
async def fees_page(request: Request, user: dict = Depends(admin_only)):
    stats = get_fee_dashboard_stats()
    departments = get_departments_for_dropdown()
    students = get_all_students()
    fee_structures = get_all_fee_structures()
    pending = get_pending_fees()
    return templates.TemplateResponse(
        request=request,
        name="admin/fees.html",
        context={
            "request": request, "stats": stats, "departments": departments,
            "students": students, "fee_structures": fee_structures, "pending": pending
        }
    )


@router.post("/admin/api/fees/structure/add")
async def api_add_fs(request: Request):
    form = await request.form()
    success, msg = add_fee_structure(dict(form))
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/fees/assign")
async def api_assign_fee(request: Request):
    form = await request.form()
    success, msg = assign_fee_to_student(int(form['student_id']), int(form['fee_structure_id']), form['discount'],
                                         form['scholarship'], form['due_date'])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/api/fees/student/{student_id}")
async def api_get_student_fee(student_id: int):
    data = get_student_fee_details_for_admin(student_id)
    return data or {}


@router.post("/admin/api/fees/pay")
async def api_pay(request: Request, user: dict = Depends(get_current_user)):
    form = await request.form()
    success, msg = save_fee_payment(int(form['student_fee_id']), form['amount'], form['payment_mode'],
                                    form.get('transaction_id'), form.get('remarks'), user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/fees/bulk-assign")
async def api_bulk_assign_fee(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    dept_id = int(form.get("department_id"))
    sem = int(form.get("semester"))
    sec = form.get("section")
    fee_structure_id = int(form.get("fee_structure_id"))
    discount = float(form.get("discount", 0))
    scholarship = float(form.get("scholarship", 0))
    due_date = form.get("due_date")

    success, msg = bulk_assign_fee_to_students(dept_id, sem, sec, fee_structure_id, discount, scholarship, due_date)
    return JSONResponse({"success": success, "message": msg})

# ==========================================
# PROFILE / ME
# ==========================================

@router.get("/admin/api/me")
async def api_get_me(user: dict = Depends(get_current_user)):
    conn = get_connection()
    if conn is None: return JSONResponse({"error": "DB Error"}, status_code=500)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, profile_image FROM users WHERE user_id = %s", (user["user_id"],))
        db_user = cursor.fetchone()
        if not db_user: return JSONResponse({"error": "User not found"}, status_code=404)

        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good Morning"
        elif hour < 17:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"

        current_date = datetime.now().strftime("%d %b, %Y")

        return {
            "full_name": db_user["full_name"],
            "profile_image": db_user["profile_image"] or "default.png",
            "greeting": greeting,
            "current_date": current_date
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


# ==========================================
# USER MANAGEMENT
# ==========================================

@router.get("/admin/users", response_class=HTMLResponse)
async def users_page(request: Request, user: dict = Depends(user_view_perm)):
    users = get_all_system_users()

    return templates.TemplateResponse(
        request=request,
        name="admin/users.html",
        context={
            "users": users,
            "current_user": user
        }
    )

@router.post("/admin/api/users/toggle")
async def api_toggle_user(request: Request, user_id: int = Form(...), status: str = Form(...), actor: dict = Depends(user_deactivate_perm)):
    success, msg = toggle_user_status_secure(user_id, status, actor["user_id"])
    return JSONResponse({"success": success, "message": msg})

@router.post("/admin/api/users/reset")
async def api_reset_user(request: Request, user_id: int = Form(...), actor: dict = Depends(user_reset_perm)):
    success, msg, token = initiate_password_reset(user_id, actor["user_id"])
    if token:
        # In production, this goes via email. For now, return it to show in UI.
        return JSONResponse({"success": True, "message": f"Reset initiated. Temp Token: {token}"})
    return JSONResponse({"success": False, "message": msg})

@router.post("/admin/api/users/assign-role")
async def api_assign_role(request: Request, user_id: int = Form(...), new_role: str = Form(...), actor: dict = Depends(user_assign_role_perm)):
    success, msg = assign_role_secure(user_id, new_role, actor["user_id"])
    return JSONResponse({"success": success, "message": msg})


# ==========================================
# REPORTS
# ==========================================

@router.get("/admin/reports", response_class=HTMLResponse)
async def reports_workspace(request: Request, user: dict = Depends(reports_view_perm)):
    analytics = get_college_analytics()
    departments = get_departments_for_dropdown()
    return templates.TemplateResponse(
        request=request,
        name="admin/reports.html",
        context={"analytics": analytics, "departments": departments}
    )

@router.get("/admin/reports/fees/csv")
async def download_fees_csv(user: dict = Depends(admin_only)):
    pending_fees = get_pending_fees()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Total Payable (Rs)", "Balance Due (Rs)"])
    for p in pending_fees:
        writer.writerow([p["full_name"], p["payable_fee"], p["balance"]])

    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=Pending_Fees_Report.csv"})

@router.get("/admin/reports/students/preview", response_class=HTMLResponse)
async def student_report_preview(
        request: Request,
        user: dict = Depends(reports_students_view_perm),
        department_id: int = None,
        semester: int = None
):
    students = get_all_students(search=None, department_id=department_id, semester=semester)
    departments = get_departments_for_dropdown()

    return templates.TemplateResponse(
        request=request,
        name="admin/report_preview.html",
        context={
            "report_title": "Student Master List",
            "columns": ["Enrollment", "Name", "Email", "Department", "Sem", "CGPA"],
            "row_keys": ["enrollment_no", "full_name", "email", "department_name", "semester", "cgpa"],
            "rows": students,
            "export_url": "/admin/reports/students/pdf",
            "filters": {"department_id": department_id, "semester": semester},
            "departments": departments
        }
    )

@router.get("/admin/reports/students/pdf")
async def download_students_pdf(
        user: dict = Depends(reports_export_perm),
        department_id: int = None,
        semester: int = None
):
    students = get_all_students(search=None, department_id=department_id, semester=semester)
    buffer = generate_student_list_pdf(students)
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=Students_Report.pdf"})

@router.get("/admin/reports/students/csv")
async def download_students_csv(
        user: dict = Depends(reports_export_csv_perm),
        department_id: int = None,
        semester: int = None
):
    students = get_all_students(search=None, department_id=department_id, semester=semester)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Enrollment", "Name", "Email", "Department", "Sem", "CGPA"])
    for s in students:
        name = f"'{s['full_name']}" if str(s['full_name']).startswith(('=', '+', '-', '@')) else s['full_name']
        writer.writerow([s['enrollment_no'], name, s['email'], s.get('department_name') or '-', s['semester'], s.get('cgpa') or '-'])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=Students_Report.csv"})

@router.get("/admin/reports/faculty/preview", response_class=HTMLResponse)
async def faculty_report_preview(
        request: Request,
        user: dict = Depends(reports_faculty_view_perm),
        department_id: int = None
):
    faculty = get_faculty_directory_report(department_id)
    departments = get_departments_for_dropdown()

    return templates.TemplateResponse(
        request=request,
        name="admin/report_preview.html",
        context={
            "report_title": "Faculty Directory",
            "columns": ["Name", "Email", "Department", "Designation", "Qualification", "Experience"],
            "row_keys": ["full_name", "email", "department_name", "designation", "qualification", "experience"],
            "rows": faculty,
            "export_url": "/admin/reports/faculty/pdf",
            "filters": {"department_id": department_id},
            "departments": departments
        }
    )

@router.get("/admin/reports/faculty/pdf")
async def download_faculty_pdf(
        user: dict = Depends(reports_export_perm),
        department_id: int = None
):
    faculty = get_faculty_directory_report(department_id)
    buffer = generate_generic_report_pdf(
        "Faculty Directory Report",
        ["Name", "Email", "Department", "Designation", "Qualification", "Experience"],
        ["full_name", "email", "department_name", "designation", "qualification", "experience"],
        faculty
    )
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=Faculty_Directory.pdf"})

@router.get("/admin/reports/faculty/csv")
async def download_faculty_csv(
        user: dict = Depends(reports_export_csv_perm),
        department_id: int = None
):
    faculty = get_faculty_directory_report(department_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Department", "Designation", "Qualification", "Experience"])
    for f in faculty:
        name = f"'{f['full_name']}" if str(f['full_name']).startswith(('=', '+', '-', '@')) else f['full_name']
        writer.writerow([name, f['email'], f.get('department_name') or '-', f.get('designation'), f.get('qualification') or '-', f.get('experience')])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=Faculty_Directory.csv"})

@router.get("/admin/reports/attendance/preview", response_class=HTMLResponse)
async def attendance_report_preview(
        request: Request,
        user: dict = Depends(reports_academics_view_perm),
        department_id: int = None,
        semester: int = None
):
    attendance_data = get_low_attendance_report(department_id, semester)
    departments = get_departments_for_dropdown()

    return templates.TemplateResponse(
        request=request,
        name="admin/report_preview.html",
        context={
            "report_title": "Low Attendance Report (< 75%)",
            "columns": ["Student Name", "Department", "Sem", "Subject", "Attendance %"],
            "row_keys": ["student_name", "department_name", "semester", "subject_name", "percentage"],
            "rows": attendance_data,
            "export_url": "/admin/reports/attendance/pdf",
            "filters": {"department_id": department_id, "semester": semester},
            "departments": departments
        }
    )

@router.get("/admin/reports/attendance/pdf")
async def download_attendance_pdf(
        user: dict = Depends(reports_export_perm),
        department_id: int = None,
        semester: int = None
):
    attendance_data = get_low_attendance_report(department_id, semester)
    buffer = generate_generic_report_pdf(
        "Low Attendance Report",
        ["Student Name", "Department", "Sem", "Subject", "Attendance %"],
        ["student_name", "department_name", "semester", "subject_name", "percentage"],
        attendance_data
    )
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=Low_Attendance.pdf"})

@router.get("/admin/reports/attendance/csv")
async def download_attendance_csv(
        user: dict = Depends(reports_export_csv_perm),
        department_id: int = None,
        semester: int = None
):
    attendance_data = get_low_attendance_report(department_id, semester)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Department", "Semester", "Subject", "Attendance %"])
    for a in attendance_data:
        name = f"'{a['student_name']}" if str(a['student_name']).startswith(('=', '+', '-', '@')) else a['student_name']
        writer.writerow([name, a.get('department_name') or '-', a.get('semester'), a.get('subject_name'), a.get('percentage')])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=Low_Attendance.csv"})

# Finance Previews
@router.get("/admin/reports/finance/collection/preview", response_class=HTMLResponse)
async def fee_collection_preview(request: Request, user: dict = Depends(reports_finance_view_perm)):
    data = get_fee_collection_summary()
    return templates.TemplateResponse(
        request=request,
        name="admin/report_preview.html",
        context={
            "report_title": "Daily Fee Collection Summary",
            "columns": ["Date", "Mode", "Transactions", "Total Collected"],
            "row_keys": ["date", "payment_mode", "count", "total"],
            "rows": data,
            "export_url": "/admin/reports/finance/collection/pdf",
            "filters": {},
            "departments": []
        }
    )

@router.get("/admin/reports/finance/outstanding/preview", response_class=HTMLResponse)
async def outstanding_fees_preview(request: Request, user: dict = Depends(reports_finance_view_perm)):
    data = get_outstanding_fees_summary()
    return templates.TemplateResponse(
        request=request,
        name="admin/report_preview.html",
        context={
            "report_title": "Outstanding Fees Summary",
            "columns": ["Student", "Enrollment", "Department", "Payable", "Balance"],
            "row_keys": ["full_name", "enrollment_no", "department_name", "payable_fee", "balance"],
            "rows": data,
            "export_url": "/admin/reports/finance/outstanding/pdf",
            "filters": {},
            "departments": []
        }
    )

# Finance Exports
@router.get("/admin/reports/finance/collection/pdf")
async def download_collection_pdf(user: dict = Depends(reports_export_perm)):
    data = get_fee_collection_summary()
    buffer = generate_generic_report_pdf(
        "Daily Fee Collection Summary",
        ["Date", "Mode", "Transactions", "Total Collected"],
        ["date", "payment_mode", "count", "total"],
        data
    )
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=Fee_Collection.pdf"})

@router.get("/admin/reports/finance/collection/csv")
async def download_collection_csv(user: dict = Depends(reports_export_csv_perm)):
    data = get_fee_collection_summary()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Mode", "Transactions", "Total Collected"])
    for d in data:
        writer.writerow([d.get('date'), d.get('payment_mode'), d.get('count'), d.get('total')])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=Fee_Collection.csv"})

@router.get("/admin/reports/finance/outstanding/pdf")
async def download_outstanding_pdf(user: dict = Depends(reports_export_perm)):
    data = get_outstanding_fees_summary()
    buffer = generate_generic_report_pdf(
        "Outstanding Fees Summary",
        ["Student", "Enrollment", "Department", "Payable", "Balance"],
        ["full_name", "enrollment_no", "department_name", "payable_fee", "balance"],
        data
    )
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=Outstanding_Fees.pdf"})

@router.get("/admin/reports/finance/outstanding/csv")
async def download_outstanding_csv(user: dict = Depends(reports_export_csv_perm)):
    data = get_outstanding_fees_summary()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student", "Enrollment", "Department", "Payable", "Balance"])
    for d in data:
        name = f"'{d['full_name']}" if str(d['full_name']).startswith(('=', '+', '-', '@')) else d['full_name']
        writer.writerow([name, d.get('enrollment_no'), d.get('department_name') or '-', d.get('payable_fee'), d.get('balance')])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=Outstanding_Fees.csv"})

# Audit Previews
@router.get("/admin/reports/audit/login/preview", response_class=HTMLResponse)
async def login_history_preview(request: Request, user: dict = Depends(reports_audit_view_perm)):
    data = get_login_history_report()
    return templates.TemplateResponse(
        request=request,
        name="admin/report_preview.html",
        context={
            "report_title": "Login History Report",
            "columns": ["Time", "User", "Role", "IP Address", "Device"],
            "row_keys": ["login_time", "full_name", "role", "ip_address", "device"],
            "rows": data,
            "export_url": "/admin/reports/audit/login/pdf",
            "filters": {},
            "departments": []
        }
    )

@router.get("/admin/reports/audit/activity/preview", response_class=HTMLResponse)
async def activity_log_preview(request: Request, user: dict = Depends(reports_audit_view_perm)):
    data = get_activity_log_report()
    return templates.TemplateResponse(
        request=request,
        name="admin/report_preview.html",
        context={
            "report_title": "System Activity Log",
            "columns": ["Time", "User", "Action"],
            "row_keys": ["log_time", "full_name", "action"],
            "rows": data,
            "export_url": "/admin/reports/audit/activity/pdf",
            "filters": {},
            "departments": []
        }
    )

# Audit Exports
@router.get("/admin/reports/audit/login/pdf")
async def download_login_pdf(user: dict = Depends(reports_export_perm)):
    data = get_login_history_report()
    buffer = generate_generic_report_pdf(
        "Login History Report",
        ["Time", "User", "Role", "IP Address", "Device"],
        ["login_time", "full_name", "role", "ip_address", "device"],
        data
    )
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=Login_History.pdf"})

@router.get("/admin/reports/audit/login/csv")
async def download_login_csv(user: dict = Depends(reports_export_csv_perm)):
    data = get_login_history_report()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Time", "User", "Role", "IP Address", "Device"])
    for d in data:
        writer.writerow([d.get('login_time'), d.get('full_name'), d.get('role'), d.get('ip_address'), d.get('device')])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=Login_History.csv"})

@router.get("/admin/reports/audit/activity/pdf")
async def download_activity_pdf(user: dict = Depends(reports_export_perm)):
    data = get_activity_log_report()
    buffer = generate_generic_report_pdf(
        "System Activity Log",
        ["Time", "User", "Action"],
        ["log_time", "full_name", "action"],
        data
    )
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=Activity_Log.pdf"})

@router.get("/admin/reports/audit/activity/csv")
async def download_activity_csv(user: dict = Depends(reports_export_csv_perm)):
    data = get_activity_log_report()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Time", "User", "Action"])
    for d in data:
        writer.writerow([d.get('log_time'), d.get('full_name'), d.get('action')])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=Activity_Log.csv"})


@router.get("/admin/receipts/{payment_id}/pdf")
async def download_fee_receipt(payment_id: int, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return HTMLResponse("Unauthorized", status_code=403)

    payment_data = get_payment_details_for_receipt(payment_id)
    if not payment_data:
        return HTMLResponse("Receipt not found", status_code=404)

    buffer = generate_fee_receipt_pdf(payment_data)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Receipt_{payment_data['receipt_number']}.pdf"}
    )


@router.post("/admin/api/fees/request-concession")
async def api_request_concession(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    success, msg = request_concession(
        int(form.get("student_fee_id")),
        float(form.get("amount")),
        form.get("reason"),
        user["user_id"]
    )
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/fees/refund")
async def api_process_refund(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    payment_id = int(form.get("payment_id"))
    refund_amount = float(form.get("refund_amount"))
    reason = form.get("reason")

    success, msg = process_refund(payment_id, refund_amount, reason, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/complaints/assign")
async def api_assign_complaint(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    success, msg = assign_complaint(int(form.get("complaint_id")), int(form.get("assignee_id")), user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/complaints/escalate")
async def api_escalate_complaint(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    success, msg = escalate_complaint(int(form.get("complaint_id")), form.get("reason"), user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/complaints/message")
async def api_add_message(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    is_internal = form.get("is_internal") == "on"
    success, msg = add_complaint_message(int(form.get("complaint_id")), user["user_id"], form.get("message"),
                                         is_internal)
    return JSONResponse({"success": success, "message": msg})

@router.get("/admin/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request, user: dict = Depends(inventory_view_perm)):
    items = get_inventory_items()
    return templates.TemplateResponse(
        request=request,
        name="admin/inventory.html",
        context={"items": items}
    )

@router.post("/admin/api/inventory/add")
async def api_add_inventory(request: Request, user: dict = Depends(inventory_manage_perm)):
    form = await request.form()
    success, msg = add_inventory_item(form.get("item_name"), form.get("unit"), form.get("reorder_level"))
    return JSONResponse({"success": success, "message": msg})

@router.post("/admin/api/inventory/movement")
async def api_stock_movement(request: Request, user: dict = Depends(inventory_manage_perm)):
    form = await request.form()
    success, msg = add_stock_movement(
        int(form.get("item_id")),
        form.get("movement_type"),
        float(form.get("quantity")),
        form.get("reason", "Manual adjustment"),
        user["user_id"]
    )
    return JSONResponse({"success": success, "message": msg})

@router.get("/admin/stock-requests", response_class=HTMLResponse)
async def stock_requests_page(request: Request, user: dict = Depends(inventory_approve_perm)):
    requests = get_stock_requests()
    return templates.TemplateResponse(
        request=request,
        name="admin/stock_requests.html",
        context={"requests": requests}
    )

@router.post("/admin/api/stock-requests/process")
async def api_process_stock_request(request: Request, user: dict = Depends(inventory_approve_perm)):
    form = await request.form()
    req_id = int(form.get("request_id"))
    action = form.get("action") # 'Approved' or 'Rejected'
    success, msg = process_stock_request(req_id, action, user["user_id"])
    return JSONResponse({"success": success, "message": msg})

@router.post("/admin/api/stock-requests/issue")
async def api_issue_stock(request: Request, user: dict = Depends(inventory_manage_perm)):
    form = await request.form()
    req_id = int(form.get("request_id"))
    success, msg = issue_stock_from_request(req_id, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


# =====================================================================
# Workstream A — Finance Report 404 Fix
# The sidebar links to /admin/reports/finance but this base route was
# never registered. Sub-routes (/collection/preview, /outstanding/preview)
# exist at lines 1304+ but the parent route was missing.
# Fix: add the missing GET /admin/reports/finance route that renders
# the existing finance_reports.html template with daily collections
# and refund register data.
# =====================================================================

@router.get("/admin/reports/finance", response_class=HTMLResponse)
async def finance_reports_page(request: Request, user: dict = Depends(reports_finance_view_perm)):
    """Finance & Reconciliation Reports page."""
    daily_report = get_fee_collection_summary()
    refunds = get_refund_register()
    return templates.TemplateResponse(
        request=request,
        name="admin/finance_reports.html",
        context={"daily_report": daily_report, "refunds": refunds}
    )


# =====================================================================
# PHASE 4 — ADMIN JARVIS AI ASSISTANT
# Uses the direct-Groq-API pattern from Student Jarvis. Pre-loads
# admin context from existing institution-wide query functions.
# Read-only + navigation only — no mutating operations.
# =====================================================================

from ai.admin_jarvis import admin_jarvis_chat
from database.principal_queries import (
    get_college_stats, get_finance_oversight_stats,
    get_hr_oversight_stats, get_sensitive_complaints_oversight
)
from services.principal_service import PrincipalApprovalService

# Admin navigation registry (allowlist — only authorized Admin routes)
ADMIN_NAVIGATION_REGISTRY = {
    "dashboard": "/admin/dashboard",
    "users": "/admin/users",
    "departments": "/admin/departments",
    "subjects": "/admin/subjects",
    "students": "/admin/students",
    "teachers": "/admin/teachers",
    "timetable": "/admin/timetable",
    "attendance": "/admin/attendance",
    "marks": "/admin/marks",
    "results": "/admin/results",
    "fees": "/admin/fees",
    "notices": "/admin/notices",
    "events": "/admin/events",
    "complaints": "/admin/complaints",
    "maintenance": "/admin/maintenance",
    "inventory": "/admin/inventory",
    "assets": "/admin/assets",
    "reports": "/admin/reports",
    "finance_reports": "/admin/reports/finance",
    "approvals": "/admin/approvals",
    "audit": "/admin/audit",
    "jarvis": "/admin/jarvis"
}


@router.get("/admin/jarvis", response_class=HTMLResponse)
async def admin_jarvis_page(request: Request, user: dict = Depends(admin_only)):
    """Admin Jarvis AI Assistant page."""
    return templates.TemplateResponse(request=request, name="admin/jarvis.html")


@router.post("/admin/api/jarvis/chat")
async def api_admin_jarvis_chat(request: Request, user: dict = Depends(admin_only)):
    """Admin Jarvis chat API — direct Groq API call with pre-loaded admin context.

    Read-only: the AI can answer questions and navigate pages but cannot
    approve, reject, publish, or execute any mutating operations.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid request format."}, status_code=400)

    message = body.get("message", "").strip()
    history = body.get("history", [])

    if not message:
        return JSONResponse({"error": "Message cannot be empty."}, status_code=400)
    if len(message) > 500:
        return JSONResponse({"error": "Message too long (max 500 characters)."}, status_code=400)

    # Pre-load admin context from existing institution-wide queries.
    admin_context = {}
    try:
        stats = get_college_stats() or {}
        admin_context.update({
            "total_students": stats.get("total_students", "N/A"),
            "total_teachers": stats.get("total_teachers", "N/A"),
            "total_departments": stats.get("total_departments", "N/A"),
            "total_subjects": stats.get("total_subjects", "N/A"),
        })
    except Exception:
        admin_context["stats_error"] = "Unable to fetch college stats."

    try:
        finance = get_finance_oversight_stats() or {}
        admin_context.update({
            "fee_demand": finance.get("demand", "N/A"),
            "fee_collected": finance.get("collected", "N/A"),
            "fee_outstanding": finance.get("outstanding", "N/A"),
            "collection_rate": finance.get("collection_rate", "N/A"),
            "pending_concessions": finance.get("pending_concessions", "N/A"),
        })
    except Exception:
        admin_context["finance_error"] = "Unable to fetch finance stats."

    try:
        hr = get_hr_oversight_stats() or {}
        admin_context.update({
            "faculty_count": hr.get("faculty", "N/A"),
            "staff_count": hr.get("staff", "N/A"),
            "pending_salary_revisions": hr.get("pending_revisions", "N/A"),
        })
    except Exception:
        admin_context["hr_error"] = "Unable to fetch HR stats."

    try:
        approvals = PrincipalApprovalService.get_all_pending_approvals() or {}
        admin_context.update({
            "pending_result_approvals": len(approvals.get("results", [])),
            "pending_concession_approvals": len(approvals.get("concessions", [])),
            "pending_notice_approvals": len(approvals.get("notices", [])),
        })
    except Exception:
        admin_context["approvals_error"] = "Unable to fetch pending approvals."

    try:
        complaints = get_sensitive_complaints_oversight() or {}
        status_counts = complaints.get("status_counts", {})
        admin_context.update({
            "sensitive_complaints_pending": status_counts.get("pending", 0),
            "sensitive_complaints_escalated": status_counts.get("escalated", 0),
        })
    except Exception:
        admin_context["complaints_error"] = "Unable to fetch complaint stats."

    admin_context["full_name"] = user.get("full_name", "Administrator")

    ai_response = admin_jarvis_chat(message, history, admin_context)
    if ai_response is None:
        return JSONResponse(
            {"error": "AI service temporarily unavailable. Please try again later."},
            status_code=503
        )

    # Validate navigation against the allowlist
    if ai_response.get("type") == "navigate":
        dest_id = ai_response.get("destination_id")
        if dest_id in ADMIN_NAVIGATION_REGISTRY:
            return JSONResponse({
                "type": "navigate",
                "message": ai_response.get("message", "Navigating..."),
                "url": ADMIN_NAVIGATION_REGISTRY[dest_id]
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