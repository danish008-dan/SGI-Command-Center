# routers/profile.py
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from utils.auth import get_current_user
from database.profile_queries import (
    get_full_profile, update_basic_info,
    update_student_info, update_teacher_info
)
from database.connection import get_connection
import shutil

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] == "Student":
        layout = "student/student_layout.html"
    elif user["role"] == "Teacher":
        layout = "teacher/teacher_layout.html"
    elif user["role"] == "HOD":
        layout = "hod/hod_layout.html"
    elif user["role"] == "Principal":
        layout = "principal/principal_layout.html"
    else:
        layout = "admin/admin_layout.html"

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "layout": layout
        }
    )


@router.get("/api/profile/details")
async def get_profile_details(user: dict = Depends(get_current_user)):
    """Returns all profile data for the logged-in user."""
    profile = get_full_profile(user["user_id"])
    if not profile:
        return JSONResponse({"error": "Profile not found"}, status_code=404)
    return profile


@router.post("/api/profile/update")
async def update_profile_details(
        request: Request,
        full_name: str = Form(...),
        mobile: str = Form(""),
        user: dict = Depends(get_current_user)
):
    """Updates basic info and delegates to role-specific updates."""
    form = await request.form()
    form_data = dict(form)

    update_basic_info(user["user_id"], full_name, mobile)

    if user["role"] == "Student":
        update_student_info(user["user_id"], form_data)
    elif user["role"] == "Teacher":
        update_teacher_info(user["user_id"], form_data)

    return JSONResponse({"success": True, "message": "Profile updated successfully!"})


@router.post("/api/profile/upload")
async def upload_profile_image(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        return JSONResponse({"success": False, "message": "Only JPG and PNG files are allowed."}, status_code=400)

    ext = file.filename.split(".")[-1]
    filename = f"user_{user['user_id']}.{ext}"
    file_path = f"static/images/{filename}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Failed to save file: {str(e)}"}, status_code=500)
    finally:
        file.file.close()

    conn = get_connection()
    if conn is None: return JSONResponse({"success": False, "message": "DB Error"}, status_code=500)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET profile_image = %s WHERE user_id = %s", (filename, user["user_id"]))
        conn.commit()
        return JSONResponse({"success": True, "message": "Profile picture updated!", "filename": filename})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        conn.close()