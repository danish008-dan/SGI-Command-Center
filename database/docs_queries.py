# database/docs_queries.py
import os
import uuid
from database.connection import get_connection


# ==========================================
# INSTITUTIONAL DOCUMENTS
# ==========================================

def get_doc_categories():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM document_categories WHERE status = 'Active' ORDER BY category_name")
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_documents(search=None, category_id=None, status=None):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT d.document_id, d.title, d.reference_number, d.status, d.expiry_date, d.created_at,
                   c.category_name, dep.department_name,
                   u.full_name AS uploaded_by_name, dv.version_number, dv.file_path
            FROM documents d
            INNER JOIN document_categories c ON d.category_id = c.category_id
            LEFT JOIN departments dep ON d.department_id = dep.department_id
            INNER JOIN users u ON d.created_by = u.user_id
            LEFT JOIN document_versions dv ON d.document_id = dv.document_id 
                AND dv.version_id = (SELECT MAX(version_id) FROM document_versions WHERE document_id = d.document_id)
            WHERE 1=1
        """
        params = []
        if search:
            sql += " AND (d.title LIKE %s OR d.reference_number LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        if category_id:
            sql += " AND d.category_id = %s"
            params.append(category_id)
        if status:
            sql += " AND d.status = %s"
            params.append(status)

        sql += " ORDER BY d.created_at DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching documents:", e)
        return []
    finally:
        conn.close()


def add_document_to_db(form_data, file_path, uploader_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Insert Document Metadata
        cursor.execute("""
            INSERT INTO documents (title, category_id, department_id, reference_number, status, expiry_date, created_by)
            VALUES (%s, %s, %s, %s, 'Draft', %s, %s)
        """, (
            form_data['title'], int(form_data['category_id']),
            form_data.get('department_id') or None, form_data.get('reference_number'),
            form_data.get('expiry_date') or None, uploader_id
        ))
        doc_id = cursor.lastrowid

        # 2. Insert Version 1
        cursor.execute("""
            INSERT INTO document_versions (document_id, version_number, file_path, change_summary, status, uploaded_by)
            VALUES (%s, 1, %s, %s, 'Draft', %s)
        """, (doc_id, file_path, form_data.get('change_summary', 'Initial upload'), uploader_id))

        conn.commit()
        return True, "Document uploaded successfully (Draft)."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def update_document_status(doc_id, new_status, user_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()

        # Update Document Status
        cursor.execute("UPDATE documents SET status = %s WHERE document_id = %s", (new_status, doc_id))

        if new_status in ['Approved', 'Published']:
            # FIX: Wrap subquery in another SELECT to avoid MySQL 1093 Error
            cursor.execute("""
                UPDATE document_versions 
                SET status = 'Approved' 
                WHERE version_id = (SELECT t.max_id FROM (SELECT MAX(version_id) as max_id FROM document_versions WHERE document_id = %s) t)
            """, (doc_id,))

        conn.commit()
        return True, f"Document status updated to {new_status}."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_document_file_path(doc_id):
    """Fetches the latest file path for secure download."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_path FROM document_versions 
            WHERE document_id = %s 
            ORDER BY version_id DESC LIMIT 1
        """, (doc_id,))
        result = cursor.fetchone()
        return result["file_path"] if result else None
    except Exception:
        return None
    finally:
        conn.close()


def get_docs_dashboard_stats():
    conn = get_connection()
    if conn is None: return {"total": 0, "pending": 0, "published": 0, "expiring": 0}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM documents")
        total = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM documents WHERE status = 'Pending Review'")
        pending = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM documents WHERE status = 'Published'")
        published = cursor.fetchone()["c"]

        cursor.execute(
            "SELECT COUNT(*) as c FROM documents WHERE expiry_date IS NOT NULL AND expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) AND status = 'Published'")
        expiring = cursor.fetchone()["c"]

        return {"total": total, "pending": pending, "published": published, "expiring": expiring}
    except Exception:
        return {"total": 0, "pending": 0, "published": 0, "expiring": 0}
    finally:
        conn.close()

# Add to database/docs_queries.py

# ==========================================
# COMPLIANCE REGISTER
# ==========================================

def get_compliance_requirements():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT cr.requirement_id, cr.body_name, cr.description, cr.academic_year, 
                   cr.status, cr.due_date, cr.evidence_doc_id,
                   d.department_name, doc.title AS evidence_title
            FROM compliance_requirements cr
            LEFT JOIN departments d ON cr.responsible_dept = d.department_id
            LEFT JOIN documents doc ON cr.evidence_doc_id = doc.document_id
            ORDER BY cr.due_date IS NULL, cr.due_date ASC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally: conn.close()

def add_compliance_requirement(form_data):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO compliance_requirements (body_name, description, academic_year, due_date, responsible_dept, status)
            VALUES (%s, %s, %s, %s, %s, 'Not Started')
        """, (
            form_data['body_name'], form_data['description'], form_data.get('academic_year'),
            form_data.get('due_date') or None, form_data.get('responsible_dept') or None
        ))
        conn.commit()
        return True, "Compliance requirement added."
    except Exception as e:
        return False, str(e)
    finally: conn.close()

def update_compliance_status(req_id, new_status):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE compliance_requirements SET status = %s WHERE requirement_id = %s", (new_status, req_id))
        conn.commit()
        return True, f"Status updated to {new_status}."
    except Exception as e:
        return False, str(e)
    finally: conn.close()

# ==========================================
# MEETING MANAGEMENT
# ==========================================

def get_meetings():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT m.meeting_id, m.title, m.meeting_type, m.meeting_date, m.venue, m.status, m.minutes,
                   u.full_name AS chairperson_name, u2.full_name AS organizer_name, d.department_name
            FROM meetings m
            INNER JOIN users u ON m.chairperson_id = u.user_id
            INNER JOIN users u2 ON m.organizer_id = u2.user_id
            LEFT JOIN departments d ON m.department_id = d.department_id
            ORDER BY m.meeting_date DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally: conn.close()

def add_meeting_to_db(form_data, user_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO meetings (title, meeting_type, department_id, meeting_date, venue, chairperson_id, organizer_id, agenda, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Scheduled')
        """, (
            form_data['title'], form_data.get('meeting_type'), form_data.get('department_id') or None,
            form_data['meeting_date'], form_data.get('venue'),
            int(form_data['chairperson_id']), user_id, form_data.get('agenda')
        ))
        conn.commit()
        return True, "Meeting scheduled."
    except Exception as e:
        return False, str(e)
    finally: conn.close()

def update_meeting_status(meeting_id, new_status, minutes=None):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        if minutes is not None:
            cursor.execute("UPDATE meetings SET status = %s, minutes = %s WHERE meeting_id = %s", (new_status, minutes, meeting_id))
        else:
            cursor.execute("UPDATE meetings SET status = %s WHERE meeting_id = %s", (new_status, meeting_id))
        conn.commit()
        return True, f"Meeting status updated to {new_status}."
    except Exception as e:
        return False, str(e)
    finally: conn.close()

def get_meeting_for_pdf(meeting_id):
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, u.full_name AS chairperson_name, u2.full_name AS organizer_name, d.department_name
            FROM meetings m
            INNER JOIN users u ON m.chairperson_id = u.user_id
            INNER JOIN users u2 ON m.organizer_id = u2.user_id
            LEFT JOIN departments d ON m.department_id = d.department_id
            WHERE m.meeting_id = %s
        """, (meeting_id,))
        return cursor.fetchone()
    except Exception:
        return None
    finally: conn.close()

# ==========================================
# ACTION ITEMS
# ==========================================

def get_action_items():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT ai.action_id, ai.description, ai.due_date, ai.status, ai.progress_notes,
                   m.title AS meeting_title,
                   u.full_name AS assigned_to_name
            FROM action_items ai
            INNER JOIN meetings m ON ai.meeting_id = m.meeting_id
            INNER JOIN users u ON ai.assigned_to = u.user_id
            ORDER BY ai.due_date IS NULL, ai.due_date ASC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally: conn.close()

def add_action_item(form_data):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO action_items (meeting_id, description, assigned_to, due_date)
            VALUES (%s, %s, %s, %s)
        """, (int(form_data['meeting_id']), form_data['description'], int(form_data['assigned_to']), form_data.get('due_date') or None))
        conn.commit()
        return True, "Action item added."
    except Exception as e:
        return False, str(e)
    finally: conn.close()

def update_action_status(action_id, new_status, notes=None):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        if notes is not None:
            cursor.execute("UPDATE action_items SET status = %s, progress_notes = %s WHERE action_id = %s", (new_status, notes, action_id))
        else:
            cursor.execute("UPDATE action_items SET status = %s WHERE action_id = %s", (new_status, action_id))
        conn.commit()
        return True, f"Action item updated to {new_status}."
    except Exception as e:
        return False, str(e)
    finally: conn.close()