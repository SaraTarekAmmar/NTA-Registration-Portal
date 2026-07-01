from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from core.database import get_db_connection
from core.auth import get_trainer_user
from datetime import datetime

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

def _assert_trainer_assigned(cursor, trainer_id: int, course_id: int):
    # Resolve national ID
    cursor.execute("SELECT national_id FROM users WHERE id = %s", (trainer_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="Trainer profile not found")
        
    cursor.execute("""
        SELECT 1 FROM course_trainers 
        WHERE trainer_national_id = %s AND course_id = %s
    """, (row['national_id'], course_id))
    if not cursor.fetchone():
        raise HTTPException(status_code=403, detail="Not assigned to this course")

@router.get("/session/{session_id}")
async def get_session_attendance(session_id: int, trainer: dict = Depends(get_trainer_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # First, find the course_id for this session
        cursor.execute("SELECT course_id, topic, scheduled_date FROM course_sessions WHERE id = %s", (session_id,))
        session = cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        course_id = session['course_id']
        _assert_trainer_assigned(cursor, trainer['id'], course_id)
        
        # Get all approved trainees for this course
        cursor.execute("""
            SELECT u.id as trainee_id, u.national_id, u.full_name_ar as name
            FROM applications a
            JOIN users u ON a.user_id = u.id
            WHERE a.course_id = %s AND a.status = 'approved'
        """, (course_id,))
        trainees = cursor.fetchall()
        
        # Get attendance logs for this session
        cursor.execute("""
            SELECT national_id, event_type, created_at, notes
            FROM attendance_logs
            WHERE session_id = %s
        """, (session_id,))
        logs = cursor.fetchall()
        
        # Build a map of national_id -> status
        attendance_map = {}
        for log in logs:
            if log['event_type'] == 'ENTER':
                attendance_map[log['national_id']] = 'present'
            elif log['event_type'] == 'ABSENT':
                attendance_map[log['national_id']] = 'absent'
            elif log['event_type'] == 'EXCUSED':
                attendance_map[log['national_id']] = 'excused'
                
        # Merge into trainees
        results = []
        for t in trainees:
            status = attendance_map.get(t['national_id'], 'pending')
            results.append({
                "trainee_id": t["trainee_id"],
                "national_id": t["national_id"],
                "name": t["name"],
                "status": status
            })
            
        return {
            "session": session,
            "attendance": results
        }
    finally:
        cursor.close()
        db.close()

@router.post("/session/{session_id}")
async def submit_session_attendance(session_id: int, records: List[Dict[str, Any]], trainer: dict = Depends(get_trainer_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT course_id FROM course_sessions WHERE id = %s", (session_id,))
        session = cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        course_id = session['course_id']
        _assert_trainer_assigned(cursor, trainer['id'], course_id)
        
        # Update attendance logs
        now = datetime.now()
        for rec in records:
            nat_id = rec.get("national_id")
            status = rec.get("status") # present, absent, excused
            
            if not nat_id or not status: continue
            
            event_type = 'ENTER' if status == 'present' else ('ABSENT' if status == 'absent' else 'EXCUSED')
            
            # Delete existing
            cursor.execute("DELETE FROM attendance_logs WHERE session_id = %s AND national_id = %s", (session_id, nat_id))
            
            if status != 'pending':
                cursor.execute("""
                    INSERT INTO attendance_logs (national_id, session_id, event_type, created_at, source)
                    VALUES (%s, %s, %s, %s, %s)
                """, (nat_id, session_id, event_type, now, 'trainer_manual'))
                
        db.commit()
        return {"message": "Attendance saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()
