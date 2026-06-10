import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from core.auth import require_editor
from core.database import get_db_connection

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


class SessionCreate(BaseModel):
    course_id: int
    session_number: Optional[int] = None
    title: Optional[str] = None
    title_ar: Optional[str] = None
    scheduled_date: Optional[str] = None
    duration_minutes: Optional[int] = 90
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "scheduled"


@router.get("")
async def list_sessions(course_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM course_sessions WHERE course_id = %s ORDER BY session_number",
            (course_id,)
        )
        return cursor.fetchall() or []
    finally:
        cursor.close()
        db.close()


@router.post("")
async def create_session(session: SessionCreate, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            """INSERT INTO course_sessions
               (course_id, session_number, title, title_ar, scheduled_date,
                duration_minutes, location, notes, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                session.course_id, session.session_number, session.title,
                session.title_ar, session.scheduled_date, session.duration_minutes,
                session.location, session.notes, session.status
            )
        )
        db.commit()
        return {"id": cursor.lastrowid, **session.dict()}
    finally:
        cursor.close()
        db.close()


@router.put("/{session_id}")
async def update_session(session_id: int, session: SessionCreate, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            """UPDATE course_sessions SET
               course_id=%s, session_number=%s, title=%s, title_ar=%s,
               scheduled_date=%s, duration_minutes=%s, location=%s,
               notes=%s, status=%s
               WHERE id=%s""",
            (
                session.course_id, session.session_number, session.title,
                session.title_ar, session.scheduled_date, session.duration_minutes,
                session.location, session.notes, session.status, session_id
            )
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"id": session_id, **session.dict()}
    finally:
        cursor.close()
        db.close()


@router.delete("/{session_id}")
async def delete_session(session_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM course_sessions WHERE id=%s", (session_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted"}
    finally:
        cursor.close()
        db.close()
