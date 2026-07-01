"""
main.py — Front Page Portal Backend
=====================================
FastAPI application for NTA Front Page Portal.
Port: 7770 (standalone) | Serves index.html + all front page assets.
"""
import sys, os, uuid, time
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Make backend/ importable
sys.path.append(str(Path(__file__).parent))
load_dotenv()

from core.logger_util import log_activity, session_context, trace_context, get_traceback
from routers import auth_login, signup, careers, page_content, media

app = FastAPI(
    title="NTA Front Page Portal API",
    description="Public-facing entry portal — login routing, signup, careers, CMS.",
    version="1.0.0"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://academy.nta.eg",
        "https://reg.nta.eg",
        "http://localhost:7770",   # self
        "http://localhost:7771",   # trainee portal
        "http://localhost:7772",   # trainer portal
        "http://localhost:8001",   # editor portal
        "http://localhost:8002",   # admin portal
        "http://localhost:8003",   # superadmin
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|null",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Middleware: Tracing + Logging ──────────────────────────────────────
from jose import jwt as jose_jwt
from core.auth_helpers import SECRET_KEY, ALGORITHM

@app.middleware("http")
async def global_debugger_middleware(request: Request, call_next):
    trace_id    = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    trace_token = trace_context.set(trace_id)
    start_time  = time.time()

    auth_header = request.headers.get("Authorization")
    sid = role = None
    if auth_header and auth_header.startswith("Bearer "):
        try:
            payload = jose_jwt.decode(auth_header.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
            sid  = payload.get("sid")
            role = payload.get("role")
        except Exception:
            pass

    session_token = session_context.set(sid)
    path      = request.url.path
    is_static = any(path.endswith(ext) for ext in
                    [".css", ".js", ".png", ".jpg", ".jpeg", ".gif",
                     ".svg", ".ico", ".woff", ".woff2", ".mp4", ".webm"])
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")

    try:
        response = await call_next(request)
        if not is_static:
            duration_ms = int((time.time() - start_time) * 1000)
            log_activity(
                category="ACTION" if path.startswith("/api/") else "PASSIVE",
                event_type="API_CALL" if path.startswith("/api/") else "PAGE_VIEW",
                role=role, ip_address=ip, user_agent=ua,
                request_path=path, status_code=response.status_code,
                trace_id=trace_id, duration_ms=duration_ms, status="Logged"
            )
        return response
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        tb = get_traceback()
        log_activity(
            category="SYSTEM", event_type="UNHANDLED_EXCEPTION",
            level="CRITICAL", component="FrontBackend",
            role=role, ip_address=ip, user_agent=ua,
            request_path=path, status_code=500,
            trace_id=trace_id, traceback=tb,
            status="Action Required", duration_ms=duration_ms
        )
        raise e
    finally:
        session_context.reset(session_token)
        trace_context.reset(trace_token)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_login.router)
app.include_router(signup.router)
app.include_router(careers.router)
app.include_router(page_content.router)
app.include_router(media.router)

# ── Static file mounts ────────────────────────────────────────────────────────
class GuardedUploadsStaticFiles(StaticFiles):
    """Serve public uploads but never expose applicant CVs directly."""

    async def get_response(self, path: str, scope):
        parts = [part for part in Path(path).parts if part not in ("", ".")]
        if parts and parts[0].lower() in {"cvs", "cv", "resumes", "resume"}:
            raise HTTPException(status_code=404, detail="File not found")
        if any(part.startswith(".") for part in parts):
            raise HTTPException(status_code=404, detail="File not found")
        return await super().get_response(path, scope)


class PrivateDataStaticFiles(StaticFiles):
    """Block direct static access to private data stored in /data."""

    BLOCKED_TOP_LEVEL = {
        "trainees",
        "trainers",
        "admins",
        "admission",
        "uploads",
        "temp",
        "standard_exams",
        "log",
    }

    async def get_response(self, path: str, scope):
        parts = [part for part in Path(path).parts if part not in ("", ".")]
        lowered = [part.lower() for part in parts]
        if any(part.startswith(".") for part in parts):
            raise HTTPException(status_code=404, detail="File not found")
        if lowered and lowered[0] in self.BLOCKED_TOP_LEVEL:
            raise HTTPException(status_code=404, detail="File not found")
        # Assignment submissions contain trainee work/PII and must be fetched via
        # authenticated APIs, never by guessing a static /data URL.
        if lowered and lowered[0] == "courses" and "submissions" in lowered:
            raise HTTPException(status_code=404, detail="File not found")
        return await super().get_response(path, scope)


# Serve public media uploads while CVs are served through authenticated API routes.
uploads_path = Path(__file__).parent.parent / "uploads"
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", GuardedUploadsStaticFiles(directory=str(uploads_path)), name="uploads")

# Serve only public-safe shared data paths.
data_path = Path(__file__).parent.parent.parent / "data"
if data_path.exists():
    app.mount("/data", PrivateDataStaticFiles(directory=str(data_path)), name="data")

# Serve front/ as the web root — index.html becomes http://localhost:7770/
static_path = Path(__file__).parent.parent
app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7770))
    uvicorn.run(app, host="0.0.0.0", port=port)
