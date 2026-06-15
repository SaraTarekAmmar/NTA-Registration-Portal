import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from core.auth import require_editor
from core.database import get_db_connection
from core.upload_manager import save_upload_file
from schemas.course import CourseBase

router = APIRouter(prefix="/api/courses", tags=["Course Save"])


@router.post("/cover-image")
async def upload_cover_image(file: UploadFile = File(...), editor: dict = Depends(require_editor)):
    # save_upload_file validates extension, MIME type and size (path-traversal safe).
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="يجب أن يكون الملف صورة (JPG/PNG/WebP)")
    rel_path = await save_upload_file(file, "course_image", str(editor.get("id", "editor")))
    return {"image_url": rel_path}

STATUS_TO_DB = {"draft": "Upcoming", "published": "Ongoing", "archived": "Completed", "قادم": "Upcoming"}
SKILL_TO_DB = {"مبتدئ": "Beginner", "متوسط": "Intermediate", "متقدم": "Advanced"}


class CourseSessionPayload(BaseModel):
    id: Optional[int] = None
    session_number: Optional[int] = None
    title: Optional[str] = None
    title_ar: Optional[str] = None
    scheduled_date: Optional[str] = None
    duration_minutes: Optional[int] = 90
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "scheduled"


class CourseWithSessionsPayload(BaseModel):
    course_id: Optional[int] = None
    course: CourseBase
    sessions: List[CourseSessionPayload] = []


def status_to_db(value):
    return STATUS_TO_DB.get(value, value if value in ("Upcoming", "Ongoing", "Completed") else "Upcoming")


def skill_to_db(value):
    return SKILL_TO_DB.get(value, value if value in ("Beginner", "Intermediate", "Advanced") else "Intermediate")


def insert_course(cursor, course):
    cursor.execute(
        """INSERT INTO courses
           (title, title_ar, short_name, classification, description, image_url,
            duration_weeks, total_sessions, skill_level, status, is_public,
            stages_json, batch_data_json)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            course.title,
            course.title_ar,
            course.short_name,
            course.classification,
            course.description,
            course.image_url or "",
            course.duration_weeks,
            course.total_sessions,
            skill_to_db(course.skill_level),
            status_to_db(course.status),
            course.is_public,
            json.dumps(course.stages, ensure_ascii=False) if course.stages is not None else None,
            json.dumps(course.batch_data, ensure_ascii=False) if course.batch_data is not None else None,
        ),
    )
    return cursor.lastrowid


def update_course(cursor, course_id, course):
    cursor.execute("SELECT id FROM courses WHERE id=%s", (course_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Course not found")
    cursor.execute(
        """UPDATE courses SET
           title=%s, title_ar=%s, short_name=%s, classification=%s,
           description=%s, image_url=%s, duration_weeks=%s, total_sessions=%s,
           skill_level=%s, status=%s, is_public=%s, stages_json=%s, batch_data_json=%s
           WHERE id=%s""",
        (
            course.title,
            course.title_ar,
            course.short_name,
            course.classification,
            course.description,
            course.image_url or "",
            course.duration_weeks,
            course.total_sessions,
            skill_to_db(course.skill_level),
            status_to_db(course.status),
            course.is_public,
            json.dumps(course.stages, ensure_ascii=False) if course.stages is not None else None,
            json.dumps(course.batch_data, ensure_ascii=False) if course.batch_data is not None else None,
            course_id,
        ),
    )


def upsert_session(cursor, course_id, session, index):
    # course_sessions is (id, course_id, session_date, topic, materials).
    topic = session.title or session.title_ar or f"الجلسة {index + 1}"
    session_date = session.scheduled_date
    if session.id:
        cursor.execute("SELECT id FROM course_sessions WHERE id=%s AND course_id=%s", (session.id, course_id))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE course_sessions SET course_id=%s, session_date=%s, topic=%s WHERE id=%s",
                (course_id, session_date, topic, session.id),
            )
            return session.id
    cursor.execute(
        "INSERT INTO course_sessions (course_id, session_date, topic) VALUES (%s,%s,%s)",
        (course_id, session_date, topic),
    )
    return cursor.lastrowid


@router.post("/save-with-sessions")
async def save_with_sessions(payload: CourseWithSessionsPayload, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        db.start_transaction()
        if payload.course_id:
            course_id = payload.course_id
            update_course(cursor, course_id, payload.course)
        else:
            course_id = insert_course(cursor, payload.course)

        kept_ids = []
        for index, session in enumerate(payload.sessions or []):
            kept_ids.append(upsert_session(cursor, course_id, session, index))

        cursor.execute("SELECT id FROM course_sessions WHERE course_id=%s", (course_id,))
        current_ids = {row[0] for row in cursor.fetchall()}
        for session_id in current_ids - set(kept_ids):
            cursor.execute("DELETE FROM course_sessions WHERE id=%s AND course_id=%s", (session_id, course_id))

        db.commit()
        return {"id": course_id, **payload.course.dict(), "sessions_saved": len(kept_ids)}
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save course and sessions") from exc
    finally:
        cursor.close()
        db.close()
