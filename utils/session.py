import jwt
from config import JWT_SECRET, JWT_ALGORITHM
from datetime import datetime, timedelta

def create_session(user):
    payload = {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
        "department_id": user.get("department_id"),
        "session_version": user["session_version"], # ADDED THIS
        "exp": datetime.utcnow() + timedelta(hours=8) # 8 hours expiry
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token