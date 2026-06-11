import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from core.auth import require_editor
from core.database import get_db_connection

router = APIRouter(prefix="/api/planning", tags=["Course Planning"])


class PlanningBase(BaseModel):
    domain: Optional[str] = "other"
    tags: Optional[List[str]] = None
    level: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    schedule_json: Optional[List[Dict[str, Any]]] = None
    instructor: Optional[str] = None
    capacity: Optional[int] = None
    prerequisites: Optional[str] = None
    syllabus: Optional[str] = None
    outcomes: Optional[str] = None


@router.get("/{course_id}")
async def get_planning(course_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM course_planning WHERE course_id=%s", (course_id,))
        row = cursor.fetchone()
        if not row:
            return {}
        for field in ("tags", "schedule_json"):
            if isinstance(row.get(field), str):
                try:
                    row[field] = json.loads(row[field])
                except Exception:
                    row[field] = None
        return row
    finally:
        cursor.close()
        db.close()


@router.put("/{course_id}")
async def upsert_planning(course_id: int, body: PlanningBase, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM courses WHERE id=%s", (course_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Course not found")

        cursor.execute("SELECT id FROM course_planning WHERE course_id=%s", (course_id,))
        existing = cursor.fetchone()

        tags_json = json.dumps(body.tags, ensure_ascii=False) if body.tags else None
        schedule = json.dumps(body.schedule_json, ensure_ascii=False) if body.schedule_json else None
        start = body.start_date or None
        end = body.end_date or None

        if existing:
            cursor.execute(
                """UPDATE course_planning SET
                   domain=%s, tags=%s, level=%s, start_date=%s, end_date=%s,
                   schedule_json=%s, instructor=%s, capacity=%s,
                   prerequisites=%s, syllabus=%s, outcomes=%s
                   WHERE course_id=%s""",
                (body.domain, tags_json, body.level, start, end,
                 schedule, body.instructor, body.capacity,
                 body.prerequisites, body.syllabus, body.outcomes,
                 course_id),
            )
        else:
            cursor.execute(
                """INSERT INTO course_planning
                   (course_id, domain, tags, level, start_date, end_date,
                    schedule_json, instructor, capacity, prerequisites, syllabus, outcomes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (course_id, body.domain, tags_json, body.level, start, end,
                 schedule, body.instructor, body.capacity,
                 body.prerequisites, body.syllabus, body.outcomes),
            )
        db.commit()
        return {"course_id": course_id, **body.dict()}
    finally:
        cursor.close()
        db.close()
