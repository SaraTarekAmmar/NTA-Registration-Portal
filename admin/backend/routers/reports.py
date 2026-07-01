from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db_connection
from core.auth import get_admin_user

router = APIRouter(prefix="/api/admin/reports", tags=["Reports"])

@router.get("/")
async def get_reports(admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Trainees by Pipeline Stage
        cursor.execute("""
            SELECT ps.status as pipeline_status, COUNT(*) as count 
            FROM pipeline_state ps 
            JOIN users u ON ps.trainee_id = u.id
            WHERE u.role = 'trainee'
            GROUP BY ps.status
        """)
        pipeline_status = cursor.fetchall()
        
        # Interview Scores
        cursor.execute("""
            SELECT recommendation, COUNT(*) as count 
            FROM admission_interview_scores 
            GROUP BY recommendation
        """)
        interviews = cursor.fetchall()

        # Courses
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM courses 
            GROUP BY status
        """)
        courses = cursor.fetchall()
        
        return {
            "pipeline_status": pipeline_status,
            "interviews": interviews,
            "courses": courses
        }
    finally:
        cursor.close()
        db.close()
