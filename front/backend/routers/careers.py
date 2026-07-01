"""
careers.py
==========
Public: GET active career listings + POST application with CV upload.
Editor-protected: full CRUD on listings and view/update applications.
"""
import os, shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from core.database import get_db_connection
from core.logger_util import log_activity
from schemas.careers import CareerCreate, CareerUpdate, ApplicationStatusUpdate

router = APIRouter(prefix="/api/careers", tags=["Front Careers"])

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "cvs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_CV_SIZE = 5 * 1024 * 1024   # 5 MB
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}


# ── Auth helper ───────────────────────────────────────────────────────────────

def _get_editor(request: Request) -> dict:
    """Require a valid editor JWT from Authorization header."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    token = header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role", "")
        if role not in ("editor", "admin", "superadmin"):
            raise HTTPException(status_code=403, detail="Editor access required.")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


def _cv_file_for_row(row: dict) -> Path:
    """Resolve a CV by stored filename while preventing path traversal."""
    filename = Path(row.get("cv_filename") or "").name
    if not filename:
        raise HTTPException(status_code=404, detail="CV file not found.")
    target = (UPLOAD_DIR / filename).resolve()
    root = UPLOAD_DIR.resolve()
    if root not in target.parents and target != root:
        raise HTTPException(status_code=400, detail="Invalid CV path.")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="CV file not found.")
    return target


# ── PUBLIC: list active jobs ──────────────────────────────────────────────────

@router.get("")
async def list_careers():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT id, title, type, location, description, requirements,
                      created_at
               FROM front_careers WHERE is_active = 1
               ORDER BY created_at DESC"""
        )
        return cursor.fetchall()
    finally:
        cursor.close(); db.close()


# ── EDITOR: manage listings ───────────────────────────────────────────────────
# Keep these routes before /{career_id:int}; otherwise /admin/... can be captured
# by the public detail route.

@router.get("/admin/all")
async def admin_list_careers(req: Request):
    editor = _get_editor(req)
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT c.*, COUNT(a.id) AS application_count
               FROM front_careers c
               LEFT JOIN front_career_applications a ON a.career_id = c.id
               GROUP BY c.id ORDER BY c.created_at DESC"""
        )
        return cursor.fetchall()
    finally:
        cursor.close(); db.close()


@router.post("/admin", status_code=201)
async def admin_create_career(req: Request, body: CareerCreate):
    editor = _get_editor(req)
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """INSERT INTO front_careers (title, type, location, description, requirements, is_active, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (body.title, body.type, body.location, body.description,
             body.requirements, int(body.is_active),
             editor.get("national_id") or editor.get("sub"))
        )
        db.commit()
        return {"id": cursor.lastrowid, "message": "Career listing created."}
    finally:
        cursor.close(); db.close()


@router.put("/admin/{career_id:int}")
async def admin_update_career(req: Request, career_id: int, body: CareerUpdate):
    editor = _get_editor(req)
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM front_careers WHERE id = %s", (career_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Career not found.")

        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if not updates:
            return {"message": "Nothing to update."}

        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cursor.execute(
            f"UPDATE front_careers SET {set_clause} WHERE id = %s",
            (*updates.values(), career_id)
        )
        db.commit()
        return {"message": "Career updated."}
    finally:
        cursor.close(); db.close()


@router.delete("/admin/{career_id:int}")
async def admin_delete_career(req: Request, career_id: int):
    editor = _get_editor(req)
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM front_careers WHERE id = %s", (career_id,))
        db.commit()
        return {"message": "Career listing deleted."}
    finally:
        cursor.close(); db.close()


# ── EDITOR: applications ──────────────────────────────────────────────────────

@router.get("/admin/{career_id:int}/applications")
async def admin_get_applications(req: Request, career_id: int):
    editor = _get_editor(req)
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
            r["cv_url"] = f"/api/careers/admin/applications/{r['id']}/cv"
        return rows
    finally:
        cursor.close(); db.close()


@router.get("/admin/applications/{app_id:int}/cv")
async def admin_download_application_cv(req: Request, app_id: int):
    editor = _get_editor(req)
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT cv_filename FROM front_career_applications WHERE id = %s",
            (app_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found.")
        target = _cv_file_for_row(row)
        return FileResponse(path=str(target), filename=target.name)
    finally:
        cursor.close(); db.close()


@router.put("/admin/applications/{app_id:int}/status")
async def admin_update_application_status(req: Request, app_id: int, body: ApplicationStatusUpdate):
    editor = _get_editor(req)
    valid = {"new", "reviewed", "shortlisted", "rejected"}
    if body.status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid}")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE front_career_applications SET status = %s WHERE id = %s",
            (body.status, app_id)
        )
        db.commit()
        return {"message": "Application status updated."}
    finally:
        cursor.close(); db.close()


@router.get("/{career_id:int}")
async def get_career(career_id: int):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM front_careers WHERE id = %s AND is_active = 1",
            (career_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Career listing not found.")
        return row
    finally:
        cursor.close(); db.close()


# ── PUBLIC: submit application ────────────────────────────────────────────────

@router.post("/{career_id:int}/apply", status_code=201)
async def apply_for_career(
    req:        Request,
    career_id:  int,
    full_name:  str = Form(...),
    national_id:str = Form(...),
    phone:      str = Form(...),
    email:      str = Form(None),
    cover_note: str = Form(...),
    cv_file:    UploadFile = File(...)
):
    ip = req.client.host if req.client else "unknown"

    # Validate file type
    ext = Path(cv_file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="CV must be PDF, DOC, or DOCX.")

    # Validate file size
    content = await cv_file.read()
    if len(content) > MAX_CV_SIZE:
        raise HTTPException(status_code=400, detail="CV file must be under 5 MB.")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Career must exist and be active
        cursor.execute(
            "SELECT id, title FROM front_careers WHERE id = %s AND is_active = 1",
            (career_id,)
        )
        career = cursor.fetchone()
        if not career:
            raise HTTPException(status_code=404, detail="Career listing not found.")

        # Save CV file
        import time, re
        safe_name = re.sub(r"[^\w\-.]", "_", cv_file.filename)
        filename  = f"{int(time.time())}_{national_id}_{safe_name}"
        file_path = UPLOAD_DIR / filename
        with open(file_path, "wb") as f:
            f.write(content)

        cursor.execute(
            """INSERT INTO front_career_applications
               (career_id, full_name, national_id, phone, email, cover_note, cv_filename, cv_path)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (career_id, full_name.strip(), national_id.strip(), phone.strip(),
             email.strip() if email else None,
             cover_note.strip(), filename, str(file_path))
        )
        db.commit()
        app_id = cursor.lastrowid

        log_activity(
            category="CAREERS", event_type="CAREER_APPLICATION_SUBMITTED",
            national_id=national_id, ip_address=ip,
            user_agent=req.headers.get("user-agent"),
            request_path=req.url.path,
            details={"career_id": career_id, "career_title": career["title"]}
        )
        return {"id": app_id, "message": "Application submitted successfully."}
    finally:
        cursor.close(); db.close()
