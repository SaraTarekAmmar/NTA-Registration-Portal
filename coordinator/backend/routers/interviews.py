"""Coordinator interview operations API.

Adds read-only interview-day endpoints for committee queue, missing evaluation
follow-up, and dashboard KPIs. The endpoints intentionally reuse existing
admission pipeline tables so they work without a new migration.
"""
import io
import csv
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from core.auth import require_coordinator, require_coordinator_or_member
from core.database import get_db_connection

router = APIRouter(prefix="/api/coordinator/interviews", tags=["Coordinator Interviews"])

INTERVIEW_STAGES = (5, 6)


def _rows(cursor):
    return cursor.fetchall() or []


@router.get("/summary")
async def interview_summary(user: dict = Depends(require_coordinator_or_member)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if user["role"] == "committee_member":
            cursor.execute(
                "SELECT committee_id FROM interview_committee_members WHERE member_user_id = %s",
                (user["id"],),
            )
            c_ids = [r["committee_id"] for r in cursor.fetchall()]
            if not c_ids:
                return {
                    "waiting_interviews": 0,
                    "missing_evaluations": 0,
                    "completed_today": 0,
                    "rejected_today": 0,
                }
            
            placeholders = ",".join(["%s"] * len(c_ids))
            
            # 1. Waiting interviews
            cursor.execute(
                f"""
                SELECT COUNT(DISTINCT u.id) AS cnt
                FROM users u
                JOIN pipeline_state ps ON ps.trainee_id = u.id
                JOIN interview_committee_applicants ica ON ica.applicant_user_id = u.id AND ica.stage_id = ps.current_stage_id
                WHERE u.role = 'applicant' AND ps.current_stage_id IN (5, 6)
                  AND ica.committee_id IN ({placeholders})
                """,
                tuple(c_ids),
            )
            waiting = cursor.fetchone()["cnt"]

            # 2. Missing evaluations
            cursor.execute("SELECT full_name_ar FROM users WHERE id = %s", (user["id"],))
            member_name = cursor.fetchone()["full_name_ar"]
            
            cursor.execute(
                f"""
                SELECT COUNT(DISTINCT u.id) AS cnt
                FROM users u
                JOIN pipeline_state ps ON ps.trainee_id = u.id
                JOIN interview_committee_applicants ica ON ica.applicant_user_id = u.id AND ica.stage_id = ps.current_stage_id
                LEFT JOIN admission_interview_scores s
                  ON s.trainee_id = u.id AND s.stage_id = ps.current_stage_id AND s.committee_member_name = %s
                WHERE u.role = 'applicant'
                  AND ps.current_stage_id IN (5, 6)
                  AND ica.committee_id IN ({placeholders})
                  AND s.id IS NULL
                """,
                (member_name,) + tuple(c_ids),
            )
            missing = cursor.fetchone()["cnt"]

            # 3. Completed today
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM admission_interview_scores "
                "WHERE committee_member_name = %s AND DATE(created_at) = CURDATE()",
                (member_name,),
            )
            completed_today = cursor.fetchone()["cnt"]

            # 4. Rejected today
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM admission_interview_scores "
                "WHERE committee_member_name = %s AND recommendation = 'unsuitable' AND DATE(created_at) = CURDATE()",
                (member_name,),
            )
            rejected_today = cursor.fetchone()["cnt"]
        else:
            cursor.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM users u
                JOIN pipeline_state ps ON ps.trainee_id = u.id
                WHERE u.role = 'applicant' AND ps.current_stage_id IN (5, 6)
                """
            )
            waiting = cursor.fetchone()["cnt"]

            cursor.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM users u
                JOIN pipeline_state ps ON ps.trainee_id = u.id
                LEFT JOIN stage_reviews sr
                  ON sr.trainee_id = u.id AND sr.stage_id = ps.current_stage_id
                WHERE u.role = 'applicant'
                  AND ps.current_stage_id IN (5, 6)
                  AND sr.id IS NULL
                """
            )
            missing = cursor.fetchone()["cnt"]

            cursor.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM stage_reviews
                WHERE stage_id IN (5, 6) AND DATE(created_at) = CURDATE()
                """
            )
            completed_today = cursor.fetchone()["cnt"]

            cursor.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM stage_reviews
                WHERE stage_id IN (5, 6)
                  AND result = 'Rejected'
                  AND DATE(created_at) = CURDATE()
                """
            )
            rejected_today = cursor.fetchone()["cnt"]

        return {
            "waiting_interviews": waiting,
            "missing_evaluations": missing,
            "completed_today": completed_today,
            "rejected_today": rejected_today,
        }
    finally:
        cursor.close()
        db.close()


@router.get("/queue")
async def interview_queue(user: dict = Depends(require_coordinator_or_member)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if user["role"] == "committee_member":
            cursor.execute(
                "SELECT committee_id FROM interview_committee_members WHERE member_user_id = %s",
                (user["id"],),
            )
            c_ids = [r["committee_id"] for r in cursor.fetchall()]
            if not c_ids:
                return []
            
            cursor.execute("SELECT full_name_ar FROM users WHERE id = %s", (user["id"],))
            member_name = cursor.fetchone()["full_name_ar"]
            
            placeholders = ",".join(["%s"] * len(c_ids))
            cursor.execute(
                f"""
                SELECT u.id,
                       u.full_name_ar AS name,
                       u.email,
                       u.national_id,
                       ps.current_stage_id AS stage_id,
                       ps.status AS pipeline_status,
                       a.course_id,
                       c.title_ar AS course_title_ar,
                       c.title AS course_title,
                       s.id AS review_id,
                       s.recommendation AS review_result,
                       s.updated_at AS reviewed_at,
                       ica.committee_id
                FROM users u
                JOIN pipeline_state ps ON ps.trainee_id = u.id
                JOIN interview_committee_applicants ica ON ica.applicant_user_id = u.id AND ica.stage_id = ps.current_stage_id
                LEFT JOIN (
                  SELECT user_id, course_id, status,
                         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY applied_at DESC, id DESC) AS rn
                  FROM applications
                ) a ON a.user_id = u.id AND a.rn = 1
                LEFT JOIN courses c ON c.id = a.course_id
                LEFT JOIN admission_interview_scores s
                  ON s.trainee_id = u.id AND s.stage_id = ps.current_stage_id AND s.committee_member_name = %s
                WHERE u.role = 'applicant' AND ps.current_stage_id IN (5, 6)
                  AND ica.committee_id IN ({placeholders})
                ORDER BY ps.current_stage_id, u.full_name_ar
                """,
                (member_name,) + tuple(c_ids),
            )
            return _rows(cursor)
        else:
            cursor.execute(
                """
                SELECT u.id,
                       u.full_name_ar AS name,
                       u.email,
                       u.national_id,
                       ps.current_stage_id AS stage_id,
                       ps.status AS pipeline_status,
                       a.course_id,
                       c.title_ar AS course_title_ar,
                       c.title AS course_title,
                       sr.id AS review_id,
                       sr.result AS review_result,
                       sr.created_at AS reviewed_at
                FROM users u
                JOIN pipeline_state ps ON ps.trainee_id = u.id
                LEFT JOIN (
                  SELECT user_id, course_id, status,
                         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY applied_at DESC, id DESC) AS rn
                  FROM applications
                ) a ON a.user_id = u.id AND a.rn = 1
                LEFT JOIN courses c ON c.id = a.course_id
                LEFT JOIN stage_reviews sr
                  ON sr.trainee_id = u.id AND sr.stage_id = ps.current_stage_id
                WHERE u.role = 'applicant' AND ps.current_stage_id IN (5, 6)
                ORDER BY ps.current_stage_id, u.full_name_ar
                """
            )
            return _rows(cursor)
    finally:
        cursor.close()
        db.close()


@router.get("/missing-evaluations")
async def missing_evaluations(coordinator: dict = Depends(require_coordinator)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.id,
                   u.full_name_ar AS name,
                   u.email,
                   ps.current_stage_id AS stage_id,
                   c.title_ar AS course_title_ar,
                   c.title AS course_title
            FROM users u
            JOIN pipeline_state ps ON ps.trainee_id = u.id
            LEFT JOIN applications a ON a.user_id = u.id AND a.status IN ('pending', 'approved')
            LEFT JOIN courses c ON c.id = a.course_id
            LEFT JOIN stage_reviews sr
              ON sr.trainee_id = u.id AND sr.stage_id = ps.current_stage_id
            WHERE u.role = 'applicant'
              AND ps.current_stage_id IN (5, 6)
              AND sr.id IS NULL
            GROUP BY u.id, u.full_name_ar, u.email, ps.current_stage_id, c.title_ar, c.title
            ORDER BY ps.current_stage_id, u.full_name_ar
            """
        )
        return _rows(cursor)
    finally:
        cursor.close()
        db.close()


# ─────────────────────────────────────────────────────────────────────
#  Interview evaluation capture  (writes admission_interview_scores)
# ─────────────────────────────────────────────────────────────────────

def _resolve_member_name(coordinator, cursor, fallback):
    """Use the supplied committee-member name, else the coordinator's own name."""
    if fallback and fallback.strip():
        return fallback.strip()
    cursor.execute("SELECT full_name_ar FROM users WHERE id = %s", (coordinator["id"],))
    row = cursor.fetchone()
    return (row["full_name_ar"] if row and row.get("full_name_ar") else str(coordinator.get("id", "")))


@router.post("/evaluate")
async def submit_evaluation(body: dict, user: dict = Depends(require_coordinator_or_member)):
    """Record one committee member's interview evaluation for an applicant.

    Computes total / max / percentage server-side and upserts a row in
    admission_interview_scores keyed by (trainee, stage, committee_member_name).
    Supports both 10-criteria (/50) and 15-criteria (/75) forms — the size is
    derived from how many scores are submitted.
    """
    trainee_id = body.get("trainee_id")
    stage_id = body.get("stage_id", 5)
    course_id = body.get("course_id")
    committee_id = body.get("committee_id")
    criteria = body.get("criteria_json") or body.get("criteria") or {}
    recommendation = body.get("recommendation")
    notes = (body.get("notes") or "").strip()

    # Interview session metadata (all optional).
    def _dt(v):
        v = (v or "").strip().replace("T", " ")
        return v or None
    session_start = _dt(body.get("session_start"))
    session_end = _dt(body.get("session_end"))
    governorate = (body.get("governorate") or "").strip() or None
    still_on_duty = body.get("still_on_duty")
    still_on_duty = 1 if still_on_duty in (True, 1, "1", "yes", "true") else (0 if still_on_duty in (False, 0, "0", "no", "false") else None)

    if not trainee_id:
        raise HTTPException(status_code=422, detail="معرّف المتقدم مطلوب")
    try:
        stage_id = int(stage_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="رقم المرحلة غير صالح")
    if stage_id not in INTERVIEW_STAGES:
        raise HTTPException(status_code=422, detail="هذه المرحلة ليست مرحلة مقابلة")
    if not isinstance(criteria, dict) or not criteria:
        raise HTTPException(status_code=422, detail="لا توجد درجات في التقييم")

    scores = {}
    for key, val in criteria.items():
        try:
            iv = int(val)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail=f"درجة غير صالحة للمحور: {key}")
        if iv < 1 or iv > 5:
            raise HTTPException(status_code=422, detail="يجب أن تكون كل درجة بين 1 و 5")
        scores[str(key)] = iv

    total_score = sum(scores.values())
    total_max = len(scores) * 5
    rec = recommendation if recommendation in ("accept", "waitlist", "unsuitable") else None

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if user["role"] == "committee_member":
            cursor.execute("SELECT full_name_ar FROM users WHERE id = %s", (user["id"],))
            member = cursor.fetchone()["full_name_ar"]
            # Authz: a committee member may only evaluate applicants assigned to
            # one of their own committees.
            cursor.execute(
                """SELECT ica.committee_id
                   FROM interview_committee_applicants ica
                   JOIN interview_committee_members icm ON icm.committee_id = ica.committee_id
                   WHERE icm.member_user_id = %s AND ica.applicant_user_id = %s AND ica.stage_id = %s
                   LIMIT 1""",
                (user["id"], trainee_id, stage_id),
            )
            allowed = cursor.fetchone()
            if not allowed:
                raise HTTPException(status_code=403, detail="غير مصرح لك بتقييم هذا المتقدم")
            if not committee_id:
                committee_id = allowed["committee_id"]
        else:
            member = _resolve_member_name(user, cursor, body.get("committee_member_name"))

        # Fallback to resolve committee_id and course_id
        if not committee_id:
            cursor.execute(
                "SELECT committee_id FROM interview_committee_applicants "
                "WHERE applicant_user_id = %s AND stage_id = %s LIMIT 1",
                (trainee_id, stage_id),
            )
            comm_row = cursor.fetchone()
            if comm_row:
                committee_id = comm_row["committee_id"]

        if not course_id:
            cursor.execute(
                """SELECT course_id FROM applications
                   WHERE user_id = %s AND status IN ('pending', 'approved')
                   ORDER BY applied_at DESC, id DESC LIMIT 1""",
                (trainee_id,),
            )
            app_row = cursor.fetchone()
            if app_row:
                course_id = app_row["course_id"]

        cursor.execute(
            "SELECT id FROM admission_interview_scores "
            "WHERE trainee_id = %s AND stage_id = %s AND committee_member_name = %s",
            (trainee_id, stage_id, member),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """UPDATE admission_interview_scores
                   SET course_id=%s, committee_id=%s, criteria_json=%s,
                       total_score=%s, total_max=%s, recommendation=%s, notes=%s,
                       session_start=%s, session_end=%s, governorate=%s, still_on_duty=%s,
                       updated_at=NOW()
                   WHERE id=%s""",
                (course_id, committee_id, json.dumps(scores, ensure_ascii=False),
                 total_score, total_max, rec, notes,
                 session_start, session_end, governorate, still_on_duty, existing["id"]),
            )
            row_id = existing["id"]
        else:
            cursor.execute(
                """INSERT INTO admission_interview_scores
                       (trainee_id, course_id, stage_id, committee_id, committee_member_name,
                        criteria_json, total_score, total_max, recommendation, notes,
                        session_start, session_end, governorate, still_on_duty)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (trainee_id, course_id, stage_id, committee_id, member,
                 json.dumps(scores, ensure_ascii=False), total_score, total_max, rec, notes,
                 session_start, session_end, governorate, still_on_duty),
            )
            row_id = cursor.lastrowid
        db.commit()
        return {
            "id": row_id,
            "trainee_id": trainee_id,
            "stage_id": stage_id,
            "committee_member_name": member,
            "total_score": total_score,
            "total_max": total_max,
            "percentage": round(total_score / total_max * 100, 1) if total_max else 0,
            "recommendation": rec,
            "updated": bool(existing),
        }
    finally:
        cursor.close()
        db.close()


@router.get("/applicant/{trainee_id}/scores")
async def applicant_scores(trainee_id: int, user: dict = Depends(require_coordinator_or_member)):
    """All committee evaluations for an applicant + average / variance across members."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if user["role"] == "committee_member":
            cursor.execute(
                """SELECT COUNT(*) AS cnt FROM interview_committee_applicants ica
                   JOIN interview_committee_members icm ON icm.committee_id = ica.committee_id
                   WHERE ica.applicant_user_id = %s AND icm.member_user_id = %s""",
                (trainee_id, user["id"]),
            )
            if not cursor.fetchone()["cnt"]:
                raise HTTPException(status_code=403, detail="غير مصرح لك بالوصول لبيانات هذا المتقدم")

        cursor.execute(
            """SELECT id, stage_id, committee_id, committee_member_name,
                      criteria_json, total_score, total_max, recommendation, notes,
                      session_start, session_end, governorate, still_on_duty, updated_at
               FROM admission_interview_scores
               WHERE trainee_id = %s
               ORDER BY stage_id, committee_member_name""",
            (trainee_id,),
        )
        rows = _rows(cursor)
        pcts = []
        for r in rows:
            if isinstance(r.get("criteria_json"), str):
                try:
                    r["criteria_json"] = json.loads(r["criteria_json"])
                except Exception:
                    pass
            tm = float(r["total_max"] or 0)
            r["percentage"] = round(float(r["total_score"]) / tm * 100, 1) if tm else 0
            pcts.append(r["percentage"])
        avg = round(sum(pcts) / len(pcts), 1) if pcts else 0
        variance = round(max(pcts) - min(pcts), 1) if len(pcts) > 1 else 0
        return {
            "trainee_id": trainee_id,
            "evaluations": rows,
            "member_count": len(rows),
            "average_percentage": avg,
            "score_variance": variance,
        }
    finally:
        cursor.close()
        db.close()


@router.get("/criteria-analysis")
async def criteria_analysis(user: dict = Depends(require_coordinator_or_member)):
    """Average score per criterion across all submitted evaluations (strongest / weakest)."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if user["role"] == "committee_member":
            cursor.execute("SELECT full_name_ar FROM users WHERE id = %s", (user["id"],))
            member_name = cursor.fetchone()["full_name_ar"]
            cursor.execute(
                "SELECT criteria_json FROM admission_interview_scores WHERE committee_member_name = %s",
                (member_name,),
            )
        else:
            cursor.execute("SELECT criteria_json FROM admission_interview_scores")

        agg = {}
        for r in _rows(cursor):
            data = r["criteria_json"]
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    continue
            if not isinstance(data, dict):
                continue
            for key, val in data.items():
                a = agg.setdefault(key, {"sum": 0, "n": 0})
                try:
                    a["sum"] += float(val)
                    a["n"] += 1
                except (TypeError, ValueError):
                    pass
        criteria = [
            {"key": k, "average": round(v["sum"] / v["n"], 2), "count": v["n"]}
            for k, v in agg.items() if v["n"]
        ]
        criteria.sort(key=lambda x: x["average"])
        return {
            "criteria": criteria,
            "weakest": criteria[:3],
            "strongest": list(reversed(criteria[-3:])),
        }
    finally:
        cursor.close()
        db.close()


@router.get("/decisions-summary")
async def decisions_summary(user: dict = Depends(require_coordinator_or_member)):
    """Final-recommendation breakdown + evaluation completion rate."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if user["role"] == "committee_member":
            cursor.execute("SELECT full_name_ar FROM users WHERE id = %s", (user["id"],))
            member_name = cursor.fetchone()["full_name_ar"]
            cursor.execute(
                "SELECT committee_id FROM interview_committee_members WHERE member_user_id = %s",
                (user["id"],),
            )
            c_ids = [r["committee_id"] for r in cursor.fetchall()]
            
            cursor.execute(
                """SELECT recommendation, COUNT(*) AS cnt
                   FROM admission_interview_scores 
                   WHERE committee_member_name = %s 
                   GROUP BY recommendation""",
                (member_name,),
            )
            rec = {"accept": 0, "waitlist": 0, "unsuitable": 0, "pending": 0}
            for r in _rows(cursor):
                rec[r["recommendation"] or "pending"] = r["cnt"]

            if c_ids:
                placeholders = ",".join(["%s"] * len(c_ids))
                cursor.execute(
                    f"""SELECT COUNT(DISTINCT applicant_user_id) AS cnt 
                        FROM interview_committee_applicants
                        WHERE committee_id IN ({placeholders}) AND stage_id IN (5,6)""",
                    tuple(c_ids),
                )
                scheduled = cursor.fetchone()["cnt"]
            else:
                scheduled = 0

            cursor.execute(
                """SELECT COUNT(DISTINCT trainee_id) AS cnt 
                   FROM admission_interview_scores 
                   WHERE committee_member_name = %s AND stage_id IN (5,6)""",
                (member_name,),
            )
            evaluated = cursor.fetchone()["cnt"]

            cursor.execute(
                """SELECT AVG(total_score/total_max*100) AS avg_pct 
                   FROM admission_interview_scores 
                   WHERE committee_member_name = %s AND total_max>0""",
                (member_name,),
            )
            avg_pct = cursor.fetchone()["avg_pct"]
        else:
            cursor.execute(
                """SELECT recommendation, COUNT(*) AS cnt
                   FROM admission_interview_scores GROUP BY recommendation"""
            )
            rec = {"accept": 0, "waitlist": 0, "unsuitable": 0, "pending": 0}
            for r in _rows(cursor):
                rec[r["recommendation"] or "pending"] = r["cnt"]

            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM users u JOIN pipeline_state ps ON ps.trainee_id=u.id "
                "WHERE u.role='applicant' AND ps.current_stage_id IN (5,6)"
            )
            scheduled = cursor.fetchone()["cnt"]
            cursor.execute(
                "SELECT COUNT(DISTINCT trainee_id) AS cnt FROM admission_interview_scores WHERE stage_id IN (5,6)"
            )
            evaluated = cursor.fetchone()["cnt"]
            cursor.execute(
                "SELECT AVG(total_score/total_max*100) AS avg_pct FROM admission_interview_scores WHERE total_max>0"
            )
            avg_pct = cursor.fetchone()["avg_pct"]

        return {
            "recommendations": rec,
            "interviews_scheduled": scheduled,
            "applicants_evaluated": evaluated,
            "evaluation_completion_rate": round(evaluated / scheduled * 100, 1) if scheduled else 0,
            "average_interview_percentage": round(float(avg_pct), 1) if avg_pct is not None else 0,
        }
    finally:
        cursor.close()
        db.close()


# ─────────────────────────────────────────────────────────────────────
#  Committee management
# ─────────────────────────────────────────────────────────────────────

@router.get("/committees")
async def list_committees(coordinator: dict = Depends(require_coordinator)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT ic.id, ic.committee_number, ic.course_id, ic.governorate, ic.interview_date,
                      c.title_ar AS course_title_ar,
                      (SELECT COUNT(*) FROM interview_committee_members m WHERE m.committee_id=ic.id) AS member_count,
                      (SELECT COUNT(*) FROM interview_committee_applicants a WHERE a.committee_id=ic.id) AS applicant_count
               FROM interview_committees ic
               LEFT JOIN courses c ON c.id = ic.course_id
               ORDER BY ic.interview_date DESC, ic.id DESC"""
        )
        return _rows(cursor)
    finally:
        cursor.close()
        db.close()


@router.post("/committees")
async def create_committee(body: dict, coordinator: dict = Depends(require_coordinator)):
    number = (body.get("committee_number") or "").strip()
    if not number:
        raise HTTPException(status_code=422, detail="رقم اللجنة مطلوب")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """INSERT INTO interview_committees
                   (committee_number, course_id, governorate, interview_date, coordinator_id)
               VALUES (%s,%s,%s,%s,%s)""",
            (number, body.get("course_id"), body.get("governorate"),
             body.get("interview_date"), coordinator["id"]),
        )
        cid = cursor.lastrowid
        for m in (body.get("members") or []):
            name = (m.get("member_name") if isinstance(m, dict) else str(m)).strip()
            if name:
                cursor.execute(
                    "SELECT id FROM users WHERE full_name_ar = %s AND role = 'committee_member'",
                    (name,),
                )
                user_row = cursor.fetchone()
                user_id = user_row["id"] if user_row else None
                
                cursor.execute(
                    "INSERT INTO interview_committee_members (committee_id, member_name, member_user_id) VALUES (%s,%s,%s)",
                    (cid, name, user_id),
                )
        db.commit()
        return {"id": cid, "committee_number": number}
    finally:
        cursor.close()
        db.close()


@router.post("/committees/{committee_id}/applicants")
async def assign_applicants(committee_id: int, body: dict, coordinator: dict = Depends(require_coordinator)):
    ids = body.get("applicant_ids") or []
    stage_id = int(body.get("stage_id", 5))
    db = get_db_connection()
    cursor = db.cursor()
    try:
        added = 0
        for aid in ids:
            cursor.execute(
                """INSERT IGNORE INTO interview_committee_applicants
                       (committee_id, applicant_user_id, stage_id) VALUES (%s,%s,%s)""",
                (committee_id, aid, stage_id),
            )
            added += cursor.rowcount
        db.commit()
        return {"committee_id": committee_id, "assigned": added}
    finally:
        cursor.close()
        db.close()


@router.get("/export")
async def export_evaluations(stage_id: int = None, recommendation: str = None,
                             coordinator: dict = Depends(require_coordinator)):
    """Download all interview evaluations as CSV (opens directly in Excel).

    One row per (applicant, committee member). Per-criterion scores are expanded
    into their own columns (union across the 10- and 15-criterion forms), plus
    total / max / percentage / recommendation. Optional stage / recommendation filters.
    """
    where, params = ["1=1"], []
    if stage_id in (5, 6):
        where.append("s.stage_id = %s")
        params.append(stage_id)
    if recommendation in ("accept", "waitlist", "unsuitable"):
        where.append("s.recommendation = %s")
        params.append(recommendation)

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""SELECT s.id, s.trainee_id, u.full_name_ar AS applicant, u.national_id,
                       s.stage_id, s.committee_id, s.committee_member_name,
                       s.criteria_json, s.total_score, s.total_max, s.recommendation,
                       s.notes, s.session_start, s.session_end, s.governorate,
                       s.still_on_duty, s.updated_at
                FROM admission_interview_scores s
                LEFT JOIN users u ON u.id = s.trainee_id
                WHERE {' AND '.join(where)}
                ORDER BY s.trainee_id, s.stage_id, s.committee_member_name""",
            tuple(params),
        )
        rows = _rows(cursor)

        crit_keys = []
        for r in rows:
            data = r.get("criteria_json")
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    data = {}
            r["_criteria"] = data if isinstance(data, dict) else {}
            for k in r["_criteria"]:
                if k not in crit_keys:
                    crit_keys.append(k)

        rec_ar = {"accept": "قبول", "waitlist": "قائمة انتظار", "unsuitable": "غير مناسب"}
        stage_ar = {5: "المقابلة الأولى", 6: "المقابلة الثانية"}
        header = (["معرّف المتقدم", "المتقدم", "الرقم القومي", "المرحلة", "رقم اللجنة", "عضو اللجنة",
                   "المحافظة", "بداية المقابلة", "نهاية المقابلة", "على رأس العمل"]
                  + crit_keys + ["الإجمالي", "الحد الأقصى", "النسبة %", "التوصية", "ملاحظات", "التاريخ"])

        buf = io.StringIO()
        buf.write("﻿")  # BOM so Excel renders Arabic correctly
        writer = csv.writer(buf)
        writer.writerow(header)
        for r in rows:
            tm = float(r["total_max"] or 0)
            pct = round(float(r["total_score"]) / tm * 100, 1) if tm else 0
            writer.writerow(
                [r["trainee_id"], r.get("applicant") or "", r.get("national_id") or "",
                 stage_ar.get(r["stage_id"], r["stage_id"]), r.get("committee_id") or "",
                 r["committee_member_name"], r.get("governorate") or "",
                 str(r.get("session_start") or ""), str(r.get("session_end") or ""),
                 ("نعم" if r.get("still_on_duty") == 1 else ("لا" if r.get("still_on_duty") == 0 else ""))]
                + [r["_criteria"].get(k, "") for k in crit_keys]
                + [r["total_score"], r["total_max"], pct,
                   rec_ar.get(r["recommendation"], ""), (r.get("notes") or "").replace("\n", " "),
                   str(r.get("updated_at") or "")]
            )
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=NTA_Interview_Evaluations.csv"},
        )
    finally:
        cursor.close()
        db.close()
