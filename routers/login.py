# routers/login.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from database.user_queries import get_user_by_email
from utils.password import verify_password
from utils.session import create_session

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def show_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@router.post("/login")
async def process_login(request: Request, email: str = Form(...), password: str = Form(...)):
    # 1. Get user from database
    user = get_user_by_email(email)

    if user is None:
        return JSONResponse({"success": False, "message": "Invalid email or password."}, status_code=400)

    if user["status"] != "Active":
        return JSONResponse({"success": False, "message": "Your account is currently inactive."}, status_code=403)

    # 2. Verify password
    try:
        valid_password = verify_password(password, user["password"])
    except Exception as e:
        print("Password Verification Error:", e)
        valid_password = False

    if not valid_password:
        return JSONResponse({"success": False, "message": "Invalid email or password."}, status_code=400)

    # 3. Create JWT Session Token
    token = create_session(user)

    response = JSONResponse({
        "success": True,
        "message": f"Welcome {user['full_name']}!",
        "role": user["role"]
    })

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )

    return response