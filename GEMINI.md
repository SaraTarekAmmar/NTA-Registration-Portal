# NTA Registration Portal — Gemini CLI / Antigravity CLI Instructions
# NOTE: Gemini CLI is transitioning to Antigravity CLI (Google I/O 2026).
# This file is read by both. Use /memory reload after editing.

## Project Overview
**NTA (National Training Academy) Registration Portal** — Egypt  
A multi-backend trainee management system serving `https://academy.nta.eg`.

## Backend Structure (3 independent FastAPI apps)
| Service     | Path                     | Port | Role                              |
|-------------|--------------------------|------|-----------------------------------|
| User portal | `user/backend/`          | 8000 | Trainees: register, apply, track  |
| Admin panel | `admin/backend/`         | 8001 | Admins: manage trainees & courses |
| Superadmin  | `superadmin/backend/`    | 8002 | System-wide reports & oversight   |
| Editor      | `editor/`                | 8003 | Content editors                   |

## Technology Stack
- **Backend**: Python 3.10+, FastAPI, Uvicorn, aiosqlite, SQLite
- **Auth**: JWT (python-jose), bcrypt password hashing
- **Config**: python-dotenv (`.env` files, never committed)
- **Frontend**: Vanilla HTML + CSS + JavaScript — no frameworks, no bundler
- **Uploads**: Custom validation in `core/upload_manager.py` per backend

## Start Commands
```bash
cd admin/backend     && uvicorn main:app --reload --port 8001
cd user/backend      && uvicorn main:app --reload --port 8000
cd superadmin/backend && uvicorn main:app --reload --port 8002
```

## API Docs (when running)
- Admin:      http://localhost:8001/docs
- User:       http://localhost:8000/docs
- Superadmin: http://localhost:8002/docs

## Development Rules
1. **Python only** — no Node.js, no TypeScript on the backend
2. **Pydantic schemas** for all request/response models (in `schemas/`)
3. **No hardcoded secrets** — use `os.getenv()` or `load_dotenv()`
4. **No SQL string concatenation** — use parameterized queries
5. **No plain-text passwords** — bcrypt only via `core/security.py`
6. **CORS** is locked to the live domain — do not widen it
7. **File uploads** must go through `upload_manager.py` — never write raw to disk
8. **Migrations** go in `deploy/` and are run manually once

## Antigravity-Specific Tips
- Use **Planning mode** for any task that touches multiple backends at once
- Use **Fast mode** for simple single-file edits
- Run `/schedule "run pytest deploy/init_db.py" every day at 09:00` to keep DB healthy
- Place reusable skills in `~/.gemini/antigravity-cli/skills/` for cross-project reuse
- Add `mcp_config.json` to `~/.gemini/config/` to share DB/GitHub MCP across IDE and CLI

## Dangerous Actions — Always Ask First
- Dropping or altering DB tables
- Deleting files from `uploads/`
- Pushing commits or creating PRs
- Changing auth middleware or CORS policy
