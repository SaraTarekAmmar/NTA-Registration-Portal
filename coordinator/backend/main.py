"""
Coordinator Portal — FastAPI Application
Handles attendance tracking, permission/excuse management, and interview-day coordination.
Port: 8005
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import os

app = FastAPI(
    title="NTA Coordinator Portal",
    description="Coordinator attendance, permissions, and interview operations management",
    version="1.1.0",
)

origins = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "https://academy.nta.eg,http://localhost:8005,http://127.0.0.1:8005,http://localhost:8002,http://localhost:8004"
).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Trace-ID"],
)

from starlette.exceptions import HTTPException as _StarletteHTTPException
from fastapi.responses import JSONResponse as _JSONResponse


@app.exception_handler(_StarletteHTTPException)
async def _sanitize_http_exception(request, exc):
    detail = exc.detail
    if isinstance(getattr(exc, "status_code", 0), int) and exc.status_code >= 500 and os.getenv("NTA_DEBUG") != "1":
        print(f"[5xx] {request.method} {request.url.path}: {detail}")
        detail = "Internal server error"
    return _JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=getattr(exc, "headers", None))

from routers import auth, attendance, permissions, interviews, tickets

app.include_router(auth.router)
app.include_router(attendance.router)
app.include_router(permissions.router)
app.include_router(interviews.router)
app.include_router(tickets.router)


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
            return _JSONResponse(
                status_code=413,
                content={"detail": "حجم الطلب كبير جدًا. الحد الأقصى 1 ميجابايت."},
            )
    return await call_next(request)

COORDINATOR_DIR = Path(__file__).parent.parent
COMMON_DIR = COORDINATOR_DIR.parent / "common"
ADMIN_HEADER_DIR = COORDINATOR_DIR.parent / "admin" / "header"
IMAGES_DIR = COORDINATOR_DIR.parent / "admin" / "images"
DATA_DIR = COORDINATOR_DIR.parent / "data"

if COMMON_DIR.exists():
    app.mount("/common", StaticFiles(directory=str(COMMON_DIR)), name="common")

if ADMIN_HEADER_DIR.exists():
    app.mount("/admin/header", StaticFiles(directory=str(ADMIN_HEADER_DIR)), name="admin_header")

if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

class PrivateDataStaticFiles(StaticFiles):
    _BLOCKED = {"trainees", "trainers", "admins", "admission", "uploads", "temp", "standard_exams", "log"}

    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] in self._BLOCKED) or any(s.startswith(".") for s in segs):
            from starlette.responses import PlainTextResponse
            return PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


if DATA_DIR.exists():
    app.mount("/data", PrivateDataStaticFiles(directory=str(DATA_DIR)), name="data")

from starlette.responses import PlainTextResponse as _PlainTextResponse


class GuardedStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] == "backend") or norm.endswith(".py") or any(s.startswith(".") for s in segs):
            return _PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "coordinator"}

@app.get("/")
async def root():
    return RedirectResponse(url="/index.html", status_code=307)


app.mount("/", GuardedStaticFiles(directory=str(COORDINATOR_DIR), html=True), name="coordinator_frontend")
