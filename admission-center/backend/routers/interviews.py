from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from core.database import get_db_connection
from core.auth import get_admission_manager_user
import os

router = APIRouter(prefix="/api/admission/interviews", tags=["Admission Interviews"])

@router.get("/candidates")
async def get_interview_candidates(staff: dict = Depends(get_admission_manager_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Dynamically determine interview stages if there was a table,
        # but since stages are implicit in NTA (5=interview1, 6=interview2), we use 5 and 6.
        query = """
            SELECT u.id, u.full_name_ar as name, u.email, u.profile_photo as image_url,
                   a.course_id, ps.current_stage_id as stage,
                   c.title as course_name,
                   (SELECT total_score FROM admission_interview_scores ais 
                    WHERE ais.trainee_id = u.id ORDER BY id DESC LIMIT 1) as latest_score,
                   (SELECT recommendation FROM admission_interview_scores ais 
                    WHERE ais.trainee_id = u.id ORDER BY id DESC LIMIT 1) as recommendation
            FROM users u
            JOIN pipeline_state ps ON u.id = ps.trainee_id
            JOIN applications a ON u.id = a.user_id
            LEFT JOIN courses c ON a.course_id = c.id
            WHERE ps.current_stage_id IN (5, 6)
            ORDER BY u.id DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        for row in results:
            # Validate image exists
            img = row.get("image_url")
            if img:
                img_str = str(img).strip()
                if img_str.lower() in ["null", "undefined", ""]:
                    row["image_url"] = None
                else:
                    try:
                        clean_path = img_str.split("/data/")[-1] if "/data/" in img_str else img_str.lstrip("/")
                        if not os.path.exists(os.path.join(project_root, "data", clean_path)) and not os.path.exists(os.path.join(project_root, clean_path)):
                            row["image_url"] = None
                    except:
                        row["image_url"] = None

        return results
    finally:
        cursor.close()
        db.close()
