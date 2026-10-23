# create_hod.py
from database.connection import get_connection
from utils.password import hash_password


def create_hod():
    conn = get_connection()
    if conn is None:
        print("DB Connection failed")
        return

    try:
        cursor = conn.cursor()

        # 1. Check if HOD already exists
        cursor.execute("SELECT user_id FROM users WHERE email = 'hod@cms.com'")
        if cursor.fetchone():
            print("HOD already exists!")
            return

        # 2. Hash the password 'hod1234'
        hashed_pw = hash_password("hod1234").decode()

        # 3. Insert into users table (Assuming Computer Science is department_id 1)
        cursor.execute("""
            INSERT INTO users (full_name, email, mobile, password, role, department_id, status)
            VALUES ('Dilep Agarwal', 'hod1234@cms.com', '9999999999', %s, 'HOD', 1, 'Active')
        """, (hashed_pw,))

        user_id = cursor.lastrowid

        # 4. Insert into teachers table
        cursor.execute("""
            INSERT INTO teachers (user_id, designation, qualification, experience)
            VALUES (%s, 'Head of Department', 'Ph.D Computer Science', 15)
        """, (user_id,))

        conn.commit()
        print("HOD Created Successfully! Email: hod1234@cms.com | Password: hod1234")

    except Exception as e:
        print("Error creating HOD:", e)
    finally:
        conn.close()
