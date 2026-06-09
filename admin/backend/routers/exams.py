from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional, Dict
from core.database import get_db_connection
from core.auth import create_access_token, verify_password, get_staff_user
from core.exam_analyzer import ExamAnalyzer
import json
import os

router = APIRouter(prefix="/api/exams", tags=["Exams"])

class ExamLoginRequest(BaseModel):
    email: str
    nationalId: str
    password: str
    role: str = "trainee"

class ExamSubmitRequest(BaseModel):
    score: Optional[float] = None # For compatibility with old dummy frontend
    details: Dict # Contains answers, elapsed_seconds, etc.

@router.post("/login")
async def exam_login(req: ExamLoginRequest):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Fetch user including password_hash for verification
        cursor.execute(
            "SELECT id, full_name_ar, password_hash FROM users "
            "WHERE email = %s AND national_id = %s AND role = 'trainee'",
            (req.email, req.nationalId)
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        # BUG 4 FIX: Verify the submitted password against the stored hash.
        # Previously this check was skipped — any person knowing an email + NID
        # could log in and take another trainee's exam.
        if not user.get("password_hash") or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        access_token = create_access_token(data={"sub": str(user['id']), "role": "trainee"})
        return {"access_token": access_token, "userId": user['id']}
    finally:
        cursor.close()
        db.close()

@router.get("/results/{trainee_id}")
async def get_trainee_exam_results_early(trainee_id: int, staff: dict = Depends(get_staff_user)):
    """Alias — defined here BEFORE the /{subject} wildcard so FastAPI matches it first."""
    return await _get_trainee_exam_results(trainee_id, staff)


@router.get("/{subject}")
async def get_exam(subject: str, authorization: Optional[str] = Header(None)):
    # BUG 18 FIX: Exam question bank was publicly accessible without any token.
    # Now requires a valid JWT — either a trainee token (issued by /api/exams/login)
    # or a staff token (for admin preview). Correct answers are still stripped before
    # returning so the response is safe even if the token check were bypassed.
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="مطلوب تسجيل الدخول للوصول إلى الامتحان")

    from core.auth import decode_access_token
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="رمز الجلسة غير صالح أو منتهي الصلاحية")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT content_json FROM exams WHERE subject = %s", (subject,))
        exam = cursor.fetchone()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        content = json.loads(exam['content_json'])
        # Strip correct answers and metadata from the questions sent to the client
        for q in content['questions']:
            if 'correct_answer' in q: del q['correct_answer']
            if 'metadata' in q: del q['metadata']
            
        return content
    finally:
        cursor.close()
        db.close()

@router.post("/{subject}/submit")
async def submit_exam(subject: str, req: ExamSubmitRequest, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # In a real app, decode token to get trainee_id.
    # For now, we'll trust the token as it's a private portal.
    from core.auth import decode_access_token
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    trainee_id = int(payload.get("sub"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Fetch the exam content (including correct answers)
        cursor.execute("SELECT content_json FROM exams WHERE subject = %s", (subject,))
        exam_row = cursor.fetchone()
        if not exam_row:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        exam_content = json.loads(exam_row['content_json'])
        answers = req.details.get('answers', {})
        
        # 2. Run analysis
        analysis = ExamAnalyzer.analyze_submission(exam_content, answers)
        
        # 3. Store submission
        cursor.execute("""
            INSERT INTO trainee_exam_submissions (trainee_id, subject, answers_json, score, processed_results)
            VALUES (%s, %s, %s, %s, %s)
        """, (trainee_id, subject, json.dumps(answers, ensure_ascii=False), analysis['score'], json.dumps(analysis, ensure_ascii=False)))
        
        db.commit()
        return {"message": "Exam submitted successfully", "score": analysis['score']}
    finally:
        cursor.close()
        db.close()

async def _get_trainee_exam_results(trainee_id: int, staff: dict):
    """Internal helper — shared by both route handlers."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM trainee_exam_submissions WHERE trainee_id = %s", (trainee_id,))
        results = cursor.fetchall()
        for r in results:
            if isinstance(r.get('processed_results'), str):
                try:
                    r['processed_results'] = json.loads(r['processed_results'])
                except Exception:
                    pass
            if isinstance(r.get('answers_json'), str):
                try:
                    r['answers_json'] = json.loads(r['answers_json'])
                except Exception:
                    pass
        return results
    finally:
        cursor.close()
        db.close()
