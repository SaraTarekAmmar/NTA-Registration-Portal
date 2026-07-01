import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import uuid
import time
from dotenv import load_dotenv

# Add current directory to sys.path for standalone portability
sys.path.append(str(Path(__file__).parent))

from core import auth
from core.logger_util import log_activity
from routers import admin, courses, chat, ai_services, exams, class_matrix, quiz_results, safe_reviews
from fastapi import Request

load_dotenv()

app = FastAPI(
    title="NTA Admin Portal API",
    description="Backend API for managing recruitment and courses.",
    version="1.0.0"
)

# CORS origins — env-driven so production can drop localhost (set ALLOWED_ORIGINS).
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "https://academy.nta.eg,https://reg.nta.eg,http://localhost:8001,http://localhost:8002"
).split(",") if o.strip()]

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
    if isinstance(getattr(exc, "status_code", 0), int) and exc.status_code >= 500 and os.getenv("NTA_DEBUG") != "1":
        print(f"[5xx] {request.method} {request.url.path}: {detail}")
        detail = "Internal server error"
    return _JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=getattr(exc, "headers", None))

from core.logger_util import log_activity, session_context, trace_context, get_traceback
from jose import jwt
from core.auth import SECRET_KEY, ALGORITHM

@app.middleware("http")
async def global_debugger_middleware(request: Request, call_next):
    # 1. Initialize Trace ID & Start Timing
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    trace_token = trace_context.set(trace_id)
    start_time = time.time()

    # 2. Extract Session ID (Security Context)
    auth_header = request.headers.get("Authorization")
    sid = None
    role = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            sid = payload.get("sid")
            role = payload.get("role")
        except Exception:
            pass

    session_token = session_context.set(sid)

    # 3. Capture Basic Info
    path = request.url.path
    is_static = any(path.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2"])
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")

    # 4. Handle Request
    try:
        response = await call_next(request)

        # 5. Post-Request Logging (Always On for APIs)
        if not is_static:
            duration_ms = int((time.time() - start_time) * 1000)

            category = "PASSIVE"
            event_type = "PAGE_VIEW"
            if path.startswith("/api/"):
                category = "ACTION"
                event_type = "API_CALL"

            log_activity(
                category=category,
                event_type=event_type,
                role=role,
                ip_address=ip,
                user_agent=ua,
                request_path=path,
                status_code=response.status_code,
                trace_id=trace_id,
                duration_ms=duration_ms,
                status="Logged"
            )

        return response

    except Exception as e:
        # 6. Critical Error Logging (Traceback & Payload)
        duration_ms = int((time.time() - start_time) * 1000)
        tb = get_traceback()

        log_activity(
            category="SYSTEM",
            event_type="UNHANDLED_EXCEPTION",
            level="CRITICAL",
            component="Backend",
            role=role,
            ip_address=ip,
            user_agent=ua,
            request_path=path,
            status_code=500,
            trace_id=trace_id,
            traceback=tb,
            status="Action Required",
            duration_ms=duration_ms
        )
        raise e
    finally:
        session_context.reset(session_token)
        trace_context.reset(trace_token)


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
app.include_router(auth.admin_router)
app.include_router(admin.router)
app.include_router(courses.router)
app.include_router(chat.router)
app.include_router(ai_services.router)
app.include_router(exams.router)
app.include_router(class_matrix.router)
app.include_router(quiz_results.router)
app.include_router(safe_reviews.router)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Simple liveness probe — returns 200 OK when the server is up."""
    return {"status": "ok", "service": "admin"}

# Send the bare root URL to the bundled landing page.
@app.get("/")
async def root():
    return RedirectResponse(url="/index.html", status_code=307)

# Serve the centralized data folder
class PrivateDataStaticFiles(StaticFiles):
    """Blocks PII / sensitive subdirectories from unauthenticated static access.
    Protected files (trainee docs, admin photos, uploads, exams) are served only
    through authenticated API routes, not this public mount."""

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

# Serve static files (HTML, CSS, JS) from the admin directory
# This allows opening http://localhost:8002/ directly
from starlette.responses import PlainTextResponse as _PlainTextResponse


class GuardedStaticFiles(StaticFiles):
    """Static server that refuses to expose backend source, .env, or dotfiles."""

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
    # Default to 8002 for standalone admin portal
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
