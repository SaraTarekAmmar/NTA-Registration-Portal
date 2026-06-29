import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import secrets
from dotenv import load_dotenv

# Add current directory to sys.path for standalone portability
sys.path.append(str(Path(__file__).parent))

from core.logger_util import log_activity
from routers import lookups, ai_services, progress

load_dotenv()

app = FastAPI(
    title="NTA Registration Portal API",
    description="Backend API for managing standalone registrations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://academy.nta.eg",
        "https://reg.nta.eg",
        "http://localhost:7770",   # front page portal
        "http://localhost:7771",   # trainee portal
        "http://localhost:7772",   # trainer portal
        "http://localhost:7775",   # registration portal (self)
        "http://localhost:8001",   # editor portal
        "http://localhost:8002",   # admin portal
        "http://localhost:8003",   # superadmin
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|null",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            samesite="lax",
            httponly=False  # Must be readable by Javascript
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


app.include_router(lookups.router)
app.include_router(ai_services.router)
app.include_router(progress.router)

@app.post("/api/debug/log")
async def debug_log(request: Request):
    data = await request.json()
    print("\n[FRONTEND ERROR LOG]:", data.get("error"), "\n[STACK]:", data.get("stack"), "\n")
    return {"status": "ok"}

# Serve the centralized data folder (optional, if needed by lookups)
data_path = Path(__file__).parent.parent.parent / "data"
if os.path.exists(data_path):
    app.mount("/data", StaticFiles(directory=str(data_path)), name="data")

# Serve static files (HTML, CSS, JS) from the registration directory
static_path = Path(__file__).parent.parent
app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Default to 7775 for standalone registration portal
    port = int(os.getenv("PORT", 7775))
    uvicorn.run(app, host="0.0.0.0", port=port)
