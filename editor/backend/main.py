import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
import time
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))

from core import auth
from core.logger_util import log_activity, session_context, trace_context, get_traceback
from routers import auth as auth_router, courses, materials, sessions, exams
from jose import jwt
from core.auth import SECRET_KEY, ALGORITHM

load_dotenv()

app = FastAPI(
    title="NTA Editor Portal API",
    description="Backend API for the Editor Portal — course content management.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://academy.nta.eg",
        "http://localhost:8003",
        "http://localhost:8002",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Trace-ID"],
)


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


app.include_router(auth_router.router)
app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(sessions.router)
app.include_router(exams.router)

project_root = Path(__file__).parent.parent.parent

data_path = project_root / "data"
if os.path.exists(data_path):
    app.mount("/data", StaticFiles(directory=str(data_path)), name="data")

common_path = project_root / "common"
if os.path.exists(common_path):
    app.mount("/common", StaticFiles(directory=str(common_path)), name="common")

images_path = project_root / "admin" / "images"
if os.path.exists(images_path):
    app.mount("/images", StaticFiles(directory=str(images_path)), name="images")

admin_header_path = project_root / "admin" / "header"
if os.path.exists(admin_header_path):
    app.mount("/admin/header", StaticFiles(directory=str(admin_header_path)), name="admin_header")

editor_path = Path(__file__).parent.parent
app.mount("/", StaticFiles(directory=str(editor_path), html=True), name="editor_static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
