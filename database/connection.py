# database/connection.py
import pymysql
from config import HOST, USER, PASSWORD, DATABASE, READ_HOST, READ_USER, READ_PASSWORD, READ_DATABASE

def get_connection():
    """Connects to the MySQL database using Read/Write credentials."""
    try:
        connection = pymysql.connect(
            host=HOST, user=USER, password=PASSWORD, database=DATABASE,
            cursorclass=pymysql.cursors.DictCursor, autocommit=True
        )
        return connection
    except Exception as e:
        print("Database Connection Error:", e)
        return None

def get_read_connection():
    """Connects to the MySQL database using strict Read-Only credentials (Defense-in-Depth for AI)."""
    try:
        connection = pymysql.connect(
            host=READ_HOST, user=READ_USER, password=READ_PASSWORD, database=READ_DATABASE,
            cursorclass=pymysql.cursors.DictCursor, autocommit=True
        )
        return connection
    except Exception as e:
        print("Read-Only DB Connection Error:", e)
        return None