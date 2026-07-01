import json
from typing import List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Body
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


VALID_REGISTRATION_TYPES = {
    'personal_info', 'contact_info', 'education_bg', 'standardized_tests',
    'work_experience', 'skills_languages', 'awards_conferences',
    'legal_status', 'document_uploads', 'references_social', 'final_acknowledgement',
    # Fallback types from flow builder just in case:
    'document_upload', 'custom_question'
}

def sync_course_steps(cursor, course_id, steps, path_type):
    # Delete existing
    cursor.execute("DELETE FROM course_steps WHERE course_id=%s AND path_type=%s", (course_id, path_type))
    if not steps:
        return
        
    for idx, step in enumerate(steps):
        step_type = step.get('step_type', '')
        if path_type == 'registration' and step_type not in VALID_REGISTRATION_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid registration step type: {step_type}")
            
        cursor.execute(
            """INSERT INTO course_steps 
               (course_id, path_type, step_key, step_type, title_ar, step_order, is_required, config_json) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                course_id,
                path_type,
                step.get('step_key', f"{path_type}_{idx}"),
                step_type,
                step.get('title_ar', 'بدون عنوان'),
                step.get('step_order', idx),
                int(step.get('is_required', 1)),
                json.dumps(step.get('config_json', {}), ensure_ascii=False)
            )
        )



import datetime as _dt
from decimal import Decimal as _Decimal


@router.get("")
async def list_courses(editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.id, c.title, c.title_ar, c.short_name, c.status, c.skill_level,
                   c.classification, c.description, c.image_url,
                   c.duration_weeks, c.total_sessions, c.is_public,
                   (SELECT COUNT(*) FROM course_materials cm WHERE cm.course_id = c.id AND cm.status='active') AS materials_count,
                   (SELECT COUNT(*) FROM course_sessions cs WHERE cs.course_id = c.id) AS sessions_count
            FROM courses c
            ORDER BY c.id DESC
        """)
        rows = cursor.fetchall()
        clean = []
        for row in rows:
            safe = {}
            for k, v in row.items():
                if isinstance(v, (_dt.datetime, _dt.date)):
                    safe[k] = v.isoformat()
                elif isinstance(v, _Decimal):
                    safe[k] = float(v)
                else:
                    safe[k] = v
            safe['status'] = DB_TO_STATUS.get(safe.get('status'), safe.get('status'))
            clean.append(safe)
        return clean
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
        
        cursor.execute("SELECT step_key, step_type, title_ar, step_order, is_required, config_json FROM course_steps WHERE course_id=%s AND path_type='registration' ORDER BY step_order", (course_id,))
        steps = cursor.fetchall()
        for s in steps:
            if isinstance(s.get('config_json'), str):
                try:
                    s['config_json'] = json.loads(s['config_json'])
                except:
                    s['config_json'] = {}
        row['registration_steps'] = steps
        
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
        
        if course.registration_steps is not None:
            sync_course_steps(cursor, new_id, course.registration_steps, 'registration')
            db.commit()
            
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
            # Check if course actually exists to avoid 404 when no fields changed
            cursor.execute("SELECT id FROM courses WHERE id=%s", (course_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Course not found")
                
        if course.registration_steps is not None:
            sync_course_steps(cursor, course_id, course.registration_steps, 'registration')
            db.commit()
            
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


VALID_ADMISSION_TYPES = {
    # Fixed core stages
    'electronic_registration', 'electronic_screening', 'security_clearance',
    'psychometric_test', 'qualifying_exams',
    # Custom/additional stages
    'first_interview', 'second_interview', 'committee_review',
    'document_verification', 'pre_assessment', 'practical_test',
    'online_exam', 'custom_step',
    # Legacy stages (for backwards compatibility)
    'admission_test', 'interview', 'essay', 'background_check',
    'admin_review', 'acceptance_decision'
}

@router.get("/{course_id}/admission-steps")
async def get_admission_steps(course_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT step_key, step_type, title_ar, step_order, is_required, config_json FROM course_steps WHERE course_id=%s AND path_type='admission' ORDER BY step_order", (course_id,))
        steps = cursor.fetchall()
        
        # 5 core stages with their default properties
        fixed_defaults = [
            {
                'step_key': 'electronic_registration',
                'step_type': 'electronic_registration',
                'title_ar': 'التسجيل الإلكتروني',
                'description_ar': 'Applicant fills the customized registration form through the portal and uploads the required documents.',
                'is_required': 1,
                'config_json': {'is_active': True, 'fixed': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'electronic_screening',
                'step_type': 'electronic_screening',
                'title_ar': 'الفرز الإلكتروني',
                'description_ar': 'The system evaluates the basic eligibility criteria using the rules engine, with optional manual review.',
                'is_required': 1,
                'config_json': {'is_active': True, 'fixed': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'security_clearance',
                'step_type': 'security_clearance',
                'title_ar': 'الاستعلام الأمني',
                'description_ar': 'Eligible applicants’ data is sent to the relevant security authority for verification and approval.',
                'is_required': 1,
                'config_json': {'is_active': True, 'fixed': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'psychometric_test',
                'step_type': 'psychometric_test',
                'title_ar': 'اختبار السمات',
                'description_ar': 'Psychometric / traits assessment with pass/fail result and related score details.',
                'is_required': 1,
                'config_json': {'is_active': True, 'fixed': True, 'canDelete': False, 'canDisable': False}
            },
            {
                'step_key': 'qualifying_exams',
                'step_type': 'qualifying_exams',
                'title_ar': 'الاختبارات التأهيلية',
                'description_ar': 'Automated qualifying exams such as foreign languages, Arabic language, general knowledge, and any program-specific exam.',
                'is_required': 1,
                'config_json': {'is_active': True, 'fixed': True, 'canDelete': False, 'canDisable': False}
            }
        ]

        # Convert config_json from string to dict safely
        for s in steps:
            cfg = s.get('config_json')
            if isinstance(cfg, str):
                try:
                    s['config_json'] = json.loads(cfg)
                except:
                    s['config_json'] = {}
            elif isinstance(cfg, dict):
                s['config_json'] = cfg
            else:
                s['config_json'] = {}

        # If empty, return fixed defaults directly
        if not steps:
            for idx, fd in enumerate(fixed_defaults):
                fd['step_order'] = idx
            return fixed_defaults

        normalized = []
        matched_keys = set()

        for s in steps:
            key = s.get('step_key', '')
            type_ = s.get('step_type', '')

            # Match to a fixed step by key or type
            matching_def = None
            for fd in fixed_defaults:
                if fd['step_key'] == key or (fd['step_type'] == type_ and fd['step_key'] not in matched_keys):
                    matching_def = fd
                    break

            if matching_def:
                s['step_key'] = matching_def['step_key']
                s['step_type'] = matching_def['step_type']
                s['title_ar'] = matching_def['title_ar'] # Fixed title label from business document
                s['is_required'] = 1
                if not isinstance(s.get('config_json'), dict):
                    s['config_json'] = {}
                s['config_json'].update({
                    'is_active': True,
                    'fixed': True,
                    'canDelete': False,
                    'canDisable': False
                })
                matched_keys.add(matching_def['step_key'])
                normalized.append(s)
            else:
                if not isinstance(s.get('config_json'), dict):
                    s['config_json'] = {}
                s['config_json'].update({
                    'fixed': False,
                    'canDelete': True,
                    'canDisable': True
                })
                normalized.append(s)

        # Re-add any missing fixed steps
        for fd in fixed_defaults:
            if fd['step_key'] not in matched_keys:
                import copy
                missing_step = copy.deepcopy(fd)
                normalized.append(missing_step)

        # Enforce relative ordering of fixed steps
        fixed_steps = []
        custom_steps = []
        for s in normalized:
            if s.get('config_json', {}).get('fixed') is True:
                fixed_steps.append(s)
            else:
                custom_steps.append(s)

        fixed_order_keys = ['electronic_registration', 'electronic_screening', 'security_clearance', 'psychometric_test', 'qualifying_exams']
        fixed_steps.sort(key=lambda x: fixed_order_keys.index(x['step_key']))

        # Match custom steps to their original intervals relative to fixed steps
        original_orders = {}
        for k in fixed_order_keys:
            orig = next((s for s in steps if s.get('step_key') == k or s.get('step_type') == k), None)
            if orig:
                original_orders[k] = orig.get('step_order', 0)

        if 'electronic_registration' not in original_orders:
            original_orders['electronic_registration'] = 0
        if 'electronic_screening' not in original_orders:
            original_orders['electronic_screening'] = original_orders['electronic_registration'] + 10
        if 'security_clearance' not in original_orders:
            original_orders['security_clearance'] = original_orders['electronic_screening'] + 10
        if 'psychometric_test' not in original_orders:
            original_orders['psychometric_test'] = original_orders['security_clearance'] + 10
        if 'qualifying_exams' not in original_orders:
            original_orders['qualifying_exams'] = original_orders['psychometric_test'] + 10

        intervals = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}
        for cs in custom_steps:
            co = cs.get('step_order', 0)
            if co < original_orders['electronic_registration']:
                intervals[1].append(cs)
            elif co < original_orders['electronic_screening']:
                intervals[1].append(cs)
            elif co < original_orders['security_clearance']:
                intervals[2].append(cs)
            elif co < original_orders['psychometric_test']:
                intervals[3].append(cs)
            elif co < original_orders['qualifying_exams']:
                intervals[4].append(cs)
            else:
                intervals[5].append(cs)

        final_list = []
        final_list.append(fixed_steps[0])
        final_list.extend(intervals[1])
        final_list.append(fixed_steps[1])
        final_list.extend(intervals[2])
        final_list.append(fixed_steps[2])
        final_list.extend(intervals[3])
        final_list.append(fixed_steps[3])
        final_list.extend(intervals[4])
        final_list.append(fixed_steps[4])
        final_list.extend(intervals[5])

        for idx, s in enumerate(final_list):
            s['step_order'] = idx

        return final_list
    finally:
        cursor.close()
        db.close()

@router.put("/{course_id}/admission-steps")
async def update_admission_steps(course_id: int, steps: List[dict] = Body(...), editor: dict = Depends(require_editor)):
    # Validation logic for fixed steps
    fixed_keys = ['electronic_registration', 'electronic_screening', 'security_clearance', 'psychometric_test', 'qualifying_exams']
    
    expected_titles = {
        'electronic_registration': 'التسجيل الإلكتروني',
        'electronic_screening': 'الفرز الإلكتروني',
        'security_clearance': 'الاستعلام الأمني',
        'psychometric_test': 'اختبار السمات',
        'qualifying_exams': 'الاختبارات التأهيلية'
    }
    
    # 1. Check if all 5 fixed steps exist in the payload
    payload_keys = [s.get('step_key') for s in steps]
    for fk in fixed_keys:
        if fk not in payload_keys:
            raise HTTPException(status_code=400, detail=f"خطوة إجبارية مفقودة: {fk}")
            
    # 2. Check each fixed step for correct flags and order
    last_fixed_index = -1
    for fk in fixed_keys:
        step = next((s for s in steps if s.get('step_key') == fk), None)
        if not step:
            raise HTTPException(status_code=400, detail=f"خطوة إجبارية مفقودة: {fk}")
        
        if step.get('step_type') != fk:
            raise HTTPException(status_code=400, detail=f"نوع الخطوة الإجبارية {fk} غير صحيح")
            
        if step.get('title_ar') != expected_titles[fk]:
            raise HTTPException(status_code=400, detail=f"عنوان الخطوة الإجبارية {fk} غير صحيح أو تم تعديله")
            
        if not step.get('is_required'):
            raise HTTPException(status_code=400, detail=f"الخطوة الإجبارية {fk} يجب أن تكون مطلوبة")
            
        cfg = step.get('config_json')
        if isinstance(cfg, str):
            try:
                cfg = json.loads(cfg)
            except:
                cfg = {}
        elif isinstance(cfg, dict):
            pass
        else:
            cfg = {}
                
        if cfg.get('is_active') is False:
            raise HTTPException(status_code=400, detail=f"الخطوة الإجبارية {fk} لا يمكن تعطيلها")
        if cfg.get('fixed') is not True:
            raise HTTPException(status_code=400, detail=f"الخطوة الإجبارية {fk} يجب أن تحمل علم ثابت")
        if cfg.get('canDelete') is not False:
            raise HTTPException(status_code=400, detail=f"الخطوة الإجبارية {fk} لا يمكن حذفها")
        if cfg.get('canDisable') is not False:
            raise HTTPException(status_code=400, detail=f"الخطوة الإجبارية {fk} لا يمكن إلغاء تفعيلها")
            
        current_index = steps.index(step)
        if current_index < last_fixed_index:
            raise HTTPException(status_code=400, detail=f"الخطوات الإجبارية خارج الترتيب المحدد: {fk}")
        last_fixed_index = current_index
        
    # Check that 'electronic_registration' is at index 0
    reg_step = next(s for s in steps if s.get('step_key') == 'electronic_registration')
    if steps.index(reg_step) != 0:
        raise HTTPException(status_code=400, detail="الخطوة الأولى يجب أن تكون التسجيل الإلكتروني (electronic_registration)")

    db = get_db_connection()
    cursor = db.cursor()
    try:
        # Delete existing
        cursor.execute("DELETE FROM course_steps WHERE course_id=%s AND path_type='admission'", (course_id,))
        for idx, step in enumerate(steps):
            step_type = step.get('step_type', '')
            if step_type not in VALID_ADMISSION_TYPES:
                raise HTTPException(status_code=400, detail=f"Invalid admission step type: {step_type}")
                
            cfg = step.get('config_json')
            if isinstance(cfg, str):
                try:
                    cfg = json.loads(cfg)
                except:
                    cfg = {}
            elif isinstance(cfg, dict):
                pass
            else:
                cfg = {}
            
            cursor.execute(
                """INSERT INTO course_steps 
                   (course_id, path_type, step_key, step_type, title_ar, step_order, is_required, config_json) 
                   VALUES (%s, 'admission', %s, %s, %s, %s, %s, %s)""",
                (
                    course_id,
                    step.get('step_key', f"admission_{idx}"),
                    step_type,
                    step.get('title_ar', 'بدون عنوان'),
                    idx, # Use actual list index as the step_order
                    int(step.get('is_required', 1)),
                    json.dumps(cfg, ensure_ascii=False)
                )
            )
        db.commit()
        return {"message": "Admission steps updated successfully"}
    finally:
        cursor.close()
        db.close()


@router.get("/{course_id}/registration-steps")
async def get_registration_steps(course_id: int, editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT step_key, step_type, title_ar, step_order, is_required, config_json FROM course_steps WHERE course_id=%s AND path_type='registration' ORDER BY step_order", (course_id,))
        steps = cursor.fetchall()
        for s in steps:
            if isinstance(s.get('config_json'), str):
                try:
                    s['config_json'] = json.loads(s['config_json'])
                except:
                    s['config_json'] = {}
        return steps
    finally:
        cursor.close()
        db.close()

@router.put("/{course_id}/registration-steps")
async def update_registration_steps(course_id: int, steps: List[dict] = Body(...), editor: dict = Depends(require_editor)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        # Delete existing
        cursor.execute("DELETE FROM course_steps WHERE course_id=%s AND path_type='registration'", (course_id,))
        
        # Insert new
        for idx, step in enumerate(steps):
            cursor.execute(
                """INSERT INTO course_steps 
                   (course_id, path_type, step_key, step_type, title_ar, step_order, is_required, config_json) 
                   VALUES (%s, 'registration', %s, %s, %s, %s, %s, %s)""",
                (
                    course_id,
                    step.get('step_key', f"reg_{idx}"),
                    step.get('step_type', ''),
                    step.get('title_ar', 'بدون عنوان'),
                    step.get('step_order', idx),
                    int(step.get('is_required', 1)),
                    json.dumps(step.get('config_json', {}), ensure_ascii=False)
                )
            )
        db.commit()
        return {"message": "Registration steps updated successfully"}
    finally:
        cursor.close()
        db.close()
