# config.py
from dotenv import load_dotenv
import os

# Load the environment variables
load_dotenv()

# Primary Database configuration (Read/Write)
HOST = os.getenv("DB_HOST")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
DATABASE = os.getenv("DB_NAME")

# Read-Only Database configuration (For AI Tools)
READ_HOST = os.getenv("DB_READ_HOST", HOST)
READ_USER = os.getenv("DB_READ_USER", USER)
READ_PASSWORD = os.getenv("DB_READ_PASSWORD", PASSWORD)
READ_DATABASE = os.getenv("DB_READ_DATABASE", DATABASE)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

# AI Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Institutional Policies
ATTENDANCE_THRESHOLD = 75.0  # Centralized attendance threshold