# NTA Registration Portal — Full Codebase Audit

**Date:** 2026-06-22
**Scope:** 5 FastAPI backends (~28k LOC Python), 63 HTML / 48 JS / 24 CSS, shared MySQL.
**Method:** Static code review + live probes against the running servers.

Severity tally (at time of audit): **4 Critical · 3 High · 4 Medium · 3 Low**

---

## Status legend
- ✅ **Fixed** in this pass (verified)
- ⏳ **Open** — recommended follow-up

---

## 🔴 Critical

### C1 — `.env` (JWT secret + DB password) served publicly · ✅ Fixed
The root static mount served the entire backend directory. Live probe **before**:
```
GET /backend/.env         → 200   (leaked SECRET_KEY + DB_PASSWORD)
GET /backend/main.py      → 200
GET /backend/core/auth.py → 200
```
**Fix:** added `GuardedStaticFiles` (admin/user/editor/coordinator `main.py`) that 404s any
path under `backend/`, any `.py`, and any dotfile. Live probe **after**: all `→ 404`.
(superadmin already served a dedicated `frontend/` dir — not affected.)

### C2 — Real DB password committed to git · ✅ Partially fixed
`deploy/credentials.txt` contained `DB_PASSWORD=…`; `documentation/credentials.txt` held
testing logins. Both **untracked** (`git rm --cached`) and added to `.gitignore`; local
copies retained.
**⏳ Still required:** the password is in git **history** — rotate the MySQL password and
scrub history (`git filter-repo`) since the repo history still contains it.

### C3 — Backend source served at `/backend/*` · ✅ Fixed
Same root cause and same fix as C1.

### C4 — Weak, shared default `SECRET_KEY` · ✅ Fixed
All backends used `os.getenv("SECRET_KEY", "your-secret-key")` (superadmin:
`"super-secret-key-for-ai-proxy"`). Worse: in admin/user/editor/superadmin the secret was
read at import time **before** `load_dotenv()` ran, so the **default was actually in use**.
**Fix:** each secret module now loads its backend `.env` explicitly, then **fails fast**
(`RuntimeError`) if `SECRET_KEY` is missing or a known default. Verified: servers boot with
the real `.env` secret and login issues valid tokens. (Existing sessions invalidated — users
re-login once.)

---

## 🟠 High

### H1 — `/data/*` served unauthenticated · ⏳ Open
`data/trainees`, `data/admins`, `data/admission`, `uploads` hold PII (national IDs, uploaded
ID documents/photos) and are served by a plain `StaticFiles` mount with no auth.
**Recommend:** replace the `/data` static mount with an authenticated route handler
(`Depends(require_*)`) that streams files after an authorization check.

### H2 — DB connection handling · ⏳ Open
`get_db_connection()` returns a raw pooled connection with no context manager, no
`connection_timeout`, no `pool_reset_session`. A missed `.close()` exhausts the pool; the
logger closes its cursor but not its connection. (Duplicated across all 5 `core/database.py`.)
**Recommend:** a `@contextmanager get_db()` / FastAPI dependency, plus
`connection_timeout=5, pool_reset_session=True`.

### H3 — Unbounded list endpoints · ⏳ Open
Permissions / attendance-logs accept `page_size` with no upper cap → memory/DoS risk.
**Recommend:** clamp `page_size` (≤100) and validate `page ≥ 1`.

---

## 🟡 Medium

- **M1 — Internal error leakage · ⏳** `raise HTTPException(500, detail=str(e))` /
  `f"...{str(e)}"` across many routers returns DB/stack details to clients. Return generic
  messages; log details server-side.
- **M2 — `localhost` origins in prod CORS · ⏳** drop `http://localhost:*` from the
  production allowlists.
- **M3 — Architecture: 5× duplicated `core/` · ⏳** `auth.py`, `database.py`,
  `logger_util.py`, `upload_manager.py`, `security.py` are copy-pasted across backends — the
  C4 bug existed 5×. Extract a shared package.
- **M4 — Logger has no DB-failure fallback and leaks a connection · ⏳**

## 🟢 Low

- **L1 — ⏳** 1 of 23 audited HTML pages missing `lang="ar"`.
- **L2 — ⏳** Fragile positional DB indexing (`row[5]`), hardcoded role strings (see
  `coordinator/backend/AUDIT_REPORT.md` for the per-line coordinator detail).
- **L3 — ⏳** Doc says bcrypt; code uses `pbkdf2_sha256` (which is fine) — update CLAUDE.md.

---

## ✅ Strengths (verified good)
- **SQL injection:** not a concern — every query is parameterized; dynamic table/column names
  are whitelisted (`admin.py` `allowed_columns_map`, `reports.py` `REPORT_TARGETS`,
  regex-validated dates).
- **Password hashing:** `pbkdf2_sha256` via passlib.
- **CORS:** explicit allowlist, no wildcard, scoped methods/headers.
- **Auth hygiene:** DB-backed rate limiting + activity logging on every login; role-separated
  tokens; passwords never echoed.
- **Accessibility:** strong baseline — skip-links, **0 images missing alt**, `lang`/`dir=rtl`,
  `aria-label`s, focus-visible rings, reduced-motion support.

---

## Recommended follow-up order
1. **Rotate** the MySQL password + JWT secret (assume both leaked via history) and scrub
   git history (completes C2).
2. **H1** — put `/data` behind auth.
3. **H2 / H3** — connection context manager + pagination caps.
4. **M1–M4** — error hygiene, CORS cleanup, de-duplicate `core/`.
