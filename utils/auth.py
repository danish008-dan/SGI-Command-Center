# utils/auth.py
from fastapi import Cookie, HTTPException, Depends
import jwt
from config import JWT_SECRET, JWT_ALGORITHM


def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # SESSION REVOCATION CHECK
        # Query DB to verify session_version and status
        from database.connection import get_connection
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, session_version FROM users WHERE user_id = %s", (payload.get("user_id"),))
            db_user = cursor.fetchone()
            conn.close()

            if not db_user:
                raise HTTPException(status_code=401, detail="User not found")
            if db_user["status"] == 'Inactive':
                raise HTTPException(status_code=403, detail="Account deactivated. Access revoked.")
            if db_user["session_version"] != payload.get("session_version", 0):
                raise HTTPException(status_code=401, detail="Session expired or revoked. Please login again.")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again.")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Token")


class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = Depends(get_current_user)):
        if user["role"] not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Access Denied. You are not authorized to view this page.")
        return user


class PermissionChecker:
    """Granular Permission Checker for RBAC."""

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, user: dict = Depends(get_current_user)):
        from database.connection import get_connection
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            # Check if user's role has the required permission
            cursor.execute("""
                SELECT 1 FROM role_permissions rp 
                INNER JOIN permissions p ON rp.permission_id = p.permission_id
                WHERE rp.role = %s AND p.permission_name = %s
            """, (user["role"], self.required_permission))

            if not cursor.fetchone():
                conn.close()
                raise HTTPException(status_code=403,
                                    detail=f"Access Denied. Missing permission: {self.required_permission}")
            conn.close()
        else:
            # Fallback if DB fails: allow Admin only
            if user["role"] != "Admin":
                raise HTTPException(status_code=403, detail="Access Denied.")
        return user