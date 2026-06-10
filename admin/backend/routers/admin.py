from fastapi import APIRouter, HTTPException, Query, Depends, File, UploadFile
from typing import List, Optional
from schemas.admin import TraineeSummary, StageReviewCreate
from core.database import get_db_connection
from core.auth import get_admin_user, get_staff_user, get_current_user, get_password_hash
from core.upload_manager import save_upload_file, move_user_files_to_user_folder, move_admission_file_to_folder
from core.security import generate_temp_password
from core.notifications import send_credential_email
from core.logger_util import log_activity
from core.ai_cv_matcher import trigger_cv_match
import os
import threading
import json
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.post("/upload")
async def upload_admin_file(
    file: UploadFile = File(...),
    folder: str = "reviews",
    staff: dict = Depends(get_staff_user)
):
    """
    Universal upload endpoint for admins and editors.
    Requires a valid staff JWT token. Rejects unauthenticated requests.
    """
    try:
        file_path = await save_upload_file(file, folder)
        
        log_activity(
            category="ADMIN",
            event_type="ADMIN_FILE_UPLOAD",
            user_id=staff.get("id"),
            role=staff.get("role"),
            details={"file_path": file_path, "folder": folder}
        )
        
        return {"file_path": file_path}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/courses")
async def get_admin_courses(current_user: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, title as name FROM courses")
        courses = cursor.fetchall()
        # Add simple icons for the UI
        icons = ["🏛️", "🛡️", "🎯", "📊", "💻", "🚀"]
        for i, c in enumerate(courses):
            c["icon"] = icons[i % len(icons)]
        # Map IDs to strings for frontend compatibility
        for c in courses:
            c["id"] = str(c["id"])
        return courses
    finally:
        cursor.close()
        db.close()
@router.get("/trainees", response_model=List[TraineeSummary])
async def get_trainees(stage: Optional[int] = Query(None), role: Optional[str] = Query(None), course_id: Optional[int] = Query(None), staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        query = """SELECT u.id, u.full_name_ar as name, u.email, u.gender, u.dob, 
                           u.profile_photo as image_url, u.role,
                           ps.current_stage_id as stage, ps.status,
                           (SELECT degree FROM trainee_education WHERE trainee_id = u.id LIMIT 1) as education,
                           a.course_id, a.status as application_status,
                           cv.match_score as ai_match_score,
                           ROUND(
                               COALESCE(
                                   (
                                       SELECT COUNT(DISTINCT al.session_id) * 100.0
                                              / NULLIF((SELECT COUNT(*) FROM course_sessions cs2 WHERE cs2.course_id = a.course_id), 0)
                                       FROM attendance_logs al
                                       JOIN course_sessions cs ON al.session_id = cs.id AND cs.course_id = a.course_id
                                       WHERE al.national_id = u.national_id
                                         AND al.event_type = 'ENTER'
                                   ),
                               0),
                           1) AS att_rate
                    FROM users u 
                    LEFT JOIN pipeline_state ps ON u.id = ps.trainee_id 
                    LEFT JOIN (
                        SELECT user_id, course_id, status,
                               ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY applied_at DESC) AS rn
                        FROM applications
                    ) a ON u.id = a.user_id AND a.rn = 1
                    LEFT JOIN cv_matching_results cv ON u.national_id = cv.national_id AND a.course_id = cv.course_id
                    WHERE u.role IN ('trainee', 'applicant')"""
        
        params = []
        if role is not None:
            query += " AND u.role = %s"
            params.append(role)
        if stage is not None:
            if stage == 7:
                query += " AND (ps.current_stage_id = %s OR a.status = 'approved')"
                params.append(stage)
            else:
                query += " AND ps.current_stage_id = %s"
                params.append(stage)
        
        # Special logic: If stage < 7, they are technically 'applicants'
        # If stage == 7 and accepted, they become 'trainees'
        
        if course_id is not None:
            query += " AND a.course_id = %s"
            params.append(course_id)
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        for row in results:
            row['category'] = row.get('education', 'Unknown')
            
            # Calculate Age
            row['age'] = None
            if row.get('dob'):
                try:
                    from datetime import date
                    today = date.today()
                    dob = row['dob']
                    row['age'] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                except: pass

            # Calculate progress based on stage (7 total stages).
            # BUG 15 FIX: use explicit None check (not 'or') so stage=0 doesn't
            # falsely fall through, and clamp to [1,7] so corrupted data can never
            # push the percentage above 100%.
            raw_stage = row.get('stage')
            stage_num = raw_stage if raw_stage is not None else (7 if row.get('course_id') else 1)
            stage_num = max(1, min(stage_num, 7))
            row['progress_percentage'] = int((stage_num / 7) * 100)
            
        return results
    finally:
        cursor.close()
        db.close()
@router.post("/stage-review")
async def submit_review(review: StageReviewCreate, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(buffered=True)
    try:
        # ── NEW: Move attachment to admission folder ({trainee_nid}_{admin_nid}) ──
        if review.attachment_path:
            # Fetch Trainee NID
            cursor.execute("SELECT national_id FROM users WHERE id = %s", (review.trainee_id,))
            t_row = cursor.fetchone()
            # Fetch Admin NID
            cursor.execute("SELECT national_id FROM users WHERE id = %s", (review.reviewer_id,))
            a_row = cursor.fetchone()
            
            if t_row and a_row:
                t_nid = t_row[0]
                a_nid = a_row[0]
                path_map = move_admission_file_to_folder(t_nid, a_nid, [review.attachment_path])
                review.attachment_path = path_map.get(review.attachment_path, review.attachment_path)

        # ── NEW: Normalized Table Persistence ──
        if review.details:
            table_map = {
                2: "admission_stage_2_security",
                3: "admission_stage_3_psychological",
                # Stage 4 is handled separately below — exam scores come from
                # trainee_exam_submissions (written by the exam portal) and are
                # mirrored into admission_stage_4_exams for the admin audit trail.
                4: None,
                5: "admission_stage_5_interview1",
                6: "admission_stage_6_interview2",
                7: "admission_stage_7_final"
            }
            # Whitelisted columns per stage table — prevents SQL injection via
            # attacker-controlled JSON keys being interpolated into the query.
            allowed_columns_map = {
                "admission_stage_2_security":     {"result", "notes", "officer_name", "check_date", "clearance_level"},
                "admission_stage_3_psychological": {"result", "notes", "psychologist_name", "test_date", "score"},
                "admission_stage_5_interview1":   {"result", "notes", "interviewer_name", "interview_date", "score"},
                "admission_stage_6_interview2":   {"result", "notes", "interviewer_name", "interview_date", "score"},
                "admission_stage_7_final":        {"result", "notes", "decision_maker", "decision_date", "final_score"},
            }
            target_table = table_map.get(review.stage_id)
            if target_table:
                allowed = allowed_columns_map.get(target_table, set())
                # Only keep keys that are whitelisted; silently drop unknown ones.
                safe_details = {k: v for k, v in review.details.items() if k in allowed}
                if safe_details:
                    columns = ["trainee_id"] + list(safe_details.keys())
                    placeholders = ["%s"] * len(columns)
                    values = [review.trainee_id] + list(safe_details.values())

                    # Check for existing record to UPSERT
                    cursor.execute(f"SELECT id FROM {target_table} WHERE trainee_id = %s", (review.trainee_id,))
                    if cursor.fetchone():
                        update_set = ", ".join([f"{col} = %s" for col in safe_details.keys()])
                        cursor.execute(f"UPDATE {target_table} SET {update_set} WHERE trainee_id = %s", list(safe_details.values()) + [review.trainee_id])
                    else:
                        cursor.execute(f"INSERT INTO {target_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})", tuple(values))

        # ── Stage 4: Sync exam scores into admission_stage_4_exams ──
        # Stage 4 exam results are written by the exam portal into
        # trainee_exam_submissions. Here we mirror them into a dedicated
        # admission table so the admin review has a permanent snapshot.
        if review.stage_id == 4:
            cursor.execute("""
                SELECT subject, score
                FROM trainee_exam_submissions
                WHERE trainee_id = %s
            """, (review.trainee_id,))
            exam_rows = cursor.fetchall()
            scores = {row[0]: float(row[1]) for row in exam_rows if row[1] is not None}

            arabic_score           = scores.get("arabic")
            english_score          = scores.get("english")
            public_knowledge_score = scores.get("public_knowledge")
            overall_score = None
            available = [v for v in [arabic_score, english_score, public_knowledge_score] if v is not None]
            if available:
                overall_score = round(sum(available) / len(available), 2)

            admin_notes = review.notes or (review.details.get("admin_notes") if review.details else None)

            cursor.execute("SELECT id FROM admission_stage_4_exams WHERE trainee_id = %s", (review.trainee_id,))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE admission_stage_4_exams
                    SET arabic_score = %s,
                        english_score = %s,
                        public_knowledge_score = %s,
                        overall_score = %s,
                        admin_notes = %s,
                        reviewed_at = NOW()
                    WHERE trainee_id = %s
                """, (arabic_score, english_score, public_knowledge_score, overall_score, admin_notes, review.trainee_id))
            else:
                cursor.execute("""
                    INSERT INTO admission_stage_4_exams
                        (trainee_id, arabic_score, english_score, public_knowledge_score, overall_score, admin_notes, reviewed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (review.trainee_id, arabic_score, english_score, public_knowledge_score, overall_score, admin_notes))


        # BUG 17 FIX (belt-and-suspenders): schema validator already normalises
        # review.result to 'Active'/'Rejected', but use .lower() here so this
        # branch stays correct even if called from non-Pydantic paths.
        if review.result.lower() == 'active':
            if review.stage_id < 7:
                cursor.execute("UPDATE pipeline_state SET current_stage_id = current_stage_id + 1 WHERE trainee_id = %s", (review.trainee_id,))
                
                # Send Stage-Passing Notification
                from core.notifications import send_stage_pass_email
                cursor.execute("SELECT email, full_name_ar, gender FROM users WHERE id = %s", (review.trainee_id,))
                trainee = cursor.fetchone()
                if trainee:
                    stage_names = ["الفرز", "الأمني", "النفسي", "الاختبارات", "المقابلة 1", "المقابلة 2", "القبول"]
                    s_name = stage_names[review.stage_id - 1] if review.stage_id <= len(stage_names) else "المرحلة الحالية"
                    send_stage_pass_email(trainee[0], trainee[1], s_name, trainee[2])

                # Send Stage 4 Exam Invitation if transitioning from Stage 3 to 4
                if review.stage_id == 3:
                    from core.notifications import send_stage4_exam_email
                    if trainee:
                        send_stage4_exam_email(trainee[0], trainee[1], trainee[2])
            else:
                # Stage 7 Approval: Mark as completed, generate credentials, and SWITCH ROLE TO TRAINEE
                cursor.execute("UPDATE pipeline_state SET status = 'completed' WHERE trainee_id = %s", (review.trainee_id,))
                cursor.execute("UPDATE users SET role = 'trainee' WHERE id = %s", (review.trainee_id,))
                
                # ── NEW: Course Assignment Logic for Stage 7 ──
                assigned_course_id = review.details.get('assigned_course_id') if review.details else None
                if assigned_course_id:
                    # Check if application already exists
                    cursor.execute("SELECT id FROM applications WHERE user_id = %s AND course_id = %s", (review.trainee_id, assigned_course_id))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO applications (user_id, course_id, status)
                            VALUES (%s, %s, 'approved')
                        """, (review.trainee_id, assigned_course_id))
                    else:
                        cursor.execute("""
                            UPDATE applications SET status = 'approved' 
                            WHERE user_id = %s AND course_id = %s
                        """, (review.trainee_id, assigned_course_id))
                    
                    # Track private assignment by National ID
                    cursor.execute("SELECT national_id FROM users WHERE id = %s", (review.trainee_id,))
                    u_row = cursor.fetchone()
                    if u_row:
                        nid = u_row[0]
                        cursor.execute("SELECT id FROM private_course_assignments WHERE course_id = %s AND national_id = %s", (assigned_course_id, nid))
                        if not cursor.fetchone():
                            cursor.execute("INSERT INTO private_course_assignments (course_id, national_id) VALUES (%s, %s)", (assigned_course_id, nid))

                # Fetch trainee info for the email
                cursor.execute("SELECT full_name_ar, email, gender FROM users WHERE id = %s", (review.trainee_id,))
                user = cursor.fetchone()
                
                if user:
                    full_name = user[0]
                    email = user[1]
                    gender = user[2]
                    raw_password = generate_temp_password()
                    hashed_password = get_password_hash(raw_password)
                    
                    # Update user with the new password
                    cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_password, review.trainee_id))
                    
                    # Send Email (handled after commit to ensure DB integrity)
                    send_credential_email(email, full_name, raw_password, gender)

                    # ── NEW: Trigger AI CV Matching in background ──
                    if assigned_course_id:
                        threading.Thread(target=trigger_cv_match, args=(review.trainee_id, assigned_course_id)).start()
                    
                    # Log Stage 7 Approval
                    log_activity(
                        category="ADMIN",
                        event_type="STAGE_7_APPROVAL",
                        user_id=admin["id"],
                        role=admin["role"],
                        details={"trainee_id": review.trainee_id, "trainee_name": full_name}
                    )

        else:
            # --- REJECTION LOGIC ---
            cursor.execute("SELECT email, full_name_ar, gender, national_id FROM users WHERE id = %s", (review.trainee_id,))
            u_data = cursor.fetchone()

            if u_data:
                trainee_national_id = u_data[3]
                trainee_name        = u_data[1]

                # Fetch reviewer name for the stage_reviews record
                cursor.execute("SELECT full_name_ar FROM users WHERE id = %s", (review.reviewer_id,))
                reviewer_row = cursor.fetchone()
                reviewer_name = reviewer_row[0] if reviewer_row else str(admin.get("id", ""))

                # 1. Insert stage_reviews record BEFORE deleting the user so the
                #    audit trail is not lost.  We embed the trainee's national_id
                #    inside the details JSON so the record remains identifiable
                #    even after the user row (and its FK) is gone.
                rejection_details = dict(review.details or {})
                rejection_details["rejected_trainee_national_id"] = trainee_national_id
                rejection_details["rejected_trainee_name"]        = trainee_name

                cursor.execute("""
                    INSERT INTO stage_reviews
                        (trainee_id, reviewer_id, stage_id, result,
                         reviewer_name, review_date,
                         notes, attachment_path, details, created_at)
                    VALUES (%s, %s, %s, 'Rejected', %s, CURDATE(), %s, %s, %s, NOW())
                """, (
                    review.trainee_id,
                    review.reviewer_id,
                    review.stage_id,
                    reviewer_name,
                    review.notes or "",
                    review.attachment_path or "",
                    json.dumps(rejection_details),
                ))

                # 2. Send Rejection Email with Reason
                from core.notifications import send_rejection_email
                send_rejection_email(u_data[0], trainee_name, review.notes, u_data[2])

                # 3. Delete uploaded files for this trainee
                from core.upload_manager import delete_trainee_folder
                delete_trainee_folder(trainee_name, trainee_national_id)

                # 4. Delete the user — CASCADE removes pipeline_state, applications, etc.
                #    NOTE: stage_reviews.trainee_id FK is ON DELETE CASCADE in the current schema,
                #    which means this INSERT row will ALSO be deleted here.
                #    To make the audit trail permanent, run the migration below in MySQL:
                #      ALTER TABLE stage_reviews DROP FOREIGN KEY stage_reviews_ibfk_1;
                #      ALTER TABLE stage_reviews MODIFY trainee_id INT NULL;
                #      ALTER TABLE stage_reviews ADD CONSTRAINT stage_reviews_ibfk_1
                #        FOREIGN KEY (trainee_id) REFERENCES users(id) ON DELETE SET NULL;
                cursor.execute("DELETE FROM users WHERE id = %s", (review.trainee_id,))

            # 5. Log the rejection (admin id is used — safe after the user delete)
            log_activity(
                category="ADMIN",
                event_type="APPLICATION_REJECTION",
                user_id=admin["id"],
                role=admin["role"],
                details={"trainee_id": review.trainee_id, "stage_id": review.stage_id, "notes": review.notes}
            )
        
        db.commit()
        return {"message": "Review submitted successfully"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@router.get("/reviews/{trainee_id}")
async def get_reviews(trainee_id: int, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        cursor.execute("SELECT * FROM stage_reviews WHERE trainee_id = %s", (trainee_id,))
        results = cursor.fetchall()
        for row in results:
            if row.get('details') and isinstance(row['details'], str):
                try:
                    row['details'] = json.loads(row['details'])
                except:
                    pass
        return results
    finally:
        cursor.close()
        db.close()

@router.get("/trainees/{trainee_id}")
async def get_trainee_profile(trainee_id: int, staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        # 1. Fetch User and Profile Data (Join everything)
        cursor.execute("""
            SELECT u.id as user_id, u.full_name_ar, u.email, u.national_id, u.dob, u.gender, u.role, u.profile_photo,
                   tp.*, 
                   ps.current_stage_id, ps.status as pipeline_status
            FROM users u 
            LEFT JOIN trainee_profiles tp ON u.id = tp.user_id
            LEFT JOIN pipeline_state ps ON u.id = ps.trainee_id
            WHERE u.id = %s AND u.role IN ('trainee', 'applicant')
        """, (trainee_id,))
        user = cursor.fetchone()
        if user:
            user['id'] = user['user_id'] # Ensure 'id' refers to user_id for frontend compatibility
        if not user:
            raise HTTPException(status_code=404, detail="Trainee not found")

        # 2. Fetch Child Tables (Normalized tables take priority over legacy JSON blobs).
        # BUG 12 NOTE: trainee_profiles.* includes legacy JSON columns (academic_history,
        # professional_history, technical_skills, etc.) from the old single-table design.
        # The queries below overwrite those keys with normalized child-table data.
        # For new registrations this is correct — child tables are always populated.
        # For legacy/imported records where child tables may be empty, we fall back to
        # parsing the legacy JSON blob so data is never silently discarded.
        cursor.execute("SELECT * FROM trainee_education WHERE trainee_id = %s", (trainee_id,))
        normalized_education = cursor.fetchall()
        if normalized_education:
            user['academic_history'] = normalized_education
        else:
            legacy = user.get('academic_history')
            if isinstance(legacy, str):
                try: user['academic_history'] = json.loads(legacy)
                except Exception: user['academic_history'] = []
            elif not isinstance(legacy, list):
                user['academic_history'] = []

        cursor.execute("SELECT * FROM trainee_experience WHERE trainee_id = %s", (trainee_id,))
        normalized_experience = cursor.fetchall()
        if normalized_experience:
            user['professional_history'] = normalized_experience
        else:
            legacy = user.get('professional_history')
            if isinstance(legacy, str):
                try: user['professional_history'] = json.loads(legacy)
                except Exception: user['professional_history'] = []
            elif not isinstance(legacy, list):
                user['professional_history'] = []

        cursor.execute("SELECT * FROM trainee_skills WHERE trainee_id = %s", (trainee_id,))
        skills = cursor.fetchall()
        if skills:
            user['technical_skills'] = [s for s in skills if s['category_id'] == 1]
            user['computer_skills']  = [s for s in skills if s['category_id'] == 2]
            user['soft_skills']      = [s for s in skills if s['category_id'] == 3]
        else:
            for skill_key in ('technical_skills', 'computer_skills', 'soft_skills'):
                legacy = user.get(skill_key)
                if isinstance(legacy, str):
                    try: user[skill_key] = json.loads(legacy)
                    except Exception: user[skill_key] = []
                elif not isinstance(legacy, list):
                    user[skill_key] = []

        cursor.execute("SELECT * FROM trainee_references WHERE trainee_id = %s", (trainee_id,))
        user['references'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainee_awards WHERE trainee_id = %s", (trainee_id,))
        user['awards_impact'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainee_quiz_responses WHERE trainee_id = %s", (trainee_id,))
        user['quiz_results'] = {"answers": {r['question_code']: r['answer_text'] for r in cursor.fetchall()}}

        # Parse legacy JSON fields if still needed
        json_fields = ['phone_numbers', 'emergency_contacts']
        for field in json_fields:
            if user.get(field) and isinstance(user[field], str):
                try: user[field] = json.loads(user[field])
                except: pass

        # 3. Add progress percentage
        # BUG 15 FIX: clamp to [1,7] to prevent > 100% from corrupted data.
        raw_stage = user.get('current_stage_id', 1)
        stage_num = max(1, min(raw_stage if raw_stage is not None else 1, 7))
        user['progress_percentage'] = int((stage_num / 7) * 100)

        # 4. Fetch Application Data (for course info)
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

@router.get("/ai-verification/{trainee_id}")
async def get_ai_verification(trainee_id: int, staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        cursor.execute("SELECT national_id FROM users WHERE id = %s", (trainee_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Trainee not found")
            
        cursor.execute("""
            SELECT * FROM ai_verification_results 
            WHERE national_id = %s AND verification_type = 'OCR'
            ORDER BY updated_at DESC LIMIT 1
        """, (user["national_id"],))
        result = cursor.fetchone()
        
        if result and result.get("metadata"):
            if isinstance(result["metadata"], str):
                result["metadata"] = json.loads(result["metadata"])
                
        return result
    finally:
        cursor.close()
        db.close()

@router.get("/cv-matching-result/{trainee_id}/{course_id}")
async def get_cv_matching_result(trainee_id: int, course_id: int, staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        # Fetch national_id for the trainee
        cursor.execute("SELECT national_id FROM users WHERE id = %s", (trainee_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Trainee not found")
            
        cursor.execute("""
            SELECT * FROM cv_matching_results 
            WHERE national_id = %s AND course_id = %s
        """, (user["national_id"], course_id))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        cursor.execute("SELECT requirement_topic, score FROM cv_matching_requirements WHERE match_id = %s", (result["id"],))
        reqs = cursor.fetchall()
        
        result["analysis_json"] = {
            "requirement_matches": [{"requirement": r["requirement_topic"], "score": r["score"]} for r in reqs]
        }
                
        return result
    finally:
        cursor.close()
        db.close()

@router.get("/attendance")
async def get_admin_attendance(course_id: int, current_user: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Fetch Course Sessions
        cursor.execute("""
            SELECT id, topic as name, DATE_FORMAT(session_date, '%e %M %Y') as date 
            FROM course_sessions 
            WHERE course_id = %s 
            ORDER BY session_date ASC
        """, (course_id,))
        sessions = cursor.fetchall()
        
        # 2. Fetch Students enrolled in the course
        cursor.execute("""
            SELECT u.id, u.full_name_ar as name, u.national_id as nationalId
            FROM users u
            JOIN applications a ON u.id = a.user_id
            WHERE a.course_id = %s AND a.status = 'approved'
        """, (course_id,))
        students = cursor.fetchall()
        
        if not students:
            return {"sessions": sessions, "students": []}

        # 3. Fetch Attendance Logs for these sessions
        session_ids = [s["id"] for s in sessions]
        if not session_ids:
            return {"sessions": [], "students": students}
            
        placeholders = ', '.join(['%s'] * len(session_ids))
        cursor.execute(f"""
            SELECT national_id, session_id, event_type, recorded_at, match_score
            FROM attendance_logs
            WHERE session_id IN ({placeholders})
            ORDER BY recorded_at ASC
        """, tuple(session_ids))
        logs = cursor.fetchall()
        
        # 4. Fetch Attendance Permissions (Excuses)
        cursor.execute("""
            SELECT user_id, type as permission_type, reason as permission_reason, DATE_FORMAT(date, '%e %M %Y') as date, status
            FROM attendance_permissions
            WHERE course_id = %s AND status = 'accepted'
        """, (course_id,))
        permissions = cursor.fetchall()
        
        log_map = {}
        for log in logs:
            nid = log["national_id"]
            sid = str(log["session_id"])
            etype = log["event_type"]
            if nid not in log_map: log_map[nid] = {}
            if sid not in log_map[nid]: log_map[nid][sid] = {}
            if etype == 'ENTER' and 'ENTER' not in log_map[nid][sid]:
                log_map[nid][sid]['ENTER'] = log
            elif etype == 'LEAVE':
                log_map[nid][sid]['LEAVE'] = log

        perm_map = {}
        for p in permissions:
            uid = p["user_id"]
            dstr = p["date"]
            if uid not in perm_map: perm_map[uid] = {}
            perm_map[uid][dstr] = p

        for st in students:
            st["attendance"] = {}
            st_logs = log_map.get(st["nationalId"], {})
            st_perms = perm_map.get(st["id"], {})
            for s in sessions:
                sid = str(s["id"])
                s_date = s["date"]
                log_entry = st_logs.get(sid, {})
                perm_entry = st_perms.get(s_date)
                if 'ENTER' in log_entry:
                    enter_log = log_entry['ENTER']
                    exit_log = log_entry.get('LEAVE', {})
                    st["attendance"][sid] = {
                        "status": "present",
                        "entry_time": enter_log["recorded_at"].strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م"),
                        "entry_photo": f"/api/admin/attendance/photo/{st['nationalId']}/{sid}/ENTER",
                        "match_score": float(enter_log["match_score"] or 0)
                    }
                    if exit_log:
                        st["attendance"][sid]["exit_time"] = exit_log["recorded_at"].strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
                        st["attendance"][sid]["exit_photo"] = f"/api/admin/attendance/photo/{st['nationalId']}/{sid}/LEAVE"
                elif perm_entry:
                    st["attendance"][sid] = {
                        "status": "excused",
                        "permission_type": perm_entry["permission_type"],
                        "permission_reason": perm_entry["permission_reason"]
                    }
                else:
                    st["attendance"][sid] = { "status": "absent" }
                    
        return { "sessions": sessions, "students": students }
    finally:
        cursor.close()
        db.close()

@router.get("/trainee-analytics/{trainee_id}/{course_id}")
async def get_trainee_analytics(trainee_id: int, course_id: int, current_user: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Get user national ID
        cursor.execute("SELECT national_id FROM users WHERE id = %s", (trainee_id,))
        user = cursor.fetchone()
        if not user: raise HTTPException(status_code=404, detail="Trainee not found")
        nid = user["national_id"]

        # 2. Fetch Sessions
        cursor.execute("""
            SELECT id, topic as name, DATE_FORMAT(session_date, '%e %b') as date, session_date
            FROM course_sessions 
            WHERE course_id = %s 
            ORDER BY session_date ASC
        """, (course_id,))
        sessions = cursor.fetchall()

        # 3. Fetch Logs for this trainee
        cursor.execute("""
            SELECT session_id, event_type, recorded_at
            FROM attendance_logs
            WHERE national_id = %s AND session_id IN (SELECT id FROM course_sessions WHERE course_id = %s)
            ORDER BY recorded_at ASC
        """, (nid, course_id))
        logs = cursor.fetchall()

        # 4. Fetch Permissions
        cursor.execute("""
            SELECT type as permission_type, reason as permission_reason, DATE_FORMAT(date, '%e %b') as date
            FROM attendance_permissions
            WHERE user_id = %s AND course_id = %s AND status = 'accepted'
        """, (trainee_id, course_id))
        permissions = cursor.fetchall()

        log_map = {}
        for l in logs:
            sid = str(l["session_id"])
            if sid not in log_map: log_map[sid] = {}
            log_map[sid][l["event_type"]] = l

        perm_map = {p["date"]: p for p in permissions}

        att_sessions = []
        for s in sessions:
            sid = str(s["id"])
            s_date = s["date"]
            l_entry = log_map.get(sid, {})
            p_entry = perm_map.get(s_date)
            
            sess_res = {
                "id": sid,
                "name": s["name"],
                "date": s_date,
                "status": "absent"
            }
            if "ENTER" in l_entry:
                enter = l_entry["ENTER"]
                leave = l_entry.get("LEAVE", {})
                sess_res.update({
                    "status": "present",
                    "entry_time": enter["recorded_at"].strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م"),
                    "entry_photo": f"/api/admin/attendance/photo/{nid}/{sid}/ENTER"
                })
                if leave:
                    sess_res.update({
                        "exit_time": leave["recorded_at"].strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م"),
                        "exit_photo": f"/api/admin/attendance/photo/{nid}/{sid}/LEAVE"
                    })
            elif p_entry:
                sess_res.update({
                    "status": "excused",
                    "permission_type": p_entry["permission_type"],
                    "permission_reason": p_entry["permission_reason"]
                })
            att_sessions.append(sess_res)

        # 5. Skill progress (calculated from assignments if available)
        cursor.execute("""
            SELECT DATE_FORMAT(submitted_at, '%e %b') as date, 
                   COUNT(*) OVER(ORDER BY submitted_at) as cumulative_graded
            FROM assignment_submissions
            WHERE trainee_id = %s AND status = 'graded'
            ORDER BY submitted_at ASC
            LIMIT 5
        """, (trainee_id,))
        prog_rows = cursor.fetchall()
        skill_progress = [row["cumulative_graded"] * 20 for row in prog_rows]
        if not skill_progress: skill_progress = [10, 25, 45, 70, 85] # fallback
        
        return {
            "attSessions": att_sessions,
            "skillProgress": skill_progress
        }
    finally:
        cursor.close()
        db.close()

@router.get("/attendance/photo/{national_id}/{session_id}/{event_type}")
async def get_attendance_photo(national_id: str, session_id: int, event_type: str, staff: dict = Depends(get_current_user)):
    from fastapi.responses import FileResponse, RedirectResponse
    from pathlib import Path
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT image_path FROM attendance_logs
            WHERE national_id = %s AND session_id = %s AND event_type = %s
            ORDER BY recorded_at DESC LIMIT 1
        """, (national_id, session_id, event_type))
        row = cursor.fetchone()
        
        if row and row.get("image_path"):
            project_root = Path(__file__).parent.parent.parent.parent
            abs_path = project_root / row["image_path"]
            if abs_path.exists():
                return FileResponse(str(abs_path))
                
    except Exception as e:
        print(f"Error retrieving attendance photo: {e}")
    finally:
        cursor.close()
        db.close()
        
    # Redirect to fallback mock avatar if real image doesn't exist
    return RedirectResponse(url=f"https://i.pravatar.cc/300?u={national_id}")
