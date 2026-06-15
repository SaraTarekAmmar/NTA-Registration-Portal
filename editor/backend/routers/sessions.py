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
    description: Optional[str] = None
    content: Optional[str] = None
    objectives: Optional[str] = None
    notes: Optional[str] = None

    def resolved_topic(self):
        return self.topic or self.title or self.title_ar

    def resolved_date(self):
        return self.session_date or self.scheduled_date


class LinkMaterial(BaseModel):
    material_id: int


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
            """INSERT INTO course_sessions
               (course_id, session_date, topic, description, content, objectives, notes)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (session.course_id, session.resolved_date(), session.resolved_topic(),
             session.description, session.content, session.objectives, session.notes)
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
            """UPDATE course_sessions
               SET course_id=%s, session_date=%s, topic=%s,
                   description=%s, content=%s, objectives=%s, notes=%s
               WHERE id=%s""",
            (session.course_id, session.resolved_date(), session.resolved_topic(),
             session.description, session.content, session.objectives, session.notes, session_id)
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


# ── Session ↔ Material linking (reuse-not-duplicate) ──────────────────

def _session_course_id(cursor, session_id):
    cursor.execute("SELECT course_id FROM course_sessions WHERE id=%s", (session_id,))
    row = cursor.fetchone()
    return row[0] if row else None


@router.get("/{session_id}/materials")
async def list_session_materials(session_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT m.id, m.file_name, m.file_path, m.file_type, m.file_size,
                      m.category, m.description, sm.created_at AS linked_at
               FROM session_materials sm
               JOIN course_materials m ON m.id = sm.material_id
               WHERE sm.session_id = %s
               ORDER BY sm.created_at DESC, m.id DESC""",
            (session_id,),
        )
        return cursor.fetchall() or []
    finally:
        cursor.close()
        db.close()


@router.post("/{session_id}/materials", status_code=201)
async def link_session_material(session_id: int, body: LinkMaterial, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        sess_course = _session_course_id(cursor, session_id)
        if sess_course is None:
            raise HTTPException(status_code=404, detail="Session not found")
        cursor.execute("SELECT course_id FROM course_materials WHERE id=%s", (body.material_id,))
        mat = cursor.fetchone()
        if not mat:
            raise HTTPException(status_code=404, detail="Material not found")
        if mat[0] != sess_course:
            raise HTTPException(status_code=400, detail="المادة لا تنتمي إلى دورة هذه الجلسة")
        cursor.execute(
            "SELECT id FROM session_materials WHERE session_id=%s AND material_id=%s",
            (session_id, body.material_id),
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="المادة مرتبطة بالفعل بهذه الجلسة")
        cursor.execute(
            "INSERT INTO session_materials (session_id, material_id) VALUES (%s,%s)",
            (session_id, body.material_id),
        )
        db.commit()
        return {"linked": True, "session_id": session_id, "material_id": body.material_id}
    finally:
        cursor.close()
        db.close()


@router.delete("/{session_id}/materials/{material_id}")
async def unlink_session_material(session_id: int, material_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        # Only removes the relation — the uploaded file/material is never deleted.
        cursor.execute(
            "DELETE FROM session_materials WHERE session_id=%s AND material_id=%s",
            (session_id, material_id),
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Link not found")
        return {"unlinked": True}
    finally:
        cursor.close()
        db.close()
