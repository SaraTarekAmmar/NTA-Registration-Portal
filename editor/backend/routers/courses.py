import json
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from core.auth import require_editor
from core.database import get_db_connection
from core.upload_manager import save_upload_file, move_course_files_to_course_folder
from schemas.course import CourseBase

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("")
async def list_courses(editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.*, caa.nature as course_type
            FROM courses c
            LEFT JOIN course_ai_analysis caa ON c.id = caa.course_id
            ORDER BY c.id DESC
        """)
        rows = cursor.fetchall()
        for row in rows:
            row['stages'] = json.loads(row['stages_json']) if isinstance(row.get('stages_json'), str) else (row.get('stages_json') or [])
            row['batch_data'] = json.loads(row['batch_data_json']) if isinstance(row.get('batch_data_json'), str) else (row.get('batch_data_json') or {})
        return rows
    finally:
        cursor.close()
        db.close()


@router.get("/{course_id}")
async def get_course(course_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.*, caa.nature as course_type
            FROM courses c
            LEFT JOIN course_ai_analysis caa ON c.id = caa.course_id
            WHERE c.id = %s
        """, (course_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Course not found")
        row['stages'] = json.loads(row['stages_json']) if isinstance(row.get('stages_json'), str) else (row.get('stages_json') or [])
        row['batch_data'] = json.loads(row['batch_data_json']) if isinstance(row.get('batch_data_json'), str) else (row.get('batch_data_json') or {})
        return row
    finally:
        cursor.close()
        db.close()


@router.post("")
async def create_course(course: CourseBase, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            """INSERT INTO courses
               (title, title_ar, short_name, classification, description, image_url,
                duration_weeks, total_sessions, skill_level, status, is_public,
                stages_json, batch_data_json)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                course.title, course.title_ar, course.short_name, course.classification,
                course.description, course.image_url, course.duration_weeks,
                course.total_sessions, course.skill_level, course.status, course.is_public,
                json.dumps(course.stages, ensure_ascii=False) if course.stages is not None else None,
                json.dumps(course.batch_data, ensure_ascii=False) if course.batch_data is not None else None,
            )
        )
        db.commit()
        new_id = cursor.lastrowid
        return {"id": new_id, **course.dict()}
    finally:
        cursor.close()
        db.close()


@router.put("/{course_id}")
async def update_course(course_id: int, course: CourseBase, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            """UPDATE courses SET
               title=%s, title_ar=%s, short_name=%s, classification=%s,
               description=%s, image_url=%s, duration_weeks=%s, total_sessions=%s,
               skill_level=%s, status=%s, is_public=%s, stages_json=%s, batch_data_json=%s
               WHERE id=%s""",
            (
                course.title, course.title_ar, course.short_name, course.classification,
                course.description, course.image_url, course.duration_weeks,
                course.total_sessions, course.skill_level, course.status, course.is_public,
                json.dumps(course.stages, ensure_ascii=False) if course.stages is not None else None,
                json.dumps(course.batch_data, ensure_ascii=False) if course.batch_data is not None else None,
                course_id,
            )
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"id": course_id, **course.dict()}
    finally:
        cursor.close()
        db.close()


@router.delete("/{course_id}")
async def delete_course(course_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM courses WHERE id=%s", (course_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"message": "Course deleted successfully"}
    finally:
        cursor.close()
        db.close()


@router.get("/{course_id}/sessions")
async def get_course_sessions(course_id: int, editor: dict = Depends(require_editor)):
    """Alias used by editor-sessions.html to load sessions for a course."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM course_sessions WHERE course_id = %s ORDER BY session_number",
            (course_id,)
        )
        return cursor.fetchall() or []
    except Exception:
        return []
    finally:
        cursor.close()
        db.close()


@router.post("/upload-image")
async def upload_course_image(
    file: UploadFile = File(...),
    course_id: int = Form(0),
    editor: dict = Depends(require_editor)
):
    rel_path = await save_upload_file(file, "course_image", str(course_id))
    return {"file_path": rel_path}
