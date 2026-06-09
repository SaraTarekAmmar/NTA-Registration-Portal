================================================================================
NTA REGISTRATION PORTAL - ROLES & WORKFLOWS GUIDE
================================================================================
Version: 4.0 | Last Updated: 2026-06-08

1. SYSTEM ADMINISTRATOR (Role: admin)
--------------------------------------------------------------------------------
CONFIGURATION:
   - Open deploy/credentials.txt.
   - Update DB_PASSWORD with your local MySQL root password.

LAUNCH:
   - Double-click deploy/RUN_SYSTEM.bat (Windows)
     OR run: python deploy/run_system.py
   - The system will: update .env files → initialize DB → seed skills/languages
     → start User Portal (8001) → start Admin Portal (8002) → start Super Admin (8003).

ACCESS:
   - User Portal:  http://localhost:8001
   - Admin Portal: http://localhost:8002
   - Super Admin:  http://localhost:8003

NOTE: If you only launch the User Portal via RUN_USER.bat, the Admin Portal
      (port 8002) and Super Admin (port 8003) will NOT respond.
      Always use RUN_SYSTEM.bat for full system functionality.

ACTION FLOW (Click-by-Click):

LOGIN:
1. Navigate to http://localhost:8002.
2. Select account type: "Admin" (مشرف).
3. Enter Admin Email and Password → Click "تسجيل الدخول".
   NOTE: Admins do NOT need a National ID to log in. Password only.
   After 5 failed login attempts from the same IP, the account is blocked
   for 15 minutes (enforced in the database via the login_attempts table).

DASHBOARD NAVIGATION:
3. View summary cards: "إجمالي المتقدمين" (Total), "المسجلين" (Enrolled),
   "المنسحبون" (Dropped).
4. Click any summary card to jump to the filtered User List.
5. Interact with ECharts (Stage Distribution, Gender, etc.) for analytics.

USER MANAGEMENT:
6. Click "عرض قائمة المرشحين والمتدربين" (View Candidate List).
7. In admin-users.html:
   - Click "عرض الملف" (View Profile) next to any trainee.
   - Use Stage Legend (stages 1-7) to filter users by pipeline status.

CANDIDATE REVIEW (admin-profile.html):
8. Data Tabs: Browse "البيانات الشخصية", "المهارات", "المستندات".
9. Document Review: Click "عرض المستند" to open CVs/IDs in a new tab.
10. Stage Review: Click "مراجعة المرحلة" to open the assessment page.
11. Decision Buttons:
    - "قبول للمرحلة التالية" (Accept): Moves trainee to next stage (e.g. 1→2).
    - "رفض المتقدم" (Reject): Prompts for rejection reason, then rejects.

PIPELINE STAGES SUMMARY:
   - Stage 1 (AI Verification): Electronic Sorting (4-phase AI Audit: Identity, CV,
     Education verification, Synthesis report). Dispatched by Super Admin AI Proxy.
   - Stage 2 (Personal Review): Manual review of personal documents by Admin.
   - Stage 3 (Security Review): Manual security clearance check.
   - Stage 4 (Exams): Automated. Invitation email is sent to applicant upon Stage 3
     approval. Admin reviews interactive Radar Charts and narrative AI summaries.
   - Stage 5 (First Interview): Manual review of first interview results.
   - Stage 6 (Second Interview): Manual review of second interview results.
   - Stage 7 (Final Decision): Admin selects Course/Batch. Approval generates
     trainee credentials and moves applicant to the "Trainees List".

   REJECTION AT ANY STAGE = HARD RESET:
   - Rejection email sent to applicant with reason.
   - All DB records deleted (cascades from users table to all child tables).
   - Physical files in data/trainees/{name_nid}/ are erased.
   - Applicant may re-register from scratch.

COURSE CATALOG (admin-courses.html):
12. Add Course:   Click "+ إضافة دورة جديدة" → Fill modal → "حفظ التغييرات".
13. Edit Course:  Click "تعديل" on any card → Modify → "حفظ".
14. Delete Course: Click "حذف" → Confirm.
    NOTE: A course with status "Completed" cannot accept new applications.


2. CONTENT EDITOR (Role: editor)
--------------------------------------------------------------------------------
The Editor is strictly focused on managing the Program Catalog.
Editors share the same login portal as Admins (http://localhost:8002).

ACTION FLOW (Click-by-Click):
1. LOGIN: Navigate to http://localhost:8002 → Enter Editor Email and Password.
2. ACCESS CATALOG: System auto-redirects to "إدارة الدورات" (admin-courses.html).
3. MANAGE PROGRAMS:
   - Create: Click "+ إضافة دورة جديدة". Set Title, Description, Image URL,
     Duration (weeks), Sessions, and Skill Level.
   - Update: Click "تعديل" on existing cards. Changing "Status" or "Visibility"
     (Public/Private) updates availability on the trainee portal immediately.
   - Delete: Click "حذف" to remove outdated programs.
4. RESTRICTIONS:
   - Editors are blocked from admin.html and admin-profile.html (auto-redirect).
   - "Stage Review", "Accept", and "Reject" buttons are hidden for Editor role.
   - Editors cannot view or modify trainee personal data.


3. SUPER ADMINISTRATOR (Role: superadmin)
--------------------------------------------------------------------------------
The Super Admin manages the AI infrastructure and high-level system monitoring.
This is a separate backend-only portal with its own frontend at port 8003.

AI MICROSERVICE PORT REGISTRY:
   - Port 2341: Face Engine (Biometrics & Enrollment)
   - Port 2343: Electronic Sorting (4-Phase AI Admission Audit)
   - Port 2345: Quiz Engine (vLLM Sequential Batch Generation)
   - Port 2346: Course Analytics (Statistical Insights)
   - Port 7834: Requirement Analyzer (Skill Gap Analysis Hub)

ACTION FLOW:
1. LOGIN: Navigate to http://localhost:8003 → Enter Super Admin credentials.
2. AI CONTROL CENTER:
   - Monitor health status of all AI microservices (Face, Sorting, Quiz, Requirement Hub).
   - Re-dispatch failed AI tasks (Electronic Sorting / Quiz Generation).
   - View global system performance stats and audit logs.
3. ATTENDANCE & PERMISSIONS:
   - Manage manual overrides for trainee attendance records.
   - Assign trainees to private/restricted courses via whitelisting.
4. DYNAMIC QUIZ MANAGEMENT:
   - Generate sequential quiz batches using vLLM grounding.
   - Set custom availability durations (in hours) per quiz session.
   - Manage Access Overrides: Search trainees and grant manual deadline extensions
     for expired or active quizzes (stored in quiz_access_overrides table).


4. TRAINEE / APPLICANT
--------------------------------------------------------------------------------
ROLE CLARIFICATION:
   - APPLICANT: The default state for anyone who completes the 11-step registration.
     Applicants are tracked through the 7-stage admission pipeline.
     They appear in the "Candidates List" (قائمة المرشحين) for Admins.
   - TRAINEE: A promoted state. An applicant becomes a "Trainee" only after
     successfully passing all 7 stages of admission (finalized in Stage 7).
     Trainees appear in the "Trainees List" (قائمة المتدربين).

ACTION FLOW (Click-by-Click):

REGISTRATION (Sign Up):
1. Navigate to http://localhost:8001 → Click "إنشاء حساب جديد".
2. A role selection modal appears. Choose "متدرب (Trainee)" or "مدرب (Trainer)".
   This sets the role parameter passed to registration.html.
3. Fill the 11-step form — click "التالي" (Next) at each step.

   RATE LIMITING: Max 3 registration submissions per IP per day.
   A 60-second cooldown is enforced between consecutive submissions.
   CSRF: A CSRF token cookie is set automatically. The form sends it as
   a request header (X-CSRF-Token). Mismatches are rejected with HTTP 403.

   FILE UPLOADS: Files are uploaded to the server in the background
   before final submission (POST /api/trainee/upload). Max 15MB per file.
   Allowed formats: PDF, DOC, DOCX, JPG, JPEG, PNG, ZIP, RAR.

   VALIDATION RULES (Step-by-Step):
   - Step 1  (Personal Data):   Full Name in Arabic & English, Date of Birth
                                (trainee must be aged 16–60), National ID (14-digit
                                Egyptian format, first 7 digits must match DOB &
                                governorate), Gender (validated against NID digit 13).
   - Step 2  (Contact Info):    Primary Email, up to 5 phone numbers
                                (international format: +XXXX or 00XXXX required),
                                Emergency Contact name and phone.
   - Step 3  (Address):         Current address, permanent address, country,
                                governorate, city. Monthly average income.
   - Step 4  (Social Media):    LinkedIn URL is MANDATORY. At least one additional
                                platform (Facebook, Instagram, TikTok, or X) required.
                                An inline Arabic error banner blocks progression if missing.
   - Step 5  (Skills):          Hierarchical skill dropdowns (Category → Subcategory
                                → Skill). Up to 30 technical, 30 computer, 30 soft skills.
   - Step 6  (Languages):       Native language, English proficiency, additional languages.
   - Step 7  (Academic):        University, Degree, Major, GPA, Graduation year.
                                Graduation certificate scan upload.
   - Step 8  (Work History):    Organization, title, start/end dates (end must be after
                                start), responsibilities, reason for leaving.
   - Step 9  (Uploads):         CV/Resume, Employer NOC, Organizational chart.
   - Step 10 (Documents):       Recommendation letters, criminal record certificate,
                                ID scan, identity photos.
   - Step 11 (Cognitive Quiz):  Personality & aptitude assessment. All questions
                                must be answered before submission.

4. Click "إرسال" (Submit).
   - Data is sent as JSON to POST /api/trainee/register.
   - Backend validates CSRF, rate limit, and duplicate email/National ID.
   - On success: uploaded files are moved from data/temp/ to
     data/trainees/{fullNameEn}_{nationalId}/
   - A registration confirmation email is sent asynchronously.
   - Browser redirects to index.html?registered=1 which shows a success
     modal. The user is NOT automatically logged in — they must log in
     separately after registration.

5. LOGIN (Returning Users):
   Navigate to http://localhost:8001.
   Select account type: "متدرب" (Trainee) or "مدرب" (Trainer).
   Enter: National ID + Email + Password → Click "تسجيل الدخول".
   NOTE: All three fields are required for trainees and trainers.
   After 5 failed attempts from the same IP, login is blocked for 15 minutes.
   A JWT token (valid 8 hours) is stored in sessionStorage as 'ntaTrainee'.

BROWSE & APPLY (courses.html — الدورات tab):
5. Browse the course card grid.
   - Click any course card to open the full Course Details modal.
   - Modal shows: image, title, description, duration, level, sessions, status.
   - Click "تقدم الآن" (Apply Now) on any available course.
6. Confirm popup: "هل أنت متأكد؟" → "Yes".
7. State Change: Button immediately changes to "قيد المراجعة" (Under Review)
   and becomes disabled.

MY ENROLLED COURSES:
8. Navigate to courses.html?filter=my to see only enrolled courses.
   - Empty state message: "لم تبدأ أي دورات بعد" when no enrollments exist.

MANAGE PROFILE (profile.html):
9. Click "الملف الشخصي" in the sidebar/header.
10. View personal stats, charts, applied courses.
11. Edit Profile: Click "تعديل الملف الشخصي" button.

    MODAL INTERACTION:
    - Update Name, Secondary Email, Address, Emergency Contact.
    - National ID is READONLY — cannot be changed.
    - Skills Section: Uses category → skill DROPDOWNS (same as registration form).
      Loaded live from /api/skills/tree. Existing skills are pre-selected.
      Add new rows with "+ إضافة مهارة" buttons. Remove rows with × button.
    - Edit Academic History, Professional History, and References.
    - Upload new profile documents using the upload buttons.
    - Click "حفظ التغييرات" (Save Changes) to submit.
      System validates inputs before persisting to database.
    - Page auto-reloads on success to refresh all profile data.

AI ASSISTANT:
12. Use the LLM chatbot for registration help, course details, and profile status.

TRACKING:
13. Monitor course badge status. "قيد المراجعة" → "مقبول" = stage progressed.


5. TRAINER (Role: trainer)
--------------------------------------------------------------------------------
Trainers register and log in through the same User Portal as trainees (port 8001).
They have a dedicated dashboard and different data tables (trainer_profiles, etc.).

REGISTRATION:
1. Navigate to http://localhost:8001 → Click "إنشاء حساب جديد".
2. Select "مدرب (Trainer)" from the role modal.
3. Complete the same 11-step registration form with role=trainer.
   Data is stored in trainer_profiles, trainer_education, trainer_skills, etc.

LOGIN:
4. Navigate to http://localhost:8001.
5. Select "مدرب" account type.
6. Enter National ID + Email + Password → Click "تسجيل الدخول".
7. On success, redirected to trainer-dashboard.html.


6. UNIFIED LOGGING & AUDIT TRAIL
--------------------------------------------------------------------------------
Every action in the system is automatically recorded in the `activity_logs` table.
Log categories:

- PASSIVE: Every page visit (IP, User-Agent, Path, Status Code).
- AUTH:    Every login attempt (Success/Failure + Reason + Role).
- ACTION:  Course applications, profile updates, registration submissions.
- ADMIN:   Approval/Rejection decisions and pipeline stage moves.
- SYSTEM:  Email sends/failures, unhandled exceptions (with traceback).

The Admin Portal middleware also logs Trace ID and response duration_ms
for every API call to enable performance monitoring and debugging.


7. REJECTION-RESET WORKFLOW (Security & Integrity)
--------------------------------------------------------------------------------
When an Admin rejects an applicant in any stage, the system performs a "Hard Reset":
1. NOTIFICATION: A rejection email is sent with the specific reason provided by the Admin.
2. DATABASE PURGE: All records associated with the applicant are deleted from the database
   (cascading from the `users` table to all profile, skill, quiz, and admission tables).
3. FILE CLEANUP: The physical data folder (data/trainees/{fullNameEn}_{nationalId}/)
   is completely erased from the filesystem.
4. RE-REGISTRATION: The applicant is now cleared to register again from scratch
   (e.g., if the rejection was due to incorrect data or poor document quality).


8. SECURITY NOTES
--------------------------------------------------------------------------------
- CSRF:          POST /api/trainee/register requires a matching csrf_token cookie
                 and X-CSRF-Token header. Mismatch → HTTP 403.
- Rate Limiting: Registration: 3 attempts/day per IP + 60s cooldown.
                 Login: 5 failed attempts → 15-minute IP block (DB-backed).
- Password Hash: pbkdf2_sha256 via passlib (pure Python, Windows compatible).
- JWT Expiry:    Access tokens expire after 480 minutes (8 hours).
- XSS:           Address fields are sanitized with html.escape() before DB insert.
- File Security: Only allowed extensions (pdf/doc/docx/jpg/png/zip/rar) and
                 MIME types are accepted. Max 15MB per file.
- Known Gaps:    (A) National ID compared as plain text for login.
                 (B) CORS allows localhost via regex — not strictly locked.
                 (C) No HTTPS enforcement (runs over HTTP locally).
                 (D) RATE_LIMIT_STORE is in-process memory — breaks with
                     multiple uvicorn workers (needs Redis for production scale).

================================================================================
EOF
