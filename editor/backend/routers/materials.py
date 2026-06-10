from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from core.auth import require_editor
from core.database import get_db_connection
from core.upload_manager import save_upload_file, move_course_files_to_course_folder

router = APIRouter(prefix="/api/materials", tags=["Materials"])


@router.post("")
async def upload_material(
    file: UploadFile = File(...),
    course_id: int = Form(0),
    editor: dict = Depends(require_editor)
):
    """Upload a course material file. Returns the saved file path."""
    rel_path = await save_upload_file(file, "course_material", str(course_id))

    if course_id:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT title FROM courses WHERE id = %s", (course_id,))
            row = cursor.fetchone()
            if row:
                move_course_files_to_course_folder(course_id, row["title"], [rel_path])
        finally:
            cursor.close()
            db.close()

    return {"file_path": rel_path, "filename": file.filename}


@router.get("/{course_id}")
async def list_materials(course_id: int, editor: dict = Depends(require_editor)):
    """List materials linked to a course from the course_materials table (if it exists)."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        try:
            cursor.execute(
                "SELECT * FROM course_materials WHERE course_id = %s ORDER BY id DESC",
                (course_id,)
            )
            return cursor.fetchall()
        except Exception:
            # Table may not exist yet; return empty list gracefully
            return []
    finally:
        cursor.close()
        db.close()
