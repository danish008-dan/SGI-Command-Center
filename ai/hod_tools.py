# ai/hod_tools.py
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from database.hod_queries import (
    get_department_stats, get_department_attendance_stats,
    get_low_attendance_students, get_department_faculty_workload,
    get_submitted_marks_for_hod, get_department_leaves,
    create_department_notice, create_department_event,
    create_department_meeting, create_maintenance_request,
    get_department_assets
)
from services.hod_services import HODService


# ==========================================
# READ TOOLS
# ==========================================

@tool
def get_department_overview_tool(config: RunnableConfig):
    """Use this tool to get a general overview of the department, including student/faculty counts, average attendance, and low attendance count."""
    user_id = config["configurable"]["user_id"]
    dept_id = HODService.get_hod_active_department_id(user_id)
    if not dept_id: return {"error": "No active department assignment found."}

    stats = get_department_stats(dept_id)
    att_stats = get_department_attendance_stats(dept_id)
    return {
        "students": stats["students"],
        "faculty": stats["teachers"],
        "subjects": stats["subjects"],
        "avg_attendance": att_stats["avg_attendance"],
        "low_attendance_count": att_stats["low_attendance_count"]
    }


@tool
def get_low_attendance_students_tool(config: RunnableConfig):
    """Use this tool to get a list of students with attendance below 75% in the HOD's department."""
    user_id = config["configurable"]["user_id"]
    dept_id = HODService.get_hod_active_department_id(user_id)
    if not dept_id: return {"error": "No active department assignment found."}
    return get_low_attendance_students(dept_id)


@tool
def get_faculty_workload_tool(config: RunnableConfig):
    """Use this tool to get the teaching workload (hours per week) for faculty in the HOD's department."""
    user_id = config["configurable"]["user_id"]
    dept_id = HODService.get_hod_active_department_id(user_id)
    if not dept_id: return {"error": "No active department assignment found."}
    return get_department_faculty_workload(dept_id)


@tool
def get_pending_approvals_tool(config: RunnableConfig):
    """Use this tool to find out what approvals are pending for the HOD (Faculty Leaves, Marks Verification)."""
    user_id = config["configurable"]["user_id"]
    dept_id = HODService.get_hod_active_department_id(user_id)
    if not dept_id: return {"error": "No active department assignment found."}

    leaves = [l for l in get_department_leaves(dept_id) if l["status"] == 'Pending']
    marks = get_submitted_marks_for_hod(dept_id)
    return {
        "pending_leaves_count": len(leaves),
        "pending_marks_count": len(marks),
        "pending_leaves": leaves,
        "pending_marks": marks
    }


# ==========================================
# EXECUTE / ACTION TOOLS (HITL)
# ==========================================

@tool
def request_create_notice_tool(title: str, description: str, category: str, config: RunnableConfig):
    """Use this tool when the HOD wants to CREATE a new department notice. This triggers a confirmation request."""
    user_id = config["configurable"]["user_id"]
    dept_id = HODService.get_hod_active_department_id(user_id)
    if not dept_id: return {"error": "No active department assignment found."}

    user_confirmation = interrupt({
        "type": "APPROVAL_REQUEST",
        "message": f"I have prepared a department notice:\n\nTitle: {title}\nCategory: {category}\nDescription: {description}\n\nDo you want me to publish this notice to your department?"
    })

    if isinstance(user_confirmation, dict) and user_confirmation.get("confirmed") == True:
        success = create_department_notice(dept_id, user_id, title, description, category)
        if success: return {"status": "EXECUTED", "message": "Notice published successfully."}
        return {"status": "FAILED", "message": "Failed to publish notice."}
    return {"status": "CANCELLED", "message": "Notice creation cancelled."}


@tool
def request_create_event_tool(event_name: str, description: str, event_date: str, venue: str, config: RunnableConfig):
    """Use this tool when the HOD wants to CREATE a new department event. This triggers a confirmation request."""
    user_id = config["configurable"]["user_id"]
    dept_id = HODService.get_hod_active_department_id(user_id)
    if not dept_id: return {"error": "No active department assignment found."}

    user_confirmation = interrupt({
        "type": "APPROVAL_REQUEST",
        "message": f"I have prepared a department event:\n\nName: {event_name}\nDate: {event_date}\nVenue: {venue}\nDescription: {description}\n\nDo you want me to create this event?"
    })

    if isinstance(user_confirmation, dict) and user_confirmation.get("confirmed") == True:
        success = create_department_event(dept_id, user_id, event_name, description, event_date, venue)
        if success: return {"status": "EXECUTED", "message": "Event created successfully."}
        return {"status": "FAILED", "message": "Failed to create event."}
    return {"status": "CANCELLED", "message": "Event creation cancelled."}


@tool
def request_create_meeting_tool(title: str, meeting_date: str, venue: str, agenda: str, config: RunnableConfig):
    """Use this tool when the HOD wants to CREATE a new department meeting. This triggers a confirmation request."""
    user_id = config["configurable"]["user_id"]
    dept_id = HODService.get_hod_active_department_id(user_id)
    if not dept_id: return {"error": "No active department assignment found."}

    user_confirmation = interrupt({
        "type": "APPROVAL_REQUEST",
        "1message": f"I have prepared a department meeting:\n\nTitle: {title}\nDate: {meeting_date}\nVenue: {venue}\nAgenda: {agenda}\n\nDo you want me to schedule this meeting?"
    })

    if isinstance(user_confirmation, dict) and user_confirmation.get("confirmed") == True:
        success = create_department_meeting(dept_id, user_id, title, meeting_date, venue, agenda)
        if success: return {"status": "EXECUTED", "message": "Meeting scheduled successfully."}
        return {"status": "FAILED", "message": "Failed to schedule meeting."}
    return {"status": "CANCELLED", "message": "Meeting creation cancelled."}


@tool
def request_create_maintenance_tool(asset_id: int, issue_description: str, priority: str, config: RunnableConfig):
    """Use this tool when the HOD wants to CREATE a maintenance request for a department asset. This triggers a confirmation request."""
    user_id = config["configurable"]["user_id"]
    dept_id = HODService.get_hod_active_department_id(user_id)
    if not dept_id: return {"error": "No active department assignment found."}

    # Verify asset belongs to department
    assets = get_department_assets(dept_id)
    asset_name = "Unknown"
    for a in assets:
        if a["asset_id"] == asset_id:
            asset_name = a["name"]
            break
    else:
        return {"error": f"Asset ID {asset_id} does not belong to your department."}

    user_confirmation = interrupt({
        "type": "APPROVAL_REQUEST",
        "message": f"I have prepared a maintenance request:\n\nAsset: {asset_name} (ID: {asset_id})\nIssue: {issue_description}\nPriority: {priority}\n\nDo you want me to submit this request to Admin/Campus Ops?"
    })

    if isinstance(user_confirmation, dict) and user_confirmation.get("confirmed") == True:
        success = create_maintenance_request(user_id, asset_id, issue_description, priority)
        if success: return {"status": "EXECUTED", "message": "Maintenance request submitted successfully."}
        return {"status": "FAIL1ED", "message": "Failed to submit maintenance request."}
    return {"status": "CANCELLED", "message": "Maintenance request cancelled."}


# ==========================================
# TOOL REGISTRY
# ==========================================
HOD_READ_TOOLS = [get_department_overview_tool, get_low_attendance_students_tool, get_faculty_workload_tool,
                  get_pending_approvals_tool]
HOD_EXECUTE_TOOLS = [request_create_notice_tool, request_create_event_tool, request_create_meeting_tool,
                     request_create_maintenance_tool]