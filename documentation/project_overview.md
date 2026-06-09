# NTA Registration Portal — Complete Project Overview

## 1. What Is This?
The **National Training Academy (NTA) Registration Portal** is a secure, bilingual (Arabic/English, RTL) multi-tier web platform for managing trainee/trainer registration, admission pipelines, course management, and AI-powered evaluation. It is composed of **three independent deployable services** sharing a single MySQL database.

---

## 2. Architecture & Services

| Service | Directory | Default Port | Purpose |
|---|---|---|---|
| **User Portal** | `/user` | `7771` (docs) / `8001` (bat) | Trainee/Trainer registration, login, courses, profile, AI chat |
| **Admin Portal** | `/admin` | `8002` | Admin/Editor dashboard, trainee review, course management |
| **Super Admin AI Proxy** | `/superadmin` | `8003` | AI microservice orchestration, attendance, quiz management |

All three share the **same MySQL database** (`nta_portal`) and the **same JWT secret key**.

### AI Microservice Port Registry (managed by SuperAdmin)
| Port | Service |
|---|---|
| 2341 | Face Engine (Biometrics) |
| 2343 | Electronic Sorting (4-phase AI audit) |
| 2345 | Quiz Engine (vLLM) |
| 2346 | Course Analytics |
| 7834 | Requirement Analyzer (Skill Gap) |

---

## 3. Tech Stack

- **Backend**: Python 3.10+ · FastAPI · uvicorn · mysql-connector-python · python-jose (JWT) · passlib (pbkdf2_sha256) · pydantic
- **Frontend**: Plain HTML + Vanilla CSS + Vanilla JS (no React/Vue). Tajawal Arabic font. RTL layout.
- **Database**: MySQL 8.0+, pool size 20, `utf8mb4` charset
- **AI**: Google Gemini API (Chatbot + CV Matching) — key in `.env`
- **Email**: SMTP (configurable) with fallback to local HTML log files in `backend/logs/sent_emails/`
- **File Storage**: Local filesystem under `/data/` directory (shared by all portals)

---

## 4. Directory Structure

```
NTA-Regestration-Portal - Final/
├── user/                          ← User Portal (Trainee/Trainer)
│   ├── backend/
│   │   ├── main.py                ← FastAPI app (port 7771/8001)
│   │   ├── .env                   ← DB, JWT, Gemini config
│   │   ├── core/
│   │   │   ├── auth.py            ← JWT login, password hashing, rate limiting
│   │   │   ├── database.py        ← MySQL pool connection
│   │   │   ├── upload_manager.py  ← File save/move logic (15MB limit)
│   │   │   ├── mail_service.py    ← SMTP email + fallback to HTML log
│   │   │   ├── logger_util.py     ← Unified activity_logs table writer
│   │   │   ├── chat_engine.py     ← Gemini chatbot singleton
│   │   │   └── ai_cv_matcher.py   ← Triggers CV-course AI matching
│   │   ├── routers/
│   │   │   ├── trainees.py        ← /api/trainee/* (register, profile, apply, update)
│   │   │   ├── courses.py         ← /api/courses/*
│   │   │   ├── trainer.py         ← /api/trainer/*
│   │   │   ├── skills.py          ← /api/skills/tree
│   │   │   ├── lookups.py         ← /api/lookups/* (countries, languages, etc.)
│   │   │   ├── exams.py           ← /api/exams/*
│   │   │   ├── assignments.py     ← /api/assignments/*
│   │   │   ├── chat.py            ← /api/chat/*
│   │   │   ├── ai_proxy.py        ← Proxy to SuperAdmin AI services
│   │   │   ├── ai_services.py     ← Direct AI calls
│   │   │   ├── permissions.py     ← /api/permissions/*
│   │   │   └── admin.py           ← Admin actions accessible from user backend
│   │   └── schemas/
│   │       ├── trainee.py         ← TraineeRegistration, TraineeUpdate, CourseApplication
│   │       └── auth.py            ← LoginRequest, TokenResponse
│   ├── index.html                 ← Login page (trainee/trainer)
│   ├── registration.html          ← 11-step registration form (~106KB)
│   ├── registration.js            ← Registration logic (~206KB)
│   ├── registration.css
│   ├── profile.html               ← Trainee profile view/edit
│   ├── courses.html               ← Course catalog + application
│   ├── course-details.html/js/css ← Course detail modal
│   ├── exam.html                  ← Exam/quiz UI
│   ├── trainer-dashboard.html
│   └── styles.css / trainee.css
│
├── admin/
│   ├── backend/
│   │   ├── main.py                ← FastAPI app (port 8002)
│   │   ├── routers/
│   │   │   ├── admin.py           ← /api/admin/* (trainee list, stage moves, reject)
│   │   │   ├── courses.py         ← /api/courses/* (admin CRUD)
│   │   │   ├── exams.py           ← /api/exams/*
│   │   │   ├── class_matrix.py    ← Class matrix management
│   │   │   ├── permissions.py     ← /api/permissions/*
│   │   │   ├── chat.py
│   │   │   └── ai_services.py
│   │   └── schemas/
│   ├── admin.html                 ← Admin dashboard (ECharts analytics)
│   ├── admin-users.html           ← Candidates + Trainees list
│   ├── admin-profile.html         ← Individual trainee review
│   ├── admin-courses.html         ← Course management
│   ├── admin-trainees.html
│   ├── admin-attendance.html
│   ├── admin-permissions.html
│   ├── recommendations.html
│   └── admin-stage-review.html
│
├── superadmin/
│   └── backend/                   ← AI Proxy backend (port 8003)
│
├── data/                          ← All uploaded files (shared volume)
│   ├── trainees/{name_nid}/       ← Per-trainee documents
│   ├── trainers/{name_nid}/
│   ├── courses/images/
│   ├── admins/
│   ├── temp/                      ← Pre-registration uploads
│   └── admission/
│
├── common/
│   ├── css/theme.css              ← Global theme variables (dark/light mode)
│   └── js/theme.js                ← Theme toggle
│
├── documentation/
│   ├── Project_Documentation.txt  ← Master technical doc
│   ├── workflows.md               ← Role-by-role click-through guide
│   ├── full_schema.sql            ← Complete DB schema (60KB)
│   ├── credentials.txt            ← Test account credentials
│   ├── registration_field_requirements.txt
│   ├── file_dictionary.json       ← All form fields mapped
│   └── NTA_System_Master_Walkthrough_Arabic.txt
│
└── deploy/
    └── RUN_SYSTEM.bat             ← One-click launcher for all 3 services
```

---

## 5. Database Overview (MySQL: `nta_portal`)

### Key Tables
| Table | Purpose |
|---|---|
| `users` | Core identity: id, full_name_ar, full_name_en, email, national_id, role, dob, gender, marital_status, profile_photo, password_hash |
| `trainee_profiles` | Extended trainee data: all personal, document paths, JSON blobs |
| `trainer_profiles` | Same structure for trainers |
| `trainee_education` | Academic history (child table) |
| `trainee_experience` | Professional history |
| `trainee_skills` | Skills (category_id: 1=technical, 2=computer, 3=soft) |
| `trainee_references` | Professional references |
| `trainee_quiz_responses` | Quiz answers (question_code → answer_text) |
| `trainee_awards` | Prizes/achievements |
| `trainee_standardized_tests` | Standardized test scores |
| `trainee_community` | Conferences/volunteer work |
| `trainee_social_media` | Social media profiles |
| `trainee_languages` | Additional languages |
| `courses` | Course catalog |
| `applications` | Trainee ↔ course applications (status: waiting, accepted, rejected) |
| `pipeline_state` | Admission pipeline: current_stage_id (1–7), status |
| `activity_logs` | Unified audit trail (all events) |
| `login_attempts` | Login rate limiting (persistent, 5 fails → 15 min block) |
| `quiz_access_overrides` | Manual quiz deadline extensions |

---

## 6. Authentication & Security

- **JWT** via `python-jose` (HS256), 480-minute expiry (stored in `sessionStorage` on frontend as `ntaTrainee`)
- **Password Hashing**: `pbkdf2_sha256` via `passlib`
- **Login**: Email + Password + National ID (trainees/trainers); Email + Password only (admins)
- **CSRF Protection**: Cookie `csrf_token` must match `X-CSRF-Token` header on `POST /api/trainee/register`
- **Rate Limiting (Registration)**: 3 attempts/day per IP, 60-second cooldown between attempts
- **Rate Limiting (Login)**: 5 failed attempts → 15-minute IP block (DB-backed)
- **XSS Prevention**: `html.escape()` on address fields before DB insert

---

## 7. Registration Flow (11-Step Form)

The multi-step form (`registration.html` + `registration.js`) collects:

| Step | Content |
|---|---|
| 1 | Personal: Full name (AR/EN), DOB, National ID, Gender, Marital Status |
| 2 | Contact: Email, Phone(s), Social Media (LinkedIn required + 1 other) |
| 3 | Skills & Languages: Hierarchical dropdowns, English proficiency |
| 4 | Academic History: University, Degree, Major, GPA, Grad Year |
| 5 | Work History: Organization, Title, Start/End dates, Responsibilities |
| 6 | Uploads: CV, National ID scan (files upload to `/api/trainee/upload` before submit) |
| 7–9 | Extra: Awards, Conferences, Volunteer work, Standardized tests |
| 10 | Documents: Recommendation letters, criminal record, etc. |
| 11 | Cognitive Quiz: Personality & aptitude assessment |

On **Submit**:
1. `POST /api/trainee/register` with all data as JSON
2. Backend validates CSRF, rate limit, duplicate email/NID
3. Inserts into `users` → `trainee_profiles` → child tables (education, skills, etc.)
4. Files moved from `data/temp/` → `data/trainees/{name_nid}/`
5. Sends registration confirmation email (async)
6. Returns `{trainee_id}` → frontend redirects to `index.html?registered=1`

---

## 8. Admin Admission Pipeline (7 Stages)

| Stage | Name | Type |
|---|---|---|
| 1 | AI Electronic Sorting | Automated (4-phase: Identity, CV, Edu, Synthesis) |
| 2 | Personal Review | Manual |
| 3 | Security Review | Manual |
| 4 | Exams | Automated (email invite sent on Stage 3 approval) |
| 5 | First Interview | Manual |
| 6 | Second Interview | Manual |
| 7 | Final Decision | Manual (course/batch assignment → credentials generated) |

**Rejection = Hard Reset**: Deletes all DB records + physical files for that applicant.

---

## 9. File Upload System

- Endpoint: `POST /api/trainee/upload?folder={category}`
- Files stored initially in `data/temp/`
- After registration, moved to `data/trainees/{fullNameEn}_{nationalId}/`
- Max size: **15MB** per file
- Allowed: `.pdf, .doc, .docx, .jpg, .jpeg, .png, .zip, .rar`
- Paths stored as relative strings in DB (e.g., `data/trainees/Omar_Nour_123/cv.pdf`)

---

## 10. Key Known Issues / Notes

| # | Issue |
|---|---|
| BUG 22 | `RATE_LIMIT_STORE` is in-process memory → breaks with `--workers > 1` (needs Redis for production) |
| Security Gap A | Trainee login uses National ID (plain text compared) as secondary factor |
| Security Gap B | CORS currently allows origins via regex matching (not strictly locked down) |
| Security Gap C | HTTP only (no HTTPS enforcement) |

---

## 11. Startup

```bat
# One-click full system start (Windows):
deploy\RUN_SYSTEM.bat

# Manual start for user portal only:
user\RUN_USER.bat     → http://localhost:8001

# Manual start for admin portal only:
admin\RUN_ADMIN.bat   → http://localhost:8002
```

---

## 12. Environment Variables (user/backend/.env)

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=<password>
DB_NAME=nta_portal
SECRET_KEY=<hex_key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
GEMINI_API_KEY=<key>
AI_SERVER_HOST=127.0.0.1
```
