from fastapi import APIRouter, HTTPException, Request, Depends
import httpx
import os
import json
import base64
import time
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel

from core.database import get_db_connection
from core.logger_util import log_activity, get_traceback
from core.security import get_superadmin_user

router = APIRouter(prefix="/ai", tags=["AI Services Proxy"])

# Register of microservice ports (Synced with .env if available)
SERVICE_REGISTRY = {
    "Face Engine": int(os.getenv("PORT_FACE_REC", 2341)),
    "Electronic Sorting": int(os.getenv("PORT_OCR_EXTRACTION", 2343)),
    "Quiz Engine": int(os.getenv("PORT_QUIZ_GEN", 2345)),
    "Course Analytics": int(os.getenv("PORT_COURSE_ANALYTICS", 2346)),
    "Requirement Analyzer": int(os.getenv("PORT_VLLM", 7834)),
    "Class Trainer Matrix": int(os.getenv("PORT_ADMIN_BACKEND", 8002)),
    "Admin Portal": int(os.getenv("PORT_ADMIN_BACKEND", 8002))
}

# Global progress tracker for background batches
PROGRESS_TRACKER = {
    "is_running": False,
    "total": 0,
    "current": 0,
    "last_message": "Idle",
    "start_time": 0
}

# Tracker for Class Trainer Matrix background jobs (local to Super Admin)
MATRIX_JOBS: Dict[int, Dict] = {}

# Tracker for Admission Full Check background jobs
ADMISSION_JOBS: Dict[int, Dict] = {}


class DispatchPayload(BaseModel):
    service: str
    endpoint: str
    data: Optional[Dict[str, Any]] = {}
    duration_hours: Optional[int] = 24  # Default to 24 hours

@router.post("/dispatch")
async def dispatch_task(payload: DispatchPayload, user: dict = Depends(get_superadmin_user)):
    import json
    import base64
    from pathlib import Path
    
    service_name = payload.service
    endpoint = payload.endpoint
    data = payload.data or {}
    
    project_root = Path("d:/Work/NTA/NTA-Regestration-Portal - Final")
    
    if service_name not in SERVICE_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Service '{service_name}' not recognized.")
    
    port = SERVICE_REGISTRY[service_name]
    host = "127.0.0.1" if service_name in ["Admin Portal", "Class Trainer Matrix"] else os.getenv("AI_SERVER_HOST", "127.0.0.1")
    target_url = f"http://{host}:{port}/{endpoint.lstrip('/')}"
    start_time = time.time()
    
    log_activity(
        category="ACTION",
        event_type="AI_DISPATCH_INIT",
        component="AI Proxy",
        level="INFO",
        details={"service": service_name, "endpoint": endpoint, "target_url": target_url},
        payload_json=data
    )
    
    async with httpx.AsyncClient() as client:
        try:
            # --- SPECIAL HANDLING: ELECTRONIC SORTING BATCH (Stage 1) ---
            if (service_name == "Electronic Sorting" or service_name == "OCR Service") and (data.get("batchSize") or data.get("batch")):
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                # Fetch Stage 1 trainees (Pending Admission Stage 1)
                cursor.execute("""
                    SELECT u.id as user_id, u.national_id, u.full_name_ar, u.gender, u.email, tp.documents 
                    FROM users u
                    JOIN pipeline_state p ON u.id = p.trainee_id
                    JOIN trainee_profiles tp ON u.id = tp.user_id
                    WHERE p.current_stage_id = 1
                    LIMIT %s
                """, (int(data.get("batchSize", 10)),))
                pending = cursor.fetchall()
                
                results = []
                for t in pending:
                    try:
                        docs = json.loads(t['documents']) if t['documents'] else {}
                        id_path = docs.get('idScan')
                        if not id_path:
                            results.append({"national_id": t['national_id'], "status": "Error", "error": "No ID scan found"})
                            continue
                            
                        full_path = project_root / id_path.lstrip('/')
                        if not full_path.exists():
                            results.append({"national_id": t['national_id'], "status": "Error", "error": f"File not found: {id_path}"})
                            continue
                        
                        # Call OCR Service with multipart/form-data
                        with open(full_path, "rb") as f:
                            files = {"file": (full_path.name, f, "image/jpeg")}
                            ocr_resp = await client.post(target_url, files=files, timeout=30.0)
                        
                        if ocr_resp.status_code == 200:
                            ocr_data = ocr_resp.json()
                            extracted_id = ocr_data.get("data", {}).get("national_id_number")
                            is_match = str(extracted_id) == str(t['national_id'])
                            status = "Accepted" if is_match else "Rejected"
                            
                            # Log to Normalized Admission Stage 1 Table
                            cursor.execute("""
                                INSERT INTO admission_stage_1_identity 
                                (trainee_id, national_id_ai, national_id_score, overall_status, confidence, rejection_reason) 
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                t['user_id'],
                                extracted_id,
                                100 if is_match else 0,
                                "Matched" if is_match else "Mismatch",
                                100 if is_match else 0,
                                "" if is_match else "رقم الهوية المستخرج لا يطابق الرقم المسجل."
                            ))

                            if status == "Accepted":
                                # --- AUTOMATED STAGE ADVANCEMENT ---
                                # 1. Get a System Admin ID for the audit trail
                                cursor.execute("SELECT id FROM users WHERE role = 'superadmin' ORDER BY id ASC LIMIT 1")
                                sys_admin = cursor.fetchone()
                                sys_id = sys_admin['id'] if sys_admin else 1
                                
                                # 2. Advance to Stage 2 (Security Inquiry)
                                cursor.execute("UPDATE pipeline_state SET current_stage_id = 2 WHERE trainee_id = %s", (t['user_id'],))
                                
                                # 3. Record the Automated Review in history
                                cursor.execute("""
                                    INSERT INTO stage_reviews (trainee_id, stage_id, reviewer_id, result, reviewer_name, review_date, notes) 
                                    VALUES (%s, 1, %s, 'Active', 'النظام الآلي (AI)', CURDATE(), 'تم اجتياز مرحلة الفرز الإلكتروني تلقائياً بعد مطابقة بيانات الهوية عبر الذكاء الاصطناعي بنجاح.')
                                """, (t['user_id'], sys_id))
                                
                                # 4. Send Passing Email
                                from core.notifications import send_stage_pass_email
                                send_stage_pass_email(t['email'], t['full_name_ar'], "الفرز الإلكتروني", t['gender'])
                            
                            else:
                                # --- REJECTION RESET ---
                                from core.notifications import send_rejection_email
                                from core.upload_manager import delete_trainee_folder
                                
                                # 1. Send Email
                                send_rejection_email(t['email'], t['full_name_ar'], "رقم الهوية في المستند المرفوع لا يطابق الرقم المسجل.", t['gender'])
                                
                                # 2. Delete Folder
                                delete_trainee_folder(t['full_name_ar'], t['national_id'])
                                
                                # 3. Delete User (Cascades to all tables)
                                cursor.execute("DELETE FROM users WHERE id = %s", (t['user_id'],))
                            
                            results.append({"national_id": t['national_id'], "status": status, "extracted": extracted_id, "auto_advanced": status == "Accepted"})
                        else:
                            results.append({"national_id": t['national_id'], "status": "Error", "error": ocr_resp.text})
                    except Exception as e:
                        results.append({"national_id": t['national_id'], "status": "Exception", "error": str(e)})
                
                conn.commit()
                cursor.close()
                conn.close()
                return {"batch_status": "complete", "processed": len(results), "results": results}

            # --- SPECIAL HANDLING: FACE ENROLL BATCH ---
            if service_name == "Face Engine" and (endpoint == "/enroll" and (data.get("trainees") or data.get("batch"))):
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                # Fetch Stage 7 trainees (Passed all stages, ready for enrollment)
                cursor.execute("""
                    SELECT u.id as user_id, u.national_id, tp.documents 
                    FROM users u
                    JOIN pipeline_state p ON u.id = p.trainee_id
                    JOIN trainee_profiles tp ON u.id = tp.user_id
                    WHERE p.current_stage_id = 7
                """)
                ready = cursor.fetchall()
                
                results = []
                for t in ready:
                    try:
                        docs = json.loads(t['documents']) if t['documents'] else {}
                        # Identity photos are usually an array
                        photos = docs.get('identityPhotos', [])
                        if not photos:
                            results.append({"national_id": t['national_id'], "status": "Error", "error": "No identity photos found"})
                            continue
                        
                        photo_path = photos[0] # Take the first one
                        full_path = project_root / photo_path.lstrip('/')
                        if not full_path.exists():
                            results.append({"national_id": t['national_id'], "status": "Error", "error": f"File not found: {photo_path}"})
                            continue
                        
                        # Encode to B64
                        with open(full_path, "rb") as f:
                            img_b64 = base64.b64encode(f.read()).decode('utf-8')
                        
                        # --- NEW: Fetch Registrations (Courses & Sessions) ---
                        cursor.execute("""
                            SELECT c.id as course_id, c.title as course_title
                            FROM courses c
                            JOIN applications a ON c.id = a.course_id
                            WHERE a.user_id = %s AND a.status = 'approved'
                        """, (t['user_id'],))
                        enrolled_courses = cursor.fetchall()
                        
                        registrations = []
                        for course in enrolled_courses:
                            cursor.execute("""
                                SELECT id as session_id, topic as session_name, session_date
                                FROM course_sessions
                                WHERE course_id = %s
                                ORDER BY session_date ASC
                            """, (course['course_id'],))
                            sessions = cursor.fetchall()
                            
                            # Convert session dates to separate date and time for JSON serialization
                            for s in sessions:
                                if s['session_date']:
                                    dt = s['session_date']
                                    s['date'] = dt.strftime("%Y-%m-%d")
                                    s['time'] = dt.strftime("%I:%M %p")
                                    del s['session_date'] # Remove the raw timestamp object
                            
                            registrations.append({
                                "course_id": course['course_id'],
                                "course_title": course['course_title'],
                                "sessions": sessions
                            })

                        # Call Face Engine with JSON including registrations
                        face_payload = {
                            "image_b64": f"data:image/jpeg;base64,{img_b64}", 
                            "label": t['national_id'],
                            "registrations": registrations
                        }
                        face_resp = await client.post(target_url, json=face_payload, timeout=30.0)
                        
                        if face_resp.status_code == 200:
                            results.append({"national_id": t['national_id'], "status": "Success", "data": face_resp.json()})
                        else:
                            results.append({"national_id": t['national_id'], "status": "Error", "error": face_resp.text})
                    except Exception as e:
                        results.append({"national_id": t['national_id'], "status": "Exception", "error": str(e)})
                
                cursor.close()
                conn.close()
                return {"batch_status": "complete", "processed": len(results), "results": results}

            # --- SPECIAL HANDLING: QUIZ ENGINE (FILE SUPPORT & PARAM SYNC) ---
            if service_name == "Quiz Engine":
                # Standardize parameters for the new Quiz Engine API (Corrected per Input.json)
                params = {
                    "num_questions": int(data.get("count", data.get("num_questions", 10))),
                    "question_type": data.get("type", "mcq"),
                    "difficulty": data.get("difficulty", "medium"),
                    "language": data.get("language", "auto")
                }
                
                # Handle Mixed type (true_false vs truefalse)
                if params["question_type"] == "truefalse": params["question_type"] = "true_false"
                
                # Prepare Files
                files = []
                material_filenames = data.get("materials", [])
                if isinstance(material_filenames, str): # Handle single string if passed
                    material_filenames = [material_filenames]
                
                # Resolve file paths (Materials are usually in 'user/uploads/files/')
                opened_files = []
                try:
                    for filename in material_filenames:
                        possible_paths = [
                            project_root / filename.lstrip('/'),
                            project_root / "uploads" / filename.lstrip('/'),
                            project_root / "data" / "uploads" / filename.lstrip('/'),
                            project_root / "user" / "uploads" / "files" / filename.lstrip('/')
                        ]
                        
                        found_path = None
                        for p in possible_paths:
                            if p.exists():
                                found_path = p
                                break
                        
                        if found_path:
                            f = open(found_path, "rb")
                            opened_files.append(f)
                            # CRITICAL: Field name MUST be 'file' per AI Input.json
                            files.append(("file", (found_path.name, f, "application/octet-stream")))
                    
                    # Call Quiz Engine with multipart/form-data if files exist, else JSON
                    if files:
                        response = await client.post(target_url, data=params, files=files, timeout=120.0)
                    else:
                        response = await client.post(target_url, json=params, timeout=60.0)
                    
                    if response.status_code != 200:
                        raise HTTPException(status_code=response.status_code, detail=f"Quiz Engine Error: {response.text}")
                    
                    resp_json = response.json()
                    
                    # --- Persistence & Synchronization (Full Lifecycle) ---
                    conn = get_db_connection()
                    cursor = conn.cursor(dictionary=True)
                    try:
                        course_id = int(data.get("course_id", 0))
                        target_session_id = int(data.get("target_session_id", 0))
                        group_id = data.get("groupId", f"Quiz_{course_id}")
                        
                        # 1. Normalized Persistence (for logs/admin)
                        cursor.execute("SELECT id FROM quizzes WHERE name = %s AND course_id = %s", (group_id, course_id))
                        quiz_row = cursor.fetchone()
                        quiz_id = quiz_row['id'] if quiz_row else None
                        
                        if not quiz_id:
                            # 1.1 First, deactivate any previous quizzes for this specific session 
                            # to ensure only the latest one is active by default
                            cursor.execute("UPDATE quizzes SET is_active = 0 WHERE session_id = %s", (target_session_id,))
                            
                            # 1.2 Insert with dynamic duration
                            cursor.execute(
                                "INSERT INTO quizzes (course_id, session_id, name, availability_duration_hours, is_active) VALUES (%s, %s, %s, %s, %s)", 
                                (course_id, target_session_id, group_id, payload.duration_hours, 1)
                            )
                            quiz_id = cursor.lastrowid
                        
                        questions_list = resp_json.get("questions", [])
                        for q in questions_list:
                            q_type_raw = q.get("type", "mcq")
                            q_type_db = "mcq"
                            if q_type_raw in ["true_false", "truefalse"]: q_type_db = "truefalse"
                            elif q_type_raw == "written": q_type_db = "essay"
                            
                            # Schema only has quiz_id, question_text, question_type, max_mark
                            cursor.execute(
                                "INSERT INTO questions (quiz_id, question_text, question_type, max_mark) VALUES (%s, %s, %s, %s)",
                                (quiz_id, q.get("question", ""), q_type_db, 1.0)
                            )
                            q_id = cursor.lastrowid
                            
                            # Insert MCQ/TF Answers
                            if q_type_raw == "mcq":
                                options = q.get("options", {})
                                correct_key = q.get("answer", "")
                                for key, text in options.items():
                                    is_correct = 1 if key == correct_key else 0
                                    cursor.execute(
                                        "INSERT INTO answers (question_id, answer_text, is_correct, fraction) VALUES (%s, %s, %s, %s)",
                                        (q_id, f"({key}) {text}", is_correct, 1.0 if is_correct else 0.0)
                                    )
                            elif q_type_raw in ["true_false", "truefalse"]:
                                correct_val = q.get("answer")
                                for val in [True, False]:
                                    is_correct = 1 if str(val).lower() == str(correct_val).lower() else 0
                                    cursor.execute(
                                        "INSERT INTO answers (question_id, answer_text, is_correct, fraction) VALUES (%s, %s, %s, %s)",
                                        (q_id, str(val), is_correct, 1.0 if is_correct else 0.0)
                                    )
                        
                        # 2. Synchronization with Trainee Portal (Critical Fix)
                        # Construct the flat JSON structure for the Trainee's exam.html
                        trainee_quiz = {
                            "courseName": data.get("courseName", "Course Quiz"),
                            "examNum": "AI Generated",
                            "title": f"اختبار تقييمي: {data.get('courseName', '')}",
                            "durationMinutes": 20,
                            "passingScore": 60,
                            "questions": []
                        }
                        
                        for idx, q in enumerate(questions_list):
                            trainee_q = {
                                "id": idx + 1,
                                "type": q.get("type", "mcq"),
                                "text": q.get("question", ""),
                                "points": 1,
                                "explanation": q.get("explanation", ""),
                                "key_points": q.get("key_points", [])
                            }
                            if trainee_q["type"] == "mcq":
                                trainee_q["options"] = [{"label": k, "text": v} for k, v in q.get("options", {}).items()]
                            elif trainee_q["type"] == "true_false":
                                trainee_q["options"] = [
                                    {"label": "T", "text": "صح"},
                                    {"label": "F", "text": "خطأ"}
                                ]
                                trainee_q["type"] = "tf" # exam.html uses 'tf'
                            trainee_quiz["questions"].append(trainee_q)
                        
                        cursor.execute(
                            "UPDATE courses SET quiz_json = %s, has_active_quiz = 1 WHERE id = %s",
                            (json.dumps(trainee_quiz, ensure_ascii=False), course_id)
                        )
                        
                        conn.commit()
                    except Exception as db_err:
                        print(f"Quiz Sync Error: {db_err}")
                        conn.rollback()
                    finally:
                        cursor.close()
                        conn.close()
                    
                    return resp_json
                    
                finally:
                    for f in opened_files:
                        f.close()

            # --- SPECIAL HANDLING: CLASS TRAINER MATRIX ---
            if service_name == "Class Trainer Matrix":
                ROOT = Path(__file__).resolve().parent.parent.parent.parent
                MATRIX_PATH = ROOT / "AI Services" / "Class Trainer Matrix"

                # Extract course_id from endpoint or data
                course_id = data.get("course_id")
                if not course_id:
                    # Try to parse from endpoint like /generate/10
                    ep_parts = endpoint.strip("/").split("/")
                    for part in reversed(ep_parts):
                        if part.isdigit():
                            course_id = int(part)
                            break

                if not course_id:
                    raise HTTPException(status_code=400, detail="course_id is required for Class Trainer Matrix")

                course_id = int(course_id)

                # Load MatrixGenerator
                try:
                    import importlib.util
                    matrix_file = MATRIX_PATH / "matrix_generator.py"
                    if not matrix_file.exists():
                        raise FileNotFoundError(f"MatrixGenerator not found at {matrix_file}")

                    spec = importlib.util.spec_from_file_location("matrix_generator", str(matrix_file))
                    matrix_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(matrix_mod)
                    MatrixGenerator = matrix_mod.MatrixGenerator
                except Exception as e:
                    log_activity(
                        category="SYSTEM",
                        event_type="AI_IMPORT_FAILURE",
                        level="CRITICAL",
                        component="AI Proxy",
                        details={"error": str(e), "path": str(MATRIX_PATH)}
                    )
                    raise HTTPException(status_code=500, detail=f"MatrixGenerator load failed: {str(e)}")

                # Check Admin Portal's MATRIX_JOBS in-memory tracker via HTTP
                admin_port = SERVICE_REGISTRY.get("Admin Portal", 8002)
                status_url = f"http://127.0.0.1:{admin_port}/api/admin/class-matrix/status/{course_id}"
                try:
                    async with httpx.AsyncClient() as chk:
                        chk_resp = await chk.get(status_url, timeout=5.0)
                        if chk_resp.status_code == 200:
                            job_state = chk_resp.json().get("status")
                            if job_state == "processing":
                                return {
                                    "status": "processing",
                                    "message": "Matrix generation already in progress.",
                                    "course_id": course_id
                                }
                except Exception:
                    pass  # Admin Portal might not be running; we'll run directly

                # Mark as processing locally
                MATRIX_JOBS[course_id] = {"status": "processing", "result": None, "error": None}

                # Run generation in a background thread (fire-and-forget)
                def _run_matrix(cid):
                    try:
                        log_activity(
                            category="ACTION",
                            event_type="MATRIX_GEN_START",
                            component="Class Trainer Matrix",
                            details={"course_id": cid}
                        )
                        gen = MatrixGenerator()
                        result = gen.generate_matrix(cid)
                        if result.get("success"):
                            MATRIX_JOBS[cid] = {"status": "done", "result": result, "error": None}
                            log_activity(
                                category="ACTION",
                                event_type="MATRIX_GEN_DONE",
                                component="Class Trainer Matrix",
                                level="INFO",
                                details={
                                    "course_id": cid,
                                    "assignments_count": result.get("assignments_count"),
                                    "trainers_count": result.get("trainers_count"),
                                    "course_nature": result.get("course_nature")
                                }
                            )
                        else:
                            MATRIX_JOBS[cid] = {"status": "error", "result": None, "error": result.get("error")}
                            log_activity(
                                category="SYSTEM",
                                event_type="MATRIX_GEN_FAILED",
                                level="CRITICAL",
                                component="Class Trainer Matrix",
                                details={"course_id": cid, "error": result.get("error")}
                            )
                    except Exception as e:
                        MATRIX_JOBS[cid] = {"status": "error", "result": None, "error": str(e)}
                        log_activity(
                            category="SYSTEM",
                            event_type="MATRIX_GEN_CRASHED",
                            level="CRITICAL",
                            component="Class Trainer Matrix",
                            details={"course_id": cid, "error": str(e)}
                        )

                thread = threading.Thread(target=_run_matrix, args=(course_id,), daemon=True)
                thread.start()

                log_activity(
                    category="ACTION",
                    event_type="AI_DISPATCH_SUCCESS",
                    component="Class Trainer Matrix",
                    level="INFO",
                    details={"course_id": course_id, "status": "background thread started"}
                )

                return {
                    "status": "processing",
                    "message": f"Matrix generation for Course #{course_id} started in background. Poll /api/ai/matrix-status/{course_id} for updates.",
                    "course_id": course_id
                }

            # --- SPECIAL HANDLING: REQUIREMENT ANALYZER BATCH ---
            if service_name == "Requirement Analyzer" and endpoint == "/process-unprocessed":
                import sys
                
                # Resolve project root dynamically
                ROOT = Path(__file__).resolve().parent.parent.parent.parent
                HUB_PATH = ROOT / "AI Services" / "Requirement Analyzer"
                
                try:
                    import importlib.util
                    analyzer_file = HUB_PATH / "analyzer.py"
                    if not analyzer_file.exists():
                        raise FileNotFoundError(f"Analyzer script not found at {analyzer_file}")
                        
                    spec = importlib.util.spec_from_file_location("analyzer_hub", str(analyzer_file))
                    analyzer_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(analyzer_mod)
                    RequirementAnalyzer = analyzer_mod.RequirementAnalyzer
                except Exception as e:
                    log_activity(
                        category="SYSTEM",
                        event_type="AI_IMPORT_FAILURE",
                        level="CRITICAL",
                        component="AI Proxy",
                        details={"error": str(e), "hub_path": str(HUB_PATH)}
                    )
                    raise HTTPException(status_code=500, detail=f"RequirementAnalyzer load failed: {str(e)}")

                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                
                # Find pending trainees (Enrolled but no analysis result)
                cursor.execute("""
                    SELECT u.id as user_id, a.course_id 
                    FROM applications a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.status = 'approved'
                    AND u.role = 'trainee'
                    AND NOT EXISTS (
                        SELECT 1 FROM cv_matching_results r 
                        WHERE r.national_id = u.national_id 
                        AND r.course_id = a.course_id
                    )
                """)
                
                pending = cursor.fetchall()
                cursor.close()
                conn.close()

                if not pending:
                    return {"status": "skipped", "message": "No pending trainees found."}

                # Define the worker function
                def run_analysis_batch(trainees_list):
                    global PROGRESS_TRACKER
                    analyzer = RequirementAnalyzer()
                    total = len(trainees_list)
                    
                    PROGRESS_TRACKER["is_running"] = True
                    PROGRESS_TRACKER["total"] = total
                    PROGRESS_TRACKER["current"] = 0
                    PROGRESS_TRACKER["start_time"] = time.time()
                    PROGRESS_TRACKER["last_message"] = f"Started processing {total} trainees..."

                    log_activity(
                        category="SYSTEM",
                        event_type="AI_BATCH_START",
                        component="Requirement Analyzer",
                        details={"total_trainees": total}
                    )
                    
                    for idx, t in enumerate(trainees_list):
                        try:
                            # Processes one-by-one to protect LLM load
                            PROGRESS_TRACKER["last_message"] = f"Analyzing Trainee {idx+1}/{total}..."
                            analyzer.analyze_trainee(t['user_id'], t['course_id'])
                            PROGRESS_TRACKER["current"] = idx + 1
                            
                            if (idx + 1) % 5 == 0 or (idx + 1) == total:
                                log_activity(
                                    category="SYSTEM",
                                    event_type="AI_BATCH_PROGRESS",
                                    component="Requirement Analyzer",
                                    details={"progress": f"{idx+1}/{total}"}
                                )
                        except Exception as e:
                            log_activity(
                                category="SYSTEM",
                                event_type="AI_BATCH_ERROR",
                                component="Requirement Analyzer",
                                level="WARNING",
                                details={"user_id": t['user_id'], "error": str(e)}
                            )
                    
                    PROGRESS_TRACKER["is_running"] = False
                    PROGRESS_TRACKER["last_message"] = "Batch Complete"
                    log_activity(
                        category="SYSTEM",
                        event_type="AI_BATCH_COMPLETE",
                        component="Requirement Analyzer",
                        details={"total_processed": total}
                    )

                # Start background thread
                thread = threading.Thread(target=run_analysis_batch, args=(pending,))
                thread.start()

                return {
                    "status": "processing",
                    "message": f"Background analysis started for {len(pending)} trainees. You can view progress in the System Logs.",
                    "estimated_time_minutes": round(len(pending) * 0.5, 1)
                }

            # --- SPECIAL HANDLING: ELECTRONIC SORTING FULL CHECK ---
            if service_name == "Electronic Sorting" and endpoint == "/process-all":
                import sys
                
                ROOT = Path(__file__).resolve().parent.parent.parent.parent
                SORT_PATH = ROOT / "AI Services" / "Electronic Sorting"
                
                try:
                    import importlib.util
                    sort_file = SORT_PATH / "electronic_sorting.py"
                    spec = importlib.util.spec_from_file_location("electronic_sorting", str(sort_file))
                    sort_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(sort_mod)
                    AdmissionAnalyzer = sort_mod.AdmissionAnalyzer
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"AdmissionAnalyzer load failed: {str(e)}")

                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                # Find pending trainees for stage 1
                cursor.execute("""
                    SELECT u.id as user_id, a.course_id 
                    FROM pipeline_state p
                    JOIN users u ON p.trainee_id = u.id
                    JOIN applications a ON u.id = a.user_id
                    WHERE p.current_stage_id = 1 AND p.status = 'active'
                """)
                pending = cursor.fetchall()
                cursor.close()
                conn.close()

                if not pending:
                    return {"status": "skipped", "message": "No pending applicants found for Stage 1."}

                def run_sorting_batch(trainees_list):
                    global PROGRESS_TRACKER
                    analyzer = AdmissionAnalyzer()
                    total = len(trainees_list)
                    PROGRESS_TRACKER.update({
                        "is_running": True,
                        "total": total,
                        "current": 0,
                        "start_time": time.time(),
                        "last_message": f"Starting batch sorting for {total} applicants..."
                    })

                    for idx, t in enumerate(trainees_list):
                        try:
                            PROGRESS_TRACKER["current"] = idx + 1
                            PROGRESS_TRACKER["last_message"] = f"Processing applicant {idx+1}/{total} (ID: {t['user_id']})..."
                            analyzer.run_full_check(t['user_id'], t['course_id'])
                        except Exception as inner_e:
                            print(f"Sorting Error for {t['user_id']}: {inner_e}")

                    PROGRESS_TRACKER["is_running"] = False
                    PROGRESS_TRACKER["last_message"] = f"Completed batch sorting for {total} applicants."

                thread = threading.Thread(target=run_sorting_batch, args=(pending,), daemon=True)
                thread.start()

                return {
                    "status": "processing",
                    "message": f"Full admission sorting started for {len(pending)} applicants.",
                    "estimated_time_minutes": round(len(pending) * 1.5, 1)
                }

            # --- DEFAULT DISPATCH ---
            response = await client.post(target_url, json=data, timeout=300.0)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Target Service Error: {response.text}")
                
            try:
                resp_data = response.json()
                duration_ms = int((time.time() - start_time) * 1000)
                log_activity(
                    category="ACTION",
                    event_type="AI_DISPATCH_SUCCESS",
                    component=service_name,
                    level="INFO",
                    status_code=response.status_code,
                    details={"service": service_name, "endpoint": endpoint},
                    duration_ms=duration_ms
                )
                return resp_data
            except Exception:
                duration_ms = int((time.time() - start_time) * 1000)
                return {"status": "success", "raw_response": response.text}
                
        except httpx.ConnectError:
            duration_ms = int((time.time() - start_time) * 1000)
            log_activity(
                category="SYSTEM",
                event_type="AI_DISPATCH_FAILURE",
                level="CRITICAL",
                component=service_name,
                status_code=503,
                details={"error": "Connection Refused", "target_url": target_url},
                status="Action Required",
                duration_ms=duration_ms
            )
            raise HTTPException(status_code=503, detail=f"Service '{service_name}' on port {port} is unreachable.")
        except HTTPException as he:
            duration_ms = int((time.time() - start_time) * 1000)
            log_activity(
                category="SYSTEM",
                event_type="AI_DISPATCH_ERROR",
                level="WARNING" if he.status_code < 500 else "CRITICAL",
                component=service_name,
                status_code=he.status_code,
                details={"error": he.detail, "target_url": target_url},
                duration_ms=duration_ms
            )
            raise he
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            tb = get_traceback()
            log_activity(
                category="SYSTEM",
                event_type="AI_DISPATCH_CRASH",
                level="CRITICAL",
                component="AI Proxy",
                status_code=500,
                traceback=tb,
                details={"error": str(e), "target_url": target_url},
                status="Action Required",
                duration_ms=duration_ms
            )
            raise HTTPException(status_code=500, detail=f"Internal Proxy Error: {str(e)}")

# Global state to track service health changes
PREVIOUS_HEALTH_STATE = {}

@router.get("/health")
async def registry_health():
    """Checks the status of all registered microservices and logs changes."""
    health_results = {}
    async with httpx.AsyncClient() as client:
        for name, port in SERVICE_REGISTRY.items():
            try:
                # Check root or health endpoint - using AI_SERVER_HOST if it's an AI service
                host = "127.0.0.1" if name in ["Admin Portal", "Class Trainer Matrix"] else os.getenv("AI_SERVER_HOST", "127.0.0.1")
                resp = await client.get(f"http://{host}:{port}/", timeout=3.0)
                # 200 is ideal, but 404 from uvicorn also means the service is alive and listening
                state = "online" if resp.status_code in [200, 404] else "error"
            except:
                state = "offline"
            
            health_results[name] = state
            
            # Log state change
            prev_state = PREVIOUS_HEALTH_STATE.get(name)
            if prev_state and prev_state != state:
                log_activity(
                    category="SYSTEM",
                    event_type="SERVICE_HEALTH_CHANGE",
                    details={"service": name, "previous_state": prev_state, "current_state": state}
                )
            PREVIOUS_HEALTH_STATE[name] = state
            
    return health_results

@router.get("/batch-status")
async def get_batch_status():
    """Returns the current state of the background AI batch."""
    return PROGRESS_TRACKER

@router.get("/matrix-status/{course_id}")
async def get_matrix_status(course_id: int):
    """
    Checks the status of matrix generation.
    First checks local Super Admin jobs, then falls back to Admin Portal.
    """
    # 1. Check local tracker
    if course_id in MATRIX_JOBS:
        return {
            "status": MATRIX_JOBS[course_id]["status"],
            "course_id": course_id,
            "result": MATRIX_JOBS[course_id].get("result"),
            "error": MATRIX_JOBS[course_id].get("error")
        }

    # 2. Fallback: Proxy to Admin Portal (port 8002)
    admin_port = SERVICE_REGISTRY.get("Admin Portal", 8002)
    target_url = f"http://127.0.0.1:{admin_port}/api/admin/class-matrix/status/{course_id}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(target_url, timeout=5.0)
            if resp.status_code == 200:
                return resp.json()
            return {"status": "idle", "course_id": course_id}
    except Exception:
        # If Admin Portal is down, just return idle (since we already checked local)
        return {"status": "idle", "course_id": course_id}
@router.post("/quiz/override-trainee-access")
async def override_trainee_access(
    payload: Dict[str, Any], 
    user: dict = Depends(get_superadmin_user)
):
    """
    Exclusively for Super Admins: Grant a specific trainee extra time for a specific quiz.
    """
    quiz_id = payload.get("quiz_id")
    trainee_id = payload.get("trainee_id")
    new_end_time = payload.get("new_end_time") # ISO Format string
    reason = payload.get("reason", "Extended by Super Admin")
    
    if not quiz_id or not trainee_id or not new_end_time:
        raise HTTPException(status_code=400, detail="Missing required override parameters.")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if record already exists for UPSERT
        cursor.execute(
            "INSERT INTO quiz_access_overrides (quiz_id, trainee_id, override_deadline, reason, created_by) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE override_deadline = VALUES(override_deadline), reason = VALUES(reason), created_by = VALUES(created_by)",
            (quiz_id, trainee_id, new_end_time, reason, user.get("id"))
        )
        conn.commit()
        
        log_activity(
            category="ADMIN",
            event_type="QUIZ_OVERRIDE_GRANTED",
            component="Quiz Manager",
            level="INFO",
            details={"quiz_id": quiz_id, "trainee_id": trainee_id, "deadline": new_end_time},
            user_id=user.get("id")
        )
        
        return {"status": "success", "message": "Override access granted successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@router.get("/quiz/overrides/{quiz_id}")
async def get_quiz_overrides(quiz_id: int, user: dict = Depends(get_superadmin_user)):
    """
    List all active overrides for a specific quiz.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT o.*, u.full_name_ar as trainee_name, u.national_id 
            FROM quiz_access_overrides o
            JOIN users u ON o.trainee_id = u.id
            WHERE o.quiz_id = %s
        """, (quiz_id,))
        overrides = cursor.fetchall()
        return {"quiz_id": quiz_id, "overrides": overrides}
    finally:
        cursor.close()
        conn.close()

@router.get("/quiz/active-quizzes")
async def get_active_quizzes(user: dict = Depends(get_superadmin_user)):
    """
    Get all active quizzes with their session info to help manage overrides.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT q.id, q.name, q.course_id, q.session_id, q.availability_duration_hours,
                   c.title as course_title, s.topic as session_topic, s.session_date
            FROM quizzes q
            JOIN courses c ON q.course_id = c.id
            JOIN course_sessions s ON q.session_id = s.id
            WHERE q.is_active = 1
            ORDER BY q.created_at DESC
        """)
        return {"quizzes": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()

# --- NEW: ADMISSION FULL CHECK (PHASE 1 OVERHAUL) ---

@router.post("/admission/full-check")
async def start_admission_check(trainee_id: int, course_id: int, user: dict = Depends(get_superadmin_user)):
    import sys
    import threading
    from pathlib import Path
    
    # 1. Register job
    ADMISSION_JOBS[trainee_id] = {
        "status": "starting",
        "progress": 0,
        "message": "Initializing AI Pipeline...",
        "result": None,
        "start_time": time.time()
    }
    
    def run_admission_pipeline(t_id, c_id):
        try:
            # Add AI Services to path
            project_root = Path(__file__).parent.parent.parent.parent
            sys.path.append(str(project_root / "AI Services" / "Electronic Sorting"))
            
            from electronic_sorting import AdmissionAnalyzer
            
            analyzer = AdmissionAnalyzer()
            
            def update_cb(msg, prog):
                ADMISSION_JOBS[t_id]["message"] = msg
                ADMISSION_JOBS[t_id]["progress"] = prog
                ADMISSION_JOBS[t_id]["status"] = "processing"
            
            result = analyzer.run_full_check(t_id, c_id, update_progress=update_cb)
            
            ADMISSION_JOBS[t_id]["status"] = "completed" if result.get("success") else "failed"
            ADMISSION_JOBS[t_id]["result"] = result
            ADMISSION_JOBS[t_id]["progress"] = 100
            
        except Exception as e:
            ADMISSION_JOBS[t_id]["status"] = "failed"
            ADMISSION_JOBS[t_id]["message"] = f"Critical Error: {str(e)}"
            log_activity("SYSTEM", "ADMISSION_AI_CRASH", "AI Proxy", details={"error": str(e), "trainee_id": t_id})

    thread = threading.Thread(target=run_admission_pipeline, args=(trainee_id, course_id), daemon=True)
    thread.start()
    
    return {"message": "Admission check started", "trainee_id": trainee_id}

@router.get("/admission/status/{trainee_id}")
async def get_admission_status(trainee_id: int, user: dict = Depends(get_superadmin_user)):
    if trainee_id not in ADMISSION_JOBS:
        # Check database if not in active memory
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admission_sorting_results WHERE trainee_id = %s ORDER BY processed_at DESC LIMIT 1", (trainee_id,))
        res = cursor.fetchone()
        
        if res:
            sorting_id = res['id']
            cursor.execute("SELECT * FROM admission_stage_1_identity WHERE trainee_id = %s ORDER BY created_at DESC LIMIT 1", (trainee_id,))
            id_res = cursor.fetchone()
            
            cursor.execute("SELECT * FROM admission_sorting_experience WHERE sorting_id = %s", (sorting_id,))
            exp_res = cursor.fetchall()
            
            cursor.execute("SELECT * FROM admission_sorting_education WHERE sorting_id = %s", (sorting_id,))
            edu_res = cursor.fetchall()
            
            cursor.close()
            conn.close()

            identity_details = {
                "match_results": {
                    "full_name": {"score": id_res['full_name_score'], "ai": id_res['full_name_ai']},
                    "national_id": {"score": id_res['national_id_score'], "ai": id_res['national_id_ai']},
                    "gender": {"score": id_res['gender_score'], "ai": id_res['gender_ai']},
                    "dob": {"score": id_res['dob_score'], "ai": id_res['dob_ai']}
                },
                "overall_status": id_res['overall_status'],
                "confidence": id_res['confidence'],
                "rejection_reason": id_res['rejection_reason']
            } if id_res else {}

            professional_details = {
                "status": res['professional_status'],
                "experience_match": [{"item": e['item_description'], "status": e['match_status'], "comment": e['ai_comment']} for e in exp_res]
            }

            education_details = {
                "status": res['education_status'],
                "education_match": [{"item": e['degree_info'], "status": e['match_status']} for e in edu_res]
            }

            return {"status": "completed", "progress": 100, "result": {
                "success": True,
                "judge": res['final_judge'],
                "confidence": res['confidence_score'],
                "summary": res['ai_summary'],
                "details": {
                    "identity": identity_details,
                    "professional": professional_details,
                    "education": education_details
                }
            }}
        
        cursor.close()
        conn.close()
        return {"status": "not_found"}
        
    return ADMISSION_JOBS[trainee_id]
