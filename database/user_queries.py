# database/user_queries.py
from database.connection import get_connection
from utils.password import hash_password

def create_user(name, email, mobile, password, role, department):
    conn = get_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        encrypted = hash_password(password)
        sql = """
        INSERT INTO users (full_name, email, mobile, password, role, department_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (name, email, mobile, encrypted.decode(), role, department))
        conn.commit()
        return True
    except Exception as e:
        print("Create User Error:", e)
        return False
    finally:
        conn.close()
def get_user_by_email(email):
    conn = get_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, full_name, email, mobile, password, role, department_id, status, profile_image, session_version, force_password_change
            FROM users 
            WHERE email = %s
        """, (email,))
        return cursor.fetchone()
    except Exception as e:
        print("Error fetching user:", e)
        return None
    finally:
        conn.close()