"""
Coordinator Portal — FastAPI Application
Handles attendance tracking and permission/excuse management.
Port: 8005
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

app = FastAPI(
    title="NTA Coordinator Portal",
    description="Coordinator attendance and permissions management",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────
origins = [
    "https://academy.nta.eg",
    "http://localhost:8005",
    "http://127.0.0.1:8005",
    "http://localhost:8002",
    "http://localhost:8004",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
from routers import auth, attendance, permissions

app.include_router(auth.router)
app.include_router(attendance.router)
app.include_router(permissions.router)

# ── Static Files ─────────────────────────────────────────────────────
# Mount coordinator frontend (coordinator/ directory, one level up from backend/)
COORDINATOR_DIR = Path(__file__).parent.parent
COMMON_DIR = COORDINATOR_DIR.parent / "common"
ADMIN_HEADER_DIR = COORDINATOR_DIR.parent / "admin" / "header"
IMAGES_DIR = COORDINATOR_DIR.parent / "admin" / "images"
DATA_DIR = COORDINATOR_DIR.parent / "data"

# Serve common assets
if COMMON_DIR.exists():
    app.mount("/common", StaticFiles(directory=str(COMMON_DIR)), name="common")

# Serve admin header CSS/JS (shared sidebar styles)
if ADMIN_HEADER_DIR.exists():
    app.mount("/admin/header", StaticFiles(directory=str(ADMIN_HEADER_DIR)), name="admin_header")

# Serve images
if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

# Serve data (attendance photos)
if DATA_DIR.exists():
    app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

# Serve coordinator frontend as root (must be last)
from starlette.responses import PlainTextResponse as _PlainTextResponse


class GuardedStaticFiles(StaticFiles):
    """Static server that refuses to expose backend source, .env, or dotfiles."""

    async def get_response(self, path, scope):
        norm = path.replace("\\", "/").strip("/").lower()
        segs = [s for s in norm.split("/") if s]
        if (segs and segs[0] == "backend") or norm.endswith(".py") or any(s.startswith(".") for s in segs):
            return _PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


app.mount("/", GuardedStaticFiles(directory=str(COORDINATOR_DIR), html=True), name="coordinator_frontend")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "coordinator"}
