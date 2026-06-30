import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
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


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.middleware("http")
async def limit_json_body(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1_048_576:
            return JSONResponse(
                status_code=413,
                content={"detail": "حجم الطلب كبير جدًا. الحد الأقصى 1 ميجابايت."},
            )
    return await call_next(request)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "registration"}

@app.post("/api/debug/log")
async def debug_log(request: Request):
    data = await request.json()
    print("\n[FRONTEND ERROR LOG]:", data.get("error"), "\n[STACK]:", data.get("stack"), "\n")
    return {"status": "ok"}

# Serve the centralized data folder (optional, if needed by lookups)
class PrivateDataStaticFiles(StaticFiles):
    _BLOCKED = {"trainees", "trainers", "admins", "admission", "uploads", "temp", "standard_exams", "log"}

    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] in self._BLOCKED) or any(s.startswith(".") for s in segs):
            from starlette.responses import PlainTextResponse
            return PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


data_path = Path(__file__).parent.parent.parent / "data"
if os.path.exists(data_path):
    app.mount("/data", PrivateDataStaticFiles(directory=str(data_path)), name="data")

# Serve static files (HTML, CSS, JS) from the registration directory
from starlette.responses import PlainTextResponse as _PlainTextResponse


class GuardedStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] == "backend") or norm.endswith(".py") or any(s.startswith(".") for s in segs):
            return _PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


static_path = Path(__file__).parent.parent
app.mount("/", GuardedStaticFiles(directory=str(static_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Default to 7775 for standalone registration portal
    port = int(os.getenv("PORT", 7775))
    uvicorn.run(app, host="0.0.0.0", port=port)
