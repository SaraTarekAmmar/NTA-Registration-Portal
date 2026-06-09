import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, '.')
try:
    from core.database import get_db_connection
except ImportError:
    # If run from backend dir
    sys.path.insert(0, '..')
    from core.database import get_db_connection

def get_real_data():
    db = get_db_connection()
    c = db.cursor(dictionary=True)

    try:
        # Get courses that have both trainers AND approved trainees
        c.execute('''
            SELECT DISTINCT c.id, c.title, c.skill_level,
                   (SELECT COUNT(*) FROM course_trainers ct WHERE ct.course_id=c.id) as trainer_count,
                   (SELECT COUNT(*) FROM applications a WHERE a.course_id=c.id AND a.status='approved') as trainee_count
            FROM courses c
            HAVING trainer_count > 0 AND trainee_count > 0
            ORDER BY trainee_count DESC
            LIMIT 5
        ''')
        courses = c.fetchall()
        print('=== Courses with trainers + trainees ===')
        for co in courses:
            print(f"Course #{co['id']}: {co['title']} | trainers={co['trainer_count']} | trainees={co['trainee_count']}")

        if not courses:
            print("No valid courses found with trainers and trainees.")
            return

        cid = courses[0]['id']
        print(f'\n=== Data for Course #{cid} ===')
        
        c.execute("SELECT * FROM courses WHERE id = %s", (cid,))
        course_meta = c.fetchone()
        
        c.execute('''
            SELECT u.id, u.full_name_ar, u.national_id,
                   tp.technical_skills, tp.professional_summary
            FROM users u
            JOIN course_trainers ct ON u.national_id = ct.trainer_national_id
            LEFT JOIN trainee_profiles tp ON u.id = tp.user_id
            WHERE ct.course_id = %s
        ''', (cid,))
        trainers = c.fetchall()
        
        c.execute('''
            SELECT u.id, u.full_name_ar, u.dob,
                   tp.technical_skills, tp.soft_skills
            FROM users u
            JOIN applications a ON u.id = a.user_id
            LEFT JOIN trainee_profiles tp ON u.id = tp.user_id
            WHERE a.course_id = %s AND a.status = 'approved'
            LIMIT 10
        ''', (cid,))
        trainees = c.fetchall()

        data = {
            "course": course_meta,
            "trainers": trainers,
            "trainees": trainees
        }
        
        with open('real_data_sample.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
        print(f"\nSaved real data for Course #{cid} to real_data_sample.json")

    finally:
        c.close()
        db.close()

if __name__ == "__main__":
    get_real_data()
