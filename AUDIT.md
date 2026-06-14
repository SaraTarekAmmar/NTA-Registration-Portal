# NTA Registration Portal — Full Code Audit Report

**Date:** 2026-06-15  
**Auditor:** Manus AI  
**Scope:** All four portals — User (`user/`), Admin (`admin/`), Editor (`editor/`), SuperAdmin (`superadmin/`)  
**Method:** Static code analysis — all pages, routes, JS flows, backend routers, auth guards, CORS config, static mounts, and deploy scripts.

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 5 |
| 🟠 Configuration / Port Mismatch | 3 |
| 🟡 Security / Hardening | 4 |
| 🔵 Missing Assets | 1 |
| **Total** | **13** |

---

## 🔴 Critical Bugs

### BUG-01 — `forgot-password.html` calls a non-existent backend endpoint

**File:** `user/forgot-password.html` (line 96)  
**Impact:** The entire password-recovery flow is broken. Submitting the form always returns a network error.

**Root cause:** The page calls `POST /api/auth/recover`, but this route is not registered in any backend. The user backend's `core/auth.py` only exposes `POST /api/auth/login`.

**Fix required:** Implement `POST /api/auth/recover` in `user/backend/core/auth.py` that:
1. Accepts `{ email }`.
2. Looks up the user by email.
3. Generates a signed reset token (e.g. a short-lived JWT or a UUID stored in DB).
4. Sends a password-reset email via the existing `mail_service.send_email_background`.
5. Returns a generic success message regardless of whether the email exists (to prevent user enumeration).

---

### BUG-02 — `user/exam.html` uses wrong relative path for theme assets

**File:** `user/exam.html` (lines 4–5)  
**Impact:** Theme JS and CSS fail to load. Page renders without dark-mode support and with broken styles.

```html
<!-- BROKEN (relative path goes one level up — outside the served root) -->
<script src="../common/js/theme.js"></script>
<link rel="stylesheet" href="../common/css/theme.css" />

<!-- CORRECT (absolute path served by the user backend) -->
<script src="/common/js/theme.js"></script>
<link rel="stylesheet" href="/common/css/theme.css" />
```

---

### BUG-03 — `user/trainer-dashboard.html` uses wrong relative path for theme assets

**File:** `user/trainer-dashboard.html` (lines 4–5)  
**Impact:** Same as BUG-02 — theme assets fail to load for the trainer dashboard.

```html
<!-- BROKEN -->
<script src="../common/js/theme.js"></script>
<link rel="stylesheet" href="../common/css/theme.css" />

<!-- CORRECT -->
<script src="/common/js/theme.js"></script>
<link rel="stylesheet" href="/common/css/theme.css" />
```

---

### BUG-04 — `user/stage 4 exams.html` uses wrong relative path for theme assets

**File:** `user/stage 4 exams.html` (lines 4–5)  
**Impact:** Same as BUG-02 — theme assets fail to load for the Stage 4 exam page.

```html
<!-- BROKEN -->
<script src="../common/js/theme.js"></script>
<link rel="stylesheet" href="../common/css/theme.css" />

<!-- CORRECT -->
<script src="/common/js/theme.js"></script>
<link rel="stylesheet" href="/common/css/theme.css" />
```

---

### BUG-05 — `superadmin/backend/main.py` — `/status` health-check route is unreachable

**File:** `superadmin/backend/main.py` (lines ~90–97)  
**Impact:** `GET /status` always returns the static `index.html` instead of the JSON health response. Any uptime monitor or load-balancer health check against `/status` will receive HTML (200 OK but wrong content-type), causing false positives.

**Root cause:** The `@app.get("/status")` route is defined **after** `app.mount("/", StaticFiles(...))`. FastAPI processes mounts before routes when the mount path is `/`, so the static mount intercepts the request first.

**Fix required:** Move the `/status` route definition to **before** the static mount, or change the health-check path to `/api/status`.

---

## 🟠 Configuration / Port Mismatches

### CFG-01 — Admin backend default port disagrees across all three documentation files

| Source | Admin port | User port | SuperAdmin port | Editor port |
|--------|-----------|-----------|-----------------|-------------|
| `AGENTS.md` | 8001 | 8000 | 8002 | 8003 |
| `CLAUDE.md` | 8001 | 8000 | 8002 | 8003 |
| `admin/backend/main.py` (`PORT` default) | **8002** | 8001 | 8003 | 8003 |
| `deploy/run_system.py` (actual launch) | **8002** | **7771** | **8003** | *(not launched)* |

`run_system.py` is the ground truth. Documentation in `AGENTS.md` and `CLAUDE.md` is out of date and will mislead developers.

**Fix required:** Update `AGENTS.md` and `CLAUDE.md` port table to match `run_system.py`:
- User Portal → `7771`
- Admin Portal → `8002`
- SuperAdmin → `8003`
- Editor → `8003` *(see CFG-02)*

---

### CFG-02 — SuperAdmin and Editor backends share the same default port (8003)

**Files:** `superadmin/backend/main.py` (env var `APP_PORT`, default `8003`), `editor/backend/main.py` (env var `PORT`, default `8003`)  
**Impact:** Running both portals simultaneously on a fresh install without explicit env overrides causes a port collision — the second server to start will crash with `Address already in use`.

**Fix required:** Change the editor backend default port to `8004` (or any unused port), and update `AGENTS.md`/`CLAUDE.md` accordingly.

---

### CFG-03 — User backend default port (8001) differs from `run_system.py` launch port (7771)

**Files:** `user/backend/main.py` (env var `PORT`, default `8001`), `deploy/run_system.py` (launches user on `7771`)  
**Impact:** Running `python user/backend/main.py` directly starts on port `8001`, but `run_system.py` uses `7771`. Developers running the user portal standalone will be on the wrong port and CORS will reject requests from the admin portal.

**Fix required:** Align the default port — either change `main.py` default to `7771`, or update `run_system.py` to use `8001` consistently.

---

## 🟡 Security / Hardening Issues

### SEC-01 — `admin/js/admin-guard.js` blocks superadmins from the admin portal

**File:** `admin/js/admin-guard.js` (line 14)  
**Impact:** A user with `role === "superadmin"` is redirected to `admin-login.html` when trying to access any admin page, even though superadmins should have full access.

```js
// CURRENT — only allows "admin"
if (!payload || payload.role !== "admin") { ... redirect ... }

// SUGGESTED — allow both admin and superadmin
if (!payload || !["admin", "superadmin"].includes(payload.role)) { ... redirect ... }
```

---

### SEC-02 — Bare `except: pass` in admin backend middleware silently swallows JWT errors

**File:** `admin/backend/main.py` (line ~47) and `superadmin/backend/main.py` (line ~47)

```python
# CURRENT — bare except hides all errors including programming mistakes
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    sid = payload.get("sid")
    role = payload.get("role")
except: pass

# BETTER — catch only expected JWT errors
except Exception:
    pass
```

While the functional impact is low (the middleware continues and the route handler re-validates the token), bare `except` is a Python anti-pattern that can hide unexpected errors during development.

---

### SEC-03 — In-process rate-limit store does not survive multi-worker deployments

**File:** `user/backend/routers/trainees.py` (line ~55, `RATE_LIMIT_STORE`)  
**Impact:** With `uvicorn --workers N`, each worker maintains its own `RATE_LIMIT_STORE` dict. The effective per-IP registration limit becomes `3 × N` instead of `3`. This is already documented as "BUG 22" in the code comments.

**Fix required (production):** Replace the in-process dict with a shared store — either a Redis counter (`redis-py`) or a DB-backed `rate_limit_log` table.

---

### SEC-04 — `user/backend/main.py` CORS does not include the editor origin

**File:** `user/backend/main.py` (lines 22–27)

```python
allow_origins=[
    "https://academy.nta.eg",
    "https://reg.nta.eg",
    "http://localhost:8001",
    "http://localhost:8002"
    # Missing: "http://localhost:8003" (editor portal)
],
```

If the editor portal ever needs to call the user backend directly (e.g. to preview trainee data), requests from `localhost:8003` will be blocked by CORS.

---

## 🔵 Missing Assets

### ASSET-01 — `common/js/icons.js` is missing from the root `common/` folder

**Impact:** The editor backend mounts the root `common/` folder at `/common`. Any editor page that calls `NTAIcons(...)` will get a JavaScript error because `icons.js` is not present in `common/js/`.

The file exists in two portal-local copies:
- `user/common/js/icons.js` ✅
- `admin/common/js/icons.js` ✅
- `common/js/icons.js` ❌ **missing**

**Fix required:** Copy `user/common/js/icons.js` → `common/js/icons.js` (the files appear identical).

---

## Architecture Notes (No Action Required)

- **All four backends** correctly use parameterised SQL queries (`cursor.execute(query, (param,))`) throughout — no SQL injection vulnerabilities found.
- **JWT validation** is consistent across all portals (HS256, `python-jose`).
- **CSRF double-submit cookie** is correctly implemented for the public registration endpoint.
- **Password hashing** uses `pbkdf2_sha256` via `passlib` — appropriate for the deployment environment.
- **Static file serving** architecture (each portal serves its own HTML alongside its backend) is sound and consistent.
- **Activity logging** middleware is present and well-structured in all four backends.
- **Upload manager** correctly validates file types and sizes before saving.

---

*End of audit report.*
