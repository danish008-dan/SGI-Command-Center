# database/fee_queries.py
from database.connection import get_connection
import random


# ==========================================
# ADMIN FEE QUERIES
# ==========================================

def get_fee_dashboard_stats():
    conn = get_connection()
    if conn is None: return {"collected": 0, "pending": 0, "today": 0}
    try:
        cursor = conn.cursor()
        # Total Collected
        cursor.execute("SELECT IFNULL(SUM(amount_paid), 0) as total FROM fee_payments")
        collected = float(cursor.fetchone()["total"])

        # Total Pending (Payable - Paid)
        cursor.execute("""
            SELECT IFNULL(SUM(sf.payable_fee - IFNULL(p.paid, 0)), 0) as pending
            FROM student_fees sf
            LEFT JOIN (SELECT student_fee_id, SUM(amount_paid) as paid FROM fee_payments GROUP BY student_fee_id) p 
            ON sf.student_fee_id = p.student_fee_id
        """)
        pending = float(cursor.fetchone()["pending"])

        # Today's Collection
        cursor.execute(
            "SELECT IFNULL(SUM(amount_paid), 0) as today FROM fee_payments WHERE DATE(payment_date) = CURDATE()")
        today = float(cursor.fetchone()["today"])

        return {"collected": collected, "pending": pending, "today": today}
    except Exception as e:
        print("Fee stats error:", e)
        return {"collected": 0, "pending": 0, "today": 0}
    finally:
        conn.close()




def get_all_fee_structures():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT fs.*, d.department_name 
            FROM fee_structure fs 
            INNER JOIN departments d ON fs.department_id = d.department_id
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


# Update add_fee_structure to include Academic Year and Duplicate Check
def add_fee_structure(form_data):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()

        # Check for duplicate structure (Same Dept, Sem, and Academic Year)
        cursor.execute("""
            SELECT fee_structure_id FROM fee_structure 
            WHERE department_id = %s AND semester = %s AND academic_year = %s
        """, (form_data['department_id'], form_data.get('semester'), form_data.get('academic_year')))
        if cursor.fetchone():
            return False, "Fee structure for this Dept/Sem/Year already exists."

        total = float(form_data['admission_fee']) + float(form_data['tuition_fee']) + float(
            form_data['examination_fee']) + float(form_data['lab_fee']) + float(form_data['library_fee']) + float(
            form_data['other_fee'])

        cursor.execute("""
            INSERT INTO fee_structure (department_id, course, semester, academic_year, admission_fee, tuition_fee, examination_fee, lab_fee, library_fee, other_fee, total_fee, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
        """, (
            form_data['department_id'], form_data.get('course'), form_data.get('semester'),
            form_data.get('academic_year'),
            form_data['admission_fee'], form_data['tuition_fee'], form_data['examination_fee'],
            form_data['lab_fee'], form_data['library_fee'], form_data['other_fee'], total
        ))
        conn.commit()
        return True, "Fee Structure added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# Update assign_fee_to_student to use Transaction Safety
def assign_fee_to_student(student_id, fee_structure_id, discount, scholarship, due_date):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)  # Start Transaction
        cursor = conn.cursor()

        # Check if already assigned (Lock row for update to prevent concurrent duplicate)
        cursor.execute("SELECT student_fee_id FROM student_fees WHERE student_id = %s FOR UPDATE", (student_id,))
        if cursor.fetchone():
            conn.rollback()
            return False, "Fee already assigned to this student."

        cursor.execute("SELECT total_fee FROM fee_structure WHERE fee_structure_id = %s", (fee_structure_id,))
        fs = cursor.fetchone()
        if not fs:
            conn.rollback()
            return False, "Fee structure not found."

        payable = float(fs["total_fee"]) - float(discount) - float(scholarship)

        cursor.execute("""
            INSERT INTO student_fees (student_id, fee_structure_id, total_fee, discount, scholarship, payable_fee, due_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
        """, (student_id, fee_structure_id, fs["total_fee"], discount, scholarship, payable, due_date))

        conn.commit()
        return True, "Fee assigned successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# NEW: Bulk Fee Assignment
def bulk_assign_fee_to_students(dept_id, sem, sec, fee_structure_id, discount, scholarship, due_date):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # Get Fee Structure
        cursor.execute("SELECT total_fee FROM fee_structure WHERE fee_structure_id = %s", (fee_structure_id,))
        fs = cursor.fetchone()
        if not fs:
            conn.rollback()
            return False, "Fee structure not found."

        payable = float(fs["total_fee"]) - float(discount) - float(scholarship)

        # Get students in scope who DON'T have a fee assigned yet
        cursor.execute("""
            SELECT s.student_id 
            FROM students s 
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE u.department_id = %s AND s.semester = %s AND s.section = %s
            AND s.student_id NOT IN (SELECT student_id FROM student_fees)
        """, (dept_id, sem, sec))
        students = cursor.fetchall()

        if not students:
            conn.rollback()
            return False, "No eligible students found (or all already have fees assigned)."

        count = 0
        for student in students:
            cursor.execute("""
                INSERT INTO student_fees (student_id, fee_structure_id, total_fee, discount, scholarship, payable_fee, due_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
            """, (student["student_id"], fee_structure_id, fs["total_fee"], discount, scholarship, payable, due_date))
            count += 1

        conn.commit()
        return True, f"Bulk fee assigned successfully to {count} students."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def get_student_fee_details_for_admin(student_id):
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = """
            SELECT sf.student_fee_id, sf.payable_fee, sf.status, 
                   IFNULL((SELECT SUM(amount_paid) FROM fee_payments WHERE student_fee_id = sf.student_fee_id), 0) as paid
            FROM student_fees sf
            WHERE sf.student_id = %s
        """
        cursor.execute(sql, (student_id,))
        return cursor.fetchone()
    except Exception:
        return None
    finally:
        conn.close()


def get_pending_fees():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT u.full_name, sf.payable_fee, 
                   (sf.payable_fee - IFNULL((SELECT SUM(amount_paid) FROM fee_payments WHERE student_fee_id = sf.student_fee_id), 0)) as balance
            FROM student_fees sf
            INNER JOIN students s ON sf.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            HAVING balance > 0
            ORDER BY balance DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


# ==========================================
# STUDENT FEE QUERIES
# ==========================================


def get_student_fee_portal(user_id):
    conn = get_connection()
    if conn is None:
        return None, []

    try:
        cursor = conn.cursor()

        # Select the most relevant fee record for the student's current profile.
        # Prefer matching department, current semester, and an active fee structure.
        # Use student_fee_id as a deterministic tie-breaker.
        cursor.execute("""
            SELECT
                sf.student_fee_id,
                sf.payable_fee,
                sf.due_date,
                sf.status,
                IFNULL(
                    (
                        SELECT SUM(fp.amount_paid)
                        FROM fee_payments fp
                        WHERE fp.student_fee_id = sf.student_fee_id
                    ),
                    0
                ) AS paid
            FROM student_fees sf
            INNER JOIN students s
                ON sf.student_id = s.student_id
            LEFT JOIN users u
                ON s.user_id = u.user_id
            LEFT JOIN fee_structure fs
                ON sf.fee_structure_id = fs.fee_structure_id
            WHERE s.user_id = %s
            ORDER BY
                (fs.department_id = u.department_id) DESC,
                (fs.semester = s.semester) DESC,
                (fs.status = 'Active') DESC,
                sf.student_fee_id DESC
            LIMIT 1
        """, (user_id,))

        fee_summary = cursor.fetchone()

        if not fee_summary:
            return None, []

        # Payment history must belong to the exact fee record selected above.
        cursor.execute("""
            SELECT
                payment_id,
                receipt_number,
                payment_date,
                amount_paid,
                payment_mode
            FROM fee_payments
            WHERE student_fee_id = %s
            ORDER BY payment_date DESC, payment_id DESC
        """, (fee_summary["student_fee_id"],))

        history = cursor.fetchall()

        return fee_summary, history

    except Exception as e:
        print("Portal error:", e)
        return None, []

    finally:
        conn.close()


# ==========================================
# ONLINE PAYMENT QUERIES
# ==========================================

def create_payment_transaction(student_fee_id, amount, payment_mode, user_id):
    """Creates a pending transaction before sending to gateway."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        ref = "TXN" + str(random.randint(100000, 999999))
        cursor.execute("""
            INSERT INTO payment_transactions (payment_reference, student_fee_id, gateway, payment_mode, amount, payment_status)
            VALUES (%s, %s, 'Simulated', %s, %s, 'Pending')
        """, (ref, student_fee_id, payment_mode, amount))
        txn_id = cursor.lastrowid

        # Audit Log
        cursor.execute(
            "INSERT INTO payment_audit (transaction_id, action, performed_by, remarks) VALUES (%s, 'Created', %s, 'Payment initiated')",
            (txn_id, user_id))
        conn.commit()
        return txn_id
    except Exception as e:
        print("Error creating txn:", e)
        return None
    finally:
        conn.close()


def save_fee_payment(student_fee_id, amount, mode, txn_id, remarks, collected_by):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)  # Use transaction
        cursor = conn.cursor()

        # 1. Lock the student fee record and validate current balance
        cursor.execute("SELECT payable_fee FROM student_fees WHERE student_fee_id = %s FOR UPDATE", (student_fee_id,))
        sf = cursor.fetchone()
        if not sf:
            conn.rollback()
            return False, "Fee record not found."

        cursor.execute("SELECT IFNULL(SUM(amount_paid), 0) as total_paid FROM fee_payments WHERE student_fee_id = %s",
                       (student_fee_id,))
        paid = float(cursor.fetchone()["total_paid"])

        # 2. Prevent Overpayments
        if float(amount) <= 0:
            conn.rollback()
            return False, "Amount must be greater than 0."
        if (paid + float(amount)) > float(sf["payable_fee"]):
            conn.rollback()
            return False, f"Amount exceeds pending balance. Current balance: {float(sf['payable_fee']) - paid}"

        # 3. Insert Payment with temporary receipt
        cursor.execute("""
            INSERT INTO fee_payments (student_fee_id, receipt_number, payment_mode, amount_paid, transaction_id, remarks, collected_by)
            VALUES (%s, 'TEMP', %s, %s, %s, %s, %s)
        """, (student_fee_id, mode, amount, txn_id, remarks, collected_by))

        payment_id = cursor.lastrowid

        # 4. Generate Concurrency-Safe Receipt Number
        receipt = "RC" + str(payment_id).zfill(6)
        cursor.execute("UPDATE fee_payments SET receipt_number = %s WHERE payment_id = %s", (receipt, payment_id))

        # 5. Update Fee Status
        new_paid = paid + float(amount)
        new_status = 'Partial'
        if new_paid >= float(sf["payable_fee"]): new_status = 'Paid'
        cursor.execute("UPDATE student_fees SET status = %s WHERE student_fee_id = %s", (new_status, student_fee_id))

        conn.commit()
        return True, f"Payment saved successfully. Receipt No: {receipt}"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def verify_and_save_transaction(transaction_id, gateway_txn_id, user_id):
    """Simulates gateway success callback, verifies, and updates DB safely."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get Transaction (Lock it)
        cursor.execute("SELECT * FROM payment_transactions WHERE transaction_id = %s FOR UPDATE", (transaction_id,))
        txn = cursor.fetchone()
        if not txn:
            conn.rollback()
            return False, "Transaction not found"
        if txn["payment_status"] != "Pending":
            conn.rollback()
            return False, "Transaction already processed"

        # 2. Update Transaction to Success
        cursor.execute("""
            UPDATE payment_transactions 
            SET payment_status = 'Success', gateway_transaction_id = %s, gateway_response = 'Payment Captured (Simulated)' 
            WHERE transaction_id = %s
        """, (gateway_txn_id, transaction_id))

        # 3. Validate Balance before posting payment
        cursor.execute("SELECT payable_fee FROM student_fees WHERE student_fee_id = %s FOR UPDATE",
                       (txn["student_fee_id"],))
        sf = cursor.fetchone()
        cursor.execute("SELECT IFNULL(SUM(amount_paid), 0) as total_paid FROM fee_payments WHERE student_fee_id = %s",
                       (txn["student_fee_id"],))
        paid = float(cursor.fetchone()["total_paid"])

        if (paid + float(txn["amount"])) > float(sf["payable_fee"]):
            conn.rollback()
            return False, "Online payment exceeds pending balance. Reverted."

        # 4. Insert Payment with temporary receipt
        cursor.execute("""
            INSERT INTO fee_payments (student_fee_id, receipt_number, payment_mode, amount_paid, transaction_id, remarks, collected_by)
            VALUES (%s, 'TEMP', %s, %s, %s, 'Online Payment (Simulated)', %s)
        """, (txn["student_fee_id"], txn["payment_mode"], txn["amount"], gateway_txn_id, user_id))

        payment_id = cursor.lastrowid

        # 5. Generate Safe Receipt
        receipt = "RC" + str(payment_id).zfill(6)
        cursor.execute("UPDATE fee_payments SET receipt_number = %s WHERE payment_id = %s", (receipt, payment_id))

        # 6. Update Fee Status
        new_paid = paid + float(txn["amount"])
        new_status = 'Partial' if new_paid < float(sf["payable_fee"]) else 'Paid'
        cursor.execute("UPDATE student_fees SET status = %s WHERE student_fee_id = %s",
                       (new_status, txn["student_fee_id"]))

        # 7. Audit Logs
        cursor.execute(
            "INSERT INTO payment_audit (transaction_id, action, performed_by, remarks) VALUES (%s, 'Gateway Success', %s, 'Payment verified')",
            (transaction_id, user_id))
        cursor.execute(
            "INSERT INTO payment_audit (transaction_id, action, performed_by, remarks) VALUES (%s, 'Receipt Generated', %s, %s)",
            (transaction_id, user_id, receipt))

        conn.commit()
        return True, f"Payment Successful! Receipt No: {receipt}"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def get_payment_details_for_receipt(payment_id):
    """Fetches all details required to generate a PDF receipt."""
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # FIXED: Added fp.student_fee_id to the SELECT list
        sql = """
            SELECT fp.payment_id, fp.student_fee_id, fp.receipt_number, fp.payment_date, fp.payment_mode, fp.amount_paid, fp.transaction_id,
                   u.full_name, s.enrollment_no, d.department_name, s.semester
            FROM fee_payments fp
            INNER JOIN student_fees sf ON fp.student_fee_id = sf.student_fee_id
            INNER JOIN students s ON sf.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE fp.payment_id = %s
        """
        cursor.execute(sql, (payment_id,))
        return cursor.fetchone()
    except Exception as e:
        print("Error fetching receipt data:", e)
        return None
    finally:
        conn.close()

# ==========================================
# PHASE 4: SCHOLARSHIPS & CONCESSIONS
# ==========================================

def request_concession(student_fee_id, amount, reason, requested_by):
    """Creates a concession request without changing the actual balance."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT payable_fee FROM student_fees WHERE student_fee_id = %s", (student_fee_id,))
        sf = cursor.fetchone()
        if not sf: return False, "Student fee record not found."
        if float(amount) > float(sf["payable_fee"]): return False, "Concession amount exceeds payable fee."

        cursor.execute("""
            INSERT INTO concession_requests (student_fee_id, amount, reason, requested_by)
            VALUES (%s, %s, %s, %s)
        """, (student_fee_id, amount, reason, requested_by))
        conn.commit()
        return True, "Concession request submitted for approval."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_pending_concessions():
    """Fetches pending concessions for the Approver (e.g., Principal)."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cr.request_id, cr.amount, cr.reason, cr.requested_at,
                   u.full_name AS student_name, s.enrollment_no, sf.payable_fee
            FROM concession_requests cr
            INNER JOIN student_fees sf ON cr.student_fee_id = sf.student_fee_id
            INNER JOIN students s ON sf.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE cr.status = 'Pending'
            ORDER BY cr.requested_at DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching concessions:", e)
        return []
    finally:
        conn.close()


def process_concession(request_id, action, approved_by, rejection_reason=None):
    """Approves or Rejects a concession. If approved, updates the student's balance."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get Request Details
        cursor.execute("SELECT * FROM concession_requests WHERE request_id = %s FOR UPDATE", (request_id,))
        req = cursor.fetchone()
        if not req:
            conn.rollback()
            return False, "Request not found."
        if req["status"] != "Pending":
            conn.rollback()
            return False, "Request already processed."

        # 2. Process Approval
        if action == "Approved":
            # Lock the student_fees record and update balance
            cursor.execute("SELECT payable_fee, discount FROM student_fees WHERE student_fee_id = %s FOR UPDATE",
                           (req["student_fee_id"],))
            sf = cursor.fetchone()
            if not sf:
                conn.rollback()
                return False, "Student fee record missing."

            new_payable = float(sf["payable_fee"]) - float(req["amount"])
            new_discount = float(sf["discount"]) + float(req["amount"])

            cursor.execute("""
                UPDATE student_fees 
                SET payable_fee = %s, discount = %s 
                WHERE student_fee_id = %s
            """, (new_payable, new_discount, req["student_fee_id"]))

            # Update Request Status
            cursor.execute("""
                UPDATE concession_requests 
                SET status = 'Approved', approved_by = %s, approved_at = NOW() 
                WHERE request_id = %s
            """, (approved_by, request_id))

        # 3. Process Rejection
        elif action == "Rejected":
            cursor.execute("""
                UPDATE concession_requests 
                SET status = 'Rejected', approved_by = %s, approved_at = NOW() 
                WHERE request_id = %s
            """, (approved_by, request_id))
        else:
            conn.rollback()
            return False, "Invalid action."

        conn.commit()
        return True, f"Concession {action} successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# ==========================================
# PHASE 5: REPORTS, REFUNDS & RECONCILIATION
# ==========================================

def process_refund(payment_id, refund_amount, reason, processed_by):
    """Processes an internal refund by creating a reversal entry without deleting original history."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get Original Payment Details
        cursor.execute("SELECT * FROM fee_payments WHERE payment_id = %s FOR UPDATE", (payment_id,))
        payment = cursor.fetchone()
        if not payment:
            conn.rollback()
            return False, "Original payment not found."

        # 2. Validate Refund Amount
        if float(refund_amount) <= 0 or float(refund_amount) > float(payment["amount_paid"]):
            conn.rollback()
            return False, "Invalid refund amount. Must be less than or equal to original payment."

        # 3. Create Reversal Entry in fee_payments (Negative Amount)
        reversal_receipt = "REV" + str(payment_id).zfill(6)
        cursor.execute("""
            INSERT INTO fee_payments (student_fee_id, receipt_number, payment_mode, amount_paid, transaction_id, remarks, collected_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            payment["student_fee_id"],
            reversal_receipt,
            payment["payment_mode"],
            -float(refund_amount),  # NEGATIVE AMOUNT for reversal
            payment["transaction_id"],
            f"Refund for {payment['receipt_number']}: {reason}",
            processed_by
        ))

        # 4. Log in Refunds Table
        cursor.execute("""
            INSERT INTO refunds (payment_id, student_fee_id, refund_amount, reason, processed_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (payment_id, payment["student_fee_id"], refund_amount, reason, processed_by))

        # 5. Update Student Fee Status (Back to Partial/Pending)
        cursor.execute("SELECT payable_fee FROM student_fees WHERE student_fee_id = %s FOR UPDATE",
                       (payment["student_fee_id"],))
        sf = cursor.fetchone()
        cursor.execute("SELECT IFNULL(SUM(amount_paid), 0) as total_paid FROM fee_payments WHERE student_fee_id = %s",
                       (payment["student_fee_id"],))
        new_paid = float(cursor.fetchone()["total_paid"])

        new_status = 'Partial' if new_paid < float(sf["payable_fee"]) else 'Paid'
        # If refund makes balance 0, it's Partial. If it was already Partial, remains Partial.
        if new_paid == 0:
            new_status = 'Pending'

        cursor.execute("UPDATE student_fees SET status = %s WHERE student_fee_id = %s",
                       (new_status, payment["student_fee_id"]))

        conn.commit()
        return True, f"Refund processed successfully. Reversal Receipt: {reversal_receipt}"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def get_daily_collection_report(date_str=None):
    """Fetches daily collection grouped by payment mode."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # If no date provided, use today
        if not date_str:
            date_str = "CURDATE()"
        else:
            date_str = f"'{date_str}'"

        cursor.execute(f"""
            SELECT payment_mode, COUNT(*) as count, SUM(amount_paid) as total
            FROM fee_payments
            WHERE DATE(payment_date) = {date_str} AND amount_paid > 0
            GROUP BY payment_mode
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Daily report error:", e)
        return []
    finally:
        conn.close()


def get_refund_register():
    """Fetches all refunds for the register."""
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.refund_id, r.refund_amount, r.reason, r.processed_at,
                   u.full_name AS student_name, fp.receipt_number AS original_receipt
            FROM refunds r
            INNER JOIN fee_payments fp ON r.payment_id = fp.payment_id
            INNER JOIN student_fees sf ON r.student_fee_id = sf.student_fee_id
            INNER JOIN students s ON sf.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            ORDER BY r.processed_at DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Refund register error:", e)
        return []
    finally:
        conn.close()