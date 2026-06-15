from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from core.auth import require_editor
from core.database import get_db_connection
from core.upload_manager import save_upload_file, move_course_files_to_course_folder

router = APIRouter(prefix="/api/materials", tags=["Materials"])

ALLOWED_CATEGORIES = {"technical", "financial", "political", "supporting"}


@router.post("")
async def upload_material(
    file: UploadFile = File(...),
    course_id: int = Form(0),
    category: str = Form("supporting"),
    description: str = Form(""),
    editor: dict = Depends(require_editor),
):
    if category not in ALLOWED_CATEGORIES:
        category = "supporting"

    rel_path = await save_upload_file(file, "course_material", str(course_id))

    if course_id:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT title FROM courses WHERE id = %s", (course_id,))
            row = cursor.fetchone()
            if row:
                mapping = move_course_files_to_course_folder(course_id, row["title"], [rel_path])
                rel_path = mapping.get(rel_path, rel_path)

            file_size = file.size if hasattr(file, "size") else None
            file_ext = (file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "")
            cursor.execute(
                """INSERT INTO course_materials
                   (course_id, file_name, file_path, file_type, file_size, category, uploader_id, description)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (course_id, file.filename, rel_path, file_ext, file_size, category, editor["id"], description or None),
            )
            db.commit()
            new_id = cursor.lastrowid
            return {"id": new_id, "file_path": rel_path, "filename": file.filename, "category": category}
        finally:
            cursor.close()
            db.close()

    return {"file_path": rel_path, "filename": file.filename, "category": category}


@router.get("/{course_id}")
async def list_materials(course_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT cm.*,
                      (SELECT COUNT(*) FROM session_materials sm WHERE sm.material_id = cm.id) AS linked_sessions
               FROM course_materials cm
               WHERE cm.course_id = %s AND cm.status='active'
               ORDER BY cm.id DESC""",
            (course_id,),
        )
        return cursor.fetchall() or []
    except Exception:
        return []
    finally:
        cursor.close()
        db.close()


@router.get("")
async def list_all_materials(editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT cm.*, c.title as course_title, c.title_ar,
                      (SELECT COUNT(*) FROM session_materials sm WHERE sm.material_id = cm.id) AS linked_sessions
               FROM course_materials cm
               LEFT JOIN courses c ON cm.course_id = c.id
               WHERE cm.status='active'
               ORDER BY cm.id DESC"""
        )
        return cursor.fetchall() or []
    except Exception:
        return []
    finally:
        cursor.close()
        db.close()


class MaterialUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


@router.patch("/{material_id}")
async def update_material(material_id: int, body: MaterialUpdate, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        updates, values = [], []
        if body.status is not None:
            updates.append("status=%s")
            values.append(body.status)
        if body.description is not None:
            updates.append("description=%s")
            values.append(body.description)
        if body.category is not None and body.category in ALLOWED_CATEGORIES:
            updates.append("category=%s")
            values.append(body.category)
        if not updates:
            raise HTTPException(status_code=400, detail="Nothing to update")
        values.append(material_id)
        cursor.execute(f"UPDATE course_materials SET {', '.join(updates)} WHERE id=%s", values)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Material not found")
        return {"id": material_id, "updated": True}
    finally:
        cursor.close()
        db.close()


@router.delete("/{material_id}")
async def delete_material(material_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE course_materials SET status='archived' WHERE id=%s", (material_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Material not found")
        return {"id": material_id, "deleted": True}
    finally:
        cursor.close()
        db.close()
