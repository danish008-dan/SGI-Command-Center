# database/hr_queries.py
from database.connection import get_connection
from utils.password import hash_password
import calendar


def get_hr_dashboard_stats():
    conn = get_connection()
    if conn is None: return {"total": 0, "active": 0, "probation": 0, "exits": 0, "pending_revisions": 0,
                             "paid_payroll": 0, "total_salary_cost": 0, "employees_paid": 0, "recent_employees": []}
    try:
        cursor = conn.cursor()

        # Employee Stats
        cursor.execute("SELECT COUNT(*) as c FROM employees")
        total = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM employees WHERE status = 'Active'")
        active = cursor.fetchone()["c"]
        cursor.execute(
            "SELECT COUNT(*) as c FROM employees WHERE employment_type = 'Probationary' AND status = 'Active'")
        probation = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) as c FROM exit_clearances WHERE status = 'Pending'")
        exits = cursor.fetchone()["c"]

        # Payroll Stats
        cursor.execute("SELECT COUNT(*) as c FROM salary_revisions WHERE status = 'Pending'")
        pending_revisions = cursor.fetchone()["c"]
        cursor.execute(
            "SELECT COUNT(*) as c, IFNULL(SUM(net_payable),0) as cost FROM payroll_runs WHERE status = 'Paid'")
        paid_data = cursor.fetchone()
        paid_payroll = paid_data["c"]
        total_salary_cost = float(paid_data["cost"])
        employees_paid = paid_data["c"]

        # Recent Employees
        cursor.execute("""
            SELECT u.full_name, e.designation, e.joining_date, e.status 
            FROM employees e 
            INNER JOIN users u ON e.user_id = u.user_id 
            ORDER BY e.created_at DESC LIMIT 5
        """)
        recent_employees = cursor.fetchall()

        return {
            "total": total, "active": active, "probation": probation, "exits": exits,
            "pending_revisions": pending_revisions, "paid_payroll": paid_payroll,
            "total_salary_cost": total_salary_cost, "employees_paid": employees_paid,
            "recent_employees": recent_employees
        }
    except Exception:
        return {"total": 0, "active": 0, "probation": 0, "exits": 0, "pending_revisions": 0, "paid_payroll": 0,
                "total_salary_cost": 0, "employees_paid": 0, "recent_employees": []}
    finally:
        conn.close()


def get_all_employees(search=None, department_id=None):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        sql = """
            SELECT e.employee_id, e.employee_code, e.designation, e.employment_type, e.status, e.joining_date,
                   u.full_name, u.email, u.mobile,
                   d.department_name
            FROM employees e
            INNER JOIN users u ON e.user_id = u.user_id
            LEFT JOIN departments d ON e.department_id = d.department_id
            WHERE 1=1
        """
        params = []
        if search:
            sql += " AND (u.full_name LIKE %s OR e.employee_code LIKE %s OR u.email LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        if department_id:
            sql += " AND e.department_id = %s"
            params.append(department_id)

        sql += " ORDER BY e.employee_id DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching employees:", e)
        return []
    finally:
        conn.close()


def add_employee_to_db(form_data, creator_id):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Check duplicate email
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (form_data['email'],))
        if cursor.fetchone():
            conn.rollback()
            return False, "This email is already registered."

        # 2. Insert into Users table
        encrypted_pw = hash_password(form_data['password']).decode()
        cursor.execute("""
            INSERT INTO users (full_name, email, mobile, password, role, department_id, status)
            VALUES (%s, %s, %s, %s, 'Staff', %s, 'Active')
        """, (form_data['name'], form_data['email'], form_data['mobile'], encrypted_pw,
              form_data.get('department_id') or None))

        user_id = cursor.lastrowid

        # 3. Insert into Employees table
        cursor.execute("""
            INSERT INTO employees (user_id, employee_code, department_id, designation, employment_type, joining_date, bank_account_number, bank_ifsc)
            VALUES (%s, 'TEMP', %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            form_data.get('department_id') or None,
            form_data['designation'],
            form_data.get('employment_type', 'Probationary'),
            form_data['joining_date'],
            form_data.get('bank_account'),
            form_data.get('bank_ifsc')
        ))

        emp_id = cursor.lastrowid

        # 4. Generate Employee Code (SGI-EMP-0001)
        emp_code = f"SGI-EMP-{str(emp_id).zfill(4)}"
        cursor.execute("UPDATE employees SET employee_code = %s WHERE employee_id = %s", (emp_code, emp_id))

        conn.commit()
        return True, f"Employee added successfully. Code: {emp_code}"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# Add to database/hr_queries.py

# ==========================================
# SALARY COMPONENTS & ASSIGNMENTS
# ==========================================

def get_salary_components():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM salary_components ORDER BY component_type, component_name")
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def get_employee_salary_assignments(employee_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sa.assignment_id, sa.amount, sa.effective_date, sc.component_name, sc.component_type
            FROM employee_salary_assignments sa
            INNER JOIN salary_components sc ON sa.component_id = sc.component_id
            WHERE sa.employee_id = %s AND sa.is_current = TRUE
            ORDER BY sc.component_type
        """, (employee_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def assign_salary_component(employee_id, component_id, amount, effective_date):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Expire current assignment for this component
        cursor.execute("""
            UPDATE employee_salary_assignments 
            SET is_current = FALSE 
            WHERE employee_id = %s AND component_id = %s
        """, (employee_id, component_id))

        # 2. Insert new assignment
        cursor.execute("""
            INSERT INTO employee_salary_assignments (employee_id, component_id, amount, effective_date, is_current)
            VALUES (%s, %s, %s, %s, TRUE)
        """, (employee_id, component_id, float(amount), effective_date))

        conn.commit()
        return True, "Salary component assigned successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


# ==========================================
# SALARY REVISIONS (WORKFLOW)
# ==========================================

def create_salary_revision(employee_id, component_id, new_amount, effective_date, reason, requested_by):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()

        # Get old amount
        cursor.execute("""
            SELECT amount FROM employee_salary_assignments 
            WHERE employee_id = %s AND component_id = %s AND is_current = TRUE
        """, (employee_id, component_id))
        old = cursor.fetchone()
        old_amount = float(old["amount"]) if old else 0

        cursor.execute("""
            INSERT INTO salary_revisions (employee_id, component_id, old_amount, new_amount, effective_date, reason, requested_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
        """, (employee_id, component_id, old_amount, float(new_amount), effective_date, reason, requested_by))
        conn.commit()
        return True, "Salary revision request submitted for approval."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_pending_salary_revisions():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.revision_id, r.old_amount, r.new_amount, r.effective_date, r.reason, r.created_at,
                   e.employee_code, u.full_name AS employee_name, sc.component_name,
                   req.full_name AS requester_name
            FROM salary_revisions r
            INNER JOIN employees e ON r.employee_id = e.employee_id
            INNER JOIN users u ON e.user_id = u.user_id
            INNER JOIN salary_components sc ON r.component_id = sc.component_id
            INNER JOIN users req ON r.requested_by = req.user_id
            WHERE r.status = 'Pending'
            ORDER BY r.created_at DESC
        """)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def process_salary_revision(revision_id, action, approved_by):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get revision details
        cursor.execute("SELECT * FROM salary_revisions WHERE revision_id = %s FOR UPDATE", (revision_id,))
        rev = cursor.fetchone()
        if not rev or rev["status"] != 'Pending':
            conn.rollback()
            return False, "Revision not found or already processed."

        new_status = 'Approved' if action == 'Approved' else 'Rejected'

        # 2. Update revision status
        cursor.execute("""
            UPDATE salary_revisions 
            SET status = %s, approved_by = %s 
            WHERE revision_id = %s
        """, (new_status, approved_by, revision_id))

        # 3. If approved, apply to employee assignments
        if new_status == 'Approved':
            # Expire old
            cursor.execute("""
                UPDATE employee_salary_assignments 
                SET is_current = FALSE 
                WHERE employee_id = %s AND component_id = %s
            """, (rev["employee_id"], rev["component_id"]))

            # Insert new
            cursor.execute("""
                INSERT INTO employee_salary_assignments (employee_id, component_id, amount, effective_date, is_current)
                VALUES (%s, %s, %s, %s, TRUE)
            """, (rev["employee_id"], rev["component_id"], rev["new_amount"], rev["effective_date"]))

        conn.commit()
        return True, f"Revision {new_status}."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

# ==========================================
# PAYROLL PERIODS & CALCULATION
# ==========================================

def get_payroll_periods():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payroll_periods ORDER BY year DESC, month DESC")
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def create_payroll_period(month, year):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO payroll_periods (month, year, status) VALUES (%s, %s, 'Open')", (month, year))
        conn.commit()
        return True, "Payroll period created."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def generate_payroll_for_period(period_id, prepared_by):
    """Calculates payroll for all active employees for a period."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        # 1. Get Period Details
        cursor.execute("SELECT * FROM payroll_periods WHERE period_id = %s", (period_id,))
        period = cursor.fetchone()
        if not period: return False, "Period not found."

        month = period["month"]
        year = period["year"]
        calendar_days = calendar.monthrange(year, month)[1]

        # 2. Get All Active Employees
        cursor.execute("SELECT * FROM employees WHERE status = 'Active'")
        employees = cursor.fetchall()

        if not employees:
            return False, "No active employees found."

        # 3. Get Active Salary Components
        cursor.execute("SELECT * FROM salary_components WHERE status = 'Active'")
        components = cursor.fetchall()

        # 4. Process each employee
        for emp in employees:
            # Check if payroll already exists
            cursor.execute("SELECT run_id FROM payroll_runs WHERE period_id = %s AND employee_id = %s",
                           (period_id, emp["employee_id"]))
            if cursor.fetchone():
                continue  # Skip if already generated

            gross_earnings = 0
            total_deductions = 0
            payable_days = calendar_days  # Default full month

            # Get current salary assignments
            cursor.execute("""
                SELECT sa.amount, sc.component_id, sc.component_name, sc.component_type, sc.calculation_type
                FROM employee_salary_assignments sa
                INNER JOIN salary_components sc ON sa.component_id = sc.component_id
                WHERE sa.employee_id = %s AND sa.is_current = TRUE
            """, (emp["employee_id"],))
            assignments = cursor.fetchall()

            for a in assignments:
                amount = float(a["amount"])
                # Proration for earnings
                if a["component_type"] == 'Earning':
                    daily_amt = amount / calendar_days
                    prorated_amt = daily_amt * payable_days
                    gross_earnings += prorated_amt
                # Skip deductions with Pending Configuration
                elif a["component_type"] == 'Deduction' and a["calculation_type"] == 'Pending Configuration':
                    continue

            net_payable = gross_earnings - total_deductions

            # 5. Create Payroll Run
            cursor.execute("""
                INSERT INTO payroll_runs (period_id, employee_id, gross_earnings, total_deductions, net_payable, calendar_days, payable_days, lwp_days, status, prepared_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 'Calculated', %s)
            """, (period_id, emp["employee_id"], gross_earnings, total_deductions, net_payable, calendar_days,
                  payable_days, prepared_by))

            run_id = cursor.lastrowid

            # 6. Create Payslip Items (Snapshot)
            for a in assignments:
                amount = float(a["amount"])
                if a["component_type"] == 'Earning':
                    daily_amt = amount / calendar_days
                    prorated_amt = daily_amt * payable_days
                    cursor.execute("""
                        INSERT INTO payslip_items (run_id, component_name, component_type, amount)
                        VALUES (%s, %s, %s, %s)
                    """, (run_id, a["component_name"], a["component_type"], prorated_amt))
                elif a["component_type"] == 'Deduction' and a["calculation_type"] == 'Pending Configuration':
                    cursor.execute("""
                        INSERT INTO payslip_items (run_id, component_name, component_type, amount)
                        VALUES (%s, %s, %s, 0)
                    """, (run_id, a["component_name"] + " (Pending Config)", a["component_type"], 0))

        # Update period status
        cursor.execute("UPDATE payroll_periods SET status = 'Processing' WHERE period_id = %s", (period_id,))

        conn.commit()
        return True, f"Payroll calculated successfully for {len(employees)} employees."
    except Exception as e:
        conn.rollback()
        print("Payroll calculation error:", e)
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()


def get_payroll_runs(period_id):
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pr.*, e.employee_code, u.full_name, e.designation
            FROM payroll_runs pr
            INNER JOIN employees e ON pr.employee_id = e.employee_id
            INNER JOIN users u ON e.user_id = u.user_id
            WHERE pr.period_id = %s
            ORDER BY u.full_name
        """, (period_id,))
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def update_payroll_run_status(run_id, new_status, user_id, user_role):
    """Updates payroll status with approval workflow logic."""
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM payroll_runs WHERE run_id = %s FOR UPDATE", (run_id,))
        run = cursor.fetchone()
        if not run:
            conn.rollback()
            return False, "Payroll run not found."

        current_status = run["status"]

        # Workflow Validation
        if new_status == 'Under Review' and current_status != 'Calculated':
            conn.rollback()
            return False, "Can only submit 'Calculated' runs for review."

        if new_status == 'Approved' and current_status != 'Under Review':
            conn.rollback()
            return False, "Can only approve 'Under Review' runs."

        # Separation of Duties: Preparer cannot approve
        if new_status == 'Approved' and run["prepared_by"] == user_id:
            conn.rollback()
            return False, "Security Error: You cannot approve a payroll run you prepared."

        if new_status == 'Approved':
            cursor.execute("UPDATE payroll_runs SET status = %s, approved_by = %s WHERE run_id = %s",
                           (new_status, user_id, run_id))
        else:
            cursor.execute("UPDATE payroll_runs SET status = %s WHERE run_id = %s", (new_status, run_id))

        conn.commit()
        return True, f"Payroll status updated to {new_status}."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()

def get_payslip_data(run_id):
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # Get Run Details
        cursor.execute("""
            SELECT pr.*, e.employee_code, e.designation, u.full_name, p.month, p.year
            FROM payroll_runs pr
            INNER JOIN employees e ON pr.employee_id = e.employee_id
            INNER JOIN users u ON e.user_id = u.user_id
            INNER JOIN payroll_periods p ON pr.period_id = p.period_id
            WHERE pr.run_id = %s
        """, (run_id,))
        run_data = cursor.fetchone()
        if not run_data: return None

        # Get Items
        cursor.execute("SELECT * FROM payslip_items WHERE run_id = %s", (run_id,))
        run_data["items"] = cursor.fetchall()

        return run_data
    except Exception:
        return None
    finally:
        conn.close()


# ==========================================
# EXIT & CLEARANCE
# ==========================================

def get_exit_requests():
    conn = get_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ec.*, e.employee_code, e.designation, u.full_name
            FROM exit_clearances ec
            INNER JOIN employees e ON ec.employee_id = e.employee_id
            INNER JOIN users u ON e.user_id = u.user_id
            ORDER BY ec.created_at DESC
        """)
        return cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()


def create_exit_request(employee_id, exit_type, last_working_day, reason):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO exit_clearances (employee_id, exit_type, last_working_day, reason, status)
            VALUES (%s, %s, %s, %s, 'Pending')
        """, (employee_id, exit_type, last_working_day, reason))
        conn.commit()
        return True, "Exit request submitted for clearance."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def process_exit_request(clearance_id, action, settlement_amount=0):
    conn = get_connection()
    if conn is None: return False, "DB Error"
    try:
        conn.autocommit(False)
        cursor = conn.cursor()

        new_status = 'Cleared' if action == 'Cleared' else 'Rejected'
        cursor.execute("""
            UPDATE exit_clearances 
            SET status = %s, final_settlement_amount = %s 
            WHERE clearance_id = %s AND status = 'Pending'
        """, (new_status, float(settlement_amount) if action == 'Cleared' else 0, clearance_id))

        if cursor.rowcount == 0:
            conn.rollback()
            return False, "Request not found or already processed."

        # If cleared, update employee status
        if new_status == 'Cleared':
            cursor.execute("SELECT employee_id FROM exit_clearances WHERE clearance_id = %s", (clearance_id,))
            req = cursor.fetchone()
            if req:
                cursor.execute("UPDATE employees SET status = 'Resigned' WHERE employee_id = %s", (req["employee_id"],))

        conn.commit()
        return True, f"Exit {new_status}. Employee status updated."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.autocommit(True)
        conn.close()