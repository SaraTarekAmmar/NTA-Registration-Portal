"""
Coordinator Portal — FastAPI Application
Handles attendance tracking and permission/excuse management.
Port: 8005
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

app = FastAPI(
    title="NTA Coordinator Portal",
    description="Coordinator attendance and permissions management",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────
# Env-driven so production can drop localhost (set ALLOWED_ORIGINS).
origins = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "https://academy.nta.eg,http://localhost:8005,http://127.0.0.1:8005,http://localhost:8002,http://localhost:8004"
).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Trace-ID"],
)


# Sanitize 5xx responses — log the real error server-side, return a generic
# message to clients (set NTA_DEBUG=1 to surface details in non-prod).
from starlette.exceptions import HTTPException as _StarletteHTTPException
from fastapi.responses import JSONResponse as _JSONResponse


@app.exception_handler(_StarletteHTTPException)
async def _sanitize_http_exception(request, exc):
    detail = exc.detail
    if isinstance(getattr(exc, "status_code", 0), int) and exc.status_code >= 500 and os.getenv("NTA_DEBUG") != "1":
        print(f"[5xx] {request.method} {request.url.path}: {detail}")
        detail = "Internal server error"
    return _JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=getattr(exc, "headers", None))

# ── Routers ──────────────────────────────────────────────────────────
from routers import auth, attendance, permissions
from fastapi import Request

app.include_router(auth.router)
app.include_router(attendance.router)
app.include_router(permissions.router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Inject security headers on every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.middleware("http")
async def limit_json_body(request: Request, call_next):
    """Reject JSON POST bodies exceeding 1 MB to prevent resource-exhaustion attacks."""
    if request.method in ("POST", "PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1_048_576:  # 1 MB
            return _JSONResponse(
                status_code=413,
                content={"detail": "حجم الطلب كبير جدًا. الحد الأقصى 1 ميجابايت."},
            )
    return await call_next(request)

# ── Static Files ─────────────────────────────────────────────────────
# Mount coordinator frontend (coordinator/ directory, one level up from backend/)
COORDINATOR_DIR = Path(__file__).parent.parent
COMMON_DIR = COORDINATOR_DIR.parent / "common"
ADMIN_HEADER_DIR = COORDINATOR_DIR.parent / "admin" / "header"
IMAGES_DIR = COORDINATOR_DIR.parent / "admin" / "images"
DATA_DIR = COORDINATOR_DIR.parent / "data"

# Serve common assets
if COMMON_DIR.exists():
    app.mount("/common", StaticFiles(directory=str(COMMON_DIR)), name="common")

# Serve admin header CSS/JS (shared sidebar styles)
if ADMIN_HEADER_DIR.exists():
    app.mount("/admin/header", StaticFiles(directory=str(ADMIN_HEADER_DIR)), name="admin_header")

# Serve images
if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

class PrivateDataStaticFiles(StaticFiles):
    """Blocks PII / sensitive subdirectories from unauthenticated static access.
    Attendance photos are served via the authenticated /api/coordinator/attendance
    /photo route, not this public mount."""

    _BLOCKED = {"trainees", "trainers", "admins", "admission", "uploads", "temp", "standard_exams", "log"}

    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] in self._BLOCKED) or any(s.startswith(".") for s in segs):
            from starlette.responses import PlainTextResponse
            return PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


# Serve data (non-sensitive assets only; PII subdirs blocked)
if DATA_DIR.exists():
    app.mount("/data", PrivateDataStaticFiles(directory=str(DATA_DIR)), name="data")

# Serve coordinator frontend as root (must be last)
from starlette.responses import PlainTextResponse as _PlainTextResponse


class GuardedStaticFiles(StaticFiles):
    """Static server that refuses to expose backend source, .env, or dotfiles."""

    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] == "backend") or norm.endswith(".py") or any(s.startswith(".") for s in segs):
            return _PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


app.mount("/", GuardedStaticFiles(directory=str(COORDINATOR_DIR), html=True), name="coordinator_frontend")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "coordinator"}
