from fastapi import APIRouter, HTTPException, Depends, Request
from core.database import get_db_connection
from core.auth import create_access_token, verify_password, get_current_user
from schemas.auth import LoginRequest
import mysql.connector
import json
from pydantic import BaseModel
from typing import Optional, Any

router = APIRouter(prefix="/api/exams", tags=["Exams"])

class ExamSubmission(BaseModel):
    score: float
    details: Optional[Any] = None

@router.post("/login")
async def exam_login(request: LoginRequest):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # For exams, we only allow trainees
        query = "SELECT id, full_name_ar, email, role, national_id, password_hash FROM users WHERE email = %s AND role = 'trainee'"
        cursor.execute(query, (request.email,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
        
        if not request.password or not user["password_hash"]:
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        if request.nationalId != user["national_id"]:
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
            
        # Create a special token with exam scope (optional but good practice)
        access_token = create_access_token(
            data={"sub": str(user["id"]), "role": user["role"], "email": user["email"], "purpose": "exam"}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "fullName": user["full_name_ar"],
            "userId": user["id"]
        }
    finally:
        cursor.close()
        db.close()

@router.get("/{course_id}")
async def get_exam(course_id: int, session_id: Optional[int] = None, quiz_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    from datetime import datetime, timedelta
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Fetch Quiz (priority: quiz_id > session_id > course default)
        if quiz_id:
            cursor.execute("SELECT * FROM quizzes WHERE id = %s", (quiz_id,))
        elif session_id:
            cursor.execute("SELECT * FROM quizzes WHERE session_id = %s AND is_active = TRUE", (session_id,))
        else:
            cursor.execute("SELECT * FROM quizzes WHERE course_id = %s AND session_id = 0 AND is_active = TRUE", (course_id,))
        
        quiz = cursor.fetchone()
        if not quiz:
            # Fallback to course.quiz_json for legacy support if needed
            cursor.execute("SELECT quiz_json FROM courses WHERE id = %s AND has_active_quiz = 1", (course_id,))
            legacy = cursor.fetchone()
            if legacy and legacy["quiz_json"]:
                return json.loads(legacy["quiz_json"]) if isinstance(legacy["quiz_json"], str) else legacy["quiz_json"]
            raise HTTPException(status_code=404, detail="لا يوجد اختبار متاح حالياً")

        # 2. Check Timing & Overrides
        if quiz["session_id"] > 0:
            # First, check for a Super Admin override for this specific user and quiz
            cursor.execute(
                "SELECT override_deadline FROM quiz_access_overrides WHERE quiz_id = %s AND trainee_id = %s",
                (quiz["id"], current_user["id"])
            )
            override = cursor.fetchone()
            
            now = datetime.now()
            has_access = False
            
            if override:
                # If override exists, it is the absolute authority
                if now <= override["override_deadline"]:
                    has_access = True
                else:
                    raise HTTPException(status_code=403, detail="انتهى وقت التمديد الخاص بك لهذا الاختبار")
            else:
                # Fallback to standard session timing
                cursor.execute("SELECT session_date FROM course_sessions WHERE id = %s", (quiz["session_id"],))
                sess = cursor.fetchone()
                if sess and sess["session_date"]:
                    start = sess["session_date"]
                    end = start + timedelta(hours=quiz["availability_duration_hours"] or 24)
                    
                    if now < start:
                        raise HTTPException(status_code=403, detail="هذا الاختبار غير متاح بعد")
                    if now > end:
                        raise HTTPException(status_code=403, detail="عذراً، انتهى وقت مراجعة الاختبار")
                    has_access = True
                else:
                    # No session date set, default to accessible if quiz exists? 
                    # Or keep it restricted. Standard is to allow if no date.
                    has_access = True
            
            if not has_access:
                raise HTTPException(status_code=403, detail="غير مسموح لك بدخول هذا الاختبار")

        # 3. Fetch Questions and Options if using relational schema
        cursor.execute("SELECT * FROM questions WHERE quiz_id = %s", (quiz["id"],))
        questions = cursor.fetchall()
        
        if not questions: # Return legacy quiz_json structure if questions table empty
             return {"id": quiz["id"], "name": quiz["name"], "questions": []}

        # Transform to frontend shape
        quiz_out = {
            "id": quiz["id"],
            "title": quiz["name"],
            "questions": []
        }
        
        for q in questions:
            cursor.execute("SELECT * FROM answers WHERE question_id = %s", (q["id"],))
            opts = cursor.fetchall()
            quiz_out["questions"].append({
                "id": q["id"],
                "text": q["question_text"],
                "type": q["question_type"],
                "options": [{"id": o["id"], "text": o["answer_text"]} for o in opts]
            })
            
        return quiz_out
    finally:
        cursor.close()
        db.close()

@router.post("/{course_id}/submit")
async def submit_exam(course_id: int, submission: ExamSubmission, current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        details_str = json.dumps(submission.details) if submission.details else "{}"
        scores_json = json.dumps({"percentage": f"{submission.score}%", "score": submission.score})
        
        query = """
            UPDATE applications 
            SET quiz_results = %s, quiz_scores = %s
            WHERE user_id = %s AND course_id = %s
        """
        cursor.execute(query, (details_str, scores_json, current_user["id"], course_id))
        db.commit()
        
        from core.logger_util import log_activity
        log_activity(
            category="ACTION",
            event_type="EXAM_COMPLETE",
            user_id=current_user["id"],
            role=current_user["role"],
            details={"course_id": course_id, "score": submission.score}
        )
        
        return {"message": "تم تقديم الاختبار بنجاح"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"خطأ في قاعدة البيانات: {err}")
    finally:
        cursor.close()
        db.close()
