# NTA Registration Portal — Claude Code Instructions

## Project Identity
Egyptian trainee registration portal for the National Training Academy (NTA).  
Live domain: `https://academy.nta.eg`

## Architecture
Four independent FastAPI backends + shared MySQL DB + vanilla JS/HTML frontend.

| Backend     | Entry point               | Default port | Purpose                        |
|-------------|---------------------------|--------------|-------------------------------|
| admin       | `admin/backend/main.py`   | 8002         | Admin CRUD, course mgmt, AI    |
| user        | `user/backend/main.py`    | 7771         | Trainee self-service portal    |
| superadmin  | `superadmin/backend/main.py` | 8003      | System-wide oversight, reports |
| editor      | `editor/`                 | 8004         | Content editor role            |

Frontend pages live alongside their backend (`admin/*.html`, `user/*.html`).  
Static assets served by FastAPI's `StaticFiles`.

## Stack
- **Runtime**: Python 3.10+
- **Framework**: FastAPI + Uvicorn
- **DB**: MySQL via `mysql-connector-python` (pool in each backend's `core/database.py`; root password synced from `deploy/credentials.txt`)
- **Auth**: JWT (python-jose) + bcrypt
- **File uploads**: custom `upload_manager.py` in each backend's `core/`
- **Frontend**: Vanilla HTML/CSS/JS — no bundler, no npm

## Key Directories
```
admin/backend/routers/   # admin API routes
user/backend/routers/    # user API routes
admin/backend/core/      # auth, security, upload_manager, chat_engine
deploy/                  # migration & seed scripts (run manually)
data/                    # static data folders (admins, trainees, uploads…)
uploads/                 # user-uploaded files
common/                  # shared utilities (if present)
```

## How to Run
```bash
# Admin backend
cd admin/backend && uvicorn main:app --reload --port 8002

# User backend
cd user/backend && uvicorn main:app --reload --port 7771

# Superadmin backend
cd superadmin/backend && uvicorn main:app --reload --port 8003

# Editor backend
cd editor/backend && uvicorn main:app --reload --port 8004
```

## Coding Rules (FOLLOW EXACTLY)
- **Python only** on the backend — no TypeScript, no Node
- **No comments** unless the WHY is non-obvious
- Match existing patterns in each router (dependency injection, `get_db`, schemas)
- Use Pydantic models for all request/response bodies
- Never hardcode secrets — read from `.env` via `python-dotenv`
- CORS is configured for the live domain; do not loosen it
- All file upload paths go through `upload_manager.py`
- Security is already hardened — do not re-introduce SQL string concatenation

## Security Constraints
- JWT secret in `.env` — never log or expose it
- Passwords hashed with bcrypt — never store plain text
- All file uploads validated by MIME type in `upload_manager.py`
- Admin and user auth flows are separate — do not mix their tokens

## Common Tasks
- **Add a route**: create in `routers/`, register in `main.py`, add Pydantic schema in `schemas/`
- **DB migration**: write a script in `deploy/`, run it once manually
- **Seed data**: use scripts in `deploy/` (e.g. `seed_fake_data.py`)
- **Debug a user**: use scripts in `deploy/` (e.g. `clear_test_user.py`)

## Claude Code Power Tips (applied here)
- Detailed per-backend rules live in `admin/backend/AGENTS.md` and `user/backend/AGENTS.md` — loaded automatically when working in those dirs
- Keep this file under 200 lines — it loads on every message
- Path-specific rules belong in `.claude/rules/<glob>.md` — only load when Claude touches matching files
- Verbose how-tos belong in `.claude/skills/` — only load when a skill is invoked
- MCP servers to consider adding: `mcp-server-sqlite` (query the DB directly), `github-mcp-server` (read/create issues)

## Git Workflow
- After a unit of work: `git add`, commit (conventional-commit message), then
  `git push origin <current-branch>` so changes reach GitHub. Don't leave work
  committed-but-unpushed.
- Default branch `master`; remote `origin` (`github.com/SaraTarekAmmar/NTA-Registration-Portal`).

## What NOT to Do
- Do not force-push or rewrite published history without asking
- Do not drop tables without confirming
- Do not add npm/node dependencies
- Do not modify `.env` files — use `.env.example` as reference
