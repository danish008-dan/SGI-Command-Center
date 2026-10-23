# routers/hr.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from database.connection import get_connection
from utils.auth import PermissionChecker
from database.admin_queries import get_departments_for_dropdown

from database.hr_queries import (
    get_hr_dashboard_stats, get_all_employees, add_employee_to_db,
    get_salary_components, assign_salary_component, get_payroll_periods,
    create_salary_revision, get_pending_salary_revisions, process_salary_revision,
    create_payroll_period, generate_payroll_for_period, get_payroll_runs,
    update_payroll_run_status, get_payslip_data, get_exit_requests,
    create_exit_request, process_exit_request
)

from fastapi.responses import StreamingResponse
from utils.pdf_generator import generate_payslip_pdf, generate_relieving_letter_pdf


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Permission Dependencies
hr_view_perm = PermissionChecker("hr.view")
hr_manage_perm = PermissionChecker("hr.manage")
hr_exit_perm = PermissionChecker("hr.exit.manage")
payroll_view_perm = PermissionChecker("payroll.view")
payroll_manage_perm = PermissionChecker("payroll.manage")
payroll_approve_perm = PermissionChecker("payroll.approve")



@router.get("/admin/hr", response_class=HTMLResponse)
async def hr_dashboard(request: Request, user: dict = Depends(hr_view_perm)):
    stats = get_hr_dashboard_stats()
    return templates.TemplateResponse(
        request=request,
        name="hr/dashboard.html",
        context={"stats": stats}
    )


@router.get("/admin/hr/employees", response_class=HTMLResponse)
async def employee_directory(request: Request, user: dict = Depends(hr_view_perm), search: str = None,
                             department_id: int = None):
    employees = get_all_employees(search, department_id)
    departments = get_departments_for_dropdown()
    filters = {"search": search, "department_id": department_id}

    return templates.TemplateResponse(
        request=request,
        name="hr/employees.html",
        context={"employees": employees, "departments": departments, "filters": filters}
    )


@router.post("/admin/api/hr/employees/add")
async def api_add_employee(request: Request, user: dict = Depends(hr_manage_perm)):
    form = await request.form()
    form_data = {
        "name": form.get("name"),
        "email": form.get("email"),
        "mobile": form.get("mobile"),
        "password": form.get("password"),
        "department_id": form.get("department_id") or None,
        "designation": form.get("designation"),
        "employment_type": form.get("employment_type"),
        "joining_date": form.get("joining_date"),
        "bank_account": form.get("bank_account"),
        "bank_ifsc": form.get("bank_ifsc")
    }
    success, msg = add_employee_to_db(form_data, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/hr/salary-components", response_class=HTMLResponse)
async def salary_components_page(request: Request, user: dict = Depends(hr_view_perm)):
    components = get_salary_components()
    return templates.TemplateResponse(
        request=request,
        name="hr/salary_components.html",
        context={"components": components}
    )


@router.post("/admin/api/hr/salary/assign")
async def api_assign_salary(request: Request, user: dict = Depends(hr_manage_perm)):
    form = await request.form()
    emp_id = int(form.get("employee_id"))
    comp_id = int(form.get("component_id"))
    amount = float(form.get("amount"))
    eff_date = form.get("effective_date")

    success, msg = assign_salary_component(emp_id, comp_id, amount, eff_date)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/hr/salary/revision-request")
async def api_revision_request(request: Request, user: dict = Depends(hr_manage_perm)):
    form = await request.form()
    emp_id = int(form.get("employee_id"))
    comp_id = int(form.get("component_id"))
    new_amount = float(form.get("new_amount"))
    eff_date = form.get("effective_date")
    reason = form.get("reason")

    success, msg = create_salary_revision(emp_id, comp_id, new_amount, eff_date, reason, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/hr/salary-revisions", response_class=HTMLResponse)
async def salary_revisions_page(request: Request, user: dict = Depends(hr_view_perm)):
    # Only Principal/Admin should approve, but anyone with hr.view can see the list
    revisions = get_pending_salary_revisions()
    return templates.TemplateResponse(
        request=request,
        name="hr/salary_revisions.html",
        context={"revisions": revisions}
    )


@router.post("/admin/api/hr/salary/revisions/process")
async def api_process_revision(request: Request, user: dict = Depends(hr_manage_perm)):
    form = await request.form()
    rev_id = int(form.get("revision_id"))
    action = form.get("action")  # 'Approved' or 'Rejected'

    success, msg = process_salary_revision(rev_id, action, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/hr/payroll", response_class=HTMLResponse)
async def payroll_page(request: Request, user: dict = Depends(payroll_view_perm)):
    periods = get_payroll_periods()
    return templates.TemplateResponse(
        request=request,
        name="hr/payroll.html",
        context={"periods": periods}
    )


@router.post("/admin/api/hr/payroll/period/add")
async def api_add_period(request: Request, user: dict = Depends(payroll_manage_perm)):
    form = await request.form()
    month = int(form.get("month"))
    year = int(form.get("year"))
    success, msg = create_payroll_period(month, year)
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/hr/payroll/generate")
async def api_generate_payroll(request: Request, user: dict = Depends(payroll_manage_perm)):
    form = await request.form()
    period_id = int(form.get("period_id"))
    success, msg = generate_payroll_for_period(period_id, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/hr/payroll/{period_id}", response_class=HTMLResponse)
async def payroll_details_page(request: Request, period_id: int, user: dict = Depends(payroll_view_perm)):
    runs = get_payroll_runs(period_id)
    periods = get_payroll_periods()
    return templates.TemplateResponse(
        request=request,
        name="hr/payroll.html",
        context={"runs": runs, "periods": periods, "current_period": period_id}
    )


@router.post("/admin/api/hr/payroll/process")
async def api_process_payroll(request: Request, user: dict = Depends(payroll_view_perm)):
    form = await request.form()
    run_id = int(form.get("run_id"))
    action = form.get("action")  # 'Under Review', 'Approved', 'Finalized', 'Paid'

    # Permission check for approval
    if action == 'Approved' and user["role"] not in ["Principal", "Admin"]:
        return JSONResponse({"success": False, "message": "Unauthorized to approve payroll."}, status_code=403)

    success, msg = update_payroll_run_status(run_id, action, user["user_id"], user["role"])
    return JSONResponse({"success": success, "message": msg})



@router.get("/admin/hr/payslip/{run_id}/pdf")
async def download_payslip(run_id: int, user: dict = Depends(payroll_view_perm)):
    payslip_data = get_payslip_data(run_id)
    if not payslip_data:
        return HTMLResponse("Payslip not found", status_code=404)

    buffer = generate_payslip_pdf(payslip_data)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Payslip_{payslip_data['employee_code']}.pdf"}
    )


@router.get("/admin/hr/exits", response_class=HTMLResponse)
async def exits_page(request: Request, user: dict = Depends(hr_exit_perm)):
    requests = get_exit_requests()
    employees = get_all_employees()  # Fetch active employees for dropdown
    return templates.TemplateResponse(
        request=request,
        name="hr/exits.html",
        context={"requests": requests, "employees": employees}
    )


@router.post("/admin/api/hr/exits/add")
async def api_add_exit(request: Request, user: dict = Depends(hr_exit_perm)):
    form = await request.form()
    success, msg = create_exit_request(
        int(form.get("employee_id")),
        form.get("exit_type"),
        form.get("last_working_day"),
        form.get("reason")
    )
    return JSONResponse({"success": success, "message": msg})


@router.post("/admin/api/hr/exits/process")
async def api_process_exit(request: Request, user: dict = Depends(hr_exit_perm)):
    form = await request.form()
    clearance_id = int(form.get("clearance_id"))
    action = form.get("action")
    settlement = form.get("settlement_amount", 0)

    success, msg = process_exit_request(clearance_id, action, settlement)
    return JSONResponse({"success": success, "message": msg})


@router.get("/admin/hr/relieving/{clearance_id}/pdf")
async def download_relieving_letter(clearance_id: int, user: dict = Depends(hr_exit_perm)):
    # Fetch Exit Details
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ec.*, e.employee_code, e.designation, u.full_name 
        FROM exit_clearances ec 
        INNER JOIN employees e ON ec.employee_id = e.employee_id
        INNER JOIN users u ON e.user_id = u.user_id 
        WHERE ec.clearance_id = %s
    """, (clearance_id,))
    exit_data = cursor.fetchone()
    conn.close()

    if not exit_data or exit_data["status"] != 'Cleared':
        return HTMLResponse("Relieving letter not available. Exit not cleared.", status_code=400)

    buffer = generate_relieving_letter_pdf(exit_data, exit_data)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Relieving_{exit_data['employee_code']}.pdf"}
    )
