"""
front_manager.py  (editor portal router)
==========================================
Editor-only management of front page CMS, careers, and media library.
These mirror the front portal's own routers but are accessed from the
editor portal with the editor's JWT.
"""
import csv, io, os, re, time
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

from core.auth import get_current_editor as get_current_user
from core.database import get_db_connection

router = APIRouter(prefix="/api/front", tags=["Editor – Front Manager"])

MEDIA_DIR = Path(__file__).parent.parent.parent / "front" / "uploads" / "media"
CV_DIR    = Path(__file__).parent.parent.parent / "front" / "uploads" / "cvs"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
CV_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MEDIA = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
                 ".mp4", ".webm", ".ogg", ".mov"}
MAX_SIZE = 50 * 1024 * 1024


def _require_editor(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ("editor", "admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Editor access required.")
    return current_user


# ── CAREERS ───────────────────────────────────────────────────────────────────

class CareerBody(BaseModel):
    title:        str
    type:         str = "Full Time"
    location:     Optional[str] = None
    description:  Optional[str] = None
    requirements: Optional[str] = None
    is_active:    bool = True


class CareerUpdateBody(BaseModel):
    title:        Optional[str] = None
    type:         Optional[str] = None
    location:     Optional[str] = None
    description:  Optional[str] = None
    requirements: Optional[str] = None
    is_active:    Optional[bool] = None


class AppStatusBody(BaseModel):
    status: str  # new | reviewed | shortlisted | rejected


@router.get("/careers")
async def editor_list_careers(user=Depends(_require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT c.*, COUNT(a.id) AS application_count
               FROM front_careers c
               LEFT JOIN front_career_applications a ON a.career_id = c.id
               GROUP BY c.id ORDER BY c.created_at DESC"""
        )
        rows = cursor.fetchall()
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = str(r["created_at"])
            if r.get("application_count") is None:
                r["application_count"] = 0
        return rows
    finally:
        cursor.close(); db.close()


@router.post("/careers", status_code=201)
async def editor_create_career(body: CareerBody, user=Depends(_require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """INSERT INTO front_careers (title, type, location, description, requirements, is_active, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (body.title, body.type, body.location, body.description,
             body.requirements, int(body.is_active), str(user.get("id")))
        )
        db.commit()
        return {"id": cursor.lastrowid, "message": "Career created."}
    finally:
        cursor.close(); db.close()


@router.put("/careers/{career_id}")
async def editor_update_career(career_id: int, body: CareerUpdateBody, user=Depends(_require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if not updates:
            return {"message": "Nothing to update."}
        if "is_active" in updates:
            updates["is_active"] = int(updates["is_active"])
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cursor.execute(
            f"UPDATE front_careers SET {set_clause} WHERE id = %s",
            (*updates.values(), career_id)
        )
        db.commit()
        return {"message": "Career updated."}
    finally:
        cursor.close(); db.close()


@router.delete("/careers/{career_id}")
async def editor_delete_career(career_id: int, user=Depends(_require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM front_careers WHERE id = %s", (career_id,))
        db.commit()
        return {"message": "Career deleted."}
    finally:
        cursor.close(); db.close()


@router.get("/careers/{career_id}/applications")
async def editor_list_applications(career_id: int, user=Depends(_require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT id, full_name, national_id, phone, email, cover_note,
                      cv_filename, status, submitted_at
               FROM front_career_applications
               WHERE career_id = %s ORDER BY submitted_at DESC""",
            (career_id,)
        )
        rows = cursor.fetchall()
        for r in rows:
            r["cv_url"] = f"http://localhost:7770/uploads/cvs/{r['cv_filename']}"
            r["submitted_at"] = str(r["submitted_at"])
        return rows
    finally:
        cursor.close(); db.close()


@router.put("/careers/{career_id}/applications/{app_id}/status")
async def editor_update_app_status(
    career_id: int, app_id: int,
    body: AppStatusBody, user=Depends(_require_editor)
):
    valid = {"new", "reviewed", "shortlisted", "rejected"}
    if body.status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid}")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE front_career_applications SET status = %s WHERE id = %s AND career_id = %s",
            (body.status, app_id, career_id)
        )
        db.commit()
        return {"message": "Application status updated."}
    finally:
        cursor.close(); db.close()


# ── CMS CONTENT ───────────────────────────────────────────────────────────────

class ContentUpdateBody(BaseModel):
    content_json: Optional[str] = None
    media_type:   Optional[str] = None
    media_path:   Optional[str] = None
    bg_color:     Optional[str] = None
    text_color:   Optional[str] = None
    is_visible:   Optional[bool] = None


class ContentCreateBody(BaseModel):
    section_key:  str
    lang:         str = "en"
    sort_order:   int = 999
    content_json: Optional[str] = None
    media_type:   str = "none"
    media_path:   Optional[str] = None
    bg_color:     Optional[str] = None
    text_color:   Optional[str] = None
    is_visible:   bool = True


class ReorderItem(BaseModel):
    section_key: str
    sort_order:  int


class ReorderBody(BaseModel):
    items: List[ReorderItem]


@router.get("/content")
async def editor_list_content(user=Depends(_require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM front_page_content ORDER BY sort_order ASC, lang ASC"
        )
        return cursor.fetchall()
    finally:
        cursor.close(); db.close()


@router.put("/content/reorder")
async def editor_reorder_content(body: ReorderBody, user=Depends(_require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        for item in body.items:
            cursor.execute(
                "UPDATE front_page_content SET sort_order = %s WHERE section_key = %s",
                (item.sort_order, item.section_key)
            )
        db.commit()
        return {"message": "Sections reordered."}
    finally:
        cursor.close(); db.close()


@router.put("/content/{section_key}")
async def editor_update_content(
    section_key: str, body: ContentUpdateBody,
    lang: str = "en", user=Depends(_require_editor)
):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if "is_visible" in updates:
            updates["is_visible"] = int(updates["is_visible"])
        updates["last_updated_by"] = str(user.get("id"))
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cursor.execute(
            f"UPDATE front_page_content SET {set_clause} WHERE section_key = %s AND lang = %s",
            (*updates.values(), section_key, lang)
        )
        db.commit()
        return {"message": "Section updated."}
    finally:
        cursor.close(); db.close()


@router.post("/content", status_code=201)
async def editor_create_content(body: ContentCreateBody, user=Depends(_require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """INSERT INTO front_page_content
               (section_key, lang, sort_order, content_json, media_type, media_path,
                bg_color, text_color, is_visible, last_updated_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (body.section_key, body.lang, body.sort_order, body.content_json,
             body.media_type, body.media_path, body.bg_color, body.text_color,
             int(body.is_visible), str(user.get("id")))
        )
        db.commit()
        return {"id": cursor.lastrowid, "message": "Section created."}
    finally:
        cursor.close(); db.close()


@router.delete("/content/{section_key}")
async def editor_delete_content(section_key: str, user=Depends(_require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "DELETE FROM front_page_content WHERE section_key = %s", (section_key,)
        )
        db.commit()
        return {"message": "Section deleted."}
    finally:
        cursor.close(); db.close()


# ── MEDIA LIBRARY ─────────────────────────────────────────────────────────────

@router.get("/media")
async def editor_list_media(user=Depends(_require_editor)):
    files = []
    for f in sorted(MEDIA_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.is_file():
            ext = f.suffix.lower()
            media_type = "video" if ext in {".mp4", ".webm", ".ogg", ".mov"} else "image"
            files.append({
                "filename": f.name,
                "url": f"http://localhost:7770/uploads/media/{f.name}",
                "media_type": media_type,
                "size_bytes": f.stat().st_size,
                "modified": int(f.stat().st_mtime)
            })
    return files


@router.post("/media", status_code=201)
async def editor_upload_media(file: UploadFile = File(...), user=Depends(_require_editor)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_MEDIA:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 50 MB.")
    safe  = re.sub(r"[^\w\-.]", "_", file.filename)
    fname = f"{int(time.time())}_{safe}"
    (MEDIA_DIR / fname).write_bytes(content)
    media_type = "video" if ext in {".mp4", ".webm", ".ogg", ".mov"} else "image"
    return {
        "filename": fname,
        "url": f"http://localhost:7770/uploads/media/{fname}",
        "media_type": media_type
    }


@router.delete("/media/{filename}")
async def editor_delete_media(filename: str, user=Depends(_require_editor)):
    safe_name = Path(filename).name
    target = MEDIA_DIR / safe_name
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    target.unlink()
    return {"message": f"{safe_name} deleted."}
