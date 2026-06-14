import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from core.auth import require_editor
from core.database import get_db_connection

router = APIRouter(prefix="/api/exams", tags=["Exams"])


class ExamCreate(BaseModel):
    subject: Optional[str] = None
    title: Optional[str] = None
    title_ar: Optional[str] = None
    questions: Optional[List[Dict[str, Any]]] = None
    duration_minutes: Optional[int] = 60
    pass_score: Optional[float] = 60.0
    status: Optional[str] = "draft"
    course_id: Optional[int] = None


def _hydrate(row):
    """Parse content_json into questions and expose a `duration` alias the UI reads."""
    if not row:
        return row
    content = row.get("content_json")
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except (ValueError, TypeError):
            content = {}
    content = content or {}
    row["questions"] = content.get("questions", [])
    row["duration"] = row.get("duration_minutes")
    row.pop("content_json", None)
    return row


@router.get("")
async def list_exams(course_id: Optional[int] = None, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if course_id:
            cursor.execute(
                "SELECT * FROM course_exams WHERE course_id = %s ORDER BY id DESC",
                (course_id,)
            )
        else:
            cursor.execute("SELECT * FROM course_exams ORDER BY id DESC")
        return [_hydrate(r) for r in (cursor.fetchall() or [])]
    finally:
        cursor.close()
        db.close()


@router.get("/{subject}")
async def get_exam(subject: str, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM course_exams WHERE subject = %s", (subject,))
        exam = cursor.fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        return _hydrate(exam)
    finally:
        cursor.close()
        db.close()


@router.post("")
async def create_exam(exam: ExamCreate, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        # BUG FIX: The old code evaluated cursor.lastrowid BEFORE the INSERT, which
        # always returned 0, causing every auto-generated subject to be identical
        # (e.g., "course_1_0") and triggering unique constraint violations.
        #
        # Fix: If a subject is not provided, INSERT with a temporary placeholder,
        # then UPDATE the subject using the real lastrowid after the INSERT.
        provided_subject = exam.subject
        content = {"questions": exam.questions or []}

        if provided_subject:
            # Subject explicitly provided — use it directly.
            cursor.execute(
                """INSERT INTO course_exams
                   (subject, course_id, title, title_ar, duration_minutes, pass_score, status, content_json)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    provided_subject, exam.course_id, exam.title, exam.title_ar,
                    exam.duration_minutes, exam.pass_score, exam.status,
                    json.dumps(content, ensure_ascii=False),
                )
            )
            db.commit()
            new_id = cursor.lastrowid
            subject = provided_subject
        else:
            # No subject provided — insert with a temporary NULL-safe placeholder,
            # then derive the subject from the real auto-increment ID.
            import uuid
            temp_subject = f"__tmp_{uuid.uuid4().hex}"
            cursor.execute(
                """INSERT INTO course_exams
                   (subject, course_id, title, title_ar, duration_minutes, pass_score, status, content_json)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    temp_subject, exam.course_id, exam.title, exam.title_ar,
                    exam.duration_minutes, exam.pass_score, exam.status,
                    json.dumps(content, ensure_ascii=False),
                )
            )
            new_id = cursor.lastrowid
            subject = f"course_{exam.course_id or 0}_{new_id}"
            cursor.execute(
                "UPDATE course_exams SET subject = %s WHERE id = %s",
                (subject, new_id)
            )
            db.commit()

        return {"id": new_id, "subject": subject, **exam.dict(exclude={"subject"})}
    finally:
        cursor.close()
        db.close()


@router.put("/{subject}")
async def update_exam(subject: str, exam: ExamCreate, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        content = {"questions": exam.questions or []}
        cursor.execute(
            """UPDATE course_exams SET title=%s, title_ar=%s, duration_minutes=%s,
               pass_score=%s, status=%s, content_json=%s WHERE subject=%s""",
            (
                exam.title, exam.title_ar, exam.duration_minutes,
                exam.pass_score, exam.status,
                json.dumps(content, ensure_ascii=False), subject,
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
        cursor.execute("DELETE FROM course_exams WHERE subject=%s", (subject,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Exam not found")
        return {"message": "Exam deleted"}
    finally:
        cursor.close()
        db.close()
