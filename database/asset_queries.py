# database/asset_queries.py
from database.connection import get_connection
import qrcode
import os


# ==========================================
# ASSET CATEGORIES
# ==========================================

def get_asset_categories():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM asset_categories WHERE status = 'Active' ORDER BY category_name")
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def add_asset_category(name, prefix):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO asset_categories (category_name, prefix) VALUES (%s, %s)", (name, prefix.upper()))
        conn.commit()
        return True, "Category added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ==========================================
# ASSET REGISTRY
# ==========================================

def get_all_assets(search=None, category_id=None, department_id=None):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT a.asset_id, a.asset_code, a.name, a.condition_status, a.lifecycle_status,
                   ac.category_name, d.department_name, u.full_name AS custodian_name,
                   r.room_number, a.serial_number
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.category_id
            LEFT JOIN departments d ON a.department_id = d.department_id
            LEFT JOIN users u ON a.custodian_id = u.user_id
            LEFT JOIN rooms r ON a.room_id = r.room_id
            WHERE 1=1
        """
        params = []
        if search:
            sql += " AND (a.asset_code LIKE %s OR a.name LIKE %s OR a.serial_number LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        if category_id:
            sql += " AND a.category_id = %s"
            params.append(category_id)
        if department_id:
            sql += " AND a.department_id = %s"
            params.append(department_id)

        sql += " ORDER BY a.asset_id DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching assets:", e)
        return []
    finally:
        conn.close()


def add_asset_to_db(form_data, creator_id):
    """Inserts a new asset and generates a unique Asset Code."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get Category Prefix
        cursor.execute("SELECT prefix FROM asset_categories WHERE category_id = %s", (form_data['category_id'],))
        cat = cursor.fetchone()
        if not cat:
            return False, "Invalid category selected."

        prefix = cat["prefix"]

        # 2. Insert Asset with temporary code
        cursor.execute("""
            INSERT INTO assets (category_id, name, description, serial_number, acquisition_date, acquisition_cost, supplier, condition_status, lifecycle_status, room_id, department_id, custodian_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Active', %s, %s, %s)
        """, (
            form_data['category_id'], form_data['name'], form_data.get('description'),
            form_data.get('serial_number'), form_data.get('acquisition_date'),
            float(form_data.get('acquisition_cost', 0)), form_data.get('supplier'),
            form_data.get('condition_status', 'Good'),
            form_data.get('room_id') or None, form_data.get('department_id') or None,
            form_data.get('custodian_id') or None
        ))

        asset_id = cursor.lastrowid

        # 3. Generate Asset Code (e.g., SGI-IT-0001)
        asset_code = f"SGI-{prefix}-{str(asset_id).zfill(4)}"
        cursor.execute("UPDATE assets SET asset_code = %s WHERE asset_id = %s", (asset_code, asset_id))

        # 4. Generate QR Code
        qr_dir = "static/uploads/qrcodes"
        os.makedirs(qr_dir, exist_ok=True)
        qr_path = f"{qr_dir}/{asset_code}.png"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(f"ASSET:{asset_code}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_path)

        conn.commit()
        return True, f"Asset registered successfully. Asset Code: {asset_code}"
    except Exception as e:
        conn.rollback()
        print("Error adding asset:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def get_asset_for_details(asset_id):
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT a.*, ac.category_name, d.department_name, u.full_name AS custodian_name, r.room_number
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.category_id
            LEFT JOIN departments d ON a.department_id = d.department_id
            LEFT JOIN users u ON a.custodian_id = u.user_id
            LEFT JOIN rooms r ON a.room_id = r.room_id
            WHERE a.asset_id = %s
        """
        cursor.execute(sql, (asset_id,))
        return cursor.fetchone()
    except Exception:
        return None
    finally:
        conn.close()


# ==========================================
# INVENTORY & CONSUMABLES
# ==========================================

def get_inventory_items():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory_items WHERE status = 'Active' ORDER BY item_name")
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def add_inventory_item(name, unit, reorder_level):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO inventory_items (item_name, unit, reorder_level) VALUES (%s, %s, %s)",
                       (name, unit, float(reorder_level)))
        conn.commit()
        return True, "Inventory item added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def add_stock_movement(item_id, movement_type, quantity, reason, performed_by):
    """Transaction-safe stock movement. Quantity is positive for receipt/return, negative for issue."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Lock item row and get current stock
        cursor.execute("SELECT current_stock FROM inventory_items WHERE item_id = %s FOR UPDATE", (item_id,))
        item = cursor.fetchone()
        if not item:
            conn.rollback()
            return False, "Item not found."

        current_stock = float(item["current_stock"])
        qty = float(quantity)

        # For issue, quantity should be negative. For receipt, positive.
        if movement_type == 'Issue':
            qty = -abs(qty)
        else:
            qty = abs(qty)

        new_stock = current_stock + qty

        # Prevent negative stock
        if new_stock < 0:
            conn.rollback()
            return False, "Insufficient stock. Cannot issue more than available."

        # 2. Update current stock
        cursor.execute("UPDATE inventory_items SET current_stock = %s WHERE item_id = %s", (new_stock, item_id))

        # 3. Insert into ledger
        cursor.execute("""
            INSERT INTO stock_movements (item_id, movement_type, quantity, balance_after, reason, performed_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (item_id, movement_type, qty, new_stock, reason, performed_by))

        conn.commit()
        return True, "Stock movement recorded successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# ==========================================
# STOCK REQUESTS
# ==========================================

def get_stock_requests(department_id=None):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT sr.request_id, sr.quantity, sr.purpose, sr.status, sr.created_at,
                   i.item_name, i.unit, u.full_name AS requester_name, d.department_name
            FROM stock_requests sr
            INNER JOIN inventory_items i ON sr.item_id = i.item_id
            INNER JOIN users u ON sr.requested_by = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE 1=1
        """
        params = []
        if department_id:
            sql += " AND u.department_id = %s"
            params.append(department_id)

        sql += " ORDER BY sr.created_at DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def create_stock_request(item_id, quantity, purpose, requested_by):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stock_requests (item_id, quantity, purpose, requested_by, status)
            VALUES (%s, %s, %s, %s, 'Pending')
        """, (item_id, float(quantity), purpose, requested_by))
        conn.commit()
        return True, "Stock request submitted."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def process_stock_request(request_id, action, approver_id):
    """Approves or Rejects a stock request. Does NOT issue stock."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        new_status = 'Approved' if action == 'Approved' else 'Rejected'
        cursor.execute("""
            UPDATE stock_requests 
            SET status = %s, approved_by = %s 
            WHERE request_id = %s AND status = 'Pending'
        """, (new_status, approver_id, request_id))

        if cursor.rowcount == 0:
            return False, "Request not found or already processed."

        conn.commit()
        return True, f"Request {new_status}."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def issue_stock_from_request(request_id, issuer_id):
    """Issues stock for an approved request. Updates movement ledger."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get Request Details
        cursor.execute("SELECT * FROM stock_requests WHERE request_id = %s FOR UPDATE", (request_id,))
        req = cursor.fetchone()
        if not req:
            conn.rollback()
            return False, "Request not found."
        if req["status"] != 'Approved':
            conn.rollback()
            return False, "Only approved requests can be issued."

        # 2. Perform Stock Movement
        reason = f"Issued against Request #{request_id}"
        success, msg = add_stock_movement(req["item_id"], 'Issue', req["quantity"], reason, issuer_id)
        if not success:
            conn.rollback()
            return False, msg

        # 3. Update Request Status
        cursor.execute("UPDATE stock_requests SET status = 'Issued' WHERE request_id = %s", (request_id,))

        conn.commit()
        return True, "Stock issued successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# ==========================================
# ASSET ALLOCATION & TRANSFERS
# ==========================================

def get_asset_allocation_history(asset_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT al.allocation_date, al.return_date, al.status,
                   u.full_name AS custodian_name, d.department_name, r.room_number,
                   actor.full_name AS allocated_by_name
            FROM asset_allocations al
            LEFT JOIN users u ON al.allocated_to_user = u.user_id
            LEFT JOIN departments d ON al.allocated_to_dept = d.department_id
            LEFT JOIN rooms r ON al.allocated_to_room = r.room_id
            INNER JOIN users actor ON al.allocated_by = actor.user_id
            WHERE al.asset_id = %s
            ORDER BY al.allocation_date DESC
        """, (asset_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def allocate_asset(asset_id, user_id, dept_id, room_id, allocated_by):
    """Allocates an asset, expires the old allocation, and updates the current pointer."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Expire current active allocation
        cursor.execute("""
            UPDATE asset_allocations 
            SET status = 'Transferred', return_date = NOW() 
            WHERE asset_id = %s AND status = 'Active'
        """, (asset_id,))

        # 2. Insert new allocation record
        cursor.execute("""
            INSERT INTO asset_allocations (asset_id, allocated_to_user, allocated_to_dept, allocated_to_room, allocated_by, status)
            VALUES (%s, %s, %s, %s, %s, 'Active')
        """, (asset_id, user_id or None, dept_id or None, room_id or None, allocated_by))

        # 3. Update assets table current pointer
        cursor.execute("""
            UPDATE assets 
            SET custodian_id = %s, department_id = %s, room_id = %s, lifecycle_status = 'Allocated'
            WHERE asset_id = %s
        """, (user_id or None, dept_id or None, room_id or None, asset_id))

        conn.commit()
        return True, "Asset allocated/transferred successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# ==========================================
# MAINTENANCE REQUESTS
# ==========================================

def get_all_maintenance_requests():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.request_id, m.issue_description, m.priority, m.status, m.created_at,
                   a.asset_code, a.name AS asset_name,
                   u.full_name AS requester_name
            FROM maintenance_requests m
            INNER JOIN assets a ON m.asset_id = a.asset_id
            INNER JOIN users u ON m.requested_by = u.user_id
            ORDER BY m.created_at DESC
        """)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def create_maintenance_request(asset_id, description, priority, requested_by):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_requests (asset_id, issue_description, priority, requested_by, status)
            VALUES (%s, %s, %s, %s, 'Submitted')
        """, (asset_id, description, priority, requested_by))
        conn.commit()
        return True, "Maintenance request submitted."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_maintenance_status(request_id, new_status, resolution_notes, assigned_to=None):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        resolved_at = "NOW()" if new_status in ['Resolved', 'Closed'] else "NULL"
        cursor.execute(f"""
            UPDATE maintenance_requests 
            SET status = %s, resolution_notes = %s, assigned_to = %s, resolved_at = {resolved_at}
            WHERE request_id = %s
        """, (new_status, resolution_notes, assigned_to, request_id))
        conn.commit()
        return True, f"Maintenance status updated to {new_status}."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ==========================================
# ASSET DISPOSALS
# ==========================================

def get_disposal_requests():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.disposal_id, d.reason, d.status, d.created_at,
                   a.asset_code, a.name AS asset_name,
                   u.full_name AS requester_name
            FROM asset_disposals d
            INNER JOIN assets a ON d.asset_id = a.asset_id
            INNER JOIN users u ON d.requested_by = u.user_id
            ORDER BY d.created_at DESC
        """)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def create_disposal_request(asset_id, reason, requested_by):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO asset_disposals (asset_id, reason, requested_by, status)
            VALUES (%s, %s, %s, 'Pending')
        """, (asset_id, reason, requested_by))
        conn.commit()
        return True, "Disposal request submitted for approval."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def process_disposal_request(disposal_id, action, approved_by):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Update Disposal Status
        new_status = 'Approved' if action == 'Approved' else 'Rejected'
        cursor.execute("""
            UPDATE asset_disposals 
            SET status = %s, approved_by = %s, disposal_date = CURDATE()
            WHERE disposal_id = %s AND status = 'Pending'
        """, (new_status, approved_by, disposal_id))

        if cursor.rowcount == 0:
            conn.rollback()
            return False, "Disposal request not found or already processed."

        # 2. If Approved, mark asset as Disposed
        if new_status == 'Approved':
            cursor.execute("SELECT asset_id FROM asset_disposals WHERE disposal_id = %s", (disposal_id,))
            disp = cursor.fetchone()
            if disp:
                cursor.execute("UPDATE assets SET lifecycle_status = 'Disposed' WHERE asset_id = %s",
                               (disp["asset_id"],))

        conn.commit()
        return True, f"Disposal {new_status}. Asset has been retired." if new_status == 'Approved' else f"Disposal {new_status}."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

def get_maintenance_requests_for_asset(asset_id):
    """Fetches maintenance history for a specific asset."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT request_id, issue_description, priority, status, created_at, resolved_at
            FROM maintenance_requests 
            WHERE asset_id = %s 
            ORDER BY created_at DESC
        """, (asset_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()