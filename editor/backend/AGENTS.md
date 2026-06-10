# Editor Backend — AGENTS.md

Standalone FastAPI application serving the NTA Editor Portal.
Runs on **port 8003** independently of the admin backend (port 8002).

## Startup

```bash
cd editor/backend
cp .env.example .env   # fill in SECRET_KEY and DB credentials
pip install -r requirements.txt
python main.py          # starts on http://0.0.0.0:8003
```

## Architecture

```
editor/backend/
├── main.py              — FastAPI app, middleware, static file serving
├── core/
│   ├── auth.py          — JWT auth (editor-only), require_editor dependency
│   ├── database.py      — MySQL pool "editor_pool" (10 connections)
│   ├── upload_manager.py — file upload, writes to shared data/ directory
│   └── logger_util.py   — activity_logs table + JSON log files
├── routers/
│   ├── auth.py          — POST /api/editor/auth/login
│   ├── courses.py       — /api/courses CRUD + /api/courses/{id}/sessions alias
│   ├── materials.py     — POST /api/materials (upload), GET /api/materials/{course_id}
│   ├── sessions.py      — /api/sessions CRUD
│   └── exams.py         — /api/exams CRUD (filterable by ?course_id=)
└── schemas/
    ├── auth.py          — LoginRequest, TokenResponse
    └── course.py        — CourseBase, Course
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/editor/auth/login | — | Editor login → JWT |
| GET | /api/courses | editor | List all courses |
| GET | /api/courses/{id} | editor | Get single course |
| POST | /api/courses | editor | Create course |
| PUT | /api/courses/{id} | editor | Update course |
| DELETE | /api/courses/{id} | editor | Delete course |
| GET | /api/courses/{id}/sessions | editor | Sessions for a course |
| POST | /api/materials | editor | Upload material file |
| GET | /api/materials/{course_id} | editor | List course materials |
| GET | /api/sessions?course_id= | editor | List sessions |
| POST | /api/sessions | editor | Create session |
| PUT | /api/sessions/{id} | editor | Update session |
| DELETE | /api/sessions/{id} | editor | Delete session |
| GET | /api/exams?course_id= | editor | List exams |
| GET | /api/exams/{subject} | editor | Get exam with questions |
| POST | /api/exams | editor | Create exam |
| PUT | /api/exams/{subject} | editor | Update exam |
| DELETE | /api/exams/{subject} | editor | Delete exam |

## Auth

- Token key: `editor_token` (sessionStorage)
- JWT signed with `SECRET_KEY`, 8-hour expiry
- All routes except `/api/editor/auth/login` require `Authorization: Bearer <token>`
- Only users with `role = 'editor'` in the `users` table are accepted

## Database

Shares the same MySQL `nta_portal` database as the admin backend.
Uses a separate connection pool (`editor_pool`, 10 connections) to avoid exhausting the admin pool.

## Uploads

Files go to the shared `data/` directory at the project root.
Path from this backend: `editor/backend/core/upload_manager.py` → `PROJECT_ROOT / "data"`.
Max file size: 20 MB. Allowed: pdf, doc, docx, jpg, jpeg, png, zip, rar.

## Environment Variables

See `.env.example` for all required variables:
- `SECRET_KEY` — must match admin backend if tokens need to be cross-verified
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `PORT` (default 8003)
