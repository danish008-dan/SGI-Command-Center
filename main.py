from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import (
    login, admin, student, asset,
    teacher, hod, principal, profile,
    hr, campus, docs
)

# 1. Initialize the FastAPI application
app = FastAPI(title="SGI Command Center")

# 2. Mount the static folder so HTML can access CSS, JS, and Images
app.mount("/static", StaticFiles(directory="static"), name="static")

# All Routers
app.include_router(login.router)
app.include_router(admin.router)
app.include_router(student.router)
app.include_router(teacher.router)
app.include_router(hod.router)
app.include_router(principal.router)
app.include_router(profile.router)
app.include_router(asset.router)
app.include_router(hr.router)
app.include_router(campus.router)
app.include_router(docs.router)


# 3. Tell FastAPI where our HTML templates are located
templates = Jinja2Templates(directory="templates")

# 4. Create the home route
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # This renders the index.html file and passes the request to it
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

# 5. Run the server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )


""""
admin email -- admin@sgi.com
admin pass -- admin123

principal email --> principal123@cms.com
principal pass  --> principal1234

HOD email --> hod1234@cms.com
HOD pass --> hod1234

teacher email --> info.agnhub123@gmail.com
teacher pass  --> agnhub@123

student email --> taleeb1234@gmail.com
student pass  --> taleeb1234
"""