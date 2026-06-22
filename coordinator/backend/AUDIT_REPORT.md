# Coordinator Backend — Code Quality Audit Report

**Backend:** `coordinator/backend/` (FastAPI, port 8005)
**Audited:** 12 Python files across 4 packages
**Date:** June 22, 2026

---

## 1. Routers (`routers/`)

### 1.1 `routers/auth.py`

#### Good Patterns
- Arabic validation messages for end-user clarity
- Rate limiting via DB (`check_rate_limit` / `record_login_attempt`)
- Activity logging on every login attempt (success + failure)
- Password is never echoed back in responses
- Session management (`user_sessions` insert, `last_login` update)

#### Issues
| Line | Issue | Severity |
|------|-------|----------|
| 31–40 | Does **not** use the `CoordinatorLoginRequest` Pydantic schema defined in `schemas/auth.py`; requests are typed as `dict` and fields extracted manually | Medium |
| 37 | No validation that `nationalId` is exactly 14 digits (only checks `if not nationalId`) | Low |
| 44 | `cursor.fetchone()` may return `None` — no explicit guard before indexing `[0]` | High |
| 66 | Rate-limit counter decrement (`login_attempts = max(0, ...)`) happens even if the user doesn't exist, which could mask brute-force on non-existent accounts | Low |
| 72 | Password comparison: `row[5]` is hardcoded index — fragile if column order changes in query (line 44 selects 6 columns) | Medium |

#### Recommendations
- Replace `dict` input type with `CoordinatorLoginRequest`
- Add a 14-digit regex validator for `nationalId`
- Use `row` dict-like access (or named tuple) instead of positional indices

---

### 1.2 `routers/permissions.py`

#### Good Patterns
- Optional query-parameter filtering (`status`, `course_id`)
- Status validation against an allowlist (`["approved","rejected"]`)
- Activity logging only on actual status change
- `JOIN` on `users` and `courses` for human-readable output

#### Issues
| Line | Issue | Severity |
|------|-------|----------|
| 30 | No pagination on `GET /api/coordinator/permissions` — could return thousands of rows | High |
| 55 | `allowlist` check uses `not in` but no error if status is same as current (idempotent update with no-op) | Low |
| 59 | `cursor.rowcount == 0` used to detect "not found" — but also triggers if the row count is 0 for any other reason (e.g. concurrent delete) | Medium |

#### Recommendations
- Add `limit`/`offset` query params with a sensible default (e.g. 50)
- Check `current_status != new_status` before logging activity to avoid noise
- Return 409 if update results in no change instead of 404

---

### 1.3 `routers/attendance.py`

#### Good Patterns
- Timezone-aware queries (`CURRENT_DATE` vs `CURDATE`)
- Searchable + paginated logs endpoint
- Photo fallback to placeholder on missing files
- Structured stats endpoint with course breakdown + hourly distribution

#### Issues
| Line | Issue | Severity |
|------|-------|----------|
| 42–50 | Hardcoded literal `'present_today'`, `'absent_today'`, etc. — typos in these strings would produce silent zeroes | Low |
| 60–65 | `/logs` default `page=1`, `page_size=10` — no upper bound on `page_size` (could request 10M rows) | Medium |
| 88 | `/photo/{log_id}` uses `urllib.parse.unquote` on `log_id` before integer cast — if `log_id` is non-numeric, 500 error | High |
| 120 | `/stats` does a `GROUP BY c.name` — if two courses have the same name, counts merge incorrectly | Medium |
| 145 | `/weekly-trend` uses `CURDATE() - INTERVAL 6 DAY` — this is MySQL-specific and would break on other DBs | Low |

#### Recommendations
- Cap `page_size` (max 100) and validate `page >= 1`
- Validate `log_id` is a positive integer before `SELECT` / `unquote`
- Use `c.id` in `GROUP BY` instead of `c.name`
- Consider DB-agnostic date functions or document MySQL dependency

---

## 2. Schemas (`schemas/`)

### 2.1 `schemas/auth.py`

#### Good Patterns
- Clean single-model file

#### Issues
| Line | Issue | Severity |
|------|-------|----------|
| 6–8 | `nationalId` is `str` but no min/max length validator — should enforce 14 digits | Low |

---

### 2.2 `schemas/permission.py`

#### Good Patterns
- `from_attributes = True` (Pydantic v2 `model_config`)
- `PermissionCreate` + `PermissionUpdate` separation

#### Issues
| Line | Issue | Severity |
|------|-------|----------|
| 16 | `PermissionUpdate.status` is `str` with no enum/validator constraint — should restrict to `["approved","rejected"]` | Medium |
| 21 | `Permission.id` is `int` but DB could be `BIGINT` — safe for now but should match DB type | Low |

---

## 3. Core (`core/`)

### 3.1 `core/database.py`

#### Good Patterns
- Connection pooling (`pool_size=10`)
- Environment-based config via `os.getenv`

#### Issues
| Line | Issue | Severity |
|------|-------|----------|
| 24 | `mysql.connector.pooling.MySQLConnectionPool` — **no connection timeout**, pool can stall on network drop | High |
| 30 | `get_db_connection()` returns raw connection — **no context manager**; callers must remember to `.close()`. A missed close leaks connections | High |
| 22 | `database` defaults to `"nta_portal"` — if the `.env` is missing, it silently connects to the wrong DB | Medium |
| 24 | No `pool_reset_session=True` — stale session state can leak between uses | Medium |

#### Recommendations
- Wrap `get_db_connection()` in a context manager (`@contextmanager`) or create a `get_db` dependency
- Add `connection_timeout=5`, `pool_reset_session=True`
- Raise `ValueError` if critical env vars are missing

---

### 3.2 `core/auth.py`

#### Good Patterns
- `create_access_token` uses `jose.jwt.encode` with expiry
- `get_current_user` validates token + user existence in DB
- `require_coordinator` checks role
- Rate-limit helpers query-based, no in-memory state

#### Issues
| Line | Issue | Severity |
|------|-------|----------|
| 13 | `SECRET_KEY` hardcoded default `"your-secret-key"` — if `.env` not loaded, token signing is trivially forgeable | **Critical** |
| 50 | `get_current_user` returns a plain `dict` — no type safety for downstream callers | Medium |
| 70 | `user = cursor.fetchone()` — if `user is None`, `get_current_user` raises `HTTPException(401)`, but `require_coordinator` on line 90 does another fetch that repeats the same query | Low |
| 95 | Hardcoded role string `"coordinator"` — if the DB enum changes, this check silently passes | Low |

#### Recommendations
- **Fail hard** if `SECRET_KEY` is the default — crash at startup
- Return a Pydantic model from `get_current_user` instead of `dict`
- Cache `get_current_user` result or pass user dict to `require_coordinator` to avoid double query

---

### 3.3 `core/logger_util.py`

#### Good Patterns
- Field truncation to column max lengths
- Auto level escalation by `status_code` (>=500 → error, >=400 → warning)
- Dual output (DB + file)

#### Issues
| Line | Issue | Severity |
|------|-------|----------|
| 35 | No retry logic — if DB write fails (connection drop), only file log is written | Medium |
| 39 | `cursor.close()` but **no `connection.close()`** — connection leak | High |
| 30 | File path `os.path.join("logs", activity_file)` — no guard that `logs/` exists; can silently fail | Low |

#### Recommendations
- Add a `try/except` that logs to stderr if DB write fails
- Close or return the connection for the caller to manage
- Ensure `logs/` directory exists at import time

---

## 4. Entry Point (`main.py`)

#### Good Patterns
- CORS allowlist (5 specific origins)
- Structured router imports

#### Issues
| Line | Issue | Severity |
|------|-------|----------|
| 23 | `app.include_router(auth_router)` — no prefix or tag; relies on the router having hardcoded prefixes | Low |
| 25–29 | Static mounts: `"/common"`, `"/admin/header"`, `"/admin/images"`, `"/data"` — these leak the directory structure; `/data` may expose sensitive files | Medium |
| 12–15 | `load_dotenv()` called with no `find_dotenv()` — if `.env` changes location, it silently fails | Medium |

---

## Summary

| Area | Critical | High | Medium | Low |
|------|----------|------|--------|-----|
| Routers | 0 | 2 | 4 | 3 |
| Schemas | 0 | 0 | 1 | 2 |
| Core | 1 | 3 | 3 | 2 |
| Entry Point | 0 | 0 | 2 | 1 |
| **Total** | **1** | **5** | **10** | **8** |

### Top 3 Fixes (by impact)
1. **`core/auth.py:13`** — Hardcoded default JWT `SECRET_KEY` (Critical)
2. **`core/database.py:24`** — No connection timeout + no context manager (High)
3. **`core/logger_util.py:39`** — Connection leak in logger (High)
