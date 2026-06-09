# NTA Registration Portal — Agent Instructions
# (Used by: opencode, Codex CLI, and any AGENTS.md-compatible tool)

## Project Summary
Egyptian trainee registration portal — National Training Academy (NTA).  
Live at `https://academy.nta.eg`. Python FastAPI backends + SQLite + vanilla JS frontend.

## Architecture at a Glance
```
admin/backend/     → FastAPI (port 8001) — admin operations, AI services, course mgmt
user/backend/      → FastAPI (port 8000) — trainee self-service
superadmin/backend/ → FastAPI (port 8002) — system oversight, reports
editor/            → FastAPI (port 8003) — content editor role
deploy/            → migration & seed scripts (Python, run manually)
data/              → SQLite database
uploads/           → user-uploaded files
```

## Running the App
```bash
# Each backend is independent — run whichever you need
cd admin/backend    && uvicorn main:app --reload --port 8001
cd user/backend     && uvicorn main:app --reload --port 8000
cd superadmin/backend && uvicorn main:app --reload --port 8002
```

## Tech Stack
- Python 3.10+, FastAPI, Uvicorn
- SQLite + aiosqlite
- JWT auth (python-jose) + bcrypt
- Pydantic v2 for schemas
- Vanilla HTML/CSS/JS (no bundler)
- python-dotenv for config

## Code Patterns to Follow
- All routes use FastAPI `APIRouter` and are registered in `main.py`
- DB access via `get_db` dependency — do not access DB outside of router deps
- All request/response bodies use Pydantic models in `schemas/`
- Secrets come from `.env` — never hardcode
- File uploads always go through `core/upload_manager.py`
- Passwords: bcrypt only — never plain text

## What Agents Should NOT Do
- Never drop or truncate tables without explicit user confirmation
- Never commit or push to git without asking
- Never loosen CORS (configured for live domain only)
- Never add npm/Node.js dependencies
- Never expose JWT secrets or API keys in logs or responses

## Adding Features (Pattern)
1. Schema: add Pydantic model to `<backend>/schemas/<file>.py`
2. Route: add endpoint to `<backend>/routers/<file>.py`
3. Register: if new file, add `app.include_router(...)` in `main.py`
4. DB change: write a migration script in `deploy/`, run manually

## Key Files
- `admin/backend/core/auth.py` — JWT auth helpers
- `admin/backend/core/security.py` — password hashing
- `admin/backend/core/upload_manager.py` — file upload validation
- `admin/backend/routers/admin.py` — main admin routes
- `user/backend/core/auth.py` — user JWT auth
- `deploy/init_db.py` — DB schema initializer
