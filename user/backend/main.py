import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse
import os
from dotenv import load_dotenv
import secrets

# Add current directory to sys.path for standalone portability
sys.path.append(str(Path(__file__).parent))

from core import auth
from core.logger_util import log_activity
from routers import (
    trainees,
    courses,
    chat,
    skills,
    exams,
    ai_services,
    permissions,
    lookups,
    assignments,
    trainer,
    ai_proxy,
    reg_steps,
    registration_flow,
    notifications,
    tickets,
)
from fastapi import Request, Depends

load_dotenv()

app = FastAPI(
    title="NTA Trainee Portal API",
    description="Backend API for managing trainee registrations.",
    version="1.0.0",
)

# CORS origins — env-driven so production can drop localhost (set ALLOWED_ORIGINS).
_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "https://academy.nta.eg,https://reg.nta.eg,http://localhost:7771,http://localhost:8002,http://localhost:8003,http://localhost:8004",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
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
    if (
        isinstance(getattr(exc, "status_code", 0), int)
        and exc.status_code >= 500
        and os.getenv("NTA_DEBUG") != "1"
    ):
        print(f"[5xx] {request.method} {request.url.path}: {detail}")
        detail = "Internal server error"
    return _JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers=getattr(exc, "headers", None),
    )


@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    token = request.cookies.get("csrf_token")
    should_create_cookie = not token
    if should_create_cookie:
        token = secrets.token_hex(32)

    unsafe_method = request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
    path = request.url.path

    # The public registration submit is the highest-risk browser form endpoint.
    # Require the double-submit token that registration.js sends from the csrf_token cookie.
    if unsafe_method and path == "/api/trainee/register":
        header_token = request.headers.get("X-CSRF-Token")
        if (
            request.cookies.get("csrf_token") is None
            or not header_token
            or header_token != request.cookies.get("csrf_token")
        ):
            response = JSONResponse(
                status_code=403,
                content={"detail": "Invalid or missing CSRF token"},
            )
            if should_create_cookie:
                response.set_cookie(
                    key="csrf_token",
                    value=token,
                    samesite="strict",
                    httponly=False,
                )
            return response

    response = await call_next(request)

    if should_create_cookie:
        response.set_cookie(
            key="csrf_token",
            value=token,
            samesite="strict",
            httponly=False,  # Must be readable by JS for the double-submit cookie pattern
        )
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Skip logging for static assets like css, images, js to avoid noise
    path = request.url.path
    if any(
        path.endswith(ext)
        for ext in [
            ".css",
            ".js",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".ico",
            ".woff",
            ".woff2",
        ]
    ):
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
        status_code=response.status_code,
    )

    return response


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
app.include_router(reg_steps.router)
app.include_router(registration_flow.router)
app.include_router(notifications.router)
app.include_router(tickets.router)


from fastapi.responses import RedirectResponse


@app.get("/")
async def root():
    return RedirectResponse(url="/index.html", status_code=307)


@app.get("/api/health")
async def health_check():
    """Simple liveness probe — returns 200 OK when the server is up."""
    return {"status": "ok", "service": "user"}


@app.post("/api/debug/log")
async def debug_log(
    request: Request, current_user: dict = Depends(auth.get_current_user)
):
    """Frontend error logger — requires a valid user JWT to prevent log injection abuse."""
    data = await request.json()
    user_id = current_user.get("id", "anon")
    print(
        f"\n[FRONTEND ERROR LOG] user={user_id} error={data.get('error')}\n[STACK]: {data.get('stack')}\n"
    )
    return {"status": "ok"}


# Serve the centralized data folder
class PrivateDataStaticFiles(StaticFiles):
    """Blocks PII / sensitive subdirectories from unauthenticated static access.
    Protected files (trainee docs, admin photos, uploads, exams) are served only
    through authenticated API routes, not this public mount."""

    _BLOCKED = {
        "trainees",
        "trainers",
        "admins",
        "admission",
        "uploads",
        "temp",
        "standard_exams",
        "log",
    }

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

# Serve static files (HTML, CSS, JS) from the user directory
# This allows opening http://localhost:8001/ directly
from starlette.responses import PlainTextResponse as _PlainTextResponse


class GuardedStaticFiles(StaticFiles):
    """Static server that refuses to expose backend source, .env, or dotfiles."""

    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (
            (segs and segs[0] == "backend")
            or norm.endswith(".py")
            or any(s.startswith(".") for s in segs)
        ):
            return _PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


static_path = Path(__file__).parent.parent
app.mount("/", GuardedStaticFiles(directory=str(static_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    # Default to 7771 to match run_system.py launcher
    port = int(os.getenv("PORT", 7771))
    uvicorn.run(app, host="0.0.0.0", port=port)
