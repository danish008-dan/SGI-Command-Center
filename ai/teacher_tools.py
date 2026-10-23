# ai/teacher_tools.py
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
import json
from datetime import datetime, date
from decimal import Decimal

from database.teacher_queries import (
    get_teacher_id_from_user, verify_teacher_subject_scope,
    get_student_risk_dashboard, get_attendance_intelligence,
    get_teacher_workload, create_lesson_plan
)


# Helper to sanitize DB data for LLM
def to_json_string(data):
    # Using default=str to handle any datetime/decimal objects safely
    return json.dumps(data, default=str, indent=2)


# ==========================================
# READ TOOLS (Strictly wrapping existing scoped queries)
# ==========================================

@tool
def get_academic_risks_tool(config: RunnableConfig):
    """Use this tool to find students with academic risk indicators (low attendance or missing marks) in your classes."""
    try:
        user_id = config["configurable"]["user_id"]
        teacher_id = get_teacher_id_from_user(user_id)
        if not teacher_id: return "Error: Teacher profile not found."

        data = get_student_risk_dashboard(teacher_id)
        if not data:
            return "No academic risks found. All students are above 75% attendance and have no missing marks."

        return to_json_string(data)
    except Exception as e:
        return f"Error fetching academic risks: {str(e)}"


@tool
def get_attendance_analytics_tool(config: RunnableConfig):
    """Use this tool to get attendance analytics and average percentages for your assigned subjects."""
    try:
        user_id = config["configurable"]["user_id"]
        teacher_id = get_teacher_id_from_user(user_id)
        if not teacher_id: return "Error: Teacher profile not found."

        data = get_attendance_intelligence(teacher_id)
        if not data:
            return "No attendance analytics available for your subjects."

        return to_json_string(data)
    except Exception as e:
        return f"Error fetching attendance analytics: {str(e)}"


@tool
def get_my_workload_tool(config: RunnableConfig):
    """Use this tool to check your current teaching workload (subjects and hours per week)."""
    try:
        user_id = config["configurable"]["user_id"]
        teacher_id = get_teacher_id_from_user(user_id)
        if not teacher_id: return "Error: Teacher profile not found."

        data = get_teacher_workload(teacher_id)
        if not data or not data.get("subjects"):
            return "You have no subjects assigned currently."

        return to_json_string(data)
    except Exception as e:
        return f"Error fetching workload: {str(e)}"


# ==========================================
# EXECUTE / ACTION TOOLS (HITL - Drafts Only)
# ==========================================

@tool
def save_lesson_plan_draft_tool(
        subject_id: int,
        section: str,
        plan_date: str,
        topic: str,
        learning_objective: str,
        teaching_method: str,
        duration: int,
        config: RunnableConfig
):
    """Use this tool when the Teacher wants to SAVE a generated Lesson Plan as a Draft. This triggers a confirmation request."""
    try:
        user_id = config["configurable"]["user_id"]
        teacher_id = get_teacher_id_from_user(user_id)
        if not teacher_id: return "Error: Teacher profile not found."

        # IDOR Protection
        if not verify_teacher_subject_scope(teacher_id, subject_id):
            return f"Error: Authorization failed. You are not assigned to Subject ID {subject_id}."

        user_confirmation = interrupt({
            "type": "APPROVAL_REQUEST",
            "message": f"I have prepared a Lesson Plan:\n\nTopic: {topic}\nDate: {plan_date}\nSection: {section}\nObjective: {learning_objective}\nMethod: {teaching_method}\nDuration: {duration} mins\n\nDo you want me to save this as a Draft?"
        })

        if isinstance(user_confirmation, dict) and user_confirmation.get("confirmed") == True:
            success = create_lesson_plan(teacher_id, subject_id, section, plan_date, topic, learning_objective,
                                         teaching_method, duration)
            if success: return "Success: Lesson plan saved as Draft successfully."
            return "Error: Failed to save lesson plan."
        return "Cancelled: Lesson plan creation cancelled."
    except Exception as e:
        return f"Error during lesson plan execution: {str(e)}"


# ==========================================
# TOOL REGISTRY
# ==========================================
TEACHER_READ_TOOLS = [get_academic_risks_tool, get_attendance_analytics_tool, get_my_workload_tool]
TEACHER_EXECUTE_TOOLS = [save_lesson_plan_draft_tool]
ALL_TEACHER_TOOLS = TEACHER_READ_TOOLS + TEACHER_EXECUTE_TOOLS