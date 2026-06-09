import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
import time
from dotenv import load_dotenv

# Add current directory to sys.path for standalone portability
sys.path.append(str(Path(__file__).parent))

from core import auth
from core.logger_util import log_activity
from routers import admin, courses, chat, ai_services, exams, permissions, class_matrix
from fastapi import Request

load_dotenv()

app = FastAPI(
    title="NTA Admin Portal API",
    description="Backend API for managing recruitment and courses.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://academy.nta.eg",
        "https://reg.nta.eg",
        "http://localhost:8001",
        "http://localhost:8002"
    ],
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
app.include_router(auth.router)
app.include_router(auth.admin_router)
app.include_router(auth.editor_router)
app.include_router(admin.router)
app.include_router(courses.router)
app.include_router(chat.router)
app.include_router(ai_services.router)
app.include_router(exams.router)
app.include_router(permissions.router)
app.include_router(class_matrix.router)

# Serve the centralized data folder
data_path = Path(__file__).parent.parent.parent / "data"
if os.path.exists(data_path):
    app.mount("/data", StaticFiles(directory=str(data_path)), name="data")

# Serve editor portal from /editor/
editor_path = Path(__file__).parent.parent.parent / "editor"
if os.path.exists(editor_path):
    app.mount("/editor", StaticFiles(directory=str(editor_path), html=True), name="editor")

# Serve static files (HTML, CSS, JS) from the admin directory
# This allows opening http://localhost:8002/ directly
static_path = Path(__file__).parent.parent
app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Default to 8002 for standalone admin portal
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
