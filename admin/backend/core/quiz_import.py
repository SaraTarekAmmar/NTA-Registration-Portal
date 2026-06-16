"""
Reusable ingest for external quiz-result JSON (the "المكاتب الفنية" exports).

Each record looks like:
  { studentFullName, userId (=national_id), examName, studentExamMark,
    examMark, studentExamMarkPercentage, correctAnswersCount,
    wrongAnswersCount, answeredQuestionsCount, studentTimeSpent,
    studentStartTime, studentSubmitTime, itemsAnswers: [...] }

Behaviour (per the agreed design):
  - one course for the whole batch (default "المكاتب الفنية")
  - auto-create a trainee user per national_id if missing (reuse if present)
  - store the per-attempt exam summary in quiz_attempts.details_json
  - idempotent: skips an attempt that already exists for (user, course, exam)

Used by both the one-off deploy importer and the admin upload endpoint.
"""
import json
from datetime import datetime

PASS_THRESHOLD = 50.0  # percentage at/above which an attempt is "pass"
BATCH_COURSE = "المكاتب الفنية"


def _parse_dt(value):
    if not value:
        return None
    s = str(value).replace("Z", "").split(".")[0]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _ensure_course(cur, title):
    cur.execute("SELECT id FROM courses WHERE title = %s OR title_ar = %s LIMIT 1", (title, title))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """INSERT INTO courses
             (title, title_ar, description, image_url, duration_weeks,
              total_sessions, skill_level, status)
           VALUES (%s, %s, %s, '', 0, 0, 'Beginner', 'Ongoing')""",
        (title, title, "نتائج اختبارات مستوردة"),
    )
    return cur.lastrowid


def _ensure_user(cur, national_id, full_name):
    cur.execute("SELECT id FROM users WHERE national_id = %s LIMIT 1", (national_id,))
    row = cur.fetchone()
    if row:
        return row[0], False
    name = full_name or national_id
    cur.execute(
        """INSERT INTO users
             (full_name_ar, full_name_en, email, national_id, role, dob, gender, marital_status)
           VALUES (%s, %s, %s, %s, 'trainee', '2000-01-01', 'male', 'single')""",
        (name, name, national_id + "@imported.nta.eg", national_id),
    )
    return cur.lastrowid, True


def ingest_records(db, records, course_title=BATCH_COURSE):
    """Ingest a flat list of attempt dicts. Returns a summary dict."""
    cur = db.cursor()
    inserted = skipped = created_users = 0
    try:
        course_id = _ensure_course(cur, course_title)
        for a in records or []:
            nid = str(a.get("userId") or "").strip()[:14]
            if not nid:
                skipped += 1
                continue
            uid, created = _ensure_user(cur, nid, a.get("studentFullName"))
            if created:
                created_users += 1
            exam = a.get("examName") or "اختبار"
            # idempotency: same user + course + exam already imported
            cur.execute(
                """SELECT id FROM quiz_attempts
                   WHERE user_id = %s AND course_id = %s
                     AND JSON_UNQUOTE(JSON_EXTRACT(details_json, '$.exam_name')) = %s
                   LIMIT 1""",
                (uid, course_id, exam),
            )
            if cur.fetchone():
                skipped += 1
                continue
            details = {
                "exam_name": exam,
                "max_grade": a.get("examMark"),
                "percentage": a.get("studentExamMarkPercentage"),
                "correct": a.get("correctAnswersCount"),
                "wrong": a.get("wrongAnswersCount"),
                "answered": a.get("answeredQuestionsCount"),
                "time_spent_min": a.get("studentTimeSpent"),
                "start_time": a.get("studentStartTime"),
                "submit_time": a.get("studentSubmitTime"),
            }
            cur.execute(
                """INSERT INTO quiz_attempts (user_id, course_id, score, details_json, created_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (uid, course_id, a.get("studentExamMark"),
                 json.dumps(details, ensure_ascii=False),
                 _parse_dt(a.get("studentSubmitTime"))),
            )
            inserted += 1
        db.commit()
        return {"inserted": inserted, "skipped": skipped,
                "created_users": created_users, "course_id": course_id}
    finally:
        cur.close()


def flatten_payload(obj):
    """Accept either a single attempt, a list of attempts, or {results:[...]}."""
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("results", "attempts", "data"):
            if isinstance(obj.get(key), list):
                return obj[key]
        return [obj]
    return []
