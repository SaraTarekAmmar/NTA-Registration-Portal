import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from core.auth import require_editor
from core.database import get_db_connection

router = APIRouter(prefix="/api/exams", tags=["Exams"])


class ExamCreate(BaseModel):
    subject: str
    title: Optional[str] = None
    title_ar: Optional[str] = None
    questions: Optional[List[Dict[str, Any]]] = None
    duration_minutes: Optional[int] = 60
    pass_score: Optional[float] = 60.0


@router.get("")
async def list_exams(editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, subject, title, title_ar, duration_minutes, pass_score FROM exams ORDER BY id DESC")
        rows = cursor.fetchall()
        return rows
    except Exception:
        return []
    finally:
        cursor.close()
        db.close()


@router.get("/{subject}")
async def get_exam(subject: str, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM exams WHERE subject = %s", (subject,))
        exam = cursor.fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        if exam.get("content_json"):
            exam["content"] = json.loads(exam["content_json"])
        return exam
    finally:
        cursor.close()
        db.close()


@router.post("")
async def create_exam(exam: ExamCreate, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        content = {"questions": exam.questions or [], "duration_minutes": exam.duration_minutes}
        cursor.execute(
            """INSERT INTO exams (subject, title, title_ar, content_json, duration_minutes, pass_score)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (
                exam.subject, exam.title, exam.title_ar,
                json.dumps(content, ensure_ascii=False),
                exam.duration_minutes, exam.pass_score
            )
        )
        db.commit()
        return {"id": cursor.lastrowid, **exam.dict()}
    finally:
        cursor.close()
        db.close()


@router.put("/{subject}")
async def update_exam(subject: str, exam: ExamCreate, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        content = {"questions": exam.questions or [], "duration_minutes": exam.duration_minutes}
        cursor.execute(
            """UPDATE exams SET title=%s, title_ar=%s, content_json=%s,
               duration_minutes=%s, pass_score=%s WHERE subject=%s""",
            (
                exam.title, exam.title_ar,
                json.dumps(content, ensure_ascii=False),
                exam.duration_minutes, exam.pass_score, subject
            )
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Exam not found")
        return {"subject": subject, **exam.dict()}
    finally:
        cursor.close()
        db.close()


@router.delete("/{subject}")
async def delete_exam(subject: str, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM exams WHERE subject=%s", (subject,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Exam not found")
        return {"message": "Exam deleted"}
    finally:
        cursor.close()
        db.close()
