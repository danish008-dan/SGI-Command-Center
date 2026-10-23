# services/principal_service.py
from database.connection import get_connection
from database.principal_queries import get_pending_results_for_principal, approve_results_by_principal, \
    reject_results_by_principal
from database.fee_queries import get_pending_concessions, process_concession
from database.admin_queries import get_notices_for_approval, process_notice_approval


def log_action(user_id, action, target_table, target_id, ai_context=None, old_state=None, new_state=None):
    """Helper to insert into the extended audit_logs table. Derives source securely."""
    conn = get_connection()
    if conn is None: return
    try:
        cursor = conn.cursor()

        # Securely derive audit provenance
        if ai_context:
            source_interface = "AI Agent"
            ai_tool_name = ai_context.get("tool_name")
            thread_id = ai_context.get("thread_id")
        else:
            source_interface = "Manual UI"
            ai_tool_name = None
            thread_id = None

        cursor.execute("""
            INSERT INTO audit_logs (user_id, action, target_table, target_id, source_interface, ai_tool_name, old_state, new_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, action, target_table, target_id, source_interface, ai_tool_name, old_state, new_state))
    except Exception as e:
        print("Audit log error:", e)
    finally:
        conn.close()


class PrincipalApprovalService:
    """Unified service for Principal approvals, ensuring audit trails for both UI and AI."""

    @staticmethod
    def get_all_pending_approvals():
        """Aggregates pending results, concessions, and notices."""
        return {
            "results": get_pending_results_for_principal(),
            "concessions": get_pending_concessions(),
            "notices": get_notices_for_approval("Principal")
        }

    @staticmethod
    def process_result_approval(semester, action, principal_id, reason=None, ai_context=None):
        """Approves or rejects results by semester and logs the action."""
        if action == "Approved":
            success, msg = approve_results_by_principal(semester, principal_id)
        elif action == "Rejected":
            if not reason: return False, "Rejection reason is required."
            success, msg = reject_results_by_principal(semester, reason, principal_id)
        else:
            return False, "Invalid action."

        if success:
            old_state = "Pending Principal"
            new_state = "Approved" if action == "Approved" else "Rejected"
            log_action(principal_id, f"Result {action}", "results", semester, ai_context, old_state, new_state)

        return success, msg

    @staticmethod
    def process_concession_approval(request_id, action, principal_id, reason=None, ai_context=None):
        """Processes fee concession and logs the action."""
        success, msg = process_concession(request_id, action, principal_id, reason)

        if success:
            old_state = "Pending"
            new_state = action
            log_action(principal_id, f"Concession {action}", "concession_requests", request_id, ai_context, old_state,
                       new_state)

        return success, msg

    @staticmethod
    def process_notice_approval(notice_id, action, principal_id, remarks=None, ai_context=None):
        """Processes notice approval and logs the action."""
        success, msg = process_notice_approval(notice_id, action, principal_id, remarks)

        if success:
            old_state = "Pending"
            new_state = "Approved" if action == "Approved" else "Rejected"
            log_action(principal_id, f"Notice {action}", "notices", notice_id, ai_context, old_state, new_state)

        return success, msg