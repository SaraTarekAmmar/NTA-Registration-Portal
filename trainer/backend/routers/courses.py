from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas.course import Course, CourseCreate
import json
import os
from core.database import get_db_connection


from core.auth import get_staff_user

router = APIRouter(prefix="/api/courses", tags=["Courses"])

@router.get("", response_model=List[Course])
async def get_courses():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM courses")
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()

@router.post("", response_model=Course)
async def create_course(course: CourseCreate, staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        query = """INSERT INTO courses (title, description, image_url, duration_weeks, total_sessions, skill_level, status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        values = (course.title, course.description, course.image_url, course.duration_weeks, 
                  course.total_sessions, course.skill_level, course.status)
        cursor.execute(query, values)
        db.commit()
        return {**course.dict(), "id": cursor.lastrowid}
    finally:
        cursor.close()
        db.close()

@router.put("/{course_id}", response_model=Course)
async def update_course(course_id: int, course: CourseCreate, staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        query = """UPDATE courses SET title=%s, description=%s, image_url=%s, duration_weeks=%s, 
                   total_sessions=%s, skill_level=%s, status=%s WHERE id=%s"""
        values = (course.title, course.description, course.image_url, course.duration_weeks, 
                  course.total_sessions, course.skill_level, course.status, course_id)
        cursor.execute(query, values)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Course not found")
        return {**course.dict(), "id": course_id}
    finally:
        cursor.close()
        db.close()

@router.delete("/{course_id}")
async def delete_course(course_id: int, staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM courses WHERE id=%s", (course_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"message": "Course deleted successfully"}
    finally:
        cursor.close()
        db.close()

@router.get("/trainer/{national_id}", response_model=List[Course])
async def get_trainer_courses(national_id: str):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT c.* FROM courses c
            JOIN course_trainers ct ON c.id = ct.course_id
            WHERE ct.trainer_national_id = %s
        """
        cursor.execute(query, (national_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()
@router.get("/{course_id}/sessions")
async def get_course_sessions(course_id: int):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, topic, materials FROM course_sessions WHERE course_id = %s", (course_id,))
        sessions = cursor.fetchall()
        for s in sessions:
            m_data = []
            if s['materials']:
                try:
                    if isinstance(s['materials'], str):
                        raw = json.loads(s['materials'])
                    else:
                        raw = s['materials']
                    
                    # Convert single object {"file_path": "..."} to array expected by UI
                    if isinstance(raw, dict) and "file_path" in raw:
                        filename = os.path.basename(raw["file_path"])
                        m_data.append({
                            "id": f"m_{s['id']}_1",
                            "name": filename,
                            "type": filename.split('.')[-1] if '.' in filename else "file",
                            "path": raw["file_path"]
                        })
                    elif isinstance(raw, list):
                        m_data = raw
                except:
                    m_data = []
            s['materials'] = m_data
        return {"sessions": sessions}

    finally:
        cursor.close()
        db.close()
