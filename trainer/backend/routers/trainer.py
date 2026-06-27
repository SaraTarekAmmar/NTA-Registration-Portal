from fastapi import APIRouter, HTTPException, Depends, Request
import httpx
import os
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel

from core.database import get_db_connection
from core.auth import get_current_user
from core.logger_util import log_activity

router = APIRouter(prefix="/api/trainer", tags=["Trainer"])

SERVICE_REGISTRY = {
    "Quiz Engine": int(os.getenv("PORT_QUIZ_GEN", 2345))
}

@router.get("/courses/{course_id}/trainees")
async def get_course_trainees(course_id: int, current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Verify trainer is assigned to this course (or is admin)
        cursor.execute("SELECT national_id FROM users WHERE id = %s", (current_user["id"],))
        user_row = cursor.fetchone()
        if not user_row: raise HTTPException(status_code=404, detail="Trainer not found")
        national_id = user_row["national_id"]

        if current_user["role"] not in ["admin", "superadmin"]:
            cursor.execute("SELECT id FROM course_trainers WHERE course_id = %s AND trainer_national_id = %s", (course_id, national_id))
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="هذه الدورة غير مسندة إليك")

        # Fetch enrolled trainees via applications table
        cursor.execute("""
            SELECT u.id, u.full_name_ar as name, u.email, u.gender, u.dob, u.national_id,
                   u.profile_photo as image_url,
                   a.status as course_status,
                   cv.match_score as ai_match_score
            FROM users u
            JOIN applications a ON u.id = a.user_id
            LEFT JOIN cv_matching_results cv ON u.national_id = cv.national_id AND cv.course_id = %s
            WHERE a.course_id = %s AND a.status = 'approved'
        """, (course_id, course_id))
        trainees = cursor.fetchall()

        # Enrich each trainee with live attendance rate
        for t in trainees:
            t["ai_match_score"] = float(t["ai_match_score"]) if t["ai_match_score"] else None

            cursor.execute("SELECT COUNT(*) as total FROM course_sessions WHERE course_id = %s", (course_id,))
            total_sessions = cursor.fetchone()["total"] or 1

            cursor.execute("""
                SELECT COUNT(DISTINCT session_id) as attended
                FROM attendance_logs
                WHERE national_id = %s AND event_type = 'ENTER'
                AND session_id IN (SELECT id FROM course_sessions WHERE course_id = %s)
            """, (t["national_id"], course_id))
            attended = cursor.fetchone()["attended"]
            t["attRate"] = round((attended / total_sessions) * 100)

            cursor.execute("""
                SELECT COUNT(*) as total_as,
                       SUM(CASE WHEN status = 'graded' THEN 1 ELSE 0 END) as graded_as
                FROM assignment_submissions asub
                JOIN assignments a ON asub.assignment_id = a.id
                WHERE asub.trainee_id = %s AND a.course_id = %s
            """, (t["id"], course_id))
            as_row = cursor.fetchone()
            if as_row and as_row["total_as"]:
                t["progress"] = round((as_row["graded_as"] / as_row["total_as"]) * 100)
            else:
                t["progress"] = t["attRate"]

        return trainees
    finally:
        cursor.close()
        db.close()


@router.get("/trainees/{trainee_id}")
async def get_trainee_for_trainer(trainee_id: int, current_user: dict = Depends(get_current_user)):
    """Returns {user, application} — matches the trainee-profile.html frontend shape."""
    if current_user["role"] not in ["trainer", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        # 1. Fetch User and Profile Data
        cursor.execute("""
            SELECT u.id as user_id, u.*, tp.id as profile_id, tp.*, ps.current_stage_id, ps.status as pipeline_status
            FROM users u 
            LEFT JOIN trainee_profiles tp ON u.id = tp.user_id
            LEFT JOIN pipeline_state ps ON u.id = ps.trainee_id
            WHERE u.id = %s
        """, (trainee_id,))
        user = cursor.fetchone()
        if user:
            user['id'] = user['user_id']
        if not user:
            raise HTTPException(status_code=404, detail="Trainee not found")

        # 2. Fetch Child Tables (Relational)
        cursor.execute("SELECT * FROM trainee_education WHERE trainee_id = %s", (trainee_id,))
        user['academic_history'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainee_experience WHERE trainee_id = %s", (trainee_id,))
        user['professional_history'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainee_skills WHERE trainee_id = %s", (trainee_id,))
        skills = cursor.fetchall()
        user['technical_skills'] = [s for s in skills if s['category_id'] == 1]
        user['computer_skills'] = [s for s in skills if s['category_id'] == 2]
        user['soft_skills'] = [s for s in skills if s['category_id'] == 3]

        cursor.execute("SELECT * FROM trainee_references WHERE trainee_id = %s", (trainee_id,))
        user['references'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainee_awards WHERE trainee_id = %s", (trainee_id,))
        user['awards_impact'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainee_community WHERE trainee_id = %s", (trainee_id,))
        user['community_extracurricular'] = cursor.fetchall()

        # Parse legacy JSON fields if still needed
        json_fields = ['phone_numbers', 'emergency_contacts']
        for field in json_fields:
            if user.get(field) and isinstance(user[field], str):
                try: user[field] = json.loads(user[field])
                except: pass

        # 3. Application + course
        cursor.execute("""
            SELECT a.*, c.title as course_title
            FROM applications a
            LEFT JOIN courses c ON a.course_id = c.id
            WHERE a.user_id = %s AND a.status = 'approved'
            ORDER BY a.applied_at DESC LIMIT 1
        """, (trainee_id,))
        app_data = cursor.fetchone()
        
        if app_data:
            app_json_fields = ['quiz_results', 'quiz_scores']
            for f in app_json_fields:
                if app_data.get(f) and isinstance(app_data[f], str):
                    try: app_data[f] = json.loads(app_data[f])
                    except: pass

        return {"user": user, "application": app_data}
    finally:
        cursor.close()
        db.close()

@router.get("/trainees/{trainee_id}/profile")
async def get_trainee_profile_for_trainer(trainee_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["trainer", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        cursor.execute("""SELECT u.*, tp.phone_numbers, tp.address, tp.technical_skills, tp.soft_skills, 
                                tp.academic_history, tp.professional_history, tp.documents
                          FROM users u 
                          LEFT JOIN trainee_profiles tp ON u.id = tp.user_id
                          WHERE u.id = %s""", (trainee_id,))
        user = cursor.fetchone()
        if not user: raise HTTPException(status_code=404, detail="Trainee not found")
        
        # Parse JSON
        for field in ['phone_numbers', 'technical_skills', 'soft_skills', 'academic_history', 'professional_history', 'documents']:
            if user.get(field) and isinstance(user[field], str):
                try: user[field] = json.loads(user[field])
                except: pass
        return user
    finally:
        cursor.close()
        db.close()

@router.get("/trainees/{trainee_id}/analytics")
async def get_trainee_analytics_for_trainer(trainee_id: int, course_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    """Returns analytics in the shape renderAnalytics() expects: overall_completion, assignments, skills, ai_summary, radar."""
    if current_user["role"] not in ["trainer", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        # 1. Assignment stats + list
        if course_id:
            cursor.execute("""
                SELECT a.id, a.title, a.max_grade, asub.submitted_at, asub.grade, asub.status
                FROM assignments a
                LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.trainee_id = %s
                WHERE a.course_id = %s
            """, (trainee_id, course_id))
        else:
            cursor.execute("""
                SELECT a.id, a.title, a.max_grade, asub.submitted_at, asub.grade, asub.status
                FROM assignments a
                LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.trainee_id = %s
                JOIN applications app ON a.course_id = app.course_id AND app.user_id = %s
            """, (trainee_id, trainee_id))
            
        ass_rows = cursor.fetchall() or []

        total_ass = len(ass_rows)
        submitted = sum(1 for r in ass_rows if r["submitted_at"])
        grades    = [float(r["grade"]) / float(r["max_grade"]) * 100
                     for r in ass_rows if r["grade"] is not None and r["max_grade"]]
        avg_grade = round(sum(grades) / len(grades)) if grades else 0

        assignments_out = []
        for r in ass_rows:
            assignments_out.append({
                "title":        r["title"],
                "submitted_at": str(r["submitted_at"]) if r["submitted_at"] else None,
                "status":       r["status"] or "pending",
                "grade":        round(float(r["grade"]) / float(r["max_grade"]) * 100)
                                if r["grade"] is not None and r["max_grade"] else None
            })

        # 2. Quiz average
        if course_id:
            cursor.execute("SELECT quiz_scores FROM applications WHERE user_id = %s AND course_id = %s", (trainee_id, course_id))
        else:
            cursor.execute("SELECT quiz_scores FROM applications WHERE user_id = %s", (trainee_id,))
        quiz_rows = cursor.fetchall()
        quiz_avg = 0
        for qr in (quiz_rows or []):
            try:
                qs = json.loads(qr["quiz_scores"]) if isinstance(qr["quiz_scores"], str) else qr["quiz_scores"]
                quiz_avg = float(str(qs.get("percentage", "0")).replace("%", ""))
            except: pass

        # 3. Overall completion
        overall = round(
            (submitted / (total_ass or 1)) * 40 +
            quiz_avg * 0.4 +
            avg_grade * 0.2
        )

        # 4. Skills from trainee_skills (Relational)
        cursor.execute("SELECT category_id FROM trainee_skills WHERE trainee_id = %s", (trainee_id,))
        skill_rows = cursor.fetchall()
        tech_count = sum(1 for s in skill_rows if s['category_id'] == 1)
        soft_count = sum(1 for s in skill_rows if s['category_id'] == 3)
        
        tech_score = min(100, tech_count * 14 + 10)
        soft_score = min(100, soft_count * 18 + 10)

        # 5. AI matching data — real from cv_matching_results
        cursor.execute("SELECT national_id FROM users WHERE id = %s", (trainee_id,))
        nid_row = cursor.fetchone()
        ai_summary     = None
        ai_match_score = None
        radar_labels   = []
        radar_scores   = []

        if nid_row:
            if course_id:
                cursor.execute("""
                    SELECT id, match_score, evidence
                    FROM cv_matching_results
                    WHERE national_id = %s AND course_id = %s
                    ORDER BY id DESC LIMIT 1
                """, (nid_row["national_id"], course_id))
            else:
                cursor.execute("""
                    SELECT id, match_score, evidence
                    FROM cv_matching_results
                    WHERE national_id = %s
                    ORDER BY id DESC LIMIT 1
                """, (nid_row["national_id"],))
            ai_row = cursor.fetchone()
            if ai_row:
                ai_match_score = float(ai_row["match_score"]) if ai_row["match_score"] else None
                ai_summary     = ai_row["evidence"]   # Arabic LLM narrative
                
                cursor.execute("SELECT requirement_topic, score FROM cv_matching_requirements WHERE match_id = %s", (ai_row["id"],))
                reqs = cursor.fetchall()
                for req in reqs:
                    radar_labels.append(req.get("requirement_topic", ""))
                    radar_scores.append(req.get("score", 0))

        # 6. Evaluation text
        grade_label = "ممتاز" if overall >= 85 else "جيد جداً" if overall >= 70 else "جيد" if overall >= 55 else "يحتاج تحسين"
        evaluation  = f"المتدرب يُقيَّم بـ \"{grade_label}\" بنسبة إنجاز {overall}%. {'أنجز جميع التكليفات' if submitted == total_ass else f'أنجز {submitted} من {total_ass} تكليف'}."

        return {
            "overall_completion": overall,
            "evaluation":         evaluation,
            "assignments":        assignments_out,
            "skills":             {"technical": tech_score, "analytical": round(quiz_avg), "soft": soft_score},
            "ai_summary":         ai_summary,
            "ai_match_score":     ai_match_score,
            "radar":              {"labels": radar_labels, "scores": radar_scores},
            "recommendations":    [
                {"tag": "مهارة",    "title": "تعزيز المهارات التقنية",   "desc": "يُنصح بالتعمق في مجالات التقنية المرتبطة بالدورة."},
                {"tag": "حضور",    "title": "الالتزام بالحضور",         "desc": "الحضور المنتظم يعزز الاستيعاب ورفع الدرجات."},
                {"tag": "تكليفات", "title": "إتمام التكليفات في موعدها", "desc": "التسليم في الوقت المحدد يرفع تقييم المتدرب."}
            ]
        }
    finally:
        cursor.close()
        db.close()

@router.get("/trainees/{trainee_id}/completion")
async def get_trainee_completion_for_trainer(trainee_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["trainer", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        # Assignments
        cursor.execute("""
            SELECT COUNT(DISTINCT a.id) as total, COUNT(DISTINCT asub.id) as submitted,
                   AVG(CASE WHEN asub.grade IS NOT NULL THEN (asub.grade / a.max_grade * 100) ELSE NULL END) as avg_grade
            FROM assignments a
            LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.trainee_id = %s
            JOIN applications app ON a.course_id = app.course_id AND app.user_id = %s
        """, (trainee_id, trainee_id))
        stats = cursor.fetchone() or {}

        # Quizzes
        cursor.execute("SELECT quiz_scores FROM applications WHERE user_id = %s", (trainee_id,))
        quiz_rows = cursor.fetchall()
        quiz_avg = 0
        if quiz_rows:
            pcts = []
            for r in quiz_rows:
                try:
                    qs = json.loads(r["quiz_scores"]) if isinstance(r["quiz_scores"], str) else r["quiz_scores"]
                    pcts.append(float(str(qs.get("percentage", "0")).replace("%","")))
                except: pass
            if pcts: quiz_avg = sum(pcts) / len(pcts)

        return {
            "overall_completion": round((stats.get("submitted",0)/(stats.get("total",1) or 1)*40) + (quiz_avg*0.4) + (float(stats.get("avg_grade",0) or 0)*0.2)),
            "assignment_stats": stats,
            "quiz_avg": round(quiz_avg)
        }
    finally:
        cursor.close()
        db.close()

@router.post("/generate-quiz")
async def generate_quiz(req: Request, current_user: dict = Depends(get_current_user)):
    # ... (Rest of my robust generate_quiz logic from before)
    try:
        data = await req.json()
    except:
        data = await req.form()
        data = dict(data)
    
    if current_user["role"] not in ["trainer", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    project_root = Path("d:/Work/NTA/NTA-Regestration-Portal - Final")
    port = SERVICE_REGISTRY.get("Quiz Engine", 2345)
    ai_host = os.getenv("AI_SERVER_HOST", "127.0.0.1")
    target_url = f"http://{ai_host}:{port}/generate-quiz"
    
    try: course_id = int(data.get("course_id", 0))
    except: course_id = 0
        
    params = {
        "num_questions": int(data.get("count", 10)),
        "question_type": data.get("type", "mcq"),
        "difficulty": data.get("difficulty", "medium"),
        "language": data.get("language", "auto")
    }
    if params["question_type"] == "truefalse": params["question_type"] = "true_false"
    
    material_filenames = data.get("materials", [])
    if isinstance(material_filenames, str):
        try: material_filenames = json.loads(material_filenames)
        except: material_filenames = [material_filenames]
    
    async with httpx.AsyncClient() as client:
        files = []
        opened_files = []
        try:
            for filename in material_filenames:
                if not filename or not isinstance(filename, str): continue
                possible_paths = [
                    project_root / filename.lstrip('/'),
                    project_root / "uploads" / filename.lstrip('/'),
                    project_root / "user" / "uploads" / "files" / filename.lstrip('/'),
                    project_root / "data" / "uploads" / filename.lstrip('/')
                ]
                found_path = None
                for p in possible_paths:
                    if p.is_file():
                        found_path = p
                        break
                if found_path:
                    f = open(found_path, "rb")
                    opened_files.append(f)
                    files.append(("file", (found_path.name, f, "application/octet-stream")))
            
            if files: response = await client.post(target_url, data=params, files=files, timeout=120.0)
            else: response = await client.post(target_url, json=params, timeout=60.0)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"AI Engine Error: {response.text}")
            
            resp_json = response.json()
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            try:
                target_session_id = int(data.get("target_session_id", 0))
                group_id = data.get("groupId", f"Quiz_{course_id}_{int(time.time())}")
                
                # ── NEW: Set all other quizzes for this session to inactive ──
                if target_session_id > 0:
                    cursor.execute("UPDATE quizzes SET is_active = FALSE WHERE session_id = %s", (target_session_id,))
                
                cursor.execute("""
                    INSERT INTO quizzes (course_id, session_id, name, is_active, availability_duration_hours) 
                    VALUES (%s, %s, %s, TRUE, %s)
                """, (course_id, target_session_id, group_id, int(data.get("duration_hours", 24))))
                quiz_id = cursor.lastrowid
                questions = resp_json.get("questions", [])
                for q in questions:
                    q_type = q.get("type", "mcq")
                    db_type = "mcq"
                    if q_type in ["true_false", "truefalse"]: db_type = "truefalse"
                    cursor.execute("INSERT INTO questions (quiz_id, question_text, question_type, max_mark) VALUES (%s, %s, %s, %s)", (quiz_id, q.get("question", ""), db_type, 1.0))
                    q_id = cursor.lastrowid
                    if q_type == "mcq":
                        opts, ans = q.get("options", {}), q.get("answer", "")
                        for k, v in opts.items():
                            cursor.execute("INSERT INTO answers (question_id, answer_text, is_correct) VALUES (%s, %s, %s)", (q_id, f"({k}) {v}", 1 if k == ans else 0))
                    elif q_type in ["true_false", "truefalse"]:
                        ans = q.get("answer")
                        for v in ["True", "False"]:
                            cursor.execute("INSERT INTO answers (question_id, answer_text, is_correct) VALUES (%s, %s, %s)", (q_id, v, 1 if v.lower() == str(ans).lower() else 0))
                
                trainee_view = {
                    "courseName": data.get("courseName", "Course Quiz"),
                    "title": f"اختبار ذكي: {data.get('courseName', '')}",
                    "questions": []
                }
                for idx, q in enumerate(questions):
                    tq = {"id": idx + 1, "type": q.get("type", "mcq"), "text": q.get("question", ""), "explanation": q.get("explanation", "")}
                    if tq["type"] == "mcq": tq["options"] = [{"label": k, "text": v} for k, v in q.get("options", {}).items()]
                    trainee_view["questions"].append(tq)
                # ── REMOVED: Overwriting course-wide quiz_json ──
                # cursor.execute("UPDATE courses SET quiz_json = %s, has_active_quiz = 1 WHERE id = %s", (json.dumps(trainee_view, ensure_ascii=False), course_id))
                db.commit()
                return resp_json
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=str(e))
            finally:
                cursor.close()
                db.close()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            for f in opened_files: f.close()
@router.post("/quizzes/{quiz_id}/activate")
async def activate_quiz(quiz_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["trainer", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Fetch quiz to find session_id
        cursor.execute("SELECT session_id FROM quizzes WHERE id = %s", (quiz_id,))
        quiz = cursor.fetchone()
        if not quiz: raise HTTPException(status_code=404, detail="Quiz not found")
        
        session_id = quiz["session_id"]
        
        # 2. Deactivate all quizzes for this session
        cursor.execute("UPDATE quizzes SET is_active = FALSE WHERE session_id = %s", (session_id,))
        
        # 3. Activate this specific quiz
        cursor.execute("UPDATE quizzes SET is_active = TRUE WHERE id = %s", (quiz_id,))
        
        db.commit()
        return {"success": True, "message": "Quiz activated successfully"}
    finally:
        cursor.close()
        db.close()


@router.get("/profile/{trainer_id}")
async def get_trainer_profile(trainer_id: int, current_user: dict = Depends(get_current_user)):
    """Returns the full isolated trainer profile and details."""
    if current_user["id"] != trainer_id and current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="غير مسموح لك بعرض هذا الملف الشخصي")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        # 1. Fetch User and isolated Trainer Profile
        cursor.execute("""
            SELECT u.id as user_id, u.*, tp.id as profile_id, tp.*
            FROM users u 
            LEFT JOIN trainer_profiles tp ON u.id = tp.user_id
            WHERE u.id = %s
        """, (trainer_id,))
        user = cursor.fetchone()
        if user:
            user['id'] = user['user_id']
        if not user:
            raise HTTPException(status_code=404, detail="المدرب غير موجود")

        # 2. Fetch Child Tables (Relational)
        cursor.execute("SELECT * FROM trainer_education WHERE trainer_id = %s", (trainer_id,))
        user['academic_history'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainer_experience WHERE trainer_id = %s", (trainer_id,))
        user['professional_history'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainer_skills WHERE trainer_id = %s", (trainer_id,))
        skills = cursor.fetchall()
        user['technical_skills'] = [s for s in skills if s['category_id'] == 1]
        user['computer_skills'] = [s for s in skills if s['category_id'] == 2]
        user['soft_skills'] = [s for s in skills if s['category_id'] == 3]

        cursor.execute("SELECT * FROM trainer_references WHERE trainer_id = %s", (trainer_id,))
        user['references'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainer_awards WHERE trainer_id = %s", (trainer_id,))
        user['awards_impact'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainer_community WHERE trainer_id = %s", (trainer_id,))
        user['community_extracurricular'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainer_social_media WHERE trainer_id = %s", (trainer_id,))
        user['social_media'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainer_standardized_tests WHERE trainer_id = %s", (trainer_id,))
        user['standardized_tests'] = cursor.fetchall()

        # Parse JSON fields
        json_fields = ['phone_numbers', 'emergency_contacts', 'technical_skills', 'soft_skills', 'computer_skills']
        for field in json_fields:
            if user.get(field) and isinstance(user[field], str):
                try: user[field] = json.loads(user[field])
                except: pass

        return user
    finally:
        cursor.close()
        db.close()

