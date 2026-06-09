from fastapi import APIRouter, HTTPException, Request
from core.database import get_db_connection
import mysql.connector
import os
import base64
import time
from pathlib import Path

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/webhook")
async def attendance_webhook(request: Request):
    """
    Inbound webhook for Face Recognition attendance events.
    Expected payload: { "national_id": "...", "session_id": "...", "match_score": 0.95, "image_b64": "...", "image_path": "..." }
    """
    data = await request.json()
    national_id = data.get("national_id")
    session_id = data.get("session_id")
    match_score = data.get("match_score", 0.0)
    event_type = data.get("event_type", "ENTER").upper()
    image_b64 = data.get("image_b64")
    image_path = data.get("image_path")

    if not national_id or not session_id:
        raise HTTPException(status_code=400, detail="Missing required fields: national_id or session_id")

    if event_type not in ["ENTER", "LEAVE"]:
        event_type = "ENTER"

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. VERIFY STAGE 7 STATUS
        cursor.execute("""
            SELECT p.current_stage_id FROM pipeline_state p
            JOIN users u ON u.id = p.trainee_id
            WHERE u.national_id = %s
        """, (national_id,))
        result = cursor.fetchone()
        
        if not result or result['current_stage_id'] != 7:
            from core.logger_util import log_activity
            log_activity(
                category="SECURITY",
                event_type="UNAUTHORIZED_ATTENDANCE",
                details={"national_id": national_id, "stage": result['current_stage_id'] if result else "Not Found"}
            )
            cursor.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Trainee not authorized for attendance (Stage 7 required)")

        # 2. Get Course ID for the given Session ID
        cursor.execute("SELECT course_id FROM course_sessions WHERE id = %s", (session_id,))
        session_row = cursor.fetchone()
        course_id = session_row["course_id"] if session_row else 0

        # 3. Handle Auto-saving of Images
        saved_image_path = None
        if image_b64:
            try:
                # Project root directory: d:\Work\NTA\NTA-Regestration-Portal - Final
                project_root = Path(__file__).parent.parent.parent.parent
                subfolder = "attendance" if event_type == "ENTER" else "leave"
                target_dir = project_root / "data" / "courses" / str(course_id) / subfolder
                
                # Automatically create directory structure if missing
                os.makedirs(target_dir, exist_ok=True)
                
                # Decode image and write binary file
                image_data = base64.b64decode(image_b64.split(",")[-1] if "," in image_b64 else image_b64)
                timestamp = int(time.time())
                filename = f"{national_id}_{session_id}_{event_type}_{timestamp}.jpg"
                file_path = target_dir / filename
                
                with open(file_path, "wb") as img_file:
                    img_file.write(image_data)
                
                # Store relative image path starting with 'data/'
                saved_image_path = f"data/courses/{course_id}/{subfolder}/{filename}"
            except Exception as save_err:
                print(f"Failed to auto-save attendance image: {save_err}")
        elif image_path:
            saved_image_path = image_path

        # 4. Log the attendance event
        query = """
            INSERT INTO attendance_logs (national_id, session_id, event_type, match_score, image_path)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (national_id, session_id, event_type, match_score, saved_image_path))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "status": "success", 
            "message": f"Attendance ({event_type}) recorded for {national_id}",
            "image_path": saved_image_path
        }
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Database persistence failed")
