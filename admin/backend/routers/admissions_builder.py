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
    config_json: Optional[Dict[str, Any]] = None
    sort_order: Optional[int] = 0
    is_active: Optional[bool] = True


class SubmissionCreate(BaseModel):
    section_id: int
    answers_json: Optional[Dict[str, Any]] = None
    uploaded_files: Optional[List[str]] = None


@router.get("/sections")
async def list_sections(current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM admission_sections ORDER BY sort_order, id")
        rows = cursor.fetchall()
        for row in rows:
            if isinstance(row.get("config_json"), str):
                try:
                    row["config_json"] = json.loads(row["config_json"])
                except Exception:
                    row["config_json"] = {}
        return rows
    finally:
        cursor.close()
        db.close()


@router.post("/sections")
async def create_section(body: SectionBase, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cfg = json.dumps(body.config_json, ensure_ascii=False) if body.config_json else None
        cursor.execute(
            """INSERT INTO admission_sections (title_ar, section_type, config_json, sort_order, is_active, created_by)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (body.title_ar, body.section_type, cfg, body.sort_order, 1 if body.is_active else 0, admin["id"]),
        )
        db.commit()
        return {"id": cursor.lastrowid, **body.dict()}
    finally:
        cursor.close()
        db.close()


@router.put("/sections/{section_id}")
async def update_section(section_id: int, body: SectionBase, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cfg = json.dumps(body.config_json, ensure_ascii=False) if body.config_json else None
        cursor.execute(
            """UPDATE admission_sections SET title_ar=%s, section_type=%s, config_json=%s,
               sort_order=%s, is_active=%s WHERE id=%s""",
            (body.title_ar, body.section_type, cfg, body.sort_order, 1 if body.is_active else 0, section_id),
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Section not found")
        return {"id": section_id, **body.dict()}
    finally:
        cursor.close()
        db.close()


@router.patch("/sections/{section_id}/toggle")
async def toggle_section(section_id: int, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
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
    cursor = db.cursor()
    try:
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
    cursor = db.cursor()
    try:
        for item in orders:
            cursor.execute(
                "UPDATE admission_sections SET sort_order=%s WHERE id=%s",
                (item["sort_order"], item["id"]),
            )
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
        cursor.execute(
            """SELECT s.*, u.full_name_ar, u.national_id, sec.title_ar as section_title
               FROM applicant_submissions s
               JOIN users u ON s.user_id = u.id
               JOIN admission_sections sec ON s.section_id = sec.id
               ORDER BY s.submitted_at DESC"""
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


@router.post("/submit")
async def submit_section(body: SubmissionCreate, current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        answers = json.dumps(body.answers_json, ensure_ascii=False) if body.answers_json else None
        files = json.dumps(body.uploaded_files, ensure_ascii=False) if body.uploaded_files else None
        cursor.execute(
            """INSERT INTO applicant_submissions (user_id, section_id, answers_json, uploaded_files, status)
               VALUES (%s, %s, %s, %s, 'submitted')
               ON DUPLICATE KEY UPDATE answers_json=%s, uploaded_files=%s, status='submitted'""",
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
        cursor.execute(
            """SELECT s.*, sec.title_ar as section_title, sec.section_type
               FROM applicant_submissions s
               JOIN admission_sections sec ON s.section_id = sec.id
               WHERE s.user_id = %s""",
            (current_user["id"],),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()
