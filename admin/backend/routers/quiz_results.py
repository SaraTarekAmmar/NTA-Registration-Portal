from fastapi import APIRouter, Depends, Query
from typing import Optional
from core.database import get_db_connection
from core.auth import get_staff_user

router = APIRouter(prefix="/api/admin/quiz-results", tags=["Quiz Results"])

@router.get("")
async def get_all_quiz_results(course_id: Optional[int] = Query(None), staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                qa.id as attempt_id,
                qa.score as raw_score,
                qa.created_at,
                u.full_name_ar as trainee_name,
                u.national_id,
                u.email,
                c.title as course_name,
                COALESCE(q.quiz_name, 'اختبار الدورة') as quiz_name,
                COALESCE(q.max_grade, 100) as max_grade
            FROM quiz_attempts qa
            JOIN users u ON qa.user_id = u.id
            JOIN courses c ON qa.course_id = c.id
            LEFT JOIN (
                SELECT course_id, MAX(name) as quiz_name, MAX(max_grade) as max_grade 
                FROM quizzes GROUP BY course_id
            ) q ON q.course_id = qa.course_id
            WHERE 1=1
        """
        params = []
        if course_id:
            query += " AND qa.course_id = %s"
            params.append(course_id)
            
        query += " ORDER BY qa.created_at DESC"
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        for row in results:
            if row['max_grade'] and row['raw_score'] is not None:
                row['percentage'] = round((float(row['raw_score']) / float(row['max_grade'])) * 100, 2)
            else:
                row['percentage'] = 0
                
        return results
    finally:
        cursor.close()
        db.close()
