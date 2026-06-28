import sys
from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.exceptions import HTTPException as _StarletteHTTPException
from fastapi.responses import JSONResponse as _JSONResponse
import os
from dotenv import load_dotenv
import secrets

# Add current directory to sys.path
sys.path.append(str(Path(__file__).parent))

from core import auth
from core.logger_util import log_activity
from routers import courses, assignments, trainer

load_dotenv()

app = FastAPI(
    title="NTA Trainer Portal API",
    description="Backend API for NTA Trainer Portal.",
    version="1.0.0"
)

# CORS
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "https://academy.nta.eg,http://localhost:8006,http://127.0.0.1:8006"
).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Trace-ID"],
)


@app.exception_handler(_StarletteHTTPException)
async def _sanitize_http_exception(request, exc):
    detail = exc.detail
    if isinstance(getattr(exc, "status_code", 0), int) and exc.status_code >= 500 and os.getenv("NTA_DEBUG") != "1":
        print(f"[5xx] {request.method} {request.url.path}: {detail}")
        detail = "Internal server error"
    return _JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=getattr(exc, "headers", None))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    if any(path.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2"]):
        return await call_next(request)

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    response = await call_next(request)

    log_activity(
        category="PASSIVE",
        event_type="API_CALL" if path.startswith("/api/") else "PAGE_VIEW",
        ip_address=ip,
        user_agent=ua,
        request_path=path,
        status_code=response.status_code,
    )
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Trainer-only auth router (login only allows role=trainer)
app.include_router(auth.router)
# Courses (trainer needs to read their assigned courses + sessions)
app.include_router(courses.router)
# Assignments (trainer creates/grades)
app.include_router(assignments.router)
# Trainer-specific routes (view trainees, analytics, AI quiz)
app.include_router(trainer.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/index.html", status_code=307)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "trainer"}


class GuardedStaticFiles(StaticFiles):
    """Static server that refuses to expose backend source, .env, or dotfiles."""
    async def get_response(self, path, scope):
        from starlette.responses import PlainTextResponse as _PT
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] == "backend") or norm.endswith(".py") or any(s.startswith(".") for s in segs):
            return _PT("Not Found", status_code=404)
        return await super().get_response(path, scope)


class PrivateDataStaticFiles(StaticFiles):
    """Blocks PII / sensitive subdirectories from unauthenticated static access.
    Protected files (trainee docs, admin photos, uploads, exams) are served only
    through authenticated API routes, not this public mount."""

    _BLOCKED = {"trainees", "trainers", "admins", "admission", "uploads", "temp", "standard_exams", "log"}

    async def get_response(self, path, scope):
        from starlette.responses import PlainTextResponse as _PT
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] in self._BLOCKED) or any(s.startswith(".") for s in segs):
            return _PT("Not Found", status_code=404)
        return await super().get_response(path, scope)


# Serve the data folder (for profile photos, uploads, etc.)
data_path = Path(__file__).parent.parent.parent / "data"
if os.path.exists(data_path):
    app.mount("/data", PrivateDataStaticFiles(directory=str(data_path)), name="data")

# Serve the shared common/ assets (theme.css, theme.js, nta-dashboard.css, …) so
# /common/* references resolve like the other portals (was previously 404).
common_path = Path(__file__).parent.parent.parent / "common"
if os.path.exists(common_path):
    app.mount("/common", StaticFiles(directory=str(common_path)), name="common")

# Serve trainer frontend files
static_path = Path(__file__).parent.parent
app.mount("/", GuardedStaticFiles(directory=str(static_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)
