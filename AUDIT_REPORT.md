# NTA Registration Portal — Full Codebase Audit

**Date:** 2026-06-22
**Scope:** 5 FastAPI backends (~28k LOC Python), 63 HTML / 48 JS / 24 CSS, shared MySQL.
**Method:** Static code review + live probes against the running servers.

Severity tally (at time of audit): **4 Critical · 3 High · 4 Medium · 3 Low**

**Remediation status:** Critical C1/C3/C4 fixed (C2 needs password rotation + history scrub);
H1/H2/H3 fixed; M1/M2 fixed; M4 was already fixed; M3 deferred by design. Remaining owner
action: **rotate the DB password + JWT secret and scrub git history.**

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

### H1 — `/data/*` served unauthenticated · ✅ Fixed
`data/trainees` etc. held PII (national-ID-named folders, uploaded ID docs) served by a plain
`StaticFiles` mount. **Fix:** `PrivateDataStaticFiles` (admin/user/editor/coordinator) 404s the
sensitive subdirs (`trainees, trainers, admins, admission, uploads, temp, standard_exams, log`)
while leaving public course images. Protected files are already served via authenticated API
routes (e.g. coordinator `/api/coordinator/attendance/photo/...`). Verified: `/data/trainees/`
→ 404.

### H2 — DB connection handling · ✅ Fixed
Added `connection_timeout` (env `DB_CONNECTION_TIMEOUT`, default 10s) to all 5
`core/database.py`. `pool_reset_session=True` was already present. (A `with`-style context
manager remains a nice-to-have but callers already use `try/finally` close patterns.)

### H3 — Unbounded list endpoints · ✅ Fixed
Most list endpoints were already capped (`Query(..., le=200)`). Capped the remaining one
(superadmin `/notifications`, now `le=100`). Coordinator attendance/permissions are bounded by
course; user permissions are scoped to the caller.

---

## 🟡 Medium

- **M1 — Internal error leakage · ✅ Fixed** — added one `HTTPException` handler per backend
  that logs the real 5xx detail server-side and returns `{"detail":"Internal server error"}`
  to clients (overridable with `NTA_DEBUG=1`). Sub-500 messages (validation, 401/403) pass
  through unchanged.
- **M2 — `localhost` origins in prod CORS · ✅ Fixed** — CORS origins are now env-driven
  (`ALLOWED_ORIGINS`) across all 5 backends; production drops localhost by setting that var.
  Removed the user portal's broad `allow_origin_regex` localhost catch-all and tightened
  coordinator's wildcard methods/headers.
- **M3 — Architecture: 5× duplicated `core/` · ⏳ Deferred (by design)** — the backends are
  intentionally standalone (separate venvs, `sys.path.append`, independent deploy). A big-bang
  shared-package refactor is high-risk and contradicts that design. The real duplication risk
  (a fix landing in one backend but not the others) was mitigated by applying every fix in
  this pass consistently across all 5. Revisit only if a shared library is introduced.
- **M4 — Logger connection leak · ✅ Already fixed** — current `logger_util.py` already uses
  `db=None` + `finally` closing both cursor and connection, with a stderr fallback in `except`.

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
