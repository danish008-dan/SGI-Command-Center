# ai/admin_jarvis.py
"""Admin JARVIS AI Assistant — Tool-Based Data Retrieval.

Two-step JSON pipeline that works with Groq's JSON mode:
  Step 1: AI classifies intent → selects tool + args
  Step 2: Backend executes tool → AI generates answer from real data

Reuses existing admin/principal/fee query functions.
Read-only. No mutating operations. All tools are server-side.
"""
import json
from openai import OpenAI
from config import GROQ_API_KEY

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# ============================================================
# TOOL DEFINITIONS — presented to the AI so it knows what's
# available. Each tool maps to an existing query function.
# ============================================================
TOOL_DEFINITIONS = """You have access to the following data-retrieval tools. Call the appropriate tool when the admin asks a question that requires real data.

AVAILABLE TOOLS:
1. get_dashboard_summary() — Returns institutional counts: total students, teachers, departments, subjects, pending fees, etc.
2. search_students(search?, department_id?, semester?) — Search students by name/enrollment. Returns list with student_id, full_name, enrollment_no, department, semester, section, cgpa.
3. get_student_details(student_id) — Get full details of a specific student by ID. Returns profile, department, semester, CGPA.
4. search_teachers(search?, department_id?) — Search faculty by name. Returns list with teacher_id, full_name, designation, department.
5. get_teacher_details(teacher_id) — Get full details of a specific teacher by ID.
6. get_departments() — List all departments with names, codes, HOD names, student/teacher counts.
7. get_department_details(department_id) — Get details of a specific department including people, HOD history.
8. search_subjects(search?, department_id?, semester?) — Search subjects. Returns subject_id, name, code, semester, credits, type, teacher.
9. get_fee_summary() — Fee dashboard: total demand, collected, outstanding, collection rate, pending concessions.
10. get_pending_fees() — List of students with outstanding fee balances.
11. get_finance_overview() — Finance oversight: demand, collected, outstanding, collection_rate, pending_concessions.
12. get_academic_overview() — Academic stats: avg attendance, avg CGPA, pending results, pending marks.
13. get_hr_overview() — HR stats: faculty count, staff count, pending salary revisions, gross/net payroll.
14. get_campus_overview() — Campus operations: hostel occupancy, transport routes, library books, visitors.
15. get_low_attendance() — Students below 75% attendance threshold.
16. get_result_analysis(semester) — Result analysis for a specific semester: pass rate, grade distribution.
17. get_department_wise_analysis() — Department-wise student/teacher/subject breakdown.
18. get_sensitive_complaints() — Sensitive complaint oversight: status counts + top 5 active cases.
19. get_notices_events_stats() — Notice/event counts: published notices, pending, upcoming events.
20. get_pending_approvals() — Pending results, concessions, and notices awaiting Principal approval.
21. get_student_fee_details(student_id) — Fee details for a specific student: payable, paid, balance.

RULES FOR TOOL SELECTION:
- If the admin asks for general institutional stats → get_dashboard_summary or get_finance_overview or get_academic_overview.
- If the admin asks about a specific student → search_students first, then get_student_details if needed.
- If the admin asks about faculty → search_teachers or get_teacher_details.
- If the admin asks about departments → get_departments or get_department_details.
- If the admin asks about fees → get_fee_summary or get_pending_fees.
- If the admin asks about attendance → get_low_attendance or get_academic_overview.
- If the admin asks about results → get_result_analysis (requires semester).
- If the admin asks about complaints → get_sensitive_complaints.
- If the admin asks about pending work → get_pending_approvals.
- If the admin just says hi, thanks, or asks for navigation → respond directly without a tool.
- If the question is ambiguous → ask for clarification instead of calling a tool.
"""

# ============================================================
# TOOL EXECUTION — maps tool name to actual query function.
# All functions are existing, verified, read-only queries.
# ============================================================
def execute_tool(tool_name, args):
    """Execute a retrieval tool by calling the corresponding existing query function.
    Returns a JSON-serializable result dict or list.
    """
    args = args or {}

    try:
        if tool_name == "get_dashboard_summary":
            from database.admin_queries import get_dashboard_stats
            return {"data": get_dashboard_stats()}

        elif tool_name == "search_students":
            from database.admin_queries import get_all_students
            results = get_all_students(
                search=args.get("search"),
                department_id=args.get("department_id"),
                semester=args.get("semester")
            )
            # Limit to 20 results for response size
            return {"count": len(results), "students": results[:20]}

        elif tool_name == "get_student_details":
            from database.admin_queries import get_student_for_admin
            student_id = args.get("student_id")
            if not student_id:
                return {"error": "student_id is required"}
            data = get_student_for_admin(int(student_id))
            return {"student": data} if data else {"error": "Student not found"}

        elif tool_name == "search_teachers":
            from database.admin_queries import get_all_teachers
            results = get_all_teachers(
                search=args.get("search"),
                department_id=args.get("department_id")
            )
            return {"count": len(results), "teachers": results[:20]}

        elif tool_name == "get_teacher_details":
            from database.admin_queries import get_teacher_for_admin
            teacher_id = args.get("teacher_id")
            if not teacher_id:
                return {"error": "teacher_id is required"}
            data = get_teacher_for_admin(int(teacher_id))
            return {"teacher": data} if data else {"error": "Teacher not found"}

        elif tool_name == "get_departments":
            from database.admin_queries import get_all_departments
            return {"departments": get_all_departments()}

        elif tool_name == "get_department_details":
            from database.admin_queries import get_department_details
            dept_id = args.get("department_id")
            if not dept_id:
                return {"error": "department_id is required"}
            return {"department": get_department_details(int(dept_id))}

        elif tool_name == "search_subjects":
            from database.admin_queries import get_all_subjects
            results = get_all_subjects(
                search=args.get("search"),
                department_id=args.get("department_id"),
                semester=args.get("semester"),
                subject_type=args.get("subject_type")
            )
            return {"count": len(results), "subjects": results[:20]}

        elif tool_name == "get_fee_summary":
            from database.fee_queries import get_fee_dashboard_stats
            return {"fee_stats": get_fee_dashboard_stats()}

        elif tool_name == "get_pending_fees":
            from database.fee_queries import get_pending_fees
            results = get_pending_fees()
            return {"count": len(results), "pending_fees": results[:20]}

        elif tool_name == "get_finance_overview":
            from database.principal_queries import get_finance_oversight_stats
            return {"finance": get_finance_oversight_stats()}

        elif tool_name == "get_academic_overview":
            from database.principal_queries import get_academic_oversight_stats
            return {"academic": get_academic_oversight_stats()}

        elif tool_name == "get_hr_overview":
            from database.principal_queries import get_hr_oversight_stats
            return {"hr": get_hr_oversight_stats()}

        elif tool_name == "get_campus_overview":
            from database.principal_queries import get_campus_oversight_stats
            return {"campus": get_campus_oversight_stats()}

        elif tool_name == "get_low_attendance":
            from database.admin_queries import get_low_attendance_students
            results = get_low_attendance_students()
            return {"count": len(results), "students": results[:20]}

        elif tool_name == "get_result_analysis":
            from database.admin_queries import get_result_analysis
            semester = args.get("semester")
            if not semester:
                return {"error": "semester is required"}
            return {"results": get_result_analysis(int(semester))}

        elif tool_name == "get_department_wise_analysis":
            from database.principal_queries import get_department_wise_analysis
            return {"departments": get_department_wise_analysis()}

        elif tool_name == "get_sensitive_complaints":
            from database.principal_queries import get_sensitive_complaints_oversight
            return {"complaints": get_sensitive_complaints_oversight()}

        elif tool_name == "get_notices_events_stats":
            from database.principal_queries import get_notices_events_oversight_stats
            return {"stats": get_notices_events_oversight_stats()}

        elif tool_name == "get_pending_approvals":
            from services.principal_service import PrincipalApprovalService
            data = PrincipalApprovalService.get_all_pending_approvals()
            return {
                "pending_results": len(data.get("results", [])),
                "pending_concessions": len(data.get("concessions", [])),
                "pending_notices": len(data.get("notices", [])),
            }

        elif tool_name == "get_student_fee_details":
            from database.fee_queries import get_student_fee_details_for_admin
            student_id = args.get("student_id")
            if not student_id:
                return {"error": "student_id is required"}
            data = get_student_fee_details_for_admin(int(student_id))
            return {"fee_details": data} if data else {"error": "Fee details not found for this student"}

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        print(f"JARVIS tool execution error ({tool_name}):", e)
        return {"error": f"Failed to retrieve data: {str(e)}"}


# ============================================================
# NAVIGATION REGISTRY (unchanged from prior implementation)
# ============================================================
NAVIGATION_REGISTRY = {
    "dashboard": "/admin/dashboard", "users": "/admin/users",
    "departments": "/admin/departments", "subjects": "/admin/subjects",
    "students": "/admin/students", "teachers": "/admin/teachers",
    "timetable": "/admin/timetable", "attendance": "/admin/attendance",
    "marks": "/admin/marks", "results": "/admin/results",
    "fees": "/admin/fees", "notices": "/admin/notices",
    "events": "/admin/events", "complaints": "/admin/complaints",
    "maintenance": "/admin/maintenance", "inventory": "/admin/inventory",
    "assets": "/admin/assets", "reports": "/admin/reports",
    "finance_reports": "/admin/reports/finance", "approvals": "/admin/approvals",
    "audit": "/admin/audit", "jarvis": "/admin/jarvis"
}


# ============================================================
# MAIN CHAT FUNCTION — Two-step pipeline
# ============================================================
def admin_jarvis_chat(message, history, admin_context):
    """Two-step tool-based chat pipeline.

    Step 1: AI classifies intent → selects tool or responds directly.
    Step 2: If tool selected, execute → AI generates answer from real data.

    Returns: {"type": "text"|"navigate", "message": "...", "destination_id"?: "..."}
    or None on API failure.
    """

    # --- Step 1: Intent classification + tool selection ---
    step1_prompt = f"""You are JARVIS, the SGI Command Center Admin AI Assistant.
You are assisting: {admin_context.get('full_name', 'Administrator')}

{TOOL_DEFINITIONS}

INSTITUTIONAL CONTEXT (pre-loaded overview):
- Total Students: {admin_context.get('total_students', 'N/A')}
- Total Teachers: {admin_context.get('total_teachers', 'N/A')}
- Total Departments: {admin_context.get('total_departments', 'N/A')}
- Total Subjects: {admin_context.get('total_subjects', 'N/A')}
- Fee Demand: Rs. {admin_context.get('fee_demand', 'N/A')}
- Fee Outstanding: Rs. {admin_context.get('fee_outstanding', 'N/A')}
- Collection Rate: {admin_context.get('collection_rate', 'N/A')}%
- Pending Result Approvals: {admin_context.get('pending_result_approvals', 'N/A')}
- Pending Concession Approvals: {admin_context.get('pending_concession_approvals', 'N/A')}
- Pending Notice Approvals: {admin_context.get('pending_notice_approvals', 'N/A')}

CRITICAL RULES:
- If the admin's question can be answered from the INSTITUTIONAL CONTEXT above, respond directly without a tool.
- If the question requires more specific data (student details, faculty list, department info, etc.), select the appropriate tool.
- If the admin asks to navigate to a page, use the navigate response.
- If the question is ambiguous, ask for clarification.
- NEVER invent data. If no tool matches, say you don't have that specific information.
- You CANNOT approve, reject, publish, or execute any mutations. You are read-only.

NAVIGATION DESTINATIONS: {", ".join(NAVIGATION_REGISTRY.keys())}

Based on the admin's message, respond with ONE of these JSON formats:

For a tool call:
{{"action": "call_tool", "tool": "<tool_name>", "args": {{<parameters>}}}}

For a direct text response (when context is sufficient or for greetings):
{{"action": "respond", "type": "text", "message": "<your answer>"}}

For navigation:
{{"action": "respond", "type": "navigate", "destination_id": "<id>", "message": "<confirmation>"}}

For clarification:
{{"action": "respond", "type": "text", "message": "<clarifying question>"}}
"""

    step1_messages = [{"role": "system", "content": step1_prompt}]
    for msg in (history or [])[-10:]:
        step1_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    step1_messages.append({"role": "user", "content": message})

    try:
        step1_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=step1_messages,
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        step1_content = step1_response.choices[0].message.content or "{}"
        step1_result = json.loads(step1_content)
    except Exception as e:
        print("Groq API Error (Admin JARVIS Step 1):", e)
        return None

    # --- Handle Step 1 result ---
    action = step1_result.get("action", "respond")

    # If direct response (no tool needed)
    if action == "respond":
        return {
            "type": step1_result.get("type", "text"),
            "message": step1_result.get("message", "I could not process that request."),
            "destination_id": step1_result.get("destination_id")
        }

    # If tool call needed → execute tool → Step 2
    if action == "call_tool":
        tool_name = step1_result.get("tool", "")
        tool_args = step1_result.get("args", {})

        # Execute the tool (calls existing query functions)
        tool_result = execute_tool(tool_name, tool_args)

        # Check for errors
        if "error" in tool_result:
            return {
                "type": "text",
                "message": f"I was unable to retrieve that information. {tool_result['error']}"
            }

        # --- Step 2: Generate answer from tool results ---
        step2_prompt = f"""You are JARVIS, the SGI Command Center Admin AI Assistant.
You are assisting: {admin_context.get('full_name', 'Administrator')}

The admin asked: "{message}"

You called the tool "{tool_name}" and received the following results:
{json.dumps(tool_result, indent=2, default=str)}

Based on these results, generate a concise, professional, and helpful answer to the admin's question.

RULES:
- Use ONLY the data from the tool results. Do not invent or assume information.
- If the results show an error or empty data, explain that clearly.
- Format the answer naturally — do not just dump the JSON.
- If there are many results, summarize the key points (counts, names, notable items).
- If the admin asked for specific details, provide them from the data.
- Keep the response under 300 words.
- Do not mention "tool" or "API" — present the information as if you retrieved it directly.

Respond with JSON:
{{"type": "text", "message": "<your answer based on the data>"}}
"""

        step2_messages = [
            {"role": "system", "content": step2_prompt},
            {"role": "user", "content": message}
        ]

        try:
            step2_response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=step2_messages,
                temperature=0.5,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            step2_content = step2_response.choices[0].message.content or "{}"
            step2_result = json.loads(step2_content)
            return {
                "type": step2_result.get("type", "text"),
                "message": step2_result.get("message", "I retrieved the data but could not generate a response.")
            }
        except Exception as e:
            print("Groq API Error (Admin JARVIS Step 2):", e)
            # Return raw tool data as fallback so the admin at least gets the info
            return {
                "type": "text",
                "message": f"I retrieved the data: {json.dumps(tool_result, default=str)[:500]}"
            }

    # Fallback
    return {
        "type": "text",
        "message": "I could not determine how to help with that request. Could you rephrase?"
    }
