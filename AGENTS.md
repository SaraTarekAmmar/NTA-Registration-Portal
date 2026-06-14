# NTA Registration Portal — Agent Instructions
# (Used by: Codex CLI, opencode, and any AGENTS.md-compatible tool.
#  Claude Code uses CLAUDE.md — keep the two consistent when editing.)

## Project Summary
Egyptian trainee registration portal — National Training Academy (NTA).
Live at `https://academy.nta.eg`. Python FastAPI backends + **MySQL** + vanilla JS frontend (RTL, Arabic).

## Architecture at a Glance
```
admin/backend/      → FastAPI (port 8002) — admin operations, AI services, course mgmt
user/backend/       → FastAPI (port 7771) — trainee self-service
superadmin/backend/ → FastAPI (port 8003) — system oversight, reports
editor/backend/     → FastAPI (port 8004) — content editor role
deploy/             → migration & seed scripts (run manually)
uploads/            → user-uploaded files
```
Frontend pages live next to their backend (`admin/*.html`, `editor/*.html`, `user/*.html`)
and are served by each backend's `StaticFiles` mount. **Mounts differ per server**: the
admin server mounts `admin/` at `/` (so `header/header.css` works, `/admin/header/...`
404s); the editor server mounts `editor/` at `/` plus `/admin/header`, `/common`, `/images`.

## Database — MySQL, not SQLite
- MySQL via `mysql-connector-python`; each backend has `core/database.py` with a connection pool.
- Root password is synced from `deploy/credentials.txt` into each backend's `.env` by `deploy/update_credentials.py`. Never commit new secrets; never modify `.env` directly.
- Schema gotchas (enforced by enums):
  - `courses.status` = ENUM('Upcoming','Ongoing','Completed')
  - `courses.skill_level` = ENUM('Beginner','Intermediate','Advanced')
  - `courses.image_url` is NOT NULL (coerce null → "").
- The **editor portal UI** speaks `draft/published/archived` + Arabic skill levels. The
  mapping happens in `editor/backend/routers/courses.py` (`STATUS_TO_DB` / `DB_TO_STATUS` /
  `SKILL_TO_DB`). Keep that translation layer intact when touching editor course routes.

## Running the App
```bash
cd admin/backend  && ./venv/Scripts/python.exe -m uvicorn main:app --reload --port 8002
cd editor/backend && ./venv/Scripts/python.exe -m uvicorn main:app --reload --port 8004
cd user/backend   && ./venv/Scripts/python.exe -m uvicorn main:app --reload --port 7771
```
Each backend has its own `venv/`. `.claude/launch.json` has launch configs for all four.
Note: uvicorn `--reload` (StatReload) is unreliable on this Windows box — after editing
backend Python, restart the server instead of trusting the auto-reload.

## Test Accounts (dev seeds — defined in admin/apply_default_credentials.py)
Login requires email + 14-digit national ID + password.
- Admin:  admin@nta.edu.eg  / 29001011234567 / NTA@Admin2026  → POST /api/admin/auth/login (port 8002)
- Editor: editor@nta.edu.eg / 29505051234567 / NTA@Editor2026 → POST /api/editor/auth/login (port 8004)
- Super:  superadmin@nta.edu.eg / 10000000000000 / NTA@Super2026 (port 8003)
Re-seed all accounts with `deploy/INSTALL_ACCOUNTS.bat`.

## Frontend Conventions
- No bundler, no npm. Vanilla HTML/CSS/JS, RTL layout, Tajawal font.
- Theme: `common/js/theme.js` — dark default, light via `html.light-mode`;
  localStorage key `nta-theme`. Sidebar pages have `#themeToggle` in the sidebar footer
  (injected by `admin/header/header.js` / `editor/js/editor-layout.js`); login pages get a
  floating FAB instead. The FAB is hidden on `body[data-page]` pages.
- Cache busting via query strings (`header.css?v=4`, `theme.css?v=3`) — bump the version
  on ALL referencing pages when editing those files.
- Inline `<script>` blocks are the norm. After editing them, syntax-check:
  extract and run `node --check` (a previous automated a11y pass inserted raw newlines
  into JS strings and mangled `<thead>` tags — that class of breakage has been fixed,
  don't reintroduce it).

## Code Patterns to Follow
- All routes use FastAPI `APIRouter`, registered in `main.py`.
- All request/response bodies use Pydantic models in `schemas/`.
- Parameterized SQL only — never string-concatenate queries.
- Secrets come from `.env` — never hardcode.
- File uploads always go through `core/upload_manager.py` (MIME-validated).
- Passwords: bcrypt/pbkdf2 hashes only — never plain text.
- Admin and editor auth flows are separate — do not mix their tokens
  (`admin_token` vs `editor_token` in localStorage).

## What Agents Should NOT Do
- Never drop or truncate tables without explicit user confirmation
- Never push to git without asking (committing locally is fine)
- Never loosen CORS (configured for the live domain only)
- Never add npm/Node.js dependencies
- Never expose JWT secrets or API keys in logs or responses
- Never modify `.env` files — use `.env.example` as reference

## Adding Features (Pattern)
1. Schema: add Pydantic model to `<backend>/schemas/<file>.py`
2. Route: add endpoint to `<backend>/routers/<file>.py`
3. Register: if new file, add `app.include_router(...)` in `main.py`
4. DB change: write a migration script in `deploy/`, run manually

## Key Files
- `admin/backend/core/auth.py` — JWT auth, login rate limiting
- `admin/backend/core/upload_manager.py` — file upload validation
- `editor/backend/routers/courses.py` — course CRUD incl. status/skill enum mapping
- `editor/js/editor-guard.js` — defines `window.editorAuth` (auth fetch helper)
- `admin/header/header.js` — injects the admin sidebar into `#ntaHeader`
- `common/js/theme.js` — theme system (load synchronously in <head>)
- `deploy/INSTALL_ACCOUNTS.bat` — reseed all accounts

## Current State (June 2026)
- Premium RTL dashboard redesign (crimson palette) landed; solid dark backgrounds
  on all admin pages (no background image).
- Full admin + editor flow test pass completed: login/logout/auth guards, all pages,
  theme toggle, editor course CRUD all verified working (commit 2793ccab).
- Known cosmetic debt: two seeded courses reference images that don't exist on disk
  (`course2.jpg`, `python_ds.jpg`) — cards fall back to placeholders.
