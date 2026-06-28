from fastapi import APIRouter, HTTPException, Depends
import httpx
import os
import json
import base64
import time
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel

from core.database import get_db_connection
from core.auth import get_current_user
from core.logger_util import log_activity

router = APIRouter(prefix="/api/ai", tags=["AI Services Proxy"])

# Register of microservice ports (Synced with Super Admin)
SERVICE_REGISTRY = {
    "Face Engine": int(os.getenv("PORT_FACE_REC", 2341)),
    "OCR Service": int(os.getenv("PORT_OCR_EXTRACTION", 2343)),
    "Quiz Engine": int(os.getenv("PORT_QUIZ_GEN", 2345)),
    "Course Analytics": int(os.getenv("PORT_COURSE_ANALYTICS", 2346)),
    "Candidate Matcher": int(os.getenv("PORT_CV_MATCHER", 2348))
}

class DispatchPayload(BaseModel):
    service: str
    endpoint: str
    data: Optional[Dict[str, Any]] = {}

@router.post("/dispatch")
async def dispatch_task(payload: DispatchPayload, current_user: dict = Depends(get_current_user)):
    # Security: Only Trainers or Admins can dispatch AI tasks
    if current_user["role"] not in ["trainer", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="غير مسموح لهذه الرتبة بتشغيل محرك الذكاء الاصطناعي")

    service_name = payload.service
    endpoint = payload.endpoint
    data = payload.data or {}
    
    # Standardize project root for portability
    project_root = Path(__file__).parent.parent.parent.parent
    
    if service_name not in SERVICE_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Service '{service_name}' not recognized.")
    
    port = SERVICE_REGISTRY[service_name]
    # Standardize endpoint call
    clean_endpoint = endpoint.lstrip('/')
    if service_name == "Quiz Engine" and clean_endpoint == "generate":
        clean_endpoint = "generate-quiz"
        
    ai_host = os.getenv("AI_SERVER_HOST", "127.0.0.1")
    target_url = f"http://{ai_host}:{port}/{clean_endpoint}"
    start_time = time.time()
    
    log_activity(
        category="ACTION",
        event_type="AI_DISPATCH_INIT",
        user_id=current_user["id"],
        role=current_user["role"],
        details={"service": service_name, "endpoint": endpoint, "target_url": target_url},
        payload_json=data
    )
    
    async with httpx.AsyncClient() as client:
        try:
            # --- SPECIAL HANDLING: QUIZ ENGINE (FILE SUPPORT & PERSISTENCE) ---
            if service_name == "Quiz Engine":
                params = {
                    "num_questions": int(data.get("count", data.get("num_questions", 10))),
                    "question_type": data.get("type", "mcq"),
                    "difficulty": data.get("difficulty", "medium"),
                    "language": data.get("language", "auto")
                }
                
                if params["question_type"] == "true_false": params["question_type"] = "true_false"
                elif params["question_type"] == "truefalse": params["question_type"] = "true_false"
                
                material_filenames = data.get("materials", [])
                if isinstance(material_filenames, str):
                    material_filenames = [material_filenames]
                
                files = []
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
                            files.append(("file", (found_path.name, f, "application/octet-stream")))
                    
                    if files:
                        response = await client.post(target_url, data=params, files=files, timeout=120.0)
                    else:
                        response = await client.post(target_url, json=params, timeout=60.0)
                    
                    if response.status_code != 200:
                        raise HTTPException(status_code=response.status_code, detail=f"Quiz Engine Error: {response.text}")
                    
                    resp_json = response.json()
                    
                    # --- Persistence & Synchronization ---
                    db = get_db_connection()
                    cursor = db.cursor(dictionary=True)
                    try:
                        course_id = int(data.get("course_id", 0))
                        target_session_id = int(data.get("target_session_id", 0))
                        group_id = data.get("groupId", f"Quiz_{course_id}_{int(time.time())}")
                        
                        # 1. Create Quiz record
                        cursor.execute("INSERT INTO quizzes (course_id, session_id, name) VALUES (%s, %s, %s)", 
                                     (course_id, target_session_id, group_id))
                        quiz_id = cursor.lastrowid
                        
                        questions_list = resp_json.get("questions", [])
                        for q in questions_list:
                            q_type_raw = q.get("type", "mcq")
                            q_type_db = "mcq"
                            if q_type_raw in ["true_false", "truefalse"]: q_type_db = "truefalse"
                            elif q_type_raw == "written": q_type_db = "essay"
                            
                            cursor.execute(
                                "INSERT INTO questions (quiz_id, question_text, question_type, max_mark) VALUES (%s, %s, %s, %s)",
                                (quiz_id, q.get("question", ""), q_type_db, 1.0)
                            )
                            q_id = cursor.lastrowid
                            
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
                        
                        # 2. Sync with Course Portal
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
                            elif trainee_q["type"] in ["true_false", "truefalse"]:
                                trainee_q["options"] = [{"label": "T", "text": "صح"}, {"label": "F", "text": "خطأ"}]
                                trainee_q["type"] = "tf"
                            trainee_quiz["questions"].append(trainee_q)
                        
                        cursor.execute(
                            "UPDATE courses SET quiz_json = %s, has_active_quiz = 1 WHERE id = %s",
                            (json.dumps(trainee_quiz, ensure_ascii=False), course_id)
                        )
                        
                        db.commit()
                        return resp_json
                    except Exception as db_err:
                        db.rollback()
                        raise HTTPException(status_code=500, detail=f"Database Sync Error: {str(db_err)}")
                    finally:
                        cursor.close()
                        db.close()
                finally:
                    for f in opened_files:
                        f.close()

            # --- DEFAULT PROXY ---
            response = await client.post(target_url, json=data, timeout=60.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"AI Service Error: {response.text}")
            
            return response.json()

        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"Service '{service_name}' on port {port} is offline.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Proxy Error: {str(e)}")

@router.get("/health")
async def check_ai_health():
    results = {}
    async with httpx.AsyncClient() as client:
        for name, port in SERVICE_REGISTRY.items():
            try:
                ai_host = os.getenv("AI_SERVER_HOST", "127.0.0.1")
                resp = await client.get(f"http://{ai_host}:{port}/", timeout=2.0)
                results[name] = "online" if resp.status_code in [200, 404] else "error"
            except:
                results[name] = "offline"
    return results
