from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
import requests
from pydantic import BaseModel
import os
import json
from core.database import get_db_connection
from core.auth import get_staff_user

router = APIRouter(prefix="/api/ai", tags=["AI Services"])

FACE_URL = os.getenv("FACE_SERVICE_URL", "http://localhost:7832")
QUIZ_URL = os.getenv("QUIZ_SERVICE_URL", "http://localhost:8001")
OCR_URL = os.getenv("OCR_SERVICE_URL", "http://localhost:2343/extract")

class FaceEnrollRequest(BaseModel):
    image_b64: str
    label: str

class FaceActionRequest(BaseModel):
    image_b64: str


@router.post("/face/enroll")
async def face_enroll(request: FaceEnrollRequest, staff: dict = Depends(get_staff_user)):
    try:
        response = requests.post(f"{FACE_URL}/enroll", json={"image_b64": request.image_b64, "label": request.label}, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Face Service error: {response.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Face service: {str(e)}")

@router.post("/face/checkin")
async def face_checkin(request: FaceActionRequest, staff: dict = Depends(get_staff_user)):
    try:
        response = requests.post(f"{FACE_URL}/checkin", json={"image_b64": request.image_b64}, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Face check-in error: {response.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Face service: {str(e)}")

@router.post("/quiz/generate")
async def generate_quiz(course_id: int = Form(...), file: UploadFile = File(...), num_questions: int = Form(10), session_id: int = Form(0), staff: dict = Depends(get_staff_user)):
    try:
        files = {"file": (file.filename, await file.read(), file.content_type)}
        data = {"num_questions": num_questions}
        response = requests.post(f"{QUIZ_URL}/generate-quiz", files=files, data=data, timeout=120)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Quiz Service error: {response.text}")
            
        quiz_data = response.json()
        
        # Parse output and save to DB
        db = get_db_connection()
        cursor = db.cursor(buffered=True)
        try:
            # Deactivate previous
            if session_id > 0:
                cursor.execute("UPDATE quizzes SET is_active = FALSE WHERE session_id = %s", (session_id,))

            # Create Quiz record
            cursor.execute("""
                INSERT INTO quizzes (course_id, session_id, name, max_grade, attempts_allowed, is_active, availability_duration_hours)
                VALUES (%s, %s, %s, %s, %s, TRUE, %s)
            """, (course_id, session_id, f"Auto-Generated Quiz for {file.filename}", 100.0, 1, 24))
            quiz_id = cursor.lastrowid
            
            # Map questions
            questions = quiz_data.get("questions", [])
            for q in questions:
                cursor.execute("""
                    INSERT INTO questions (quiz_id, name, question_text, question_type, max_mark)
                    VALUES (%s, %s, %s, 'mcq', %s)
                """, (quiz_id, "Q", q.get("question", ""), 10.0))
                q_id = cursor.lastrowid
                
                # Insert Answers (Choices)
                for choice in q.get("options", []):
                    is_correct = True if choice == q.get("answer") else False
                    cursor.execute("""
                        INSERT INTO answers (question_id, answer_text, is_correct, fraction)
                        VALUES (%s, %s, %s, %s)
                    """, (q_id, choice, is_correct, 1.0 if is_correct else 0.0))
            
            db.commit()
            return {"message": "Quiz generated and stored successfully", "quiz_id": quiz_id, "raw_data": quiz_data}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error while saving quiz: {str(e)}")
        finally:
            cursor.close()
            db.close()
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Quiz service: {str(e)}")


@router.post("/admission/full-check")
async def run_full_admission_check(trainee_id: int, course_id: int = 1, staff: dict = Depends(get_staff_user)):
    import sys
    from pathlib import Path
    
    try:
        # Add AI Services to path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.append(str(project_root / "AI Services" / "Electronic Sorting"))
        
        from electronic_sorting import AdmissionAnalyzer
        analyzer = AdmissionAnalyzer()
        
        # In the admin router, we'll run it synchronously for now 
        # or we could make it async if we add the job tracker here too.
        # But since the UI will handle the loading, synchronous is fine for the API call.
        result = analyzer.run_full_check(trainee_id, course_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/id/extract")
async def extract_id_data(trainee_id: int, course_id: int = 1, staff: dict = Depends(get_staff_user)):
    # For backwards compatibility, redirects to the full multi-step AI check
    return await run_full_admission_check(trainee_id, course_id)
