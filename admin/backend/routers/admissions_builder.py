import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from core.auth import get_admin_user, get_current_user
from core.database import get_db_connection

router = APIRouter(prefix="/api/admissions-builder", tags=["Admissions Builder"])


class SectionBase(BaseModel):
    title_ar: str
    section_type: str
    course_type: Optional[str] = "default"
    config_json: Optional[Dict[str, Any]] = None
    visibility_rules: Optional[Dict[str, Any]] = None
    unlock_rules: Optional[Dict[str, Any]] = None
    sort_order: Optional[int] = 0
    is_required: Optional[bool] = True
    is_active: Optional[bool] = True


class SubmissionCreate(BaseModel):
    section_id: int
    answers_json: Optional[Dict[str, Any]] = None
    uploaded_files: Optional[List[str]] = None


def _normalize_course_type(value: Optional[str]) -> str:
    value = (value or "").strip()
    return value or "default"


def _parse_json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return value or {}


def _json_or_none(value):
    return json.dumps(value, ensure_ascii=False) if value else None


def _ensure_admissions_schema(cursor):
    required = {
        "course_type": "ALTER TABLE admission_sections ADD COLUMN course_type VARCHAR(100) NOT NULL DEFAULT 'default' AFTER id",
        "visibility_rules": "ALTER TABLE admission_sections ADD COLUMN visibility_rules LONGTEXT NULL AFTER config_json",
        "unlock_rules": "ALTER TABLE admission_sections ADD COLUMN unlock_rules LONGTEXT NULL AFTER visibility_rules",
        "is_required": "ALTER TABLE admission_sections ADD COLUMN is_required TINYINT(1) NOT NULL DEFAULT 1 AFTER sort_order",
    }
    for column, ddl in required.items():
        cursor.execute(
            """
            SELECT COUNT(*) AS n
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'admission_sections'
              AND COLUMN_NAME = %s
            """,
            (column,),
        )
        row = cursor.fetchone()
        exists = row.get("n") if isinstance(row, dict) else row[0]
        if not exists:
            cursor.execute(ddl)


def _hydrate_section(row):
    if not row:
        return row
    row["course_type"] = _normalize_course_type(row.get("course_type"))
    row["config_json"] = _parse_json(row.get("config_json"))
    row["visibility_rules"] = _parse_json(row.get("visibility_rules"))
    row["unlock_rules"] = _parse_json(row.get("unlock_rules"))
    row["is_required"] = bool(row.get("is_required", 1))
    row["is_active"] = bool(row.get("is_active", 1))
    return row


def _get_applicant_course_type(cursor, user_id: int) -> str:
    cursor.execute(
        """
        SELECT COALESCE(NULLIF(c.classification, ''), NULLIF(c.short_name, '')) AS course_type
        FROM applications a
        LEFT JOIN courses c ON c.id = a.course_id
        WHERE a.user_id = %s
        ORDER BY a.id DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    if row and row.get("course_type"):
        return _normalize_course_type(row["course_type"])
    return "default"


def _assert_section_available_for_user(cursor, section_id: int, current_user: dict):
    cursor.execute("SELECT * FROM admission_sections WHERE id=%s", (section_id,))
    section = cursor.fetchone()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    section = _hydrate_section(section)
    if not section["is_active"]:
        raise HTTPException(status_code=403, detail="This admissions section is inactive")
    if current_user.get("role") not in ["admin", "superadmin"]:
        user_course_type = _get_applicant_course_type(cursor, current_user["id"])
        if section["course_type"] not in (user_course_type, "default"):
            raise HTTPException(status_code=403, detail="This admissions section is not assigned to your course flow")
    return section


@router.get("/sections")
async def list_sections(course_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        _ensure_admissions_schema(cursor)
        if current_user.get("role") == "admin":
            if course_type:
                cursor.execute(
                    "SELECT * FROM admission_sections WHERE course_type=%s ORDER BY sort_order, id",
                    (_normalize_course_type(course_type),),
                )
            else:
                cursor.execute("SELECT * FROM admission_sections ORDER BY course_type, sort_order, id")
        else:
            resolved_course_type = _normalize_course_type(course_type) if course_type else _get_applicant_course_type(cursor, current_user["id"])
            cursor.execute(
                """
                SELECT * FROM admission_sections
                WHERE is_active=1 AND course_type IN (%s, 'default')
                ORDER BY sort_order, id
                """,
                (resolved_course_type,),
            )
        return [_hydrate_section(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        db.close()


@router.post("/sections")
async def create_section(body: SectionBase, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        _ensure_admissions_schema(cursor)
        cursor.execute(
            """
            INSERT INTO admission_sections
              (course_type, title_ar, section_type, config_json, visibility_rules, unlock_rules,
               sort_order, is_required, is_active, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                _normalize_course_type(body.course_type), body.title_ar, body.section_type,
                _json_or_none(body.config_json), _json_or_none(body.visibility_rules), _json_or_none(body.unlock_rules),
                body.sort_order or 0, 1 if body.is_required else 0, 1 if body.is_active else 0, admin["id"],
            ),
        )
        db.commit()
        cursor.execute("SELECT * FROM admission_sections WHERE id=%s", (cursor.lastrowid,))
        return _hydrate_section(cursor.fetchone())
    finally:
        cursor.close()
        db.close()


@router.put("/sections/{section_id}")
async def update_section(section_id: int, body: SectionBase, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        _ensure_admissions_schema(cursor)
        cursor.execute(
            """
            UPDATE admission_sections SET
              course_type=%s, title_ar=%s, section_type=%s, config_json=%s,
              visibility_rules=%s, unlock_rules=%s, sort_order=%s,
              is_required=%s, is_active=%s
            WHERE id=%s
            """,
            (
                _normalize_course_type(body.course_type), body.title_ar, body.section_type,
                _json_or_none(body.config_json), _json_or_none(body.visibility_rules), _json_or_none(body.unlock_rules),
                body.sort_order or 0, 1 if body.is_required else 0, 1 if body.is_active else 0, section_id,
            ),
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Section not found")
        cursor.execute("SELECT * FROM admission_sections WHERE id=%s", (section_id,))
        return _hydrate_section(cursor.fetchone())
    finally:
        cursor.close()
        db.close()


@router.patch("/sections/{section_id}/toggle")
async def toggle_section(section_id: int, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        _ensure_admissions_schema(cursor)
        cursor.execute("UPDATE admission_sections SET is_active = NOT is_active WHERE id=%s", (section_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Section not found")
        return {"id": section_id, "toggled": True}
    finally:
        cursor.close()
        db.close()


@router.delete("/sections/{section_id}")
async def delete_section(section_id: int, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        _ensure_admissions_schema(cursor)
        cursor.execute("DELETE FROM admission_sections WHERE id=%s", (section_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Section not found")
        return {"deleted": True}
    finally:
        cursor.close()
        db.close()


@router.post("/sections/reorder")
async def reorder_sections(orders: List[Dict[str, int]], admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        _ensure_admissions_schema(cursor)
        for item in orders:
            cursor.execute("UPDATE admission_sections SET sort_order=%s WHERE id=%s", (item["sort_order"], item["id"]))
        db.commit()
        return {"reordered": True}
    finally:
        cursor.close()
        db.close()


@router.get("/submissions")
async def list_submissions(admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        _ensure_admissions_schema(cursor)
        cursor.execute(
            """
            SELECT s.*, u.full_name_ar, u.national_id, sec.title_ar as section_title, sec.course_type
            FROM applicant_submissions s
            JOIN users u ON s.user_id = u.id
            JOIN admission_sections sec ON s.section_id = sec.id
            ORDER BY s.submitted_at DESC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


@router.post("/submit")
async def submit_section(body: SubmissionCreate, current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        _ensure_admissions_schema(cursor)
        _assert_section_available_for_user(cursor, body.section_id, current_user)
        answers = _json_or_none(body.answers_json)
        files = _json_or_none(body.uploaded_files)
        cursor.execute(
            """
            INSERT INTO applicant_submissions (user_id, section_id, answers_json, uploaded_files, status)
            VALUES (%s, %s, %s, %s, 'submitted')
            ON DUPLICATE KEY UPDATE answers_json=%s, uploaded_files=%s, status='submitted'
            """,
            (current_user["id"], body.section_id, answers, files, answers, files),
        )
        db.commit()
        return {"submitted": True, "submission_id": cursor.lastrowid}
    finally:
        cursor.close()
        db.close()


@router.get("/my-submissions")
async def my_submissions(current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        _ensure_admissions_schema(cursor)
        cursor.execute(
            """
            SELECT s.*, sec.title_ar as section_title, sec.section_type, sec.course_type
            FROM applicant_submissions s
            JOIN admission_sections sec ON s.section_id = sec.id
            WHERE s.user_id = %s
            """,
            (current_user["id"],),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()
