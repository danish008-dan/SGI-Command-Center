# routers/campus.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from utils.auth import PermissionChecker
from database.campus_queries import (
    get_campus_dashboard_stats, get_hostel_rooms, add_hostel_room,
    get_hostel_applications, allocate_bed_to_student, get_available_beds,
    get_transport_stats, get_transport_vehicles, get_available_assets_for_transport, add_transport_vehicle,
    get_routes, add_route, get_transport_allocations, allocate_transport_to_student,
    get_library_stats, get_library_books, add_library_book, add_library_copy,
    get_active_loans, issue_book, return_book, get_visitor_stats, get_visitors, register_visitor, approve_visitor,
    check_in_visitor, check_out_visitor, get_visitor_for_pass
)

from database.admin_queries import get_all_system_users
from database.admin_queries import get_all_students
from fastapi.responses import StreamingResponse
from utils.pdf_generator import generate_visitor_pass_pdf


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Permission Dependencies
hostel_view_perm = PermissionChecker("hostel.view")
library_view_perm = PermissionChecker("library.view")
hostel_manage_perm = PermissionChecker("hostel.manage")
visitors_view_perm = PermissionChecker("visitors.view")
transport_view_perm = PermissionChecker("transport.view")
hostel_approve_perm = PermissionChecker("hostel.approve")
library_manage_perm = PermissionChecker("library.manage")
visitors_manage_perm = PermissionChecker("visitors.manage")
transport_manage_perm = PermissionChecker("transport.manage")
visitors_check_in_perm = PermissionChecker("visitors.check_in")
library_circulation_perm = PermissionChecker("library.circulation")


@router.get("/admin/campus", response_class=HTMLResponse)
async def campus_dashboard(request: Request, user: dict = Depends(hostel_view_perm)):
    stats = get_campus_dashboard_stats()
    return templates.TemplateResponse(
        request=request,
        name="campus/dashboard.html",
        context={"stats": stats}
    )


@router.get("/admin/campus/hostel/rooms", response_class=HTMLResponse)
async def hostel_rooms_page(request: Request, user: dict = Depends(hostel_view_perm)):
    rooms = get_hostel_rooms()
    return templates.TemplateResponse(
        request=request,
        name="campus/hostel_rooms.html",
        context={"rooms": rooms}
    )


@router.post("/admin/api/campus/hostel/rooms/add")
async def api_add_hostel_room(request: Request, user: dict = Depends(hostel_manage_perm)):
    form = await request.form()
    form_data = {
        "hostel_name": form.get("hostel_name"),
        "floor": form.get("floor"),
        "room_number": form.get("room_number"),
        "capacity": form.get("capacity"),
        "room_type": form.get("room_type")
    }
    success, msg = add_hostel_room(form_data)
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/campus/hostel/applications", response_class=HTMLResponse)
async def hostel_applications_page(request: Request, user: dict = Depends(hostel_view_perm)):
    applications = get_hostel_applications()
    beds = get_available_beds()
    return templates.TemplateResponse(
        request=request,
        name="campus/hostel_applications.html",
        context={"applications": applications, "beds": beds}
    )


@router.post("/admin/api/campus/hostel/allocate")
async def api_allocate_bed(request: Request, user: dict = Depends(hostel_approve_perm)):
    form = await request.form()
    app_id = int(form.get("application_id"))
    bed_id = int(form.get("bed_id"))

    success, msg = allocate_bed_to_student(app_id, bed_id, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/campus/transport", response_class=HTMLResponse)
async def transport_page(request: Request, user: dict = Depends(transport_view_perm)):
    stats = get_transport_stats()
    vehicles = get_transport_vehicles()
    routes = get_routes()
    allocations = get_transport_allocations()
    available_assets = get_available_assets_for_transport()
    students = get_all_students()

    return templates.TemplateResponse(
        request=request,
        name="campus/transport.html",
        context={
            "stats": stats, "vehicles": vehicles, "routes": routes,
            "allocations": allocations, "available_assets": available_assets, "students": students
        }
    )


@router.post("/admin/api/campus/transport/vehicle/add")
async def api_add_transport_vehicle(request: Request, user: dict = Depends(transport_manage_perm)):
    form = await request.form()
    form_data = {
        "asset_id": int(form.get("asset_id")),
        "route_id": form.get("route_id") or None,
        "driver_name": form.get("driver_name"),
        "driver_contact": form.get("driver_contact"),
        "capacity": form.get("capacity", 30)
    }
    success, msg = add_transport_vehicle(form_data)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/campus/transport/route/add")
async def api_add_transport_route(request: Request, user: dict = Depends(transport_manage_perm)):
    form = await request.form()
    success, msg = add_route(form.get("route_name"), form.get("start_point"), form.get("end_point"))
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/campus/transport/allocate")
async def api_allocate_transport(request: Request, user: dict = Depends(transport_manage_perm)):
    form = await request.form()
    student_id = int(form.get("student_id"))
    route_id = int(form.get("route_id"))
    stop_id = form.get("stop_id") or None

    success, msg = allocate_transport_to_student(student_id, route_id, stop_id, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/campus/library", response_class=HTMLResponse)
async def library_page(request: Request, user: dict = Depends(library_view_perm)):
    stats = get_library_stats()
    books = get_library_books()
    loans = get_active_loans()
    members = get_all_system_users()  # Students + Staff

    return templates.TemplateResponse(
        request=request,
        name="campus/library.html",
        context={"stats": stats, "books": books, "loans": loans, "members": members}
    )


@router.post("/admin/api/campus/library/book/add")
async def api_add_book(request: Request, user: dict = Depends(library_manage_perm)):
    form = await request.form()
    form_data = {
        "title": form.get("title"),
        "author": form.get("author"),
        "isbn": form.get("isbn"),
        "publisher": form.get("publisher"),
        "category": form.get("category")
    }
    success, msg = add_library_book(form_data)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/campus/library/copy/add")
async def api_add_copy(request: Request, user: dict = Depends(library_manage_perm)):
    form = await request.form()
    success, msg = add_library_copy(int(form.get("book_id")), form.get("accession_number"))
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/campus/library/issue")
async def api_issue_book(request: Request, user: dict = Depends(library_circulation_perm)):
    form = await request.form()
    copy_id = int(form.get("copy_id"))
    user_id = int(form.get("user_id"))

    success, msg = issue_book(copy_id, user_id, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/campus/library/return")
async def api_return_book(request: Request, user: dict = Depends(library_circulation_perm)):
    form = await request.form()
    loan_id = int(form.get("loan_id"))

    success, msg = return_book(loan_id)
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/campus/visitors", response_class=HTMLResponse)
async def visitors_page(request: Request, user: dict = Depends(visitors_view_perm)):
    stats = get_visitor_stats()
    visitors = get_visitors()
    hosts = get_all_system_users()  # Fetch all staff/faculty for host selection

    return templates.TemplateResponse(
        request=request,
        name="campus/visitors.html",
        context={"stats": stats, "visitors": visitors, "hosts": hosts}
    )


@router.post("/admin/api/campus/visitors/register")
async def api_register_visitor(request: Request, user: dict = Depends(visitors_manage_perm)):
    form = await request.form()
    form_data = {
        "full_name": form.get("full_name"),
        "mobile": form.get("mobile"),
        "host_user_id": form.get("host_user_id"),
        "purpose": form.get("purpose"),
        "visit_date": form.get("visit_date")
    }
    success, msg = register_visitor(form_data, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/campus/visitors/approve")
async def api_approve_visitor(request: Request, user: dict = Depends(visitors_manage_perm)):
    form = await request.form()
    visitor_id = int(form.get("visitor_id"))
    success, msg = approve_visitor(visitor_id, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/campus/visitors/checkin")
async def api_check_in(request: Request, user: dict = Depends(visitors_check_in_perm)):
    form = await request.form()
    visitor_id = int(form.get("visitor_id"))
    success, msg = check_in_visitor(visitor_id)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/campus/visitors/checkout")
async def api_check_out(request: Request, user: dict = Depends(visitors_check_in_perm)):
    form = await request.form()
    visitor_id = int(form.get("visitor_id"))
    success, msg = check_out_visitor(visitor_id)
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/campus/visitors/{visitor_id}/pass/pdf")
async def download_visitor_pass(visitor_id: int, user: dict = Depends(visitors_view_perm)):
    visitor_data = get_visitor_for_pass(visitor_id)
    if not visitor_data:
        return HTMLResponse("Visitor not found", status_code=404)

    buffer = generate_visitor_pass_pdf(visitor_data)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=VisitorPass_{visitor_data['qr_reference']}.pdf"}
    )