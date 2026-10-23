# create_principal.py
from database.connection import get_connection
from utils.password import hash_password

def create_principal():
    conn = get_connection()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email = 'principal123@cms.com'")
        if cursor.fetchone():
            print("Principal already exists!")
            return

        hashed_pw = hash_password("principal1234").decode()

        # Principal is usually not tied to a single department (department_id = NULL)
        cursor.execute("""
            INSERT INTO users (full_name, email, mobile, password, role, department_id, status)
            VALUES ('Dr. Principal SGI', 'principal123@cms.com', '9999999999', %s, 'Principal', NULL, 'Active')
        """, (hashed_pw,))

        conn.commit()
        print("Principal Created Successfully! Email: principal123@cms.com | Password: principal1234")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()
