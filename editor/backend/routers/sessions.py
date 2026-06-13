import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from core.auth import require_editor
from core.database import get_db_connection

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


# The course_sessions table is (id, course_id, session_date, topic, materials).
# The frontend speaks topic/session_date but also sends legacy title/scheduled_date —
# accept either and normalize here.
class SessionCreate(BaseModel):
    course_id: int
    topic: Optional[str] = None
    title: Optional[str] = None
    title_ar: Optional[str] = None
    session_date: Optional[str] = None
    scheduled_date: Optional[str] = None
    status: Optional[str] = None

    def resolved_topic(self):
        return self.topic or self.title or self.title_ar

    def resolved_date(self):
        return self.session_date or self.scheduled_date


@router.get("")
async def list_sessions(course_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM course_sessions WHERE course_id = %s ORDER BY session_date, id",
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
            "INSERT INTO course_sessions (course_id, session_date, topic) VALUES (%s,%s,%s)",
            (session.course_id, session.resolved_date(), session.resolved_topic())
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
            "UPDATE course_sessions SET course_id=%s, session_date=%s, topic=%s WHERE id=%s",
            (session.course_id, session.resolved_date(), session.resolved_topic(), session_id)
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
