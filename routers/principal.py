# routers/principal.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from services.principal_service import PrincipalApprovalService
from utils.auth import get_current_user, RoleChecker
from database.connection import get_connection
from ai.graph import app_graph
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from database.fee_queries import (
    get_pending_concessions, process_concession
)

from database.principal_queries import (
    get_finance_oversight_stats, get_principal_audit_trail,
    get_hr_oversight_stats, get_campus_oversight_stats,
    get_college_stats, get_department_wise_analysis,
    get_academic_oversight_stats, get_department_wise_academics,
    get_pending_results_for_principal, approve_results_by_principal,
    reject_results_by_principal, get_compliance_oversight_stats, get_meetings_oversight_stats,
    get_notices_events_oversight_stats, get_sensitive_complaints_oversight, get_executive_report_data,
    get_principal_notifications,
    # Principal Panel Enhancement — Issue 3: Admin-created notices/events lists
    get_all_admin_notices, get_all_admin_events,
)
from database.admin_queries import (
    get_notices_for_approval, process_notice_approval,
    get_sensitive_complaints
)



router = APIRouter()
templates = Jinja2Templates(directory="templates")
# Security gate: Only Principal can access these routes
principal_only = RoleChecker(["Principal"])


@router.get("/principal/dashboard", response_class=HTMLResponse)
async def principal_dashboard(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(
        request=request,
        name="principal/dashboard.html"
    )



@router.get("/principal/api/me")
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


@router.get("/principal/api/dashboard")
async def api_get_dashboard(user: dict = Depends(principal_only)):
    stats = get_college_stats()
    departments = get_department_wise_analysis()

    # Calculate total pending actions for Today's Priorities
    total_pending = (stats.get("pending_results", 0) +
                     stats.get("pending_concessions", 0) +
                     stats.get("pending_notices", 0))

    return {
        "stats": stats,
        "departments": departments,
        "total_pending_actions": total_pending
    }

@router.get("/principal/ai-assistant", response_class=HTMLResponse)
async def ai_assistant_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(
        request=request,
        name="principal/ai_assistant.html"
    )

@router.post("/principal/api/ai/ask")
async def api_ask_assistant(request: Request, user: dict = Depends(principal_only)):
    form = await request.form()
    question = form.get("question")

    thread_id = f"principal_{user['user_id']}"
    config = {"configurable": {"thread_id": thread_id, "user_id": user['user_id']}}

    try:
        # Check if graph is currently paused (waiting for HITL confirmation)
        state = await app_graph.aget_state(config)

        if state and state.next:
            # Graph is paused, user's input is a confirmation
            is_confirmed = question.lower().strip() in ["yes", "y", "confirm", "haan", "okay"]
            resume_val = {"confirmed": is_confirmed}

            # Resume the graph
            output = await app_graph.ainvoke(Command(resume=resume_val), config=config)
        else:
            # Normal message, start/continue standard flow
            input_messages = [HumanMessage(content=question)]
            output = await app_graph.ainvoke({"messages": input_messages}, config=config)

        last_msg = output["messages"][-1]

        # Check if graph is NOW waiting for HITL confirmation
        # (We do this by checking the state again after execution)
        current_state = await app_graph.aget_state(config)
        is_paused = current_state and current_state.next and any(
            "interrupt" in str(task) for task in current_state.tasks
        )

        if is_paused:
            # Extract the message from the interrupt object
            interrupt_data = current_state.tasks[0].interrupts[0].value
            return JSONResponse({
                "success": True,
                "answer": interrupt_data.get("message", "Action requires confirmation. Reply 'Yes' to confirm."),
                "requires_confirmation": True
            })

        return JSONResponse({"success": True, "answer": last_msg.content})

    except Exception as e:
        print("AI Graph Error:", e)
        return JSONResponse({"success": False, "answer": "I encountered an error processing that request."})

@router.get("/principal/results", response_class=HTMLResponse)
async def principal_results_page(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Principal":
        return HTMLResponse("Unauthorized", status_code=403)

    # Fetch all pending results across all semesters
    pending = get_pending_results_for_principal()

    # Group by semester
    semesters = {}
    for r in pending:
        if r["semester"] not in semesters:
            semesters[r["semester"]] = []
        semesters[r["semester"]].append(r)

    return templates.TemplateResponse(
        request=request,
        name="principal/results_approval.html",
        context={"semesters": semesters}
    )


@router.post("/principal/api/results/approve")
async def api_approve_results(semester: int = Form(...), user: dict = Depends(get_current_user)):
    if user["role"] != "Principal":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)
    success, msg = approve_results_by_principal(semester, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.post("/principal/api/results/reject")
async def api_reject_results(semester: int = Form(...), reason: str = Form(...),
                             user: dict = Depends(get_current_user)):
    if user["role"] != "Principal":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)
    success, msg = reject_results_by_principal(semester, reason, user["user_id"])
    return JSONResponse({"success": success, "message": msg})


@router.get("/principal/concessions", response_class=HTMLResponse)
async def principal_concessions_page(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Principal":
        return HTMLResponse("Unauthorized", status_code=403)

    pending = get_pending_concessions()
    return templates.TemplateResponse(
        request=request,
        name="principal/concessions.html",
        context={"pending": pending}
    )


@router.post("/principal/api/concessions/process")
async def api_process_concession(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Principal":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    request_id = int(form.get("request_id"))
    action = form.get("action")  # 'Approved' or 'Rejected'

    success, msg = process_concession(request_id, action, user["user_id"])
    return JSONResponse({"success": success, "message": msg})

@router.get("/principal/notice-approvals", response_class=HTMLResponse)
async def principal_notice_approvals_page(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Principal":
        return HTMLResponse("Unauthorized", status_code=403)

    pending = get_notices_for_approval("Principal")
    return templates.TemplateResponse(
        request=request,
        name="principal/notice_approvals.html",
        context={"pending": pending}
    )


@router.post("/principal/api/notices/process")
async def api_process_notice(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Principal":
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=403)

    form = await request.form()
    notice_id = int(form.get("notice_id"))
    action = form.get("action")  # 'Approved' or 'Rejected'
    remarks = form.get("remarks")

    success, msg = process_notice_approval(notice_id, action, user["user_id"], remarks)
    return JSONResponse({"success": success, "message": msg})


@router.get("/principal/sensitive-complaints", response_class=HTMLResponse)
async def principal_sensitive_complaints_page(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "Principal":
        return HTMLResponse("Unauthorized", status_code=403)

    complaints = get_sensitive_complaints()
    return templates.TemplateResponse(
        request=request,
        name="principal/sensitive_complaints.html",
        context={"complaints": complaints}
    )


# ==========================================
# UNIFIED APPROVAL CENTER
# ==========================================

@router.get("/principal/approvals", response_class=HTMLResponse)
async def approval_center_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(
        request=request,
        name="principal/approvals.html"
    )

@router.get("/principal/api/approvals")
async def api_get_approvals(user: dict = Depends(principal_only)):
    data = PrincipalApprovalService.get_all_pending_approvals()
    return JSONResponse(data)

@router.post("/principal/api/approvals/process")
async def api_process_approval(request: Request, user: dict = Depends(principal_only)):
    form = await request.form()
    approval_type = form.get("type")
    action = form.get("action")
    target_id = form.get("target_id")
    reason = form.get("reason")

    if not target_id or not action:
        return JSONResponse({"success": False, "message": "Missing parameters."}, status_code=400)

    try:
        if approval_type == "result":
            # target_id for results is semester
            success, msg = PrincipalApprovalService.process_result_approval(int(target_id), action, user["user_id"], reason)
        elif approval_type == "concession":
            success, msg = PrincipalApprovalService.process_concession_approval(int(target_id), action, user["user_id"], reason)
        elif approval_type == "notice":
            success, msg = PrincipalApprovalService.process_notice_approval(int(target_id), action, user["user_id"], reason)
        else:
            return JSONResponse({"success": False, "message": "Invalid approval type."}, status_code=400)

        return JSONResponse({"success": success, "message": msg})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)



@router.get("/principal/academic", response_class=HTMLResponse)
async def academic_oversight_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(
        request=request,
        name="principal/academic_oversight.html"
    )

@router.get("/principal/api/academic")
async def api_get_academic_data(user: dict = Depends(principal_only)):
    stats = get_academic_oversight_stats()
    departments = get_department_wise_academics()
    return {"stats": stats, "departments": departments}

@router.get("/principal/finance", response_class=HTMLResponse)
async def finance_oversight_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/finance_oversight.html")

@router.get("/principal/api/finance")
async def api_get_finance_data(user: dict = Depends(principal_only)):
    return get_finance_oversight_stats()


@router.get("/principal/hr", response_class=HTMLResponse)
async def hr_oversight_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/hr_oversight.html")

@router.get("/principal/api/hr")
async def api_get_hr_data(user: dict = Depends(principal_only)):
    return get_hr_oversight_stats()

@router.get("/principal/campus", response_class=HTMLResponse)
async def campus_oversight_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/campus_oversight.html")

@router.get("/principal/api/campus")
async def api_get_campus_data(user: dict = Depends(principal_only)):
    return get_campus_oversight_stats()

@router.get("/principal/compliance", response_class=HTMLResponse)
async def compliance_oversight_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/compliance_oversight.html")

@router.get("/principal/api/compliance")
async def api_get_compliance_data(user: dict = Depends(principal_only)):
    return get_compliance_oversight_stats()


@router.get("/principal/meetings", response_class=HTMLResponse)
async def meetings_oversight_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/meetings_oversight.html")

@router.get("/principal/api/meetings")
async def api_get_meetings_data(user: dict = Depends(principal_only)):
    return get_meetings_oversight_stats()


@router.get("/principal/notices", response_class=HTMLResponse)
async def notices_oversight_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/notices_oversight.html")

@router.get("/principal/api/notices")
async def api_get_notices_data(user: dict = Depends(principal_only)):
    # Principal Panel Enhancement (Issue 3): extend the existing 3 numeric
    # counts with two new arrays — admin_notices and admin_events — so the
    # Principal can see the actual list of Admin-created notices/events
    # (similar to the Student Panel notice board, but with institution-wide
    # oversight visibility). The existing 3 counts are preserved unchanged.
    stats = get_notices_events_oversight_stats()
    stats["admin_notices"] = get_all_admin_notices(limit=20)
    stats["admin_events"] = get_all_admin_events(limit=20)
    return stats


@router.get("/principal/complaints", response_class=HTMLResponse)
async def complaints_oversight_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/complaints_oversight.html")

@router.get("/principal/api/complaints")
async def api_get_complaints_data(user: dict = Depends(principal_only)):
    return get_sensitive_complaints_oversight()

@router.get("/principal/reports", response_class=HTMLResponse)
async def reports_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/reports.html")

@router.get("/principal/api/reports")
async def api_get_reports(user: dict = Depends(principal_only)):
    return get_executive_report_data()


@router.get("/principal/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/notifications.html")

@router.get("/principal/api/notifications")
async def api_get_notifications(user: dict = Depends(principal_only)):
    return {"notifications": get_principal_notifications()}


@router.get("/principal/audit", response_class=HTMLResponse)
async def audit_page(request: Request, user: dict = Depends(principal_only)):
    return templates.TemplateResponse(request=request, name="principal/audit.html")

@router.get("/principal/api/audit")
async def api_get_audit(user: dict = Depends(principal_only)):
    trail = get_principal_audit_trail(user["user_id"])
    return {"audit_trail": trail}


async def principal_future_module(request: Request, user: dict = Depends(principal_only)):
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Module Under Construction</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    </head>
    <body class="bg-light d-flex align-items-center justify-content-center vh-100">
        <div class="text-center">
            <i class="bi bi-tools text-primary" style="font-size: 4rem;"></i>
            <h2 class="mt-4 text-dark">Module Under Construction</h2>
            <p class="text-muted">This module will be implemented in the upcoming phases of the Principal Command Center.</p>
            <a href="/principal/dashboard" class="btn btn-primary mt-3">Back to Dashboard</a>
        </div>
    </body>
    </html>
    """)