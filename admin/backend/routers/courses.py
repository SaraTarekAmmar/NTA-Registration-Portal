from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import List, Optional
from schemas.course import Course, CourseCreate
from core.database import get_db_connection
from core.auth import get_staff_user, require_editor, get_admin_user
from core.upload_manager import move_course_files_to_course_folder, save_upload_file
import csv
import io
import json

router = APIRouter(prefix="/api/courses", tags=["Courses"])

@router.get("", response_model=List[Course])
async def get_courses(staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.*, caa.nature as course_type
            FROM courses c
            LEFT JOIN course_ai_analysis caa ON c.id = caa.course_id
        """)
        rows = cursor.fetchall()
        for row in rows:
            # Map DB columns to schema field names and parse JSON if needed
            if row.get('stages_json'):
                row['stages'] = json.loads(row['stages_json']) if isinstance(row['stages_json'], str) else row['stages_json']
            else:
                row['stages'] = []
                
            if row.get('batch_data_json'):
                row['batch_data'] = json.loads(row['batch_data_json']) if isinstance(row['batch_data_json'], str) else row['batch_data_json']
            else:
                row['batch_data'] = {}
        return rows
    finally:
        cursor.close()
        db.close()

@router.post("", response_model=Course)
async def create_course(course: CourseCreate, staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        query = """
            INSERT INTO courses
                (title, title_ar, short_name, classification, description,
                 image_url, duration_weeks, total_sessions, skill_level,
                 status, is_public, stages_json, batch_data_json)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            course.title,
            course.title_ar,
            course.short_name,
            course.classification,
            course.description,
            course.image_url,
            course.duration_weeks,
            course.total_sessions,
            course.skill_level,
            course.status,
            course.is_public,
            json.dumps(course.stages, ensure_ascii=False) if course.stages is not None else None,
            json.dumps(course.batch_data, ensure_ascii=False) if course.batch_data is not None else None,
        )
        cursor.execute(query, values)
        db.commit()
        course_id = cursor.lastrowid

        # ── Move image to course-specific folder ──
        if course.image_url:
            path_map = move_course_files_to_course_folder(course_id, course.title, [course.image_url])
            course.image_url = path_map.get(course.image_url, course.image_url)
            # Update DB with new path
            cursor.execute("UPDATE courses SET image_url = %s WHERE id = %s", (course.image_url, course_id))
            db.commit()

        # ── NEW: Sync Course Sessions and Rename Files ──
        sync_course_sessions(db, course_id, course.title, course.batch_data)

        from core.logger_util import log_activity
        log_activity(
            category="ADMIN",
            event_type="COURSE_CREATED",
            user_id=staff.get("id"),
            role=staff.get("role"),
            details={"course_id": course_id, "title": course.title}
        )
        # Re-fetch from DB so the response matches exactly what GET /api/courses returns
        # (stages_json and batch_data_json are parsed back from JSON strings, not raw Python objects)
        cursor2 = db.cursor(dictionary=True)
        try:
            cursor2.execute("""
                SELECT c.*, caa.nature as course_type
                FROM courses c
                LEFT JOIN course_ai_analysis caa ON c.id = caa.course_id
                WHERE c.id = %s
            """, (course_id,))
            row = cursor2.fetchone()
            if row:
                row['stages'] = json.loads(row['stages_json']) if isinstance(row.get('stages_json'), str) else (row.get('stages_json') or [])
                row['batch_data'] = json.loads(row['batch_data_json']) if isinstance(row.get('batch_data_json'), str) else (row.get('batch_data_json') or {})
            return row
        finally:
            cursor2.close()
    finally:
        cursor.close()
        db.close()

def sync_course_sessions(db, course_id, course_title, batch_data):
    """
    Syncs the batch_data (JSON) with the course_sessions (Table).
    Also renames physical files on disk based on the session topic.
    """
    import os
    import shutil
    import json
    from pathlib import Path
    
    if not batch_data:
        return
        
    # Project root is 4 levels up from admin/backend/routers/courses.py
    ROOT = Path(__file__).parent.parent.parent.parent
    
    cursor = db.cursor(dictionary=True)
    try:
        # BUG FIX: Previously this function ran DELETE FROM course_sessions WHERE course_id = %s
        # before re-inserting. Because attendance_logs has ON DELETE CASCADE linked to course_sessions,
        # this wiped all attendance records every time a course was saved.
        #
        # Fix: Use an UPSERT strategy instead.
        # 1. Collect all new session keys (batch_key + index) from batch_data.
        # 2. For each session, INSERT or UPDATE using a stable unique key (batch_key + session_index).
        # 3. DELETE only sessions that are no longer present in the new batch_data.
        # This preserves existing session IDs and their linked attendance_logs.

        # Fetch existing sessions keyed by (batch_key, session_index) if that column exists,
        # otherwise fall back to topic-based matching.
        cursor.execute(
            "SELECT id, topic, batch_key, session_index FROM course_sessions WHERE course_id = %s",
            (course_id,)
        )
        existing_rows = cursor.fetchall()
        # Build a lookup: (batch_key, session_index) -> session_id
        existing_map = {}
        for row in existing_rows:
            bk = row.get("batch_key") or ""
            si = row.get("session_index")
            if bk and si is not None:
                existing_map[(bk, si)] = row["id"]

        new_keys = set()  # track which (batch_key, session_index) pairs exist in new data

        # 2. Iterate through batches and sessions
        # batchData structure: key = 's{stageId}b{bIdx}' -> {sessionNames:[], sessionMaterials:[], sessionDates:[]}
        for key, bd in batch_data.items():
            session_names = bd.get('sessionNames', [])
            session_materials = bd.get('sessionMaterials', []) # List of lists
            session_dates = bd.get('sessionDates', [])
            
            for i, topic in enumerate(session_names):
                if not topic:
                    topic = f"Session {i+1}"
                
                mats = session_materials[i] if i < len(session_materials) else []
                s_date = session_dates[i] if i < len(session_dates) else None
                
                materials_json = {"file_path": None, "links": []}
                
                if isinstance(mats, list) and len(mats) > 0:
                    old_rel_path = mats[0]
                    if old_rel_path and isinstance(old_rel_path, str):
                        # 1. Ensure it's in the course folder
                        from core.upload_manager import move_course_files_to_course_folder
                        path_map = move_course_files_to_course_folder(course_id, course_title, [old_rel_path])
                        current_rel_path = path_map.get(old_rel_path, old_rel_path)
                        
                        # 2. RENAME on disk to match Topic
                        full_path = ROOT / current_rel_path.lstrip('/')
                        if full_path.exists():
                            ext = full_path.suffix
                            import re
                            # Safe filename: keep arabic but remove weird symbols
                            # For now just underscores for spaces and remove non-word
                            safe_topic = re.sub(r'[^\w\s]', '', topic).strip().replace(' ', '_')
                            if not safe_topic: safe_topic = f"session_{i+1}"
                            
                            new_filename = f"Session_{i+1}_{safe_topic}{ext}"
                            new_full_path = full_path.parent / new_filename
                            
                            try:
                                # BUG 10 FIX: the old guard compared old_rel_path to materials_json["file_path"]
                                # which is always None at this point — making the condition always True.
                                # Correct guard: only rename if source and destination are different paths.
                                if full_path != new_full_path:
                                    os.rename(full_path, new_full_path)
                                
                                # Update relative path
                                rel_dir = os.path.dirname(current_rel_path).replace("\\", "/")
                                materials_json["file_path"] = f"{rel_dir}/{new_filename}"
                            except Exception as e:
                                print(f"Error renaming session file: {e}")
                                materials_json["file_path"] = current_rel_path
                        else:
                            materials_json["file_path"] = current_rel_path
                
                # 3. UPSERT into course_sessions
                # If a session with this (batch_key, session_index) already exists, UPDATE it
                # to preserve its primary key (id) and linked attendance_logs.
                # Otherwise INSERT a new row.
                new_keys.add((key, i))
                existing_id = existing_map.get((key, i))
                if existing_id:
                    cursor.execute("""
                        UPDATE course_sessions
                        SET session_date = %s, topic = %s, materials = %s
                        WHERE id = %s
                    """, (s_date, topic, json.dumps(materials_json, ensure_ascii=False), existing_id))
                else:
                    cursor.execute("""
                        INSERT INTO course_sessions (course_id, session_date, topic, materials, batch_key, session_index)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (course_id, s_date, topic, json.dumps(materials_json, ensure_ascii=False), key, i))

        # 4. Remove sessions that are no longer in batch_data.
        # Only delete sessions that have a batch_key (i.e., managed by this sync).
        # Sessions without a batch_key are manually created and must not be touched.
        stale_ids = [
            sid for (bk, si), sid in existing_map.items()
            if (bk, si) not in new_keys
        ]
        if stale_ids:
            placeholders = ",".join(["%s"] * len(stale_ids))
            cursor.execute(
                f"DELETE FROM course_sessions WHERE id IN ({placeholders})",
                tuple(stale_ids)
            )

        db.commit()
    finally:
        cursor.close()

@router.get("/{course_id}", response_model=Course)
async def get_course(course_id: int, staff: dict = Depends(get_staff_user)):
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


@router.get("/{course_id}/sessions")
async def get_course_sessions(course_id: int, staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, topic, session_date, materials FROM course_sessions WHERE course_id = %s ORDER BY id",
            (course_id,)
        )
        sessions = cursor.fetchall()
        for s in sessions:
            raw = s.get('materials')
            m_data = []
            if raw:
                try:
                    parsed = json.loads(raw) if isinstance(raw, str) else raw
                    if isinstance(parsed, dict) and "file_path" in parsed:
                        fname = parsed["file_path"].split("/")[-1] if parsed["file_path"] else ""
                        m_data = [{"id": f"m_{s['id']}_1", "name": fname,
                                   "type": fname.rsplit(".", 1)[-1] if "." in fname else "file",
                                   "path": parsed["file_path"]}]
                    elif isinstance(parsed, list):
                        m_data = parsed
                except Exception:
                    m_data = []
            s['materials'] = m_data
        return {"sessions": sessions}
    finally:
        cursor.close()
        db.close()


@router.put("/{course_id}", response_model=Course)
async def update_course(course_id: int, course: CourseCreate, staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        query = """
            UPDATE courses SET
                title=%s, title_ar=%s, short_name=%s, classification=%s,
                description=%s, image_url=%s, duration_weeks=%s,
                total_sessions=%s, skill_level=%s, status=%s, is_public=%s,
                stages_json=%s, batch_data_json=%s
            WHERE id=%s
        """
        values = (
            course.title,
            course.title_ar,
            course.short_name,
            course.classification,
            course.description,
            course.image_url,
            course.duration_weeks,
            course.total_sessions,
            course.skill_level,
            course.status,
            course.is_public,
            json.dumps(course.stages, ensure_ascii=False) if course.stages is not None else None,
            json.dumps(course.batch_data, ensure_ascii=False) if course.batch_data is not None else None,
            course_id,
        )
        cursor.execute(query, values)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Course not found")
            
        # ── NEW: Sync Course Sessions and Rename Files ──
        sync_course_sessions(db, course_id, course.title, course.batch_data)

        # Log Archival if status is Completed or Archived
        if course.status in ['Completed', 'Archived']:
            from core.logger_util import log_activity
            log_activity(
                category="ADMIN",
                event_type="COURSE_ARCHIVED",
                user_id=staff.get("id"),
                role=staff.get("role"),
                details={"course_id": course_id, "status": course.status, "title": course.title}
            )

        # Re-fetch from DB so the response matches exactly what GET /api/courses returns
        cursor2 = db.cursor(dictionary=True)
        try:
            cursor2.execute("""
                SELECT c.*, caa.nature as course_type
                FROM courses c
                LEFT JOIN course_ai_analysis caa ON c.id = caa.course_id
                WHERE c.id = %s
            """, (course_id,))
            row = cursor2.fetchone()
            if row:
                row['stages'] = json.loads(row['stages_json']) if isinstance(row.get('stages_json'), str) else (row.get('stages_json') or [])
                row['batch_data'] = json.loads(row['batch_data_json']) if isinstance(row.get('batch_data_json'), str) else (row.get('batch_data_json') or {})
            return row
        finally:
            cursor2.close()
    finally:
        cursor.close()
        db.close()

@router.delete("/{course_id}")
async def delete_course(course_id: int, staff: dict = Depends(get_admin_user)):
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

@router.post("/bulk-enroll")
async def bulk_enroll(
    course_id: int = Form(...),
    file: UploadFile = File(...),
    staff: dict = Depends(get_admin_user)
):
    """
    Unified bulk enrollment/assignment endpoint.
    Expects CSV or Excel. First row must be 'trainees' or 'trainers'.
    """
    content = await file.read()
    filename = file.filename.lower()
    
    ids = []
    mode = None # 'trainees' or 'trainers'
    
    if filename.endswith('.csv'):
        text_content = content.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(text_content))
        rows = list(reader)
        if not rows:
            raise HTTPException(status_code=400, detail="Empty file")
        
        mode = rows[0][0].strip().lower()
        if mode not in ['trainees', 'trainers']:
            raise HTTPException(status_code=400, detail="First row must be 'trainees' or 'trainers'")
        
        for row in rows[1:]:
            if row and row[0].strip():
                ids.append(row[0].strip())
    
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        # Placeholder for Excel support (Step 6 in task list)
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content))
            sheet = wb.active
            rows = list(sheet.rows)
            if not rows:
                raise HTTPException(status_code=400, detail="Empty file")
            
            mode = str(rows[0][0].value).strip().lower()
            if mode not in ['trainees', 'trainers']:
                raise HTTPException(status_code=400, detail="First cell must be 'trainees' or 'trainers'")
            
            for row in rows[1:]:
                if row[0].value:
                    ids.append(str(row[0].value).strip())
        except ImportError:
            raise HTTPException(status_code=500, detail="Excel support not installed. Please use CSV for now.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading Excel: {str(e)}")
    # ── NEW: Save the enrollment file to the course folder ──
    # Reset file cursor after initial read (important for saving)
    await file.seek(0)
    # Save to temp
    temp_path = await save_upload_file(file, "temp", f"bulk_enroll_{course_id}")

    # Use existing cursor or create one
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    count = 0
    try:
        # 1. Fetch course title to move files
        cursor.execute("SELECT title FROM courses WHERE id = %s", (course_id,))
        c_info = cursor.fetchone()
        if c_info:
            move_course_files_to_course_folder(course_id, c_info['title'], [temp_path])

        if not ids:
            return {"message": "No valid National IDs found in the file.", "enrolled_count": 0}

        # Ensure course exists
        cursor.execute("SELECT id FROM courses WHERE id = %s", (course_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Course not found")

        for nid in ids:
            # Check if user exists
            cursor.execute("SELECT id, role FROM users WHERE national_id = %s", (nid,))
            user = cursor.fetchone()
            if not user:
                continue
            
            uid, role = user
            
            if mode == 'trainees':
                # Check if already applied
                cursor.execute("SELECT id FROM applications WHERE user_id = %s AND course_id = %s", (uid, course_id))
                if not cursor.fetchone():
                    # BUG 11 FIX: '{}' values were baked into the SQL string literal.
                    # Moving them to the parameter tuple ensures MySQL's connector
                    # validates them as JSON before inserting into json-typed columns.
                    empty_json = '{}'
                    cursor.execute("""
                        INSERT INTO applications
                            (user_id, course_id, status, motivation_data, research_publication,
                             references_data, logistics, identity_photos, quiz_results, quiz_scores)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (uid, course_id, 'approved',
                           empty_json, empty_json, empty_json,
                           empty_json, empty_json, empty_json, empty_json))
                    
                    # Update pipeline state
                    cursor.execute("SELECT id FROM pipeline_state WHERE trainee_id = %s", (uid,))
                    if cursor.fetchone():
                        cursor.execute("UPDATE pipeline_state SET current_stage_id = 1, status = 'active' WHERE trainee_id = %s", (uid,))
                    else:
                        cursor.execute("INSERT INTO pipeline_state (trainee_id, current_stage_id, status) VALUES (%s, 1, 'active')", (uid,))
                    
                    # Track private assignment
                    cursor.execute("SELECT id FROM private_course_assignments WHERE course_id = %s AND national_id = %s", (course_id, nid))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO private_course_assignments (course_id, national_id) VALUES (%s, %s)", (course_id, nid))
                    count += 1
            
            elif mode == 'trainers':
                # Assign as trainer
                cursor.execute("SELECT id FROM course_trainers WHERE course_id = %s AND trainer_national_id = %s", (course_id, nid))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO course_trainers (course_id, trainer_national_id) VALUES (%s, %s)", (course_id, nid))
                    count += 1
        
        db.commit()
        
        if count > 0:
            from core.logger_util import log_activity
            log_activity(
                category="ADMIN",
                event_type="TRAINER_ASSIGNMENT" if mode == 'trainers' else "BULK_ENROLLMENT",
                user_id=staff.get("id"),
                role=staff.get("role"),
                details={"course_id": course_id, "count": count, "mode": mode}
            )

        return {"message": f"Successfully processed {count} {mode}.", "enrolled_count": count, "mode": mode}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()
