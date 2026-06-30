import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import uuid
import time
from dotenv import load_dotenv

# Add current directory to sys.path for standalone portability
sys.path.append(str(Path(__file__).parent))

from core import auth
from core.logger_util import log_activity
from routers import admission, ai_services

load_dotenv()

app = FastAPI(
    title="NTA Admission Center API",
    description="Backend API for managing admissions and stages.",
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
        "http://localhost:7776",   # admission center
        "http://localhost:8001",   # editor portal
        "http://localhost:8002",   # admin portal
        "http://localhost:8003",   # superadmin
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|null",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        except: pass
    
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

# In standalone mode, auth router is local
from routers import tickets
app.include_router(tickets.router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(auth.router)
app.include_router(admission.router)
app.include_router(ai_services.router)


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
    return {"status": "ok", "service": "admission"}

# Serve the centralized data folder
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

# Serve static files (HTML, CSS, JS) from the admission directory
# This allows opening http://localhost:8006/ directly
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
    # Default to 7776 for standalone admission portal
    port = int(os.getenv("PORT", 7776))
    uvicorn.run(app, host="0.0.0.0", port=port)
