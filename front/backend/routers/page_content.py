"""
page_content.py
===============
CMS endpoints for the front page sections.
Public: GET (read all visible sections).
Editor-protected: full creative control — update text/media/colors/order,
add new sections, delete sections, upload image/video per section.
"""
import os, shutil, time, re
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from jose import JWTError, jwt
from core.database import get_db_connection
from core.logger_util import log_activity
from schemas.page_content import ContentUpdate, ContentCreate, ReorderRequest

router = APIRouter(prefix="/api/content", tags=["Front CMS"])

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

MEDIA_DIR = Path(__file__).parent.parent.parent / "uploads" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
MAX_MEDIA_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
ALLOWED_VIDEO = {".mp4", ".webm", ".ogg", ".mov"}


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


# ── PUBLIC ─────────────────────────────────────────────────────────────────────

@router.get("")
async def get_all_content(lang: str = "en"):
    """Return all visible sections sorted by sort_order for the given lang."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT section_key, lang, sort_order, content_json,
                      media_type, media_path, bg_color, text_color, is_visible
               FROM front_page_content
               WHERE lang = %s AND is_visible = 1
               ORDER BY sort_order ASC""",
            (lang,)
        )
        return cursor.fetchall()
    finally:
        cursor.close(); db.close()


@router.get("/{section_key}")
async def get_section(section_key: str, lang: str = "en"):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM front_page_content WHERE section_key = %s AND lang = %s",
            (section_key, lang)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Section not found.")
        return row
    finally:
        cursor.close(); db.close()


# ── EDITOR ────────────────────────────────────────────────────────────────────

@router.get("/admin/all")
async def admin_get_all(req: Request):
    """Editor view — all sections for all languages."""
    _get_editor(req)
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM front_page_content ORDER BY sort_order ASC, lang ASC"
        )
        return cursor.fetchall()
    finally:
        cursor.close(); db.close()


@router.post("", status_code=201)
async def create_section(req: Request, body: ContentCreate):
    editor = _get_editor(req)
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
             int(body.is_visible), editor.get("sub"))
        )
        db.commit()
        log_activity(
            category="CMS", event_type="SECTION_CREATED",
            ip_address=req.client.host if req.client else "unknown",
            details={"section_key": body.section_key, "lang": body.lang}
        )
        return {"id": cursor.lastrowid, "message": "Section created."}
    finally:
        cursor.close(); db.close()


@router.put("/reorder")
async def reorder_sections(req: Request, body: ReorderRequest):
    editor = _get_editor(req)
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


@router.put("/{section_key}")
async def update_section(req: Request, section_key: str, body: ContentUpdate, lang: str = "en"):
    editor = _get_editor(req)
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id FROM front_page_content WHERE section_key = %s AND lang = %s",
            (section_key, lang)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Section not found.")

        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if "is_visible" in updates:
            updates["is_visible"] = int(updates["is_visible"])
        updates["last_updated_by"] = editor.get("sub")

        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cursor.execute(
            f"UPDATE front_page_content SET {set_clause} WHERE section_key = %s AND lang = %s",
            (*updates.values(), section_key, lang)
        )
        db.commit()
        log_activity(
            category="CMS", event_type="SECTION_UPDATED",
            ip_address=req.client.host if req.client else "unknown",
            details={"section_key": section_key, "lang": lang, "fields": list(updates.keys())}
        )
        return {"message": "Section updated."}
    finally:
        cursor.close(); db.close()


@router.post("/{section_key}/media")
async def upload_section_media(req: Request, section_key: str, file: UploadFile = File(...)):
    editor = _get_editor(req)

    ext = Path(file.filename).suffix.lower()
    is_image = ext in ALLOWED_IMAGE
    is_video = ext in ALLOWED_VIDEO

    if not (is_image or is_video):
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    content = await file.read()
    if len(content) > MAX_MEDIA_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 50 MB limit.")

    safe_name = re.sub(r"[^\w\-.]", "_", file.filename)
    filename  = f"{int(time.time())}_{section_key}{ext}"
    save_path = MEDIA_DIR / filename

    with open(save_path, "wb") as f:
        f.write(content)

    media_type = "image" if is_image else "video"
    media_url  = f"/uploads/media/{filename}"

    # Auto-update DB
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """UPDATE front_page_content
               SET media_type = %s, media_path = %s, last_updated_by = %s
               WHERE section_key = %s""",
            (media_type, media_url, editor.get("sub"), section_key)
        )
        db.commit()
    finally:
        cursor.close(); db.close()

    return {
        "filename": filename,
        "url": media_url,
        "media_type": media_type,
        "message": "Media uploaded and section updated."
    }


@router.delete("/{section_key}")
async def delete_section(req: Request, section_key: str):
    editor = _get_editor(req)
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "DELETE FROM front_page_content WHERE section_key = %s",
            (section_key,)
        )
        db.commit()
        log_activity(
            category="CMS", event_type="SECTION_DELETED",
            ip_address=req.client.host if req.client else "unknown",
            details={"section_key": section_key}
        )
        return {"message": "Section deleted."}
    finally:
        cursor.close(); db.close()
