import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import uuid
import time
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))

from core import auth
from core.logger_util import log_activity, session_context, trace_context, get_traceback
from routers import auth as auth_router, courses, course_save, materials, sessions, flow_builder, tickets, front_manager
from jose import jwt
from core.auth import SECRET_KEY, ALGORITHM

load_dotenv()

app = FastAPI(
    title="NTA Editor Portal API",
    description="Backend API for the Editor Portal — course content management.",
    version="1.0.0"
)

# CORS origins — env-driven so production can drop localhost (set ALLOWED_ORIGINS).
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "https://academy.nta.eg,http://localhost:8004,http://localhost:8002"
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


@app.middleware("http")
async def global_debugger_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    trace_token = trace_context.set(trace_id)
    start_time = time.time()

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

    path = request.url.path
    is_static = any(path.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2"])
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")

    try:
        response = await call_next(request)

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
        duration_ms = int((time.time() - start_time) * 1000)
        tb = get_traceback()
        log_activity(
            category="SYSTEM",
            event_type="UNHANDLED_EXCEPTION",
            level="CRITICAL",
            component="EditorBackend",
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


app.include_router(auth_router.router)
app.include_router(course_save.router)
app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(sessions.router)
app.include_router(flow_builder.router)
app.include_router(tickets.router)
app.include_router(front_manager.router)


@app.get("/api/health")
async def health_check():
    """Simple liveness probe — returns 200 OK when the server is up."""
    return {"status": "ok", "service": "editor"}


@app.get("/")
async def root():
    return RedirectResponse(url="/index.html", status_code=307)


project_root = Path(__file__).parent.parent.parent


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


data_path = project_root / "data"
if os.path.exists(data_path):
    app.mount("/data", PrivateDataStaticFiles(directory=str(data_path)), name="data")

common_path = project_root / "common"
if os.path.exists(common_path):
    app.mount("/common", StaticFiles(directory=str(common_path)), name="common")

images_path = project_root / "admin" / "images"
if os.path.exists(images_path):
    app.mount("/images", StaticFiles(directory=str(images_path)), name="images")

admin_header_path = project_root / "admin" / "header"
if os.path.exists(admin_header_path):
    app.mount("/admin/header", StaticFiles(directory=str(admin_header_path)), name="admin_header")

from starlette.responses import PlainTextResponse as _PlainTextResponse


class GuardedStaticFiles(StaticFiles):
    """Static server that refuses to expose backend source, .env, or dotfiles."""

    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] == "backend") or norm.endswith(".py") or any(s.startswith(".") for s in segs):
            return _PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


editor_path = Path(__file__).parent.parent
app.mount("/", GuardedStaticFiles(directory=str(editor_path), html=True), name="editor_static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
