from core.database import get_db_connection
import json
import sys
from datetime import datetime, timedelta

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

db = get_db_connection()
cursor = db.cursor(dictionary=True)

# 1. Get Python Course ID
cursor.execute("SELECT id FROM courses WHERE title LIKE '%Python%' LIMIT 1")
course = cursor.fetchone()
if not course:
    print("Python course not found")
    sys.exit(1)
course_id = course['id']

# 2. Get Assignments for this course
cursor.execute("SELECT id, title FROM assignments WHERE course_id = %s", (course_id,))
assignments = cursor.fetchall()
print(f"Found {len(assignments)} assignments for course {course_id}")

# 3. Seed Target Trainees
target_ids = [65, 66, 67]

for tid in target_ids:
    print(f"Seeding trainee {tid}...")
    
    # Update Trainee Profile (Skills & AI Summary)
    if tid == 65:
        skills_tech = ["Python", "Flask", "SQL", "Data Analysis", "NumPy"]
        skills_soft = ["Communication", "Problem Solving", "Teamwork"]
        summary = {
            "evaluation": "المتدرب يظهر التزاماً ممتازاً وفهماً عميقاً للمفاهيم التقنية المتقدمة. يوصى بالتركيز على مشاريع الذكاء الاصطناعي مستقبلاً.",
            "strengths": ["القدرة التحليلية", "التعلم السريع"],
            "weaknesses": ["إدارة الوقت في المشروعات الضخمة"]
        }
    elif tid == 66:
        skills_tech = ["JavaScript", "React", "Node.js", "Express", "MongoDB"]
        skills_soft = ["Leadership", "Agile Methodology", "Public Speaking"]
        summary = {
            "evaluation": "مستوى المتدرب متوسط في بعض التقنيات الحديثة، يحتاج إلى تحسين مهارات قواعد البيانات العلاقية لتتناسب مع متطلبات الدورة.",
            "strengths": ["العمل الجماعي", "البرمجة التفاعلية"],
            "weaknesses": ["التعامل مع البيانات الضخمة"]
        }
    else:
        skills_tech = ["Java", "Spring Boot", "Docker", "Kubernetes", "AWS"]
        skills_soft = ["Critical Thinking", "Mentoring", "Time Management"]
        summary = {
            "evaluation": "يمتلك المتدرب خلفية قوية في هندسة النظم السحابية، ولكنه يحتاج لمراجعة بعض أساسيات الخوارزميات المتقدمة.",
            "strengths": ["تصميم النظم", "الاعتمادية"],
            "weaknesses": ["مهارات العرض والتقديم"]
        }
    
    cursor.execute("""
        UPDATE trainee_profiles SET 
        technical_skills = %s,
        soft_skills = %s,
        professional_summary = %s
        WHERE user_id = %s
    """, (json.dumps(skills_tech), json.dumps(skills_soft), json.dumps(summary), tid))
    
    # Ensure profile exists if update affected 0 rows
    if cursor.rowcount == 0:
        cursor.execute("""
            INSERT INTO trainee_profiles (user_id, technical_skills, soft_skills, professional_summary, phone_numbers)
            VALUES (%s, %s, %s, %s, '[]')
        """, (tid, json.dumps(skills_tech), json.dumps(skills_soft), json.dumps(summary)))

    # Seed Assignment Submissions
    for i, assign in enumerate(assignments):
        # Only seed some submissions to show progress
        if i > 2 and tid == 67: continue # Skip for one trainee
        
        grade = 85 + (i * 2) if tid == 65 else 90 if tid == 66 else 75
        status = 'graded'
        
        cursor.execute("""
            SELECT id FROM assignment_submissions WHERE assignment_id = %s AND trainee_id = %s
        """, (assign['id'], tid))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO assignment_submissions (assignment_id, trainee_id, file_path, status, grade, submitted_at, feedback)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (assign['id'], tid, "uploads/dummy_assignment.pdf", status, grade, datetime.now() - timedelta(days=7-i), "ممتاز، استمر في هذا الأداء."))

    # Seed Attendance Logs
    cursor.execute("SELECT national_id FROM users WHERE id = %s", (tid,))
    user = cursor.fetchone()
    if user:
        nid = user['national_id']
        for d in range(10):
            event_date = datetime.now() - timedelta(days=d)
            if event_date.weekday() >= 5: continue # Skip weekends
            
            # ENTER
            cursor.execute("""
                INSERT INTO attendance_logs (national_id, session_id, event_type, recorded_at, match_score)
                VALUES (%s, %s, %s, %s, %s)
            """, (nid, 1, 'ENTER', event_date.replace(hour=9, minute=0), 0.95))
            # LEAVE
            cursor.execute("""
                INSERT INTO attendance_logs (national_id, session_id, event_type, recorded_at, match_score)
                VALUES (%s, %s, %s, %s, %s)
            """, (nid, 1, 'LEAVE', event_date.replace(hour=16, minute=0), 0.92))

db.commit()
print("Seeding completed successfully.")
db.close()
