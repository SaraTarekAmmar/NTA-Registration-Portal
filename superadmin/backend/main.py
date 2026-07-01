import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add current directory to sys.path for standalone portability
sys.path.append(str(Path(__file__).parent))

from routers import attendance, auth, ai_proxy, stats, logs, alerts, reports, management, tickets
import os
import uuid
import time
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="NTA Super Admin AI Proxy", version="1.0.0")

# Configure CORS — restrict to known origins; never use wildcard in production
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "https://academy.nta.eg,https://reg.nta.eg,http://localhost:8001,http://localhost:8002,http://localhost:8003"
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

from fastapi import Request
from core.logger_util import log_activity, session_context, trace_context, get_traceback
from jose import jwt
from core.security import SECRET_KEY, ALGORITHM

@app.middleware("http")
async def global_debugger_middleware(request: Request, call_next):
    # 1. Initialize Trace ID & Start Timing
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    trace_token = trace_context.set(trace_id)
    start_time = time.time()
    
    # 2. Extract Session ID (Security Context)
    auth_header = request.headers.get("Authorization")
    sid = None
    role = "superadmin" # Default for this backend
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            sid = payload.get("sid")
            role = payload.get("role", "superadmin")
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
        
        # 5. Post-Request Logging
        if not is_static:
            duration_ms = int((time.time() - start_time) * 1000)
            
            category = "ADMIN"
            event_type = "API_CALL"
            if path.startswith("/auth/"):
                category = "AUTH"
            
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
        # 6. Critical Error Logging
        duration_ms = int((time.time() - start_time) * 1000)
        tb = get_traceback()
        
        log_activity(
            category="SYSTEM",
            event_type="UNHANDLED_EXCEPTION",
            level="CRITICAL",
            component="Superadmin Backend",
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

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(ai_proxy.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(management.router, prefix="/api")
app.include_router(tickets.router)

@app.get("/api/status")
@app.get("/status")
async def root():
    return {
        "status": "online",
        "service": "Super Admin AI Proxy",
        "description": "Functional proxy for AI services and attendance webhooks"
    }

# Static Files - Frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8003)),
        reload=True if os.getenv("DEBUG") == "True" else False
    )
