import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Add current directory to sys.path for standalone portability
sys.path.append(str(Path(__file__).parent))

from core import auth
from core.logger_util import log_activity
from routers import trainees, courses, chat, skills, exams, ai_services, permissions, lookups, assignments, trainer, ai_proxy, admin, reg_steps, registration_flow
from fastapi import Request

load_dotenv()

app = FastAPI(
    title="NTA Trainee Portal API",
    description="Backend API for managing trainee registrations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://academy.nta.eg",
        "https://reg.nta.eg",
        "http://localhost:8001",
        "http://localhost:8002"
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Trace-ID"],
)

import secrets

@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    token = request.cookies.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        
    response = await call_next(request)
    
    if not request.cookies.get("csrf_token"):
        response.set_cookie(
            key="csrf_token",
            value=token,
            samesite="strict",
            httponly=False  # Must be readable by JS for the double-submit cookie pattern
        )
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Skip logging for static assets like css, images, js to avoid noise
    path = request.url.path
    if any(path.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2"]):
        return await call_next(request)

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    response = await call_next(request)
    
    # Log HTML visits and API calls
    category = "PASSIVE"
    event_type = "PAGE_VIEW"
    
    if path.startswith("/api/"):
        event_type = "API_CALL"
    
    log_activity(
        category=category,
        event_type=event_type,
        ip_address=ip,
        user_agent=ua,
        request_path=path,
        status_code=response.status_code
    )
    
    return response

# In standalone mode, auth router is local
app.include_router(auth.router)
app.include_router(trainees.router)
app.include_router(courses.router)
app.include_router(chat.router)
app.include_router(skills.router)
app.include_router(ai_services.router)
app.include_router(ai_proxy.router)
app.include_router(permissions.router)
app.include_router(lookups.router)
app.include_router(exams.router)
app.include_router(assignments.router)
app.include_router(trainer.router)
app.include_router(admin.router)
app.include_router(reg_steps.router)
app.include_router(registration_flow.router)



@app.post("/api/debug/log")
async def debug_log(request: Request):
    data = await request.json()
    print("\n[FRONTEND ERROR LOG]:", data.get("error"), "\n[STACK]:", data.get("stack"), "\n")
    return {"status": "ok"}


# Serve the centralized data folder
data_path = Path(__file__).parent.parent.parent / "data"
if os.path.exists(data_path):
    app.mount("/data", StaticFiles(directory=str(data_path)), name="data")

# Serve static files (HTML, CSS, JS) from the user directory
# This allows opening http://localhost:8001/ directly
static_path = Path(__file__).parent.parent
app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Default to 8001 for standalone user portal
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
