from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Request
from schemas.trainee import TraineeRegistration, CourseApplication, TraineeUpdate
from core.database import get_db_connection
from core.auth import get_current_user
from core.upload_manager import save_upload_file, move_user_files_to_user_folder
from core.logger_util import log_activity
from core.ai_cv_matcher import trigger_cv_match
from core.mail_service import send_registration_success_email
import json
import threading
import os
import html
import time
from datetime import datetime

router = APIRouter(prefix="/api/trainee", tags=["Trainee"])


def _db_json(val):
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return None
    return None

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), folder: str = "general"):
    """
    Universal upload endpoint for trainees.
    Supports any file format (Images, PDF, DOCX, etc.)
    """
    try:
        file_path = await save_upload_file(file, folder)
        return {"file_path": file_path}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Rate Limiting Dictionary: { "ip_address": {"last_hit": float, "daily_count": int, "day": string} }
# BUG 22 — PRODUCTION WARNING: This dict is in-process memory.
# With uvicorn --workers > 1 each worker has its own copy, making the effective
# per-IP limit 3 × N_workers instead of 3. For single-worker / development use
# this is fine. Before scaling to multiple workers, replace with a shared store
# (e.g. Redis via redis-py or a DB-backed counter table).
RATE_LIMIT_STORE = {}

@router.post("/register")
async def register_trainee(request: Request, data: TraineeRegistration):
    # --- 0. Rate Limiting Protection ---
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    today = time.strftime("%Y-%m-%d")
    
    bypass_header = request.headers.get("x-testing-bypass-rate-limit")
    is_local = client_ip in ("127.0.0.1", "::1", "localhost", "unknown")
    
    # --- 0. CSRF Validation (must come BEFORE rate limiting) ---
    # Reject bad CSRF tokens immediately so they cannot burn rate-limit slots.
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("x-csrf-token")
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(status_code=403, detail="خطأ في التحقق من صحة الطلب (CSRF). يرجى إعادة تحميل الصفحة.")

    # --- 1. Rate Limiting Protection ---
    # BUG 19 guarantee: CSRF validation runs BEFORE this block (see BUG 3 fix above).
    # Requests with an invalid/missing CSRF token are rejected with 403 before reaching
    # here, so CSRF failures never consume a user's daily rate-limit quota.
    # A user who loses their CSRF cookie mid-session can reload the page to get a fresh
    # token and retry without being locked out.
    if not (bypass_header == "1" and is_local):
        if client_ip in RATE_LIMIT_STORE:
            record = RATE_LIMIT_STORE[client_ip]
            if record["day"] != today:
                record["daily_count"] = 0
                record["day"] = today
                
            if record["daily_count"] >= 3:
                raise HTTPException(status_code=429, detail="لقد تجاوزت الحد الأقصى للتسجيل اليوم (3 محاولات).")
                
            if now - record["last_hit"] < 60.0:
                raise HTTPException(status_code=429, detail="يرجى الانتظار دقيقة واحدة قبل محاولة التسجيل مرة أخرى.")
                
            record["daily_count"] += 1
            record["last_hit"] = now
        else:
            RATE_LIMIT_STORE[client_ip] = {"last_hit": now, "daily_count": 1, "day": today}

    db = get_db_connection()
    cursor = db.cursor(buffered=True)
    try:
        # Check for existing user by email or national ID (Duplicate Registration Guard)
        cursor.execute("SELECT id FROM users WHERE email = %s OR national_id = %s", (data.email, data.nationalId))
        existing_user = cursor.fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني أو رقم الهوية مسجل بالفعل.")

        # 1. Insert into users table
        user_query = """INSERT INTO users (full_name_ar, full_name_en, email, national_id, role, dob, gender, marital_status, profile_photo) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        # Normalize photo path with leading slash
        photo_val = ("/" + str(data.photoFront).lstrip('/')) if data.photoFront else None
        
        cursor.execute(user_query, (data.fullName, data.fullNameEn, data.email, data.nationalId, data.role, data.dob, data.gender, data.maritalStatus, photo_val))
        user_id = cursor.lastrowid

        # ── NEW: Reorganize files into a user-centric folder ──
        # Extract nested graduation certificate scan
        grad_cert = None
        if data.educationalBackground and isinstance(data.educationalBackground, dict):
            grad_cert = data.educationalBackground.get('graduationCertificateScan')

        # Extract certificates from prizes/awards
        prize_certs = []
        for p in (data.prizesAwardsEntries or []):
            if isinstance(p, dict) and p.get('certificateScan'):
                prize_certs.append(p.get('certificateScan'))

        # Extract documents from standardized tests
        test_docs = []
        for t in (data.standardizedTestsEntries or []):
            if isinstance(t, dict) and t.get('document'):
                test_docs.append(t.get('document'))

        # Collect all potential file paths from the registration data
        file_fields = [
            data.cvResume, data.organizationalChart, data.idScan, 
            data.identityDocumentScan, data.employmentSectionCv, data.criminalRecord, 
            data.sectionSevenCriminalRecordCertificate, data.employerNoc, 
            data.scholarshipEssayFile, data.photoFront, grad_cert
        ]
        # Flatten lists/dicts if they contain paths
        if isinstance(data.lettersOfRecommendation, list):
            file_fields.extend(data.lettersOfRecommendation)
        if isinstance(data.identityPhotos, dict):
            # Front-only identity photo file reorganization
            front_photo = data.identityPhotos.get('front')
            if front_photo:
                file_fields.append(front_photo)
        file_fields.extend(prize_certs)
        file_fields.extend(test_docs)
        
        # Move files and get the mapping
        path_map = move_user_files_to_user_folder(data.fullNameEn, data.nationalId, data.role, file_fields)
        
        # Helper to get the new path
        def _p(old_path):
            if isinstance(old_path, list):
                return [path_map.get(p, p) for p in old_path]
            return path_map.get(old_path, old_path)

        # Update registration data with new paths
        data.cvResume = _p(data.cvResume)
        data.organizationalChart = _p(data.organizationalChart)
        data.idScan = _p(data.idScan)
        data.identityDocumentScan = _p(data.identityDocumentScan)
        data.employmentSectionCv = _p(data.employmentSectionCv)
        data.criminalRecord = _p(data.criminalRecord)
        data.sectionSevenCriminalRecordCertificate = _p(data.sectionSevenCriminalRecordCertificate)
        data.employerNoc = _p(data.employerNoc)
        data.scholarshipEssayFile = _p(data.scholarshipEssayFile)
        data.photoFront = _p(data.photoFront)
        if isinstance(data.lettersOfRecommendation, list):
            data.lettersOfRecommendation = [_p(p) for p in data.lettersOfRecommendation]
        if isinstance(data.identityPhotos, dict) and 'front' in data.identityPhotos:
            data.identityPhotos['front'] = _p(data.identityPhotos['front'])
        if data.educationalBackground and isinstance(data.educationalBackground, dict):
            data.educationalBackground['graduationCertificateScan'] = _p(grad_cert)
        grad_cert = _p(grad_cert)  # Keep local var in sync with the moved path for DB insert
        for p in (data.prizesAwardsEntries or []):
            if isinstance(p, dict) and p.get('certificateScan'):
                p['certificateScan'] = _p(p['certificateScan'])
        for t in (data.standardizedTestsEntries or []):
            if isinstance(t, dict) and t.get('document'):
                t['document'] = _p(t['document'])

        # Security: Prevent Cross-Site Scripting (XSS) by escaping HTML characters in rich text fields
        data.currentAddress = html.escape(data.currentAddress) if data.currentAddress else ""

        # 2. Insert into profiles table (Dynamic Trainer/Trainee routing)
        prefix = "trainer" if data.role == "trainer" else "trainee"

        # Prepare JSON packets for unmapped fields to prevent data loss
        documents_payload = {
            "lettersOfRecommendation": data.lettersOfRecommendation or [],
            "identityDocumentScanFiles": data.identityDocumentScanFiles or [],
            "organizationalChartFiles": data.organizationalChartFiles or [],
            "idScanFiles": data.idScanFiles or [],
            "employerNocFiles": data.employerNocFiles or []
        }

        registration_extra_payload = {
            "interests": data.interests or [],
            "hasPrizesAwards": data.hasPrizesAwards,
            "hasConferencesWorkshops": data.hasConferencesWorkshops,
            "hasPublicVoluntaryWork": data.hasPublicVoluntaryWork
        }

        profile_query = f"""INSERT INTO {prefix}_profiles (
            user_id, phone_numbers, secondary_email, address, emergency_contacts,
            photo_front_path, nationality, military_status, military_reason,
            native_language, english_proficiency, permanent_address,
            portfolio_url, learning_objectives, dietary_restrictions,
            accessibility_requirements, other_skills_free_text, interests_description,
            uses_social_media, data_accuracy_confirmed, professional_summary_text,
            years_experience, id_scan_path, cv_resume_path, organizational_chart_path,
            criminal_record_path, employer_noc_path, scholarship_essay_path,
            graduation_certificate_path, id_card_front_path, has_political_participation,
            political_party_name, political_role, political_work_details,
            has_political_candidacy, candidacy_position_name, candidacy_result,
            candidacy_experience, has_criminal_convictions, conviction_description,
            country_of_stay, government_or_state, city, monthly_average_income,
            number_of_nationalities, identity_doc_type, documents, registration_extra
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )"""
        
        # Flattened paths from path_map (Identity photos: front only)
        id_front = (data.identityPhotos or {}).get('front') if isinstance(data.identityPhotos, dict) else None

        cursor.execute(profile_query, (
            user_id,
            json.dumps(data.phoneNumbers),
            str(data.secondaryEmail) if data.secondaryEmail else None,
            data.currentAddress,
            json.dumps({"name": data.emergencyName, "phone": data.emergencyPhone}),
            photo_val,
            data.nationality,
            data.militaryStatus,
            data.militaryReason,
            data.nativeLanguage,
            data.englishProficiency,
            data.permanentAddress,
            data.portfolioUrl,
            data.learningObjectives,
            data.dietaryRestrictions,
            data.accessibilityRequirements,
            data.otherSkillsFreeText,
            data.interestsDescription,
            data.usesSocialMedia,
            data.dataAccuracyTermsConfirmed,
            data.objective,
            data.yearsExperience,
            data.idScan or data.identityDocumentScan,
            data.cvResume,
            data.organizationalChart,
            data.criminalRecord,
            data.employerNoc,
            data.scholarshipEssayFile,
            grad_cert,
            id_front,
            data.hasPoliticalParticipation,
            data.politicalPartyName,
            data.politicalRole,
            data.politicalWorkDetails,
            data.hasPoliticalCandidacy,
            data.candidacyPositionName,
            data.candidacyResult,
            data.candidacyExperienceDescription,
            data.hasPriorCriminalConvictions,
            data.priorConvictionDescription,
            data.countryOfStay,
            data.governmentOrState,
            data.city,
            data.monthlyAverageIncome,
            data.numberOfNationalities,
            data.identityDocType,
            json.dumps(documents_payload),
            json.dumps(registration_extra_payload)
        ))

        # ── 3. Insert into Child Tables ───────────────────────────────────────
        
        # 3.1 Education History
        for edu in data.academicHistory:
            if isinstance(edu, dict):
                cursor.execute(f"""
                    INSERT INTO {prefix}_education ({prefix}_id, institution, major, degree, gpa, grad_year, ranking)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, edu.get('institution'), edu.get('major'), edu.get('degree'), edu.get('gpa'), edu.get('gradYear'), edu.get('ranking')))

        # 3.2 Professional History
        for job in data.professionalHistory:
            if isinstance(job, dict):
                cursor.execute(f"""
                    INSERT INTO {prefix}_experience ({prefix}_id, organization, title, start_date, end_date, responsibilities, reason_for_leaving)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, job.get('organization'), job.get('title'), job.get('startDate') or None, job.get('endDate') or None, job.get('responsibilities'), job.get('reasonForLeaving')))

        # 3.3 Skills
        all_skills = []
        if data.technicalSkills:
            for s in data.technicalSkills: all_skills.append({'n': s.get('name') if isinstance(s, dict) else s, 'c': 1, 'p': s.get('proficiency') if isinstance(s, dict) else None})
        if data.softSkills:
            for s in data.softSkills: all_skills.append({'n': s.get('name') if isinstance(s, dict) else s, 'c': 3, 'p': s.get('proficiency') if isinstance(s, dict) else None})
        if data.computerSkills:
            for s in data.computerSkills: all_skills.append({'n': s.get('name') if isinstance(s, dict) else s, 'c': 2, 'p': s.get('proficiency') if isinstance(s, dict) else None})
        
        for sk in all_skills:
            if sk['n']:
                cursor.execute(f"""
                    INSERT INTO {prefix}_skills ({prefix}_id, category_id, skill_name, proficiency)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, sk['c'], sk['n'], sk['p']))

        # 3.4 References
        for r in data.references or []:
            if isinstance(r, dict):
                cursor.execute(f"""
                    INSERT INTO {prefix}_references ({prefix}_id, name, relationship, contact_info)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, r.get('name'), r.get('relationship'), r.get('contact')))

        # 3.5 Quiz Responses (Trainee only)
        if prefix == "trainee" and data.quizResults and isinstance(data.quizResults, dict) and "answers" in data.quizResults:
            for q_code, ans in data.quizResults['answers'].items():
                # JS stores answers as { selectedLetter: fullAnswerText } — exactly one key.
                # Extract the single value directly; fall back to the or-chain for resilience.
                if isinstance(ans, dict):
                    ans_text = next((v for v in ans.values() if v), None) \
                               or ans.get('a') or ans.get('b') or ans.get('c') or ans.get('d') \
                               or str(ans)
                    ans_text = str(ans_text)
                else:
                    ans_text = str(ans)
                cursor.execute("""
                    INSERT INTO trainee_quiz_responses (trainee_id, question_code, answer_text)
                    VALUES (%s, %s, %s)
                """, (user_id, q_code, ans_text))

        # 3.6 Awards & Achievements
        for aw in data.prizesAwardsEntries:
            if isinstance(aw, dict):
                cursor.execute(f"""
                    INSERT INTO {prefix}_awards ({prefix}_id, award_title, issuing_body, achievement)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, aw.get('prizeName'), aw.get('issuingBody'), aw.get('certificateScan')))

        # 3.7 Standardized Tests
        for test in data.standardizedTestsEntries:
            if isinstance(test, dict):
                cursor.execute(f"""
                    INSERT INTO {prefix}_standardized_tests ({prefix}_id, test_name, score, date_taken, verification_url)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, test.get('testName'), test.get('testScore') or test.get('score'), test.get('dateObtained') or test.get('dateTaken'), test.get('verificationUrl')))

        # 3.8 Community & Extracurricular
        community_data = []
        if data.conferencesWorkshopsEntries:
            for c in data.conferencesWorkshopsEntries:
                if isinstance(c, dict):
                    community_data.append({'t': c.get('eventName'), 'r': c.get('participationLevel') or 'Participant', 'o': c.get('organizingEntity'), 'd': c.get('activityType')})
        if data.publicVoluntaryWorkEntries:
            for v in data.publicVoluntaryWorkEntries:
                if isinstance(v, dict):
                    community_data.append({'t': v.get('foundationOrCharityName'), 'r': v.get('position'), 'o': v.get('country') or v.get('foundationOrCharityName'), 'd': v.get('scopeOfWork')})
        
        for item in community_data:
            cursor.execute(f"""
                INSERT INTO {prefix}_community ({prefix}_id, skill_name, role, organization, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, item['t'], item['r'], item['o'], item['d']))

        # 3.9 Social Media Accounts (Platform details row-by-row inserts)
        if data.usesSocialMedia == 'yes' and data.socialMediaProfileUrls:
            urls_dict = data.socialMediaProfileUrls
            if isinstance(urls_dict, str):
                try:
                    urls_dict = json.loads(urls_dict)
                except Exception:
                    urls_dict = {}
            if isinstance(urls_dict, dict):
                for platform, url in urls_dict.items():
                    if url:
                        cursor.execute(f"""
                            INSERT INTO {prefix}_social_media ({prefix}_id, platform_name, profile_url)
                            VALUES (%s, %s, %s)
                        """, (user_id, platform, url))

        # 3.10 Additional Languages
        for lang in (data.additionalLanguages or []):
            if isinstance(lang, dict) and lang.get('languageId'):
                cursor.execute(f"""
                    INSERT INTO {prefix}_languages ({prefix}_id, language_name, proficiency)
                    VALUES (%s, %s, %s)
                """, (user_id, lang.get('languageId'), lang.get('proficiencyId')))

        db.commit()
        
        event_type = "TRAINER_REGISTRATION" if data.role == "trainer" else "TRAINEE_REGISTRATION"
        
        log_activity(
            category="ACTION",
            event_type=event_type,
            user_id=user_id,
            national_id=data.nationalId,
            role=data.role,
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
            request_path=request.url.path,
            details={"email": data.email, "fullName": data.fullName}
        )
        # Send registration confirmation email
        try:
            send_registration_success_email(data.email, data.fullName)
        except Exception as mail_err:
            print(f"Failed to trigger registration email: {mail_err}")
            
        return {"message": "Registration successful", "trainee_id": user_id}
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        # Orphan File Cleanup
        try:
            if 'file_fields' in locals() and file_fields:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                for path in file_fields:
                    if isinstance(path, str) and path.startswith("uploads/"):
                        full_path = os.path.join(base_dir, path)
                        if os.path.exists(full_path):
                            os.remove(full_path)
                    elif isinstance(path, list):
                        for p in path:
                            if isinstance(p, str) and p.startswith("uploads/"):
                                full_path = os.path.join(base_dir, p)
                                if os.path.exists(full_path):
                                    os.remove(full_path)
        except Exception as cleanup_e:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()
@router.get("/profile/{trainee_id}")
async def get_profile(trainee_id: int, current_user: dict = Depends(get_current_user)):
    # Authorization check: Admin can see any profile, Trainee can only see their own
    if current_user["role"] != "admin" and current_user["id"] != trainee_id:
        raise HTTPException(status_code=403, detail="غير مسموح لك بالوصول إلى هذا الملف")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        # 1. Fetch User and Profile Data (Join everything)
        cursor.execute("""
            SELECT u.*, tp.*, ps.current_stage_id, ps.status as pipeline_status
            FROM users u 
            LEFT JOIN trainee_profiles tp ON u.id = tp.user_id
            LEFT JOIN pipeline_state ps ON u.id = ps.trainee_id
            WHERE u.id = %s
        """, (trainee_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Trainee not found")

        # 2. Fetch Child Tables
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

        cursor.execute("SELECT * FROM trainee_quiz_responses WHERE trainee_id = %s", (trainee_id,))
        user['quiz_results'] = {"answers": {r['question_code']: r['answer_text'] for r in cursor.fetchall()}}

        cursor.execute("SELECT * FROM trainee_social_media WHERE trainee_id = %s", (trainee_id,))
        user['social_media'] = cursor.fetchall()

        cursor.execute("SELECT * FROM trainee_community WHERE trainee_id = %s", (trainee_id,))
        user['community_extracurricular'] = cursor.fetchall()

        # Parse legacy JSON fields if still needed for compatibility
        json_fields = ['phone_numbers', 'emergency_contacts']
        for field in json_fields:
            if user.get(field) and isinstance(user[field], str):
                try: user[field] = json.loads(user[field])
                except: pass

        # 3. Fetch Application and Pipeline Data
        cursor.execute("""
            SELECT a.*, c.title, c.description, ps.current_stage_id, ps.status as pipeline_status
            FROM applications a 
            LEFT JOIN courses c ON a.course_id = c.id 
            LEFT JOIN pipeline_state ps ON a.user_id = ps.trainee_id 
            WHERE a.user_id = %s
        """, (trainee_id,))
        courses = cursor.fetchall()
        
        return {
            "user": user,
            "courses": courses
        }
    finally:
        cursor.close()
        db.close()
APPLY_RATE_LIMIT = {}

@router.post("/apply")
async def apply_to_course(data: CourseApplication, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    now = time.time()

    if user_id in APPLY_RATE_LIMIT:
        if now - APPLY_RATE_LIMIT[user_id] < 10:
            raise HTTPException(status_code=429, detail="يرجى الانتظار 10 ثوانٍ قبل التقديم مرة أخرى.")
    APPLY_RATE_LIMIT[user_id] = now

    db = get_db_connection()
    cursor = db.cursor(buffered=True)
    try:
        # Check course status
        cursor.execute("SELECT status FROM courses WHERE id = %s", (data.course_id,))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="الدورة غير موجودة")
        
        if course[0] == 'Completed':
            raise HTTPException(status_code=400, detail="عذراً، هذه الدورة انتهت ولا يمكن التقديم لها")

        # Check if already applied
        cursor.execute("SELECT id FROM applications WHERE user_id = %s AND course_id = %s", (current_user["id"], data.course_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="لقد تقدمت بالفعل لهذه الدورة")

        # Create application
        cursor.execute("""
            INSERT INTO applications (user_id, course_id, status, motivation_data, research_publication, references_data, logistics, identity_photos, quiz_results, quiz_scores)
            VALUES (%s, %s, 'waiting', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
        """, (current_user["id"], data.course_id))
        
        # Check and Update/Insert pipeline state
        cursor.execute("SELECT id FROM pipeline_state WHERE trainee_id = %s", (current_user["id"],))
        if cursor.fetchone():
            cursor.execute("UPDATE pipeline_state SET current_stage_id = 1, status = 'active' WHERE trainee_id = %s", (current_user["id"],))
        else:
            cursor.execute("INSERT INTO pipeline_state (trainee_id, current_stage_id, status) VALUES (%s, 1, 'active')", (current_user["id"],))
            
        db.commit()
        
        log_activity(
            category="ACTION",
            event_type="COURSE_APPLICATION",
            user_id=current_user["id"],
            role=current_user["role"],
            details={"course_id": data.course_id}
        )

        # ── NEW: Trigger AI CV Matching in background ──
        threading.Thread(target=trigger_cv_match, args=(current_user["id"], data.course_id)).start()
        
        return {"message": "Application submitted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()
@router.put("/profile/{trainee_id}")
async def update_profile(trainee_id: int, data: TraineeUpdate, current_user: dict = Depends(get_current_user)):
    # Authorization: Trainee can only edit their own
    if current_user["id"] != trainee_id:
        raise HTTPException(status_code=403, detail="غير مسموح لك بتعديل هذا الملف")
    
    db = get_db_connection()
    cursor = db.cursor(buffered=True)
    try:
        # Fetch user info for folder naming and movement
        cursor.execute("SELECT full_name_en, national_id, role FROM users WHERE id = %s", (trainee_id,))
        uinfo = cursor.fetchone()
        if not uinfo:
            raise HTTPException(status_code=404, detail="User not found")
        
        u_name_en, u_nid, u_role = uinfo

        # Collect and move any newly uploaded files
        files_to_move = []
        if data.photoFront: files_to_move.append(data.photoFront)
        if data.idCardFront: files_to_move.append(data.idCardFront)
        if data.graduationCertificate: files_to_move.append(data.graduationCertificate)
        if data.cvResume: files_to_move.append(data.cvResume)
        if data.idScan: files_to_move.append(data.idScan)
        if data.organizationalChart: files_to_move.append(data.organizationalChart)
        if data.criminalRecord: files_to_move.append(data.criminalRecord)
        if data.employerNoc: files_to_move.append(data.employerNoc)
        if data.scholarshipEssayFile: files_to_move.append(data.scholarshipEssayFile)
        if data.lettersOfRecommendation: files_to_move.extend(data.lettersOfRecommendation)
        
        if files_to_move:
            path_map = move_user_files_to_user_folder(u_name_en, u_nid, u_role, files_to_move)
            def _up(val):
                if isinstance(val, str): return path_map.get(val, val)
                if isinstance(val, list): return [path_map.get(x, x) for x in val]
                return val
            if data.photoFront: data.photoFront = _up(data.photoFront)
            if data.idCardFront: data.idCardFront = _up(data.idCardFront)
            if data.graduationCertificate: data.graduationCertificate = _up(data.graduationCertificate)
            if data.cvResume: data.cvResume = _up(data.cvResume)
            if data.idScan: data.idScan = _up(data.idScan)
            if data.organizationalChart: data.organizationalChart = _up(data.organizationalChart)
            if data.criminalRecord: data.criminalRecord = _up(data.criminalRecord)
            if data.employerNoc: data.employerNoc = _up(data.employerNoc)
            if data.scholarshipEssayFile: data.scholarshipEssayFile = _up(data.scholarshipEssayFile)
            if data.lettersOfRecommendation: data.lettersOfRecommendation = _up(data.lettersOfRecommendation)

        # 1. Update users table
        user_updates = []
        user_params = []
        if data.fullName is not None: user_updates.append("full_name_ar = %s"); user_params.append(data.fullName)
        if data.fullNameEn is not None: user_updates.append("full_name_en = %s"); user_params.append(data.fullNameEn)
        if data.email is not None: user_updates.append("email = %s"); user_params.append(str(data.email))
        if data.dob is not None and data.dob != "": user_updates.append("dob = %s"); user_params.append(data.dob)
        if data.gender is not None: user_updates.append("gender = %s"); user_params.append(data.gender)
        if data.maritalStatus is not None: user_updates.append("marital_status = %s"); user_params.append(data.maritalStatus)
        if data.photoFront is not None: 
            user_updates.append("profile_photo = %s")
            user_params.append("/" + str(data.photoFront).lstrip('/') if data.photoFront else None)
        
        if user_updates:
            user_query = f"UPDATE users SET {', '.join(user_updates)} WHERE id = %s"
            user_params.append(trainee_id)
            cursor.execute(user_query, tuple(user_params))

        # 2. Update trainee_profiles table (Relational)
        profile_updates = []
        profile_params = []
        
        # Mapping flat fields
        flat_map = {
            "secondary_email": data.secondaryEmail,
            "address": html.escape(data.currentAddress) if data.currentAddress else None,
            "permanent_address": data.permanentAddress,
            "nationality": data.nationality,
            "military_status": data.militaryStatus,
            "military_reason": data.militaryReason,
            "native_language": data.nativeLanguage,
            "english_proficiency": data.englishProficiency,
            "portfolio_url": data.portfolioUrl,
            "learning_objectives": data.learningObjectives,
            "dietary_restrictions": data.dietaryRestrictions,
            "accessibility_requirements": data.accessibilityRequirements,
            "other_skills_free_text": data.otherSkillsFreeText,
            "professional_summary_text": data.objective,
            "years_experience": data.yearsExperience,
            "id_scan_path": data.idScan,
            "cv_resume_path": data.cvResume,
            "organizational_chart_path": data.organizationalChart,
            "criminal_record_path": data.criminalRecord,
            "employer_noc_path": data.employerNoc,
            "scholarship_essay_path": data.scholarshipEssayFile,
            "graduation_certificate_path": data.graduationCertificate,
            "id_card_front_path": data.idCardFront,
            "letters_of_recommendation": json.dumps(data.lettersOfRecommendation) if data.lettersOfRecommendation is not None else None,
            "has_political_participation": data.hasPoliticalParticipation,
            "political_party_name": data.politicalPartyName,
            "political_role": data.politicalRole,
            "political_work_details": data.politicalWorkDetails,
            "has_political_candidacy": data.hasPoliticalCandidacy,
            "candidacy_position_name": data.candidacyPositionName,
            "candidacy_result": data.candidacyResult,
            "candidacy_experience": data.candidacyExperienceDescription,
            "has_criminal_convictions": data.hasPriorCriminalConvictions,
            "conviction_description": data.priorConvictionDescription,
            "country_of_stay": getattr(data, "countryOfStay", None),
            "government_or_state": getattr(data, "governmentOrState", None),
            "city": getattr(data, "city", None),
            "monthly_average_income": getattr(data, "monthlyAverageIncome", None),
            "number_of_nationalities": getattr(data, "numberOfNationalities", None),
            "identity_doc_type": getattr(data, "identityDocType", None)
        }

        if data.phoneNumbers is not None:
            profile_updates.append("phone_numbers = %s")
            profile_params.append(json.dumps(data.phoneNumbers))
            
        if data.emergencyName is not None or data.emergencyPhone is not None:
            profile_updates.append("emergency_contacts = %s")
            profile_params.append(json.dumps({"name": data.emergencyName, "phone": data.emergencyPhone}))

        for col, val in flat_map.items():
            if val is not None:
                profile_updates.append(f"{col} = %s")
                profile_params.append(val)

        if profile_updates:
            profile_query = f"UPDATE trainee_profiles SET {', '.join(profile_updates)} WHERE user_id = %s"
            profile_params.append(trainee_id)
            cursor.execute(profile_query, tuple(profile_params))

        # ── 3. Sync Child Tables ──────────────────────────────────────────────
        
        # 3.1 Education
        if data.academicHistory is not None:
            cursor.execute("DELETE FROM trainee_education WHERE trainee_id = %s", (trainee_id,))
            for edu in data.academicHistory:
                if isinstance(edu, dict):
                    cursor.execute("""
                        INSERT INTO trainee_education (trainee_id, institution, major, degree, gpa, grad_year, ranking)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (trainee_id, edu.get('institution'), edu.get('major'), edu.get('degree'), edu.get('gpa'), edu.get('gradYear'), edu.get('ranking')))

        # 3.2 Experience
        if data.professionalHistory is not None:
            cursor.execute("DELETE FROM trainee_experience WHERE trainee_id = %s", (trainee_id,))
            for job in data.professionalHistory:
                if isinstance(job, dict):
                    cursor.execute("""
                        INSERT INTO trainee_experience (trainee_id, organization, title, start_date, end_date, responsibilities, reason_for_leaving)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (trainee_id, job.get('organization'), job.get('title'), job.get('startDate') or None, job.get('endDate') or None, job.get('responsibilities'), job.get('reasonForLeaving')))

        # 3.3 Skills
        if data.technicalSkills is not None or data.softSkills is not None or data.computerSkills is not None:
            cursor.execute("DELETE FROM trainee_skills WHERE trainee_id = %s", (trainee_id,))
            all_skills = []
            if data.technicalSkills is not None:
                for s in data.technicalSkills: all_skills.append({'n': s.get('name') if isinstance(s, dict) else s, 'c': 1, 'p': s.get('proficiency') if isinstance(s, dict) else None})
            if data.softSkills is not None:
                for s in data.softSkills: all_skills.append({'n': s.get('name') if isinstance(s, dict) else s, 'c': 3, 'p': s.get('proficiency') if isinstance(s, dict) else None})
            if data.computerSkills is not None:
                for s in data.computerSkills: all_skills.append({'n': s.get('name') if isinstance(s, dict) else s, 'c': 2, 'p': s.get('proficiency') if isinstance(s, dict) else None})
            
            for sk in all_skills:
                if sk['n']:
                    cursor.execute("INSERT INTO trainee_skills (trainee_id, category_id, skill_name, proficiency) VALUES (%s, %s, %s, %s)", (trainee_id, sk['c'], sk['n'], sk['p']))

        # 3.4 Quiz Responses
        if data.quizResults is not None and isinstance(data.quizResults, dict) and "answers" in data.quizResults:
            cursor.execute("DELETE FROM trainee_quiz_responses WHERE trainee_id = %s", (trainee_id,))
            for q_code, ans in data.quizResults['answers'].items():
                ans_text = str(ans.get('a') or ans.get('b') or ans.get('c') or ans.get('d') or ans) if isinstance(ans, dict) else str(ans)
                cursor.execute("INSERT INTO trainee_quiz_responses (trainee_id, question_code, answer_text) VALUES (%s, %s, %s)", (trainee_id, q_code, ans_text))

        # 3.5 Community & Extracurricular Sync
        # Note: In TraineeUpdate, we don't have these explicitly yet, but if they were added, we'd sync them here.
        # For now, let's just ensure the table exists and is queried.
        
        db.commit()
        
        log_activity(
            category="ACTION",
            event_type="PROFILE_UPDATE",
            user_id=trainee_id,
            role=current_user["role"]
        )
        
        return {"message": "Profile updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@router.get("/course/{course_id}/details")
async def get_course_details(course_id: int, current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Resolve national_id if not in token (for backward compatibility during migration)
        national_id = current_user.get("national_id")
        if not national_id:
            cursor.execute("SELECT national_id FROM users WHERE id = %s", (current_user["id"],))
            user_row = cursor.fetchone()
            if user_row:
                national_id = user_row["national_id"]
        
        if not national_id:
             raise HTTPException(status_code=400, detail="Could not resolve user identity")

        # 1. Fetch Course Metadata
        cursor.execute("""
            SELECT id, title, description, skill_level, duration_weeks, total_sessions, status, has_active_quiz, image_url
            FROM courses WHERE id = %s
        """, (course_id,))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # 2. Fetch Sessions and Materials + Session Quizzes + User Overrides
        from datetime import timedelta
        cursor.execute("""
            SELECT s.id, s.session_date, s.topic, s.materials, q.id as quiz_id, q.availability_duration_hours,
                   o.override_deadline
            FROM course_sessions s
            LEFT JOIN quizzes q ON s.id = q.session_id AND q.is_active = TRUE
            LEFT JOIN quiz_access_overrides o ON q.id = o.quiz_id AND o.trainee_id = %s
            WHERE s.course_id = %s 
            ORDER BY s.session_date ASC
        """, (current_user["id"], course_id))
        sessions = cursor.fetchall()
        
        now = datetime.now()
        for s in sessions:
            m_json = _db_json(s['materials'])
            s['materials'] = m_json if isinstance(m_json, dict) else {}
            
            # ── Quiz Status Calculation ──
            s['quiz'] = None
            if s['quiz_id']:
                start_time = s['session_date']
                duration = s['availability_duration_hours'] or 24
                # Priority: Override Deadline > Standard End Time
                standard_end = start_time + timedelta(hours=duration) if start_time else None
                override_end = s['override_deadline']
                
                final_end_time = override_end if override_end else standard_end
                
                status = "AVAILABLE"
                if not start_time or now < start_time:
                    status = "LOCKED"
                elif final_end_time and now > final_end_time:
                    status = "EXPIRED"
                
                s['quiz'] = {
                    "id": s['quiz_id'],
                    "status": status,
                    "end_time": final_end_time.isoformat() if final_end_time else None,
                    "is_extended": override_end is not None
                }

        # 3. Fetch Announcements (from system_alerts)
        # Handle case where table might not exist yet during migration
        announcements = []
        try:
            cursor.execute("""
                SELECT alert_text as title, created_at, target_type
                FROM system_alerts 
                WHERE (target_type = 'global' OR (target_type = 'course' AND target_id = %s))
                ORDER BY created_at DESC LIMIT 5
            """, (course_id,))
            announcements = cursor.fetchall()
        except:
            # Fallback if table missing
            announcements = [{
                "title": "مرحباً بك في الدورة التدريبية! يرجى متابعة المنهج بانتظام.",
                "created_at": datetime.now(),
                "target_type": "global"
            }]

        # 4. Fetch Progress (mocking until trainee_progress table is created)
        # We can also calculate a fake progress if needed for now
        progress = {
            "percentage": 0,
            "completed_materials": []
        }
        
        # 5. Fetch Grade if exists
        cursor.execute("SELECT percentage FROM grades WHERE national_id = %s AND course_id = %s", 
                       (national_id, course_id))
        grade = cursor.fetchone()
        if grade:
            progress["percentage"] = int(grade['percentage'])

        return {
            "course": course,
            "sessions": sessions,
            "announcements": announcements,
            "progress": progress
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@router.get("/completion")
async def get_my_completion(current_user: dict = Depends(get_current_user)):
    """Returns completion rate data for the current trainee: assignments, quiz scores, and overall progress."""
    if current_user["role"] != "trainee":
        raise HTTPException(status_code=403, detail="هذا الرابط مخصص للمتدربين فقط")
    
    trainee_id = current_user["id"]
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        # 1. Assignments: total assigned vs submitted vs graded
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT a.id) as total_assignments,
                COUNT(DISTINCT asub.id) as submitted,
                SUM(CASE WHEN asub.status = 'graded' THEN 1 ELSE 0 END) as graded,
                AVG(CASE WHEN asub.grade IS NOT NULL THEN (asub.grade / a.max_grade * 100) ELSE NULL END) as avg_grade_pct
            FROM assignments a
            LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.trainee_id = %s
            JOIN applications app ON a.course_id = app.course_id AND app.user_id = %s
        """, (trainee_id, trainee_id))
        assign_stats = cursor.fetchone() or {}

        # 2. Individual assignment details
        cursor.execute("""
            SELECT a.id, a.title, a.max_grade, a.deadline,
                   asub.grade, asub.status, asub.submitted_at, asub.feedback,
                   c.title as course_title
            FROM assignments a
            JOIN applications app ON a.course_id = app.course_id AND app.user_id = %s
            JOIN courses c ON a.course_id = c.id
            LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.trainee_id = %s
            ORDER BY a.deadline DESC
        """, (trainee_id, trainee_id))
        assignments = cursor.fetchall() or []

        # 3. Quiz scores from applications
        cursor.execute("""
            SELECT a.quiz_scores, a.quiz_results, c.title as course_title
            FROM applications a
            JOIN courses c ON a.course_id = c.id
            WHERE a.user_id = %s
            ORDER BY a.id DESC
        """, (trainee_id,))
        quiz_rows = cursor.fetchall() or []
        quiz_data = []
        for row in quiz_rows:
            qs = row.get("quiz_scores")
            qr = row.get("quiz_results")
            try: qs = json.loads(qs) if isinstance(qs, str) else qs
            except: qs = {}
            try: qr = json.loads(qr) if isinstance(qr, str) else qr
            except: qr = {}
            quiz_data.append({
                "course_title": row.get("course_title"),
                "quiz_scores": qs or {},
                "quiz_results": qr or {}
            })

        # 4. Fetch Profile Skills for Radar Chart
        cursor.execute("""
            SELECT category_id, COUNT(*) as count 
            FROM trainee_skills 
            WHERE trainee_id = %s 
            GROUP BY category_id
        """, (trainee_id,))
        skill_counts = {r['category_id']: r['count'] for r in cursor.fetchall()}
        
        tech_count = skill_counts.get(1, 0)
        soft_count = skill_counts.get(3, 0)
        
        # Latest Quiz Results for cognitive skills (Relational)
        cursor.execute("""
            SELECT question_code, answer_text 
            FROM trainee_quiz_responses 
            WHERE trainee_id = %s
        """, (trainee_id,))
        latest_quiz = {r['question_code']: r['answer_text'] for r in cursor.fetchall()}
        
        analytical = 0 # Calculate based on answers if logic exists
        creative = 0
        strategic = 0

        # 5. Calculate overall completion score
        total_assign = int(assign_stats.get("total_assignments") or 0)
        submitted = int(assign_stats.get("submitted") or 0)
        avg_grade_pct = float(assign_stats.get("avg_grade_pct") or 0)

        # Submission rate (40% weight)
        submission_rate = (submitted / total_assign * 100) if total_assign > 0 else 0
        # Quiz score average (40% weight)
        quiz_pcts = []
        for qd in quiz_data:
            pct_str = qd["quiz_scores"].get("percentage", "0%")
            try: quiz_pcts.append(float(str(pct_str).replace("%", "")))
            except: pass
        quiz_avg = (sum(quiz_pcts) / len(quiz_pcts)) if quiz_pcts else 0
        # Grade avg (20% weight)
        overall = round(submission_rate * 0.4 + quiz_avg * 0.4 + avg_grade_pct * 0.2)

        return {
            "overall_completion": overall,
            "submission_rate": round(submission_rate),
            "quiz_avg": round(quiz_avg),
            "avg_grade_pct": round(avg_grade_pct),
            "assignments": {
                "total": total_assign,
                "submitted": submitted,
                "graded": int(assign_stats.get("graded") or 0),
                "details": assignments
            },
            "quiz_data": quiz_data,
            "skills_radar": [
                min(100, tech_count * 15 + 40), # التقني
                min(100, soft_count * 20 + 30), # الناعم
                min(100, quiz_avg * 0.8 + 10),  # اللغوي (using quiz avg as proxy if no specific lang test)
                min(100, strategic * 0.7 + 30), # القيادي
                min(100, analytical * 0.9 + 10) # التحليلي
            ]
        }
    finally:
        cursor.close()
        db.close()
