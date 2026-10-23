# routers/asset.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from database.connection import get_connection
from utils.auth import PermissionChecker
from database.admin_queries import get_departments_for_dropdown
from database.asset_queries import (
    get_asset_categories, add_asset_category,
    get_all_assets, add_asset_to_db,
    allocate_asset, get_all_maintenance_requests,
    update_maintenance_status, get_disposal_requests,
    process_disposal_request, get_asset_allocation_history,
    get_maintenance_requests_for_asset, get_asset_for_details
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Permission Dependencies
assets_view_perm = PermissionChecker("assets.view")
assets_create_perm = PermissionChecker("assets.create")
# Define Permission Dependencies
assets_allocate_perm = PermissionChecker("assets.allocate")
assets_maintenance_perm = PermissionChecker("assets.manage_maintenance")
assets_disposal_perm = PermissionChecker("assets.approve_disposal")


@router.get("/admin/assets", response_class=HTMLResponse)
async def asset_dashboard(request: Request, user: dict = Depends(assets_view_perm)):
    assets = get_all_assets()
    categories = get_asset_categories()
    departments = get_departments_for_dropdown()

    # KPIs
    total_assets = len(assets)
    active_assets = len([a for a in assets if a["lifecycle_status"] == 'Active'])

    return templates.TemplateResponse(
        request=request,
        name="admin/assets.html",
        context={
            "assets": assets,
            "categories": categories,
            "departments": departments,
            "total_assets": total_assets,
            "active_assets": active_assets
        }
    )


@router.post("/admin/api/assets/add")
async def api_add_asset(request: Request, user: dict = Depends(assets_create_perm)):
    form = await request.form()
    form_data = {
        "category_id": int(form.get("category_id")),
        "name": form.get("name"),
        "description": form.get("description"),
        "serial_number": form.get("serial_number"),
        "acquisition_date": form.get("acquisition_date") or None,
        "acquisition_cost": form.get("acquisition_cost") or 0,
        "supplier": form.get("supplier"),
        "condition_status": form.get("condition_status", 'Good'),
        "room_id": form.get("room_id") or None,
        "department_id": form.get("department_id") or None,
        "custodian_id": form.get("custodian_id") or None
    }
    success, msg = add_asset_to_db(form_data, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/assets/categories/add")
async def api_add_asset_category(request: Request, user: dict = Depends(assets_create_perm)):
    form = await request.form()
    success, msg = add_asset_category(form.get("category_name"), form.get("prefix"))
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/assets/allocate")
async def api_allocate_asset(request: Request, user: dict = Depends(assets_allocate_perm)):
    form = await request.form()
    asset_id = int(form.get("asset_id"))
    user_id = form.get("user_id") or None
    dept_id = form.get("department_id") or None
    room_id = form.get("room_id") or None

    success, msg = allocate_asset(asset_id, user_id, dept_id, room_id, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/maintenance", response_class=HTMLResponse)
async def maintenance_page(request: Request, user: dict = Depends(assets_maintenance_perm)):
    requests = get_all_maintenance_requests()
    return templates.TemplateResponse(
        request=request,
        name="admin/maintenance.html",
        context={"requests": requests}
    )


@router.post("/admin/api/maintenance/update")
async def api_update_maintenance(request: Request, user: dict = Depends(assets_maintenance_perm)):
    form = await request.form()
    req_id = int(form.get("request_id"))
    status = form.get("status")
    notes = form.get("resolution_notes")

    success, msg = update_maintenance_status(req_id, status, notes, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/asset-disposals", response_class=HTMLResponse)
async def disposals_page(request: Request, user: dict = Depends(assets_disposal_perm)):
    requests = get_disposal_requests()
    return templates.TemplateResponse(
        request=request,
        name="admin/disposals.html",
        context={"requests": requests}
    )


@router.post("/admin/api/disposals/process")
async def api_process_disposal(request: Request, user: dict = Depends(assets_disposal_perm)):
    form = await request.form()
    disposal_id = int(form.get("disposal_id"))
    action = form.get("action")  # 'Approved' or 'Rejected'

    success, msg = process_disposal_request(disposal_id, action, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/assets/{asset_id}", response_class=HTMLResponse)
async def asset_details_page(request: Request, asset_id: int, user: dict = Depends(assets_view_perm)):
    asset = get_asset_for_details(asset_id)
    if not asset:
        return HTMLResponse("Asset not found", status_code=404)

    allocations = get_asset_allocation_history(asset_id)
    maintenance_reqs = get_maintenance_requests_for_asset(asset_id)

    return templates.TemplateResponse(
        request=request,
        name="admin/asset_details.html",
        context={
            "asset": asset,
            "allocations": allocations,
            "maintenance_reqs": maintenance_reqs
        }
    )

