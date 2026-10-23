# database/campus_queries.py
from database.connection import get_connection


# ==========================================
# HOSTEL MANAGEMENT
# ==========================================
def get_campus_dashboard_stats():
    conn = get_connection()
    if conn is None: return {"total_beds": 0, "occupied": 0, "available": 0, "pending_apps": 0, "total_vehicles": 0,
                             "total_titles": 0, "issued_books": 0, "today_visits": 0, "recent_activity": []}
    try:
        cursor = conn.cursor()

        # Hostel Stats
        cursor.execute("SELECT COUNT(*) as c FROM hostel_beds")
        total_beds = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM hostel_beds WHERE status = 'Occupied'")
        occupied = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM hostel_beds WHERE status = 'Available'")
        available = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM hostel_applications WHERE status = 'Pending'")
        pending_apps = cursor.fetchone()["c"]

        # Transport Stats
        cursor.execute("SELECT COUNT(*) as c FROM transport_vehicles WHERE status = 'Active'")
        total_vehicles = cursor.fetchone()["c"]

        # Library Stats
        cursor.execute("SELECT COUNT(*) as c FROM library_books WHERE status = 'Active'")
        total_titles = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM library_copies WHERE status = 'Issued'")
        issued_books = cursor.fetchone()["c"]

        # Visitor Stats
        cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE visit_date = CURDATE()")
        today_visits = cursor.fetchone()["c"]

        # Recent Activity (Simulated for now, can be made dynamic later)
        recent_activity = [
            {"type": "Visitor", "details": "Sunil Shetty checked in", "date": "Today"},
            {"type": "Library", "details": "Book LIB-0002 issued", "date": "Today"},
            {"type": "Hostel", "details": "Bed B2 allocated in Room 101", "date": "Today"}
        ]

        return {
            "total_beds": total_beds, "occupied": occupied, "available": available,
            "pending_apps": pending_apps, "total_vehicles": total_vehicles,
            "total_titles": total_titles, "issued_books": issued_books,
            "today_visits": today_visits, "recent_activity": recent_activity
        }
    except Exception:
        return {"total_beds": 0, "occupied": 0, "available": 0, "pending_apps": 0, "total_vehicles": 0,
                "total_titles": 0, "issued_books": 0, "today_visits": 0, "recent_activity": []}
    finally:
        conn.close()


def get_hostel_rooms():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT r.room_id, r.hostel_name, r.floor, r.room_number, r.capacity, r.room_type, r.status,
                   (SELECT COUNT(*) FROM hostel_beds b WHERE b.room_id = r.room_id AND b.status = 'Occupied') as occupied_beds
            FROM hostel_rooms r
            ORDER BY r.hostel_name, r.floor, r.room_number
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def add_hostel_room(form_data):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO hostel_rooms (hostel_name, floor, room_number, capacity, room_type, status)
            VALUES (%s, %s, %s, %s, %s, 'Active')
        """, (form_data['hostel_name'], form_data['floor'], form_data['room_number'], int(form_data['capacity']),
              form_data.get('room_type', 'Non-AC')))

        room_id = cursor.lastrowid

        # Auto-generate beds based on capacity
        for i in range(1, int(form_data['capacity']) + 1):
            cursor.execute("INSERT INTO hostel_beds (room_id, bed_number, status) VALUES (%s, %s, 'Available')",
                           (room_id, f"B{i}"))

        conn.commit()
        return True, "Room and beds added successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def get_hostel_applications():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT a.application_id, a.preferred_hostel, a.status, a.requested_at,
                   u.full_name AS student_name, s.enrollment_no, d.department_name
            FROM hostel_applications a
            INNER JOIN students s ON a.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            ORDER BY a.requested_at DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def allocate_bed_to_student(application_id, bed_id, admin_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get Application Details
        cursor.execute("SELECT student_id FROM hostel_applications WHERE application_id = %s", (application_id,))
        app = cursor.fetchone()
        if not app:
            conn.rollback()
            return False, "Application not found."

        student_id = app["student_id"]

        # 2. Check Bed Availability
        cursor.execute("SELECT status FROM hostel_beds WHERE bed_id = %s FOR UPDATE", (bed_id,))
        bed = cursor.fetchone()
        if not bed or bed["status"] != 'Available':
            conn.rollback()
            return False, "Bed is not available."

        # 3. Allocate Bed
        cursor.execute("""
            INSERT INTO hostel_allocations (student_id, bed_id, check_in_date, status, allocated_by)
            VALUES (%s, %s, CURDATE(), 'Active', %s)
        """, (student_id, bed_id, admin_id))

        # 4. Update Bed Status
        cursor.execute("UPDATE hostel_beds SET status = 'Occupied' WHERE bed_id = %s", (bed_id,))

        # 5. Update Application Status
        cursor.execute(
            "UPDATE hostel_applications SET status = 'Allocated', reviewed_by = %s WHERE application_id = %s",
            (admin_id, application_id))

        conn.commit()
        return True, "Bed allocated successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def get_available_beds():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT b.bed_id, b.bed_number, r.hostel_name, r.room_number
            FROM hostel_beds b
            INNER JOIN hostel_rooms r ON b.room_id = r.room_id
            WHERE b.status = 'Available'
            ORDER BY r.hostel_name, r.room_number
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


# Add to database/campus_queries.py

# ==========================================
# TRANSPORT MANAGEMENT
# ==========================================

def get_transport_stats():
    conn = get_connection()
    if conn is None: return {"total_vehicles": 0, "active_routes": 0, "active_allocations": 0}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM transport_vehicles")
        total_vehicles = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM transport_routes WHERE status = 'Active'")
        active_routes = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM transport_allocations WHERE status = 'Active'")
        active_allocations = cursor.fetchone()["c"]

        return {"total_vehicles": total_vehicles, "active_routes": active_routes,
                "active_allocations": active_allocations}
    except Exception:
        return {"total_vehicles": 0, "active_routes": 0, "active_allocations": 0}
    finally:
        conn.close()


def get_transport_vehicles():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT tv.transport_vehicle_id, tv.driver_name, tv.driver_contact, tv.capacity, tv.status,
                   a.asset_code, a.name AS vehicle_name, a.serial_number AS reg_number,
                   tr.route_name
            FROM transport_vehicles tv
            INNER JOIN assets a ON tv.asset_id = a.asset_id
            LEFT JOIN transport_routes tr ON tv.route_id = tr.route_id
            ORDER BY tv.transport_vehicle_id DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_available_assets_for_transport():
    """Fetches assets that are not yet linked to transport_vehicles."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT asset_id, asset_code, name 
            FROM assets 
            WHERE asset_id NOT IN (SELECT asset_id FROM transport_vehicles)
            AND lifecycle_status = 'Active'
            ORDER BY name
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def add_transport_vehicle(form_data):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transport_vehicles (asset_id, route_id, driver_name, driver_contact, capacity, status)
            VALUES (%s, %s, %s, %s, %s, 'Active')
        """, (
            form_data['asset_id'],
            form_data.get('route_id') or None,
            form_data.get('driver_name'),
            form_data.get('driver_contact'),
            int(form_data.get('capacity', 30))
        ))
        conn.commit()
        return True, "Transport vehicle added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_routes():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transport_routes ORDER BY route_name")
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def add_route(name, start_point, end_point):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transport_routes (route_name, start_point, end_point) VALUES (%s, %s, %s)",
                       (name, start_point, end_point))
        conn.commit()
        return True, "Route added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_transport_allocations():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT ta.allocation_id, ta.effective_from, ta.status, ta.allocated_by,
                   u.full_name AS student_name, s.enrollment_no,
                   tr.route_name, ts.stop_name
            FROM transport_allocations ta
            INNER JOIN students s ON ta.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN transport_routes tr ON ta.route_id = tr.route_id
            LEFT JOIN transport_stops ts ON ta.stop_id = ts.stop_id
            ORDER BY ta.allocation_id DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def allocate_transport_to_student(student_id, route_id, stop_id, admin_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # Check if student already has an active allocation
        cursor.execute("SELECT allocation_id FROM transport_allocations WHERE student_id = %s AND status = 'Active'",
                       (student_id,))
        if cursor.fetchone():
            conn.rollback()
            return False, "Student already has an active transport allocation."

        cursor.execute("""
            INSERT INTO transport_allocations (student_id, route_id, stop_id, effective_from, status, allocated_by)
            VALUES (%s, %s, %s, CURDATE(), 'Active', %s)
        """, (student_id, route_id, stop_id or None, admin_id))

        conn.commit()
        return True, "Transport allocated successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# Add to database/campus_queries.py
from datetime import datetime, timedelta


# ==========================================
# LIBRARY MANAGEMENT
# ==========================================

def get_library_stats():
    conn = get_connection()
    if conn is None: return {"total_titles": 0, "total_copies": 0, "issued": 0, "available": 0}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM library_books WHERE status = 'Active'")
        total_titles = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM library_copies")
        total_copies = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM library_copies WHERE status = 'Issued'")
        issued = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM library_copies WHERE status = 'Available'")
        available = cursor.fetchone()["c"]

        return {"total_titles": total_titles, "total_copies": total_copies, "issued": issued, "available": available}
    except Exception:
        return {"total_titles": 0, "total_copies": 0, "issued": 0, "available": 0}
    finally:
        conn.close()


def get_library_books():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT b.book_id, b.title, b.author, b.isbn, b.category,
                   (SELECT COUNT(*) FROM library_copies c WHERE c.book_id = b.book_id) as total_copies,
                   (SELECT COUNT(*) FROM library_copies c WHERE c.book_id = b.book_id AND c.status = 'Available') as available_copies
            FROM library_books b
            WHERE b.status = 'Active'
            ORDER BY b.title
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def add_library_book(form_data):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO library_books (title, author, isbn, publisher, category)
            VALUES (%s, %s, %s, %s, %s)
        """, (form_data['title'], form_data['author'], form_data.get('isbn'), form_data.get('publisher'),
              form_data.get('category')))
        conn.commit()
        return True, "Book added to catalogue."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def add_library_copy(book_id, accession_number):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT copy_id FROM library_copies WHERE accession_number = %s", (accession_number,))
        if cursor.fetchone():
            return False, "Accession Number already exists."

        cursor.execute("INSERT INTO library_copies (book_id, accession_number, status) VALUES (%s, %s, 'Available')",
                       (book_id, accession_number))
        conn.commit()
        return True, "Physical copy added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_active_loans():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT l.loan_id, l.issue_date, l.due_date, l.status, l.fine_amount,
                   c.accession_number, b.title, b.author,
                   u.full_name AS member_name, u.role AS member_role
            FROM library_loans l
            INNER JOIN library_copies c ON l.copy_id = c.copy_id
            INNER JOIN library_books b ON c.book_id = b.book_id
            INNER JOIN users u ON l.user_id = u.user_id
            WHERE l.status IN ('Issued', 'Overdue')
            ORDER BY l.issue_date DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def issue_book(copy_id, user_id, issued_by):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Check Copy Availability
        cursor.execute("SELECT status FROM library_copies WHERE copy_id = %s FOR UPDATE", (copy_id,))
        copy = cursor.fetchone()
        if not copy or copy["status"] != 'Available':
            conn.rollback()
            return False, "Book copy is not available."

        # 2. Create Loan Record (14-day loan period)
        issue_date = datetime.now().date()
        due_date = issue_date + timedelta(days=14)

        cursor.execute("""
            INSERT INTO library_loans (copy_id, user_id, issue_date, due_date, status, issued_by)
            VALUES (%s, %s, %s, %s, 'Issued', %s)
        """, (copy_id, user_id, issue_date, due_date, issued_by))

        # 3. Update Copy Status
        cursor.execute("UPDATE library_copies SET status = 'Issued' WHERE copy_id = %s", (copy_id,))

        conn.commit()
        return True, "Book issued successfully. Due date: " + str(due_date)
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def return_book(loan_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get Loan Details
        cursor.execute("SELECT * FROM library_loans WHERE loan_id = %s FOR UPDATE", (loan_id,))
        loan = cursor.fetchone()
        if not loan or loan["status"] == 'Returned':
            conn.rollback()
            return False, "Loan not found or already returned."

        # 2. Update Copy Status
        cursor.execute("UPDATE library_copies SET status = 'Available' WHERE copy_id = %s", (loan["copy_id"],))

        # 3. Update Loan Status
        # Check if overdue
        is_overdue = datetime.now().date() > loan["due_date"]
        new_status = 'Returned'
        if is_overdue:
            # For MVP, we just mark as returned. Fine calculation is disabled.
            new_status = 'Returned'

        cursor.execute("UPDATE library_loans SET status = %s, return_date = CURDATE() WHERE loan_id = %s",
                       (new_status, loan_id))

        conn.commit()
        return True, "Book returned successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# Add to database/campus_queries.py
import uuid


# ==========================================
# VISITOR MANAGEMENT
# ==========================================

def get_visitor_stats():
    conn = get_connection()
    if conn is None: return {"today_visits": 0, "checked_in": 0, "pending_approval": 0}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE visit_date = CURDATE()")
        today_visits = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE status = 'Checked In'")
        checked_in = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE approval_status = 'Pending'")
        pending_approval = cursor.fetchone()["c"]

        return {"today_visits": today_visits, "checked_in": checked_in, "pending_approval": pending_approval}
    except Exception:
        return {"today_visits": 0, "checked_in": 0, "pending_approval": 0}
    finally:
        conn.close()


def get_visitors():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT v.visitor_id, v.full_name, v.mobile, v.purpose, v.visit_date, 
                   v.approval_status, v.status, v.check_in_time, v.check_out_time, v.qr_reference,
                   u.full_name AS host_name, d.department_name,
                   reg.full_name AS registered_by_name
            FROM visitors v
            INNER JOIN users u ON v.host_user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            INNER JOIN users reg ON v.registered_by = reg.user_id
            ORDER BY v.visit_date DESC, v.visitor_id DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def register_visitor(form_data, registered_by):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        qr_ref = str(uuid.uuid4().hex)[:12].upper()

        cursor.execute("""
            INSERT INTO visitors (full_name, mobile, host_user_id, purpose, visit_date, approval_status, status, qr_reference, registered_by)
            VALUES (%s, %s, %s, %s, %s, 'Pending', 'Scheduled', %s, %s)
        """, (
            form_data['full_name'], form_data['mobile'], int(form_data['host_user_id']),
            form_data['purpose'], form_data['visit_date'], qr_ref, registered_by
        ))
        conn.commit()
        return True, f"Visitor registered. Reference: {qr_ref}"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def approve_visitor(visitor_id, approver_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET approval_status = 'Approved' 
            WHERE visitor_id = %s AND approval_status = 'Pending'
        """, (visitor_id,))

        if cursor.rowcount == 0:
            return False, "Visitor not found or already processed."

        conn.commit()
        return True, "Visitor approved."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def check_in_visitor(visitor_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET status = 'Checked In', check_in_time = NOW() 
            WHERE visitor_id = %s AND status = 'Scheduled' AND approval_status = 'Approved'
        """, (visitor_id,))

        if cursor.rowcount == 0:
            return False, "Visitor not found, not approved, or already checked in."

        conn.commit()
        return True, "Visitor checked in."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def check_out_visitor(visitor_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET status = 'Checked Out', check_out_time = NOW() 
            WHERE visitor_id = %s AND status = 'Checked In'
        """, (visitor_id,))

        if cursor.rowcount == 0:
            return False, "Visitor not found or not checked in."

        conn.commit()
        return True, "Visitor checked out."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_visitor_for_pass(visitor_id):
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT v.*, u.full_name AS host_name, d.department_name
            FROM visitors v
            INNER JOIN users u ON v.host_user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE v.visitor_id = %s
        """
        cursor.execute(sql, (visitor_id,))
        return cursor.fetchone()
    except Exception:
        return None
    finally:
        conn.close()