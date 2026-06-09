"""
Dump full courses data from the database with all related tables.
"""
import json
import mysql.connector

DB_CONFIG = dict(
    host="localhost", port=3306,
    user="root", password="OmarNour@Work161996",
    database="nta_portal",
)

db = mysql.connector.connect(**DB_CONFIG)
cur = db.cursor(dictionary=True)

# 1. All courses
cur.execute("SELECT * FROM courses")
courses = cur.fetchall()

for c in courses:
    cid = c["id"]

    # 2. Sessions
    cur.execute("SELECT * FROM course_sessions WHERE course_id = %s", (cid,))
    c["sessions"] = cur.fetchall()

    # 3. Trainers
    cur.execute("""
        SELECT ct.*, u.full_name_ar, u.full_name_en, u.email
        FROM course_trainers ct
        LEFT JOIN users u ON u.national_id = ct.trainer_national_id
        WHERE ct.course_id = %s
    """, (cid,))
    c["trainers"] = cur.fetchall()

    # 4. Applications / enrolled trainees
    cur.execute("""
        SELECT a.id, a.user_id, a.status, a.applied_at,
               u.full_name_ar, u.full_name_en, u.national_id
        FROM applications a
        LEFT JOIN users u ON u.id = a.user_id
        WHERE a.course_id = %s
    """, (cid,))
    c["applications"] = cur.fetchall()

    # 5. Private assignments
    cur.execute("SELECT * FROM private_course_assignments WHERE course_id = %s", (cid,))
    c["private_assignments"] = cur.fetchall()

    # 6. Cohorts
    cur.execute("SELECT * FROM course_cohorts WHERE course_id = %s", (cid,))
    c["cohorts"] = cur.fetchall()

    # 7. Topic priorities
    cur.execute("SELECT * FROM topic_priorities WHERE course_id = %s", (cid,))
    c["topic_priorities"] = cur.fetchall()

    # 8. Quizzes
    cur.execute("SELECT * FROM quizzes WHERE course_id = %s", (cid,))
    quizzes = cur.fetchall()
    for q in quizzes:
        cur.execute("SELECT * FROM questions WHERE quiz_id = %s", (q["id"],))
        questions = cur.fetchall()
        for qu in questions:
            cur.execute("SELECT * FROM answers WHERE question_id = %s", (qu["id"],))
            qu["answers"] = cur.fetchall()
        q["questions"] = questions
    c["quizzes"] = quizzes

    # Convert datetime/date objects to strings
    def fix_types(obj):
        if isinstance(obj, dict):
            return {k: fix_types(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [fix_types(i) for i in obj]
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return obj

    courses[courses.index(c)] = fix_types(c)

cur.close()
db.close()

out = json.dumps(courses, ensure_ascii=False, indent=2)
with open("courses_full_dump.json", "w", encoding="utf-8") as f:
    f.write(out)

print(f"[OK] Dumped {len(courses)} courses to courses_full_dump.json")
