import json
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from core.auth import require_editor
from core.database import get_db_connection
from core.upload_manager import save_upload_file, move_course_files_to_course_folder
from schemas.course import CourseBase

router = APIRouter(prefix="/api/courses", tags=["Courses"])

# DB enums are ('Upcoming','Ongoing','Completed') / ('Beginner','Intermediate','Advanced');
# the editor UI speaks draft/published/archived and Arabic skill levels.
STATUS_TO_DB = {"draft": "Upcoming", "published": "Ongoing", "archived": "Completed", "قادم": "Upcoming"}
DB_TO_STATUS = {"Upcoming": "draft", "Ongoing": "published", "Completed": "archived"}
SKILL_TO_DB = {"مبتدئ": "Beginner", "متوسط": "Intermediate", "متقدم": "Advanced"}


def status_to_db(value):
    return STATUS_TO_DB.get(value, value if value in DB_TO_STATUS else "Upcoming")


def skill_to_db(value):
    return SKILL_TO_DB.get(value, value if value in ("Beginner", "Intermediate", "Advanced") else "Intermediate")


@router.get("")
async def list_courses(editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.*, caa.nature as course_type,
                   (SELECT COUNT(*) FROM course_materials cm WHERE cm.course_id = c.id AND cm.status='active') AS materials_count,
                   (SELECT COUNT(*) FROM course_sessions cs WHERE cs.course_id = c.id) AS sessions_count
            FROM courses c
            LEFT JOIN course_ai_analysis caa ON c.id = caa.course_id
            ORDER BY c.id DESC
        """)
        rows = cursor.fetchall()
        for row in rows:
            try:
                row['stages'] = json.loads(row['stages_json']) if isinstance(row.get('stages_json'), str) else (row.get('stages_json') or [])
            except json.JSONDecodeError:
                row['stages'] = []
            try:
                row['batch_data'] = json.loads(row['batch_data_json']) if isinstance(row.get('batch_data_json'), str) else (row.get('batch_data_json') or {})
            except json.JSONDecodeError:
                row['batch_data'] = {}
            row['status'] = DB_TO_STATUS.get(row.get('status'), row.get('status'))
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
        try:
            row['stages'] = json.loads(row['stages_json']) if isinstance(row.get('stages_json'), str) else (row.get('stages_json') or [])
        except json.JSONDecodeError:
            row['stages'] = []
        try:
            row['batch_data'] = json.loads(row['batch_data_json']) if isinstance(row.get('batch_data_json'), str) else (row.get('batch_data_json') or {})
        except json.JSONDecodeError:
            row['batch_data'] = {}
        row['status'] = DB_TO_STATUS.get(row.get('status'), row.get('status'))
        return row
    finally:
        cursor.close()
        db.close()


@router.post("")
async def create_course(course: CourseBase, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        if status_to_db(course.status) == "Ongoing":
            raise HTTPException(status_code=400, detail="لا يمكن إنشاء الدورة كمنشورة مباشرة. يجب إنشاؤها كمسودة أولاً وإضافة الجلسات والمواد.")
            
        cursor.execute(
            """INSERT INTO courses
               (title, title_ar, short_name, classification, description, image_url,
                duration_weeks, total_sessions, skill_level, status, is_public,
                stages_json, batch_data_json)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                course.title, course.title_ar, course.short_name, course.classification,
                course.description, course.image_url or "", course.duration_weeks,
                course.total_sessions, skill_to_db(course.skill_level), status_to_db(course.status), course.is_public,
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
        if status_to_db(course.status) == "Ongoing":
            cursor.execute("SELECT id FROM course_sessions WHERE course_id=%s", (course_id,))
            sessions = cursor.fetchall()
            if not sessions:
                raise HTTPException(status_code=400, detail="لا يمكن نشر الدورة: يجب إضافة جلسة واحدة على الأقل.")
            for sess in sessions:
                cursor.execute("SELECT id FROM session_materials WHERE session_id=%s", (sess[0],))
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail="لا يمكن نشر الدورة: جميع الجلسات يجب أن تحتوي على مادة تعليمية واحدة على الأقل.")

        cursor.execute(
            """UPDATE courses SET
               title=%s, title_ar=%s, short_name=%s, classification=%s,
               description=%s, image_url=%s, duration_weeks=%s, total_sessions=%s,
               skill_level=%s, status=%s, is_public=%s, stages_json=%s, batch_data_json=%s
               WHERE id=%s""",
            (
                course.title, course.title_ar, course.short_name, course.classification,
                course.description, course.image_url or "", course.duration_weeks,
                course.total_sessions, skill_to_db(course.skill_level), status_to_db(course.status), course.is_public,
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
            "SELECT * FROM course_sessions WHERE course_id = %s ORDER BY session_date, id",
            (course_id,)
        )
        return cursor.fetchall() or []
    finally:
        cursor.close()
        db.close()


@router.post("/cover-image")
async def upload_course_cover(
    file: UploadFile = File(...),
    editor: dict = Depends(require_editor)
):
    # Pass "0" as ref_id since course_id might not exist yet
    rel_path = await save_upload_file(file, "course_image", "0")
    return {"image_url": rel_path}
