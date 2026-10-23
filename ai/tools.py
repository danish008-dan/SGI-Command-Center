# ai/tools.py
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
import pymysql
import time

from database.principal_queries import (
    get_academic_oversight_stats, get_finance_oversight_stats,
    get_pending_results_for_principal, get_hr_oversight_stats,
    get_campus_oversight_stats, get_compliance_oversight_stats,
    get_meetings_oversight_stats, get_sensitive_complaints_oversight,
    get_college_stats
)
from database.fee_queries import get_pending_concessions
from services.principal_service import PrincipalApprovalService


# ==========================================
# RETRY HELPER (Phase 24)
# ==========================================
def execute_with_retry(func, *args, max_retries=2, **kwargs):
    delay = 1
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except (pymysql.OperationalError, TimeoutError) as e:
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            return {"status": "ERROR", "message": "Backend service temporarily unavailable."}
        except Exception as e:
            return {"status": "ERROR", "message": "An error occurred while processing the request."}


# ==========================================
# READ TOOLS
# ==========================================
@tool
def fetch_academic_stats():
    """Use this tool to get institution-wide academic health metrics."""
    return execute_with_retry(get_academic_oversight_stats)


@tool
def fetch_finance_stats():
    """Use this tool to get financial health metrics."""
    return execute_with_retry(get_finance_oversight_stats)


@tool
def fetch_pending_approvals():
    """Use this tool to find out what approval requests are currently pending."""
    pending_results = execute_with_retry(get_pending_results_for_principal)
    pending_concessions = execute_with_retry(get_pending_concessions)
    if "ERROR" in str(pending_results) or "ERROR" in str(pending_concessions):
        return {"status": "ERROR", "message": "Could not fetch pending approvals."}
    return {"pending_results_count": len(pending_results), "pending_concessions_count": len(pending_concessions)}


@tool
def fetch_hr_stats():
    """Use this tool to get HR and Payroll metrics."""
    return execute_with_retry(get_hr_oversight_stats)


@tool
def fetch_campus_stats():
    """Use this tool to get Campus Operations metrics."""
    return execute_with_retry(get_campus_oversight_stats)


@tool
def fetch_compliance_status():
    """Use this tool to get compliance and document health metrics."""
    return execute_with_retry(get_compliance_oversight_stats)


@tool
def fetch_meetings_status():
    """Use this tool to get meeting and action item metrics."""
    return execute_with_retry(get_meetings_oversight_stats)


@tool
def fetch_sensitive_complaints_summary():
    """Use this tool to get a summary of sensitive complaints."""
    return execute_with_retry(get_sensitive_complaints_oversight)


@tool
def get_principal_daily_briefing():
    """Use this tool to fetch the Principal's daily institutional briefing, including pending approvals, academic alerts, financial alerts, and compliance items."""
    stats = execute_with_retry(get_college_stats)
    academic = execute_with_retry(get_academic_oversight_stats)
    finance = execute_with_retry(get_finance_oversight_stats)
    campus = execute_with_retry(get_campus_oversight_stats)
    compliance = execute_with_retry(get_compliance_oversight_stats)

    # Structured data for the LLM to summarize
    return {
        "pending_approvals": {
            "results": stats.get("pending_results", 0),
            "concessions": stats.get("pending_concessions", 0),
            "notices": stats.get("pending_notices", 0)
        },
        "academic_alerts": {
            "pending_marks_verification": academic.get("pending_marks", 0),
            "avg_attendance": academic.get("avg_attendance", 0)
        },
        "finance_alerts": {
            "outstanding_fees": finance.get("outstanding", 0),
            "pending_concessions": finance.get("pending_concessions", 0)
        },
        "compliance_alerts": {
            "pending_compliance": compliance.get("pending_compliance", 0),
            "overdue_compliance": compliance.get("overdue_compliance", 0)
        },
        "campus_alerts": {
            "low_stock_items": campus.get("low_stock", 0),
            "pending_visitor_approvals": campus.get("pending_visitors", 0)
        }
    }


# ==========================================
# EXECUTE / ACTION TOOLS (HITL)
# ==========================================
@tool
def request_result_approval(semester: int, config: RunnableConfig):
    """Use this tool when the Principal wants to APPROVE pending results for a specific semester."""
    user_confirmation = interrupt({
        "type": "APPROVAL_REQUEST",
        "message": f"I have prepared the approval for Semester {semester}.\n\nThis action will change the workflow status of all pending results for this semester.\n\nPlease reply 'Yes' to confirm execution, or 'Cancel' to abort."
    })

    if isinstance(user_confirmation, dict) and user_confirmation.get("confirmed") == True:
        user_id = config["configurable"].get("user_id", 1)
        thread_id = config["configurable"].get("thread_id", "unknown")

        # Securely construct AI Context for Audit
        ai_context = {
            "tool_name": "request_result_approval",
            "thread_id": thread_id
        }

        success, msg = execute_with_retry(
            PrincipalApprovalService.process_result_approval,
            semester=semester, action="Approved", principal_id=user_id, ai_context=ai_context
        )
        if success:
            return {"status": "EXECUTED", "message": f"Success! {msg}"}
        return {"status": "FAILED", "message": f"Execution failed: {msg}"}
    return {"status": "CANCELLED", "message": "Approval action cancelled by Principal."}


# ==========================================
# TOOL REGISTRY
# ==========================================
ACADEMIC_TOOLS = [fetch_academic_stats, fetch_pending_approvals, request_result_approval]
FINANCE_TOOLS = [fetch_finance_stats]
HR_TOOLS = [fetch_hr_stats]
CAMPUS_TOOLS = [fetch_campus_stats]
COMPLIANCE_TOOLS = [fetch_compliance_status, fetch_meetings_status]
GRIEVANCE_TOOLS = [fetch_sensitive_complaints_summary]

# Supervisor gets the briefing tool so it can handle generic greetings proactively
SUPERVISOR_TOOLS = [get_principal_daily_briefing]