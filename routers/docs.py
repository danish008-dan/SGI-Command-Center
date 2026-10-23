# routers/docs.py
import os
import uuid
from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import StreamingResponse

from utils.auth import PermissionChecker
from database.docs_queries import (
    get_doc_categories, get_documents, add_document_to_db,
    update_document_status, get_document_file_path, get_docs_dashboard_stats,
    get_compliance_requirements, add_compliance_requirement, update_compliance_status,
    get_meetings, add_meeting_to_db, update_meeting_status, get_meeting_for_pdf,
    get_action_items, add_action_item, update_action_status
)
from database.admin_queries import (
     get_departments_for_dropdown, get_all_system_users
)
from utils.pdf_generator import generate_mom_pdf

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Permission Dependencies
docs_view_perm = PermissionChecker("docs.view")
docs_manage_perm = PermissionChecker("docs.manage")
docs_approve_perm = PermissionChecker("docs.approve")
compliance_view_perm = PermissionChecker("compliance.view")
compliance_manage_perm = PermissionChecker("compliance.manage")
meetings_view_perm = PermissionChecker("meetings.view")
meetings_manage_perm = PermissionChecker("meetings.manage")

# Private Storage Directory
PRIVATE_DOC_DIR = "private_uploads/docs"
os.makedirs(PRIVATE_DOC_DIR, exist_ok=True)


@router.get("/admin/docs", response_class=HTMLResponse)
async def docs_dashboard(request: Request, user: dict = Depends(docs_view_perm)):
    stats = get_docs_dashboard_stats()
    return templates.TemplateResponse(
        request=request,
        name="docs/dashboard.html",
        context={"stats": stats}
    )


@router.get("/admin/docs/repository", response_class=HTMLResponse)
async def docs_repository_page(
        request: Request,
        user: dict = Depends(docs_view_perm),
        search: str = None,
        category_id: int = None,
        status: str = None
):
    documents = get_documents(search, category_id, status)
    categories = get_doc_categories()
    departments = get_departments_for_dropdown()
    filters = {"search": search, "category_id": category_id, "status": status}

    return templates.TemplateResponse(
        request=request,
        name="docs/repository.html",
        context={"documents": documents, "categories": categories, "departments": departments, "filters": filters}
    )


@router.post("/admin/api/docs/upload")
async def api_upload_doc(
        request: Request,
        file: UploadFile = File(...),
        user: dict = Depends(docs_manage_perm)
):
    form = await request.form()
    form_data = {
        "title": form.get("title"),
        "category_id": form.get("category_id"),
        "department_id": form.get("department_id") or None,
        "reference_number": form.get("reference_number"),
        "expiry_date": form.get("expiry_date") or None,
        "change_summary": form.get("change_summary")
    }

    # Validate file type
    allowed_types = ["application/pdf", "application/msword",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "image/jpeg",
                     "image/png"]
    if file.content_type not in allowed_types:
        return JSONResponse({"success": False, "message": "Invalid file type. Only PDF, DOC, DOCX, JPG, PNG allowed."},
                            status_code=400)

    # Generate safe filename and save to private dir
    ext = file.filename.split(".")[-1]
    safe_filename = f"doc_{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(PRIVATE_DOC_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    success, msg = add_document_to_db(form_data, file_path, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/docs/status")
async def api_update_doc_status(request: Request, user: dict = Depends(docs_approve_perm)):
    form = await request.form()
    doc_id = int(form.get("document_id"))
    new_status = form.get("status")  # 'Pending Review', 'Approved', 'Published', 'Rejected'

    success, msg = update_document_status(doc_id, new_status, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/docs/download/{doc_id}")
async def download_doc(doc_id: int, user: dict = Depends(docs_view_perm)):
    file_path = get_document_file_path(doc_id)
    if not file_path or not os.path.exists(file_path):
        return HTMLResponse("File not found.", status_code=404)

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=f"SGI_Document_{doc_id}.pdf"  # Force download with safe name
    )

@router.get("/admin/docs/compliance", response_class=HTMLResponse)
async def compliance_page(request: Request, user: dict = Depends(compliance_view_perm)):
    requirements = get_compliance_requirements()
    departments = get_departments_for_dropdown()
    return templates.TemplateResponse(
        request=request,
        name="docs/compliance.html",
        context={"requirements": requirements, "departments": departments}
    )


@router.post("/admin/api/docs/compliance/add")
async def api_add_compliance(request: Request, user: dict = Depends(compliance_manage_perm)):
    form = await request.form()
    form_data = {
        "body_name": form.get("body_name"),
        "description": form.get("description"),
        "academic_year": form.get("academic_year"),
        "due_date": form.get("due_date"),
        "responsible_dept": form.get("responsible_dept") or None
    }
    success, msg = add_compliance_requirement(form_data)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/docs/compliance/status")
async def api_compliance_status(request: Request, user: dict = Depends(compliance_manage_perm)):
    form = await request.form()
    req_id = int(form.get("requirement_id"))
    status = form.get("status")
    success, msg = update_compliance_status(req_id, status)
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/docs/meetings", response_class=HTMLResponse)
async def meetings_page(request: Request, user: dict = Depends(meetings_view_perm)):
    meetings = get_meetings()
    users = get_all_system_users()
    departments = get_departments_for_dropdown()
    return templates.TemplateResponse(
        request=request,
        name="docs/meetings.html",
        context={"meetings": meetings, "users": users, "departments": departments}
    )


@router.post("/admin/api/docs/meetings/add")
async def api_add_meeting(request: Request, user: dict = Depends(meetings_manage_perm)):
    form = await request.form()
    form_data = {
        "title": form.get("title"),
        "meeting_type": form.get("meeting_type"),
        "department_id": form.get("department_id") or None,
        "meeting_date": form.get("meeting_date"),
        "venue": form.get("venue"),
        "chairperson_id": form.get("chairperson_id"),
        "agenda": form.get("agenda")
    }
    success, msg = add_meeting_to_db(form_data, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/docs/meetings/minutes")
async def api_record_minutes(request: Request, user: dict = Depends(meetings_manage_perm)):
    form = await request.form()
    meeting_id = int(form.get("meeting_id"))
    minutes = form.get("minutes")
    success, msg = update_meeting_status(meeting_id, 'Minutes Draft', minutes)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/docs/meetings/approve")
async def api_approve_meeting(request: Request, user: dict = Depends(meetings_manage_perm)):
    form = await request.form()
    meeting_id = int(form.get("meeting_id"))
    success, msg = update_meeting_status(meeting_id, 'Approved')
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/docs/meetings/{meeting_id}/mom/pdf")
async def download_mom_pdf(meeting_id: int, user: dict = Depends(meetings_view_perm)):
    meeting_data = get_meeting_for_pdf(meeting_id)
    if not meeting_data or meeting_data["status"] != 'Approved':
        return HTMLResponse("MoM not available. Minutes must be approved.", status_code=400)

    buffer = generate_mom_pdf(meeting_data)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=MoM_{meeting_data['title']}.pdf"}
    )


@router.get("/admin/docs/action-items", response_class=HTMLResponse)
async def action_items_page(request: Request, user: dict = Depends(meetings_view_perm)):
    items = get_action_items()
    meetings = get_meetings()
    users = get_all_system_users()
    return templates.TemplateResponse(
        request=request,
        name="docs/action_items.html",
        context={"items": items, "meetings": meetings, "users": users}
    )


@router.post("/admin/api/docs/action-items/add")
async def api_add_action_item(request: Request, user: dict = Depends(meetings_manage_perm)):
    form = await request.form()
    form_data = {
        "meeting_id": form.get("meeting_id"),
        "description": form.get("description"),
        "assigned_to": form.get("assigned_to"),
        "due_date": form.get("due_date")
    }
    success, msg = add_action_item(form_data)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/docs/action-items/status")
async def api_action_item_status(request: Request, user: dict = Depends(meetings_manage_perm)):
    form = await request.form()
    action_id = int(form.get("action_id"))
    status = form.get("status")
    notes = form.get("notes")
    success, msg = update_action_status(action_id, status, notes)
    return JSONResponse({"success": success, "message": msg})