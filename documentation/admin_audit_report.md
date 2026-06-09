# NTA Admin Portal — Fresh Code & Logic Audit Report

**Generated:** 2026-06-08  
**Audited Scope:** `admin/` — all backend Python routers, core modules, schemas, and supporting scripts  
**Auditor:** Antigravity (AI Code Review) — Full fresh read of every file

---

## Executive Summary

This is a **clean-slate** audit based on a direct line-by-line read of the current codebase.  
The previous round of fixes resolved a number of bugs (BUG 10–19). This report identifies **17 issues**
that remain open or are newly discovered. Issues are classified by severity:

| Severity | Count |
|----------|-------|
| 🔴 Critical (security / data loss) | 5 |
| 🟠 High (silent failure / wrong behaviour) | 6 |
| 🟡 Medium (correctness risk) | 4 |
| 🔵 Low (code quality / maintenance) | 2 |

---

## 🔴 Critical Issues

---

### BUG-C1 · `decode_access_token` Is Imported But Does Not Exist in `core/auth.py`

**Files:**  
- `admin/backend/routers/exams.py` — Lines 58, 90  

```python
from core.auth import decode_access_token   # Line 58 — dynamic import inside function body
payload = decode_access_token(token)        # Line 60
```

**Current state (confirmed):** `core/auth.py` exposes only `create_access_token`, `get_current_user`,
`get_admin_user`, `get_staff_user`, `verify_password`, `get_password_hash`, `check_rate_limit`,
`record_login_attempt`. There is **no `decode_access_token`** anywhere in the file.

Both `GET /api/exams/{subject}` (line 58) and `POST /api/exams/{subject}/submit` (line 90) do
`from core.auth import decode_access_token` inside the function body. This raises an `ImportError`
every time either endpoint is called. The exam portal is completely broken at the server level.

**Fix — add to `core/auth.py`:**
```python
def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
```

---

### BUG-C2 · `SECRET_KEY` Defaults to a Weak Literal String

**File:** `admin/backend/core/auth.py` — Line 22

```python
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
```

**Problem:** If `SECRET_KEY` is missing from `.env` (e.g., first deployment, missing env injection),
the application silently falls back to the public string `"your-secret-key"`. Any attacker can forge
a valid JWT for any role (admin, editor, trainee) by signing with this well-known default.  
There is no startup assertion, warning, or crash to alert operators.

**Fix:**
```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set. Cannot start server securely.")
```

---

### BUG-C3 · `.env` Contains Live Credentials Committed to the Repository

**File:** `admin/backend/.env`  
**Lines:** `DB_PASSWORD`, `SENDGRID_API_KEY`

```env
DB_PASSWORD=OmarNour@Work161996
SENDGRID_API_KEY=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
```

**Problem:** Live MySQL root password and real SendGrid API key stored on disk in plain text.
If this directory is ever version-controlled, shared, or copied, both credentials are fully exposed.
The SendGrid key allows unlimited email sending billed to the account. The DB password grants
root access to the entire `nta_portal` database.

**Fix:**
1. Add `.env` to `.gitignore` immediately.
2. Rotate the DB password and the SendGrid API key.
3. Use a secrets manager or environment injection for production.

---

### BUG-C4 · `apply_default_credentials.py` Has Hardcoded Production Password as Fallback

**File:** `admin/apply_default_credentials.py` — Line ~18

```python
db_pass = os.getenv('DB_PASSWORD', 'OmarNour@Work161996')  # hardcoded DB password fallback
```

Also contains hardcoded plaintext staff passwords (`NTA@Admin2026`, `NTA@Editor2026`, etc.).  
Even if `.env` is secured, this file independently leaks the DB password. Anyone with read
access to this script can log in to every role in the system.

**Fix:**
- Remove the hardcoded `db_pass` fallback — fail loudly if `.env` is missing.
- Move default passwords to environment variables, or generate them randomly on first run.

---

### BUG-C5 · Rejection Audit Trail Is Silently Destroyed by Its Own Cascade

**File:** `admin/backend/routers/admin.py` — Lines 326–358

```python
# 1. Insert stage_reviews record ...
cursor.execute("INSERT INTO stage_reviews (...) VALUES (...)", (...))

# 4. Delete the user — CASCADE removes pipeline_state, applications, etc.
#    NOTE: stage_reviews.trainee_id FK is ON DELETE CASCADE ...
#    which means this INSERT row will ALSO be deleted here.
cursor.execute("DELETE FROM users WHERE id = %s", (review.trainee_id,))
```

**Problem:** The code itself documents this as a known bug in a comment (lines 351–357), but
**no fix has been applied**. The `stage_reviews` row is inserted for audit purposes, then
immediately deleted by `ON DELETE CASCADE` when the user row is deleted. The entire rejection
audit trail is silently destroyed on every rejection.

The migration needed is documented in the comment but has not been run:
```sql
ALTER TABLE stage_reviews DROP FOREIGN KEY stage_reviews_ibfk_1;
ALTER TABLE stage_reviews MODIFY trainee_id INT NULL;
ALTER TABLE stage_reviews ADD CONSTRAINT stage_reviews_ibfk_1
  FOREIGN KEY (trainee_id) REFERENCES users(id) ON DELETE SET NULL;
```

**Fix:** Run the migration above in MySQL. This cannot be fixed in Python alone.

---

## 🟠 High Issues

---

### BUG-H1 · `TraineeSummary` Schema Has Non-Optional Required Fields That Fail on NULL Pipeline Records

**File:** `admin/backend/schemas/admin.py` — Lines 5–12

```python
class TraineeSummary(BaseModel):
    id: int
    name: str
    email: str
    stage: int      # required, no default
    status: str     # required, no default
    gender: str     # required, no default
    dob: date       # required, no default
```

**Problem:** The `GET /api/admin/trainees` endpoint uses a `LEFT JOIN` on `pipeline_state`.
For newly registered applicants without a pipeline record, `stage` (mapped from
`ps.current_stage_id`) and `status` (from `ps.status`) will be `NULL`. Similarly, `gender`
and `dob` can be empty. When any of these are `NULL`, Pydantic raises a `ValidationError`
and the entire `/trainees` list endpoint returns a `500` error — blocking the whole admin
dashboard.

**Fix:**
```python
stage:  Optional[int]  = 1
status: Optional[str]  = "pending"
gender: Optional[str]  = "unknown"
dob:    Optional[date] = None
```

---

### BUG-H2 · Exam Re-Submission Is Allowed Without Restriction

**File:** `admin/backend/routers/exams.py` — Lines 112–118

```python
cursor.execute("""
    INSERT INTO trainee_exam_submissions (trainee_id, subject, ...)
    VALUES (%s, %s, ...)
""", (trainee_id, subject, ...))
```

**Problem:** Every call to `POST /api/exams/{subject}/submit` unconditionally inserts a new row.
There is no duplicate check. A trainee can submit the same exam any number of times. When the
Stage 4 review later reads scores (in `admin.py` lines 185–191), it uses a plain dict comprehension
over `fetchall()` results with no `ORDER BY` or deduplication — so the score used for the review
is whichever row happened to be returned last by MySQL.

**Fix:** Before inserting, check for an existing submission:
```python
cursor.execute(
    "SELECT id FROM trainee_exam_submissions WHERE trainee_id = %s AND subject = %s",
    (trainee_id, subject)
)
if cursor.fetchone():
    raise HTTPException(status_code=409, detail="لقد قدمت هذا الاختبار بالفعل")
```

---

### BUG-H3 · `sync_course_sessions` Deletes All Sessions Before Re-Inserting (Attendance Data Loss)

**File:** `admin/backend/routers/courses.py` — Lines 130–131

```python
# 1. Clear existing sessions for this course to re-sync
cursor.execute("DELETE FROM course_sessions WHERE course_id = %s", (course_id,))
```

**Problem:** Every time a course is saved or updated (even a minor title change), all sessions
are deleted and re-inserted. If `attendance_logs` or `attendance_permissions` have a foreign key
to `course_sessions.id`, deleting sessions orphans all past attendance records. Additionally,
session IDs change on every re-insert, invalidating all stored references in related tables.
This is a data integrity risk on every course save.

**Fix:** Use an UPSERT strategy — match on `(course_id, topic, session_date)` — instead of
delete-all-and-reinsert. Or: only delete sessions that no longer appear in the new batch, and
preserve sessions that still match.

---

### BUG-H4 · `GET /api/ai/admission/full-check` and `/id/extract` Have No Authentication Guard

**File:** `admin/backend/routers/ai_services.py` — Lines 101–130

```python
@router.post("/admission/full-check")
async def run_full_admission_check(trainee_id: int, course_id: int = 1):
    # No Depends(get_admin_user) or Depends(get_staff_user)

@router.post("/id/extract")
async def extract_id_data(trainee_id: int, course_id: int = 1):
    # No auth — delegates to run_full_admission_check
```

**Problem:** Both endpoints are completely unauthenticated. Anyone who knows the API path
can trigger expensive AI processing for arbitrary trainee IDs without a valid token.

**Fix:**
```python
@router.post("/admission/full-check")
async def run_full_admission_check(
    trainee_id: int,
    course_id: int = 1,
    staff: dict = Depends(get_staff_user)
):
```

---

### BUG-H5 · `get_trainee_analytics` and `get_reviews` Use `get_admin_user` — Editors Locked Out

**File:** `admin/backend/routers/admin.py`  
- Line 379: `get_reviews` uses `Depends(get_admin_user)`
- Line 668: `get_trainee_analytics` uses `Depends(get_admin_user)`

**Problem:** Both are read-only endpoints. Editors (`get_staff_user`) can view trainees and
their profiles, but cannot access their stage review history or analytics. This is an
unintentional privilege inconsistency that breaks the editor workflow — editors can see a
trainee's profile card but cannot view the review trail or analytics that appear on the same
page.

**Fix:** Change both to `Depends(get_staff_user)`.

---

### BUG-H6 · `bulk_enroll` Has No Duplicate Guard on `private_course_assignments` INSERT

**File:** `admin/backend/routers/courses.py` — Line 389

```python
# Track private assignment
cursor.execute(
    "INSERT INTO private_course_assignments (course_id, national_id) VALUES (%s, %s)",
    (course_id, nid)
)
```

**Problem:** The `applications` INSERT is correctly guarded by a duplicate check (line 366–367),
but the `private_course_assignments` INSERT directly follows with no guard. If the CSV is
uploaded a second time, the `applications` check skips duplicate trainees — but no `private_course_assignments`
row is inserted for them either (it's inside the `if not cursor.fetchone()` block). However,
if the guard logic is ever changed, or if the same national ID appears twice in the CSV file,
a `UNIQUE` constraint violation will crash the entire batch and roll back all enrollments.

**Fix:**
```python
cursor.execute(
    "SELECT id FROM private_course_assignments WHERE course_id = %s AND national_id = %s",
    (course_id, nid)
)
if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO private_course_assignments (course_id, national_id) VALUES (%s, %s)",
        (course_id, nid)
    )
```

---

## 🟡 Medium Issues

---

### BUG-M1 · Stage 4 Exam Score Sync Has No `ORDER BY` — Score Is Non-Deterministic After Re-Submission

**File:** `admin/backend/routers/admin.py` — Lines 185–191

```python
cursor.execute("""
    SELECT subject, score
    FROM trainee_exam_submissions
    WHERE trainee_id = %s
""", (review.trainee_id,))
exam_rows = cursor.fetchall()
scores = {row[0]: float(row[1]) for row in exam_rows if row[1] is not None}
```

**Problem:** If a trainee re-submitted an exam (see BUG-H2), multiple rows exist for the same
subject. The dict comprehension silently uses the **last** row MySQL returns, which is
non-deterministic without an `ORDER BY`. The admin review may snap an old, lower score or a
different attempt entirely.

**Fix:**
```sql
SELECT subject, score
FROM trainee_exam_submissions
WHERE trainee_id = %s
ORDER BY submitted_at DESC
```
Then use `dict.setdefault()` or build the dict in reverse so only the latest is kept.

---

### BUG-M2 · Attendance Date Matching Uses Formatted String Comparison — Fragile for Single-Digit Days

**File:** `admin/backend/routers/admin.py` — Lines 572, 607, 625–640

```python
# Sessions: DATE_FORMAT(session_date, '%e %M %Y') as date
# Permissions: DATE_FORMAT(date, '%e %M %Y') as date
perm_map[uid][dstr] = p
...
perm_entry = st_perms.get(s_date)  # string-to-string match
```

**Problem:** `%e` is space-padded (` 5 June 2026` for single-digit days). If the MySQL locale
differs between the two queries, or if one query returns `5` and the other ` 5`, the string
comparison silently fails. Single-digit-day permissions are never matched to sessions —
making those sessions appear as "absent" even when an excused absence permission exists.

**Fix:** Match by raw `session_id` or raw `DATE` value. Store `p["session_id"]` in the
permission if available, or compare using `date` objects, not formatted strings.

---

### BUG-M3 · `ExamAnalyzer.analyze_submission` Will Crash on Exams Without `metadata` Key

**File:** `admin/backend/core/exam_analyzer.py` — Lines 32–35

```python
results.append({
    "number": q['number'],
    "Pillar":      q['metadata']['Pillar'],    # KeyError if metadata missing
    "CEFR_Level":  q['metadata']['CEFR_Level'],
    "Topic":       q['metadata']['Topic'],
```

**Problem:** The AI quiz generator (`POST /api/ai/quiz/generate`) saves questions into the
`exams` table **without** a `metadata` block per question. When a trainee later submits one
of these AI-generated quizzes via `POST /api/exams/{subject}/submit`, `ExamAnalyzer.analyze_submission`
is called on the content. It hits `q['metadata']` which raises a `KeyError`, returning a `500`
error and preventing grading for all AI-generated quizzes.

**Fix:**
```python
meta = q.get('metadata', {})
results.append({
    "number":     q['number'],
    "Pillar":     meta.get('Pillar',     'General'),
    "CEFR_Level": meta.get('CEFR_Level', 'A1'),
    "Topic":      meta.get('Topic',      'General'),
    "Outcome":    is_correct
})
```

---

### BUG-M4 · `get_trainee_profile` Order of `if user` and `if not user` Checks Is Inverted

**File:** `admin/backend/routers/admin.py` — Lines 411–415

```python
user = cursor.fetchone()
if user:
    user['id'] = user['user_id']  # Line 413
if not user:                       # Line 414
    raise HTTPException(status_code=404, detail="Trainee not found")
```

**Problem:** The `if user` block (line 413) runs before the `if not user` guard (line 414).
If `user` is `None`, line 413 raises an unhandled `TypeError: 'NoneType' object does not
support item assignment`, which produces a confusing `500 Internal Server Error` instead of a
clean `404 Not Found`. The correct pattern is to check `if not user` first, then set the field.

**Fix:** Swap the order:
```python
user = cursor.fetchone()
if not user:
    raise HTTPException(status_code=404, detail="Trainee not found")
user['id'] = user['user_id']
```

---

## 🔵 Low / Code Quality Issues

---

### BUG-L1 · `chat.py` In-Memory Rate Limiter Resets on Every Server Restart

**File:** `admin/backend/routers/chat.py` — Lines 26, 34–52

```python
CHAT_RATE_LIMIT = {}  # In-memory dict — lost on every restart
```

**Problem:** The rate limiter is a process-level Python dictionary. Any server restart, Uvicorn
worker reload, or crash resets all counters to zero. A blocked user can bypass the limit by
waiting for a deployment or triggering a reload. Low severity in a private admin portal, but
worth hardening for production.

**Fix:** Store rate-limit state in Redis, or in a DB table with `user_id`, `date`, and
`daily_count` columns, queried and incremented on each request.

---

### BUG-L2 · `class_matrix.py` Manual Token Decode Duplicates `get_current_user` Logic

**File:** `admin/backend/routers/class_matrix.py` — Lines 46–58, 106–115

```python
# In generate_matrix and get_matrix_status:
from core.auth import get_current_user
token = auth_header.split(" ")[1]
user = get_current_user(token)  # <-- called with a raw string, not a Request object
```

**Problem:** `get_current_user` is a FastAPI dependency that expects to receive a token via
`Depends(OAuth2PasswordBearer(...))`. When called directly with a raw string (as done here),
it works by coincidence because `OAuth2PasswordBearer` only wraps the token extraction — but
this is non-idiomatic and fragile. The `is_internal` localhost bypass also allows any process
running on the same machine to call this endpoint without authentication.

Additionally, `MATRIX_JOBS` is a module-level in-memory dict, so it suffers the same restart-reset
problem as `CHAT_RATE_LIMIT`.

**Fix:** Use `Depends(get_staff_user)` with an `Optional` pattern, or create a helper that
returns `None` instead of raising an exception for flexible auth. Reconsider the localhost
bypass — it is a security assumption that may not hold in containerised or shared environments.

---

## Summary Table

| ID | Severity | File | Description |
|----|----------|------|-------------|
| C1 | 🔴 Critical | `routers/exams.py` | `decode_access_token` imported but not defined — `ImportError` on every exam call |
| C2 | 🔴 Critical | `core/auth.py` | `SECRET_KEY` defaults to `"your-secret-key"` — allows JWT forgery if `.env` is missing |
| C3 | 🔴 Critical | `backend/.env` | Live DB password + SendGrid API key stored in plain text on disk |
| C4 | 🔴 Critical | `apply_default_credentials.py` | Hardcoded DB password fallback + plaintext default staff passwords |
| C5 | 🔴 Critical | `routers/admin.py` | Rejection audit trail (`stage_reviews`) instantly cascade-deleted with the user row |
| H1 | 🟠 High | `schemas/admin.py` | `TraineeSummary` required fields fail on NULL pipeline records → 500 on trainee list |
| H2 | 🟠 High | `routers/exams.py` | Exam re-submission allowed without restriction; score is non-deterministic |
| H3 | 🟠 High | `routers/courses.py` | `sync_course_sessions` DELETE-all orphans attendance logs on every course save |
| H4 | 🟠 High | `routers/ai_services.py` | `/admission/full-check` and `/id/extract` are completely unauthenticated |
| H5 | 🟠 High | `routers/admin.py` | `get_admin_user` vs `get_staff_user` inconsistency locks editors out of analytics and reviews |
| H6 | 🟠 High | `routers/courses.py` | No duplicate guard on `private_course_assignments` INSERT in bulk enrollment |
| M1 | 🟡 Medium | `routers/admin.py` | Stage 4 exam score sync has no ORDER BY — wrong score used after re-submission |
| M2 | 🟡 Medium | `routers/admin.py` | Attendance permission matching by formatted string fails for single-digit days |
| M3 | 🟡 Medium | `core/exam_analyzer.py` | `q['metadata']` KeyError crashes grading for all AI-generated quizzes |
| M4 | 🟡 Medium | `routers/admin.py` | `if user` / `if not user` order inverted — TypeError instead of 404 on missing trainee |
| L1 | 🔵 Low | `routers/chat.py` | In-memory rate limiter resets on every server restart |
| L2 | 🔵 Low | `routers/class_matrix.py` | Manual token decode duplicates `get_current_user` logic non-idiomatically; localhost bypass is unsafe |

---

## Recommended Fix Priority

### 1. Immediate (before any deployment or sharing)
- **C1** — Add `decode_access_token` to `core/auth.py`; exam portal is completely broken
- **C2** — Remove the `SECRET_KEY` default; fail loudly on startup if missing
- **C3** — Rotate credentials, add `.env` to `.gitignore`
- **C4** — Remove hardcoded password fallbacks from `apply_default_credentials.py`
- **H4** — Add auth guard to AI endpoints

### 2. Before production traffic
- **C5** — Run the DB migration for `stage_reviews ON DELETE SET NULL`
- **H1** — Make `TraineeSummary` fields Optional with defaults
- **H2** — Add exam re-submission guard (409 on duplicate)
- **M4** — Fix inverted None-check in `get_trainee_profile`

### 3. Stability hardening
- **H3** — Replace delete-all session sync with UPSERT
- **H5** — Change `get_reviews` and `get_trainee_analytics` to `get_staff_user`
- **H6** — Add duplicate guard to `private_course_assignments`
- **M1** — Add `ORDER BY submitted_at DESC` to Stage 4 score query
- **M3** — Add `.get('metadata', {})` safety in `ExamAnalyzer`

### 4. Code quality pass
- **M2** — Replace string-date matching in attendance with session_id or raw DATE comparison
- **L1** — Persist chat rate limiter in DB or Redis
- **L2** — Refactor class_matrix auth to use `Depends`
