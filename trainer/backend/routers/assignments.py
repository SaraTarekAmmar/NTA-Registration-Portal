from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import List, Optional
from schemas.assignment import Assignment, AssignmentCreate, Submission, SubmissionCreate
from core.database import get_db_connection
from core.auth import get_staff_user, get_current_user
from core.upload_manager import save_upload_file
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])

# Project root for path management
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

def get_course_folder(cursor, course_id: int) -> str:
    """Returns the correctly formatted course folder name: {title_slug}_{id}"""
    import re
    cursor.execute("SELECT title FROM courses WHERE id = %s", (course_id,))
    row = cursor.fetchone()
    if not row:
        return str(course_id)
    
    title = row[0]
    # Slugify title
    slug = re.sub(r'[^a-zA-Z0-9]', '_', title).strip('_')
    return f"{slug}_{course_id}"

# --- Trainer Endpoints ---

@router.post("/create", response_model=Assignment)
async def create_assignment(
    course_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    deadline: str = Form(...),
    max_grade: float = Form(10.0),
    file: Optional[UploadFile] = File(None)
):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        # Check if course exists
        cursor.execute("SELECT id FROM courses WHERE id = %s", (course_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Course not found")

        file_path = None
        if file:
            # Save instructions file in data/courses/{course_folder}/assignments/
            course_folder = get_course_folder(cursor, course_id)
            import time
            import re
            timestamp = int(time.time())
            file_extension = Path(file.filename).suffix.lower()
            clean_original = re.sub(r'[^a-zA-Z0-9_]', '', Path(file.filename).stem)
            unique_filename = f"assign_{course_id}_{timestamp}_{clean_original}{file_extension}"
            
            target_dir = PROJECT_ROOT / "data" / "courses" / course_folder / "assignments"
            os.makedirs(target_dir, exist_ok=True)
            
            file_path_full = target_dir / unique_filename
            
            with open(file_path_full, "wb") as buffer:
                while chunk := await file.read(8192):
                    buffer.write(chunk)
            
            file_path = f"data/courses/{course_folder}/assignments/{unique_filename}"

        query = """
            INSERT INTO assignments (course_id, title, description, deadline, max_grade, file_path)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (course_id, title, description, deadline, max_grade, file_path))
        db.commit()
        
        assignment_id = cursor.lastrowid
        
        # Fetch the created assignment to return full data (including created_at)
        cursor.execute("SELECT * FROM assignments WHERE id = %s", (assignment_id,))
        result = cursor.fetchone()
        
        # Convert tuple result if not using dictionary=True (default cursor here)
        if result and not isinstance(result, dict):
            # Manual mapping for non-dictionary cursor
            return {
                "id": result[0],
                "course_id": result[1],
                "title": result[2],
                "description": result[3],
                "deadline": result[4],
                "max_grade": result[5],
                "file_path": result[6],
                "created_at": result[7]
            }
        return result
    finally:
        cursor.close()
        db.close()

@router.get("/course/{course_id}", response_model=List[Assignment])
async def get_assignments(course_id: int):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM assignments WHERE course_id = %s ORDER BY created_at DESC", (course_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()

@router.get("/{assignment_id}/submissions", response_model=List[dict])
async def get_assignment_submissions(assignment_id: int):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT asub.*, u.full_name_ar as trainee_name, u.email as trainee_email
            FROM assignment_submissions asub
            JOIN users u ON asub.trainee_id = u.id
            WHERE asub.assignment_id = %s
        """
        cursor.execute(query, (assignment_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()

@router.patch("/submissions/{submission_id}/grade")
async def grade_submission(submission_id: int, grade: float = Form(...), feedback: str = Form(None)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE assignment_submissions 
            SET grade = %s, feedback = %s, status = 'graded'
            WHERE id = %s
        """, (grade, feedback, submission_id))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Submission not found")
        return {"message": "Graded successfully"}
    finally:
        cursor.close()
        db.close()

# --- Trainee Endpoints ---

@router.post("/submit", response_model=Submission)
async def submit_assignment(
    assignment_id: int = Form(...),
    trainee_id: int = Form(...),
    file: UploadFile = File(...)
):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        # Get course_id for this assignment to store in the correct folder
        cursor.execute("SELECT course_id FROM assignments WHERE id = %s", (assignment_id,))
        course_row = cursor.fetchone()
        if not course_row:
            raise HTTPException(status_code=404, detail="Assignment not found")
        course_id = course_row[0]
        course_folder = get_course_folder(cursor, course_id)

        # Define target directory: data/courses/{course_folder}/submissions/
        import time
        import re
        timestamp = int(time.time())
        file_extension = Path(file.filename).suffix.lower()
        clean_original = re.sub(r'[^a-zA-Z0-9_]', '', Path(file.filename).stem)
        unique_filename = f"submission_{trainee_id}_{timestamp}_{clean_original}{file_extension}"
        
        target_dir = PROJECT_ROOT / "data" / "courses" / course_folder / "submissions"
        os.makedirs(target_dir, exist_ok=True)
        
        file_path_full = target_dir / unique_filename
        
        # Save file manually to ensure it goes to the right place
        with open(file_path_full, "wb") as buffer:
            while chunk := await file.read(8192):
                buffer.write(chunk)
        
        file_path = f"data/courses/{course_folder}/submissions/{unique_filename}"

        # Check if already submitted (Unique constraint will handle it, but better to check)
        cursor.execute("SELECT id FROM assignment_submissions WHERE assignment_id = %s AND trainee_id = %s", (assignment_id, trainee_id))
        existing = cursor.fetchone()
        
        if existing:
            query = "UPDATE assignment_submissions SET file_path = %s, submitted_at = CURRENT_TIMESTAMP, status = 'pending' WHERE id = %s"
            cursor.execute(query, (file_path, existing[0]))
            submission_id = existing[0]
        else:
            query = "INSERT INTO assignment_submissions (assignment_id, trainee_id, file_path) VALUES (%s, %s, %s)"
            cursor.execute(query, (assignment_id, trainee_id, file_path))
            submission_id = cursor.lastrowid
            
        db.commit()
        
        # Fetch the created/updated submission
        cursor.execute("SELECT * FROM assignment_submissions WHERE id = %s", (submission_id,))
        result = cursor.fetchone()
        
        if result and not isinstance(result, dict):
            return {
                "id": result[0],
                "assignment_id": result[1],
                "trainee_id": result[2],
                "file_path": result[3],
                "submitted_at": result[4],
                "grade": result[5],
                "feedback": result[6],
                "status": result[7]
            }
        return result
    finally:
        cursor.close()
        db.close()

@router.get("/my-submission/{assignment_id}/{trainee_id}", response_model=Optional[Submission])
async def get_my_submission(assignment_id: int, trainee_id: int):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM assignment_submissions WHERE assignment_id = %s AND trainee_id = %s", (assignment_id, trainee_id))
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()
