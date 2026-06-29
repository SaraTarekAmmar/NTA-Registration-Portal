"""
media.py
========
Global media library — list all uploaded files, upload new ones,
delete files. Editor-protected.
"""
import os, re, time
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from jose import JWTError, jwt

router = APIRouter(prefix="/api/media", tags=["Front Media"])

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

MEDIA_DIR = Path(__file__).parent.parent.parent / "uploads" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
MAX_SIZE   = 50 * 1024 * 1024
ALLOWED    = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
              ".mp4", ".webm", ".ogg", ".mov", ".pdf"}


def _get_editor(request: Request) -> dict:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    token = header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") not in ("editor", "admin", "superadmin"):
            raise HTTPException(status_code=403, detail="Editor access required.")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


@router.get("")
async def list_media(req: Request):
    _get_editor(req)
    files = []
    for f in sorted(MEDIA_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.is_file():
            ext = f.suffix.lower()
            media_type = "video" if ext in {".mp4", ".webm", ".ogg", ".mov"} else "image"
            files.append({
                "filename": f.name,
                "url": f"/uploads/media/{f.name}",
                "media_type": media_type,
                "size_bytes": f.stat().st_size,
                "modified": int(f.stat().st_mtime)
            })
    return files


@router.post("", status_code=201)
async def upload_media(req: Request, file: UploadFile = File(...)):
    editor = _get_editor(req)
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 50 MB limit.")

    safe = re.sub(r"[^\w\-.]", "_", file.filename)
    fname = f"{int(time.time())}_{safe}"
    (MEDIA_DIR / fname).write_bytes(content)

    media_type = "video" if ext in {".mp4", ".webm", ".ogg", ".mov"} else "image"
    return {"filename": fname, "url": f"/uploads/media/{fname}", "media_type": media_type}


@router.delete("/{filename}")
async def delete_media(req: Request, filename: str):
    _get_editor(req)
    # Safety: strip any path traversal
    safe_filename = Path(filename).name
    target = MEDIA_DIR / safe_filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    target.unlink()
    return {"message": f"{safe_filename} deleted."}
