import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import PlainTextResponse
import os
import secrets
from dotenv import load_dotenv

# Add current directory to sys.path for standalone portability
sys.path.append(str(Path(__file__).parent))

from core.logger_util import log_activity
from routers import lookups, ai_services, progress

load_dotenv()

app = FastAPI(
    title="NTA Registration Portal API",
    description="Backend API for managing standalone registrations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://academy.nta.eg",
        "https://reg.nta.eg",
        "http://localhost:7770",
        "http://localhost:7771",
        "http://localhost:7772",
        "http://localhost:7775",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|null",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    token = request.cookies.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        
    response = await call_next(request)
    
    if not request.cookies.get("csrf_token"):
        response.set_cookie(
            key="csrf_token",
            value=token,
            samesite="lax",
            httponly=False
        )
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    if any(path.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2"]):
        return await call_next(request)

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    response = await call_next(request)
    
    event_type = "API_CALL" if path.startswith("/api/") else "PAGE_VIEW"
    log_activity(
        category="PASSIVE",
        event_type=event_type,
        ip_address=ip,
        user_agent=ua,
        request_path=path,
        status_code=response.status_code
    )
    return response


app.include_router(lookups.router)
app.include_router(ai_services.router)
app.include_router(progress.router)

@app.post("/api/debug/log")
async def debug_log(request: Request):
    if os.getenv("NTA_DEBUG") == "1":
        data = await request.json()
        print("[FRONTEND ERROR LOG]", data.get("error"))
    return {"status": "ok"}


class PrivateDataStaticFiles(StaticFiles):
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
        is_private_submission = bool(segs and segs[0] == "courses" and "submissions" in segs)
        if (
            (segs and segs[0] in self._BLOCKED)
            or is_private_submission
            or any(s.startswith(".") for s in segs)
        ):
            return PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


class GuardedStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (
            (segs and segs[0] in {"backend", "core", "routers", "schemas"})
            or norm.endswith(".py")
            or any(s.startswith(".") for s in segs)
        ):
            return PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


data_path = Path(__file__).parent.parent.parent / "data"
if os.path.exists(data_path):
    app.mount("/data", PrivateDataStaticFiles(directory=str(data_path)), name="data")

static_path = Path(__file__).parent.parent
app.mount("/", GuardedStaticFiles(directory=str(static_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7775))
    uvicorn.run(app, host="0.0.0.0", port=port)
