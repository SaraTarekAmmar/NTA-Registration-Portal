"""Coordinator interview operations API.

Adds read-only interview-day endpoints for committee queue, missing evaluation
follow-up, and dashboard KPIs. The endpoints intentionally reuse existing
admission pipeline tables so they work without a new migration.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from core.auth import require_coordinator
from core.database import get_db_connection

router = APIRouter(prefix="/api/coordinator/interviews", tags=["Coordinator Interviews"])

INTERVIEW_STAGES = (5, 6)


def _rows(cursor):
    return cursor.fetchall() or []


@router.get("/summary")
async def interview_summary(coordinator: dict = Depends(require_coordinator)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
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
async def interview_queue(coordinator: dict = Depends(require_coordinator)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
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
async def submit_evaluation(body: dict, coordinator: dict = Depends(require_coordinator)):
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
        member = _resolve_member_name(coordinator, cursor, body.get("committee_member_name"))
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
                       updated_at=NOW()
                   WHERE id=%s""",
                (course_id, committee_id, json.dumps(scores, ensure_ascii=False),
                 total_score, total_max, rec, notes, existing["id"]),
            )
            row_id = existing["id"]
        else:
            cursor.execute(
                """INSERT INTO admission_interview_scores
                       (trainee_id, course_id, stage_id, committee_id, committee_member_name,
                        criteria_json, total_score, total_max, recommendation, notes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (trainee_id, course_id, stage_id, committee_id, member,
                 json.dumps(scores, ensure_ascii=False), total_score, total_max, rec, notes),
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
async def applicant_scores(trainee_id: int, coordinator: dict = Depends(require_coordinator)):
    """All committee evaluations for an applicant + average / variance across members."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT id, stage_id, committee_id, committee_member_name,
                      criteria_json, total_score, total_max, recommendation, notes, updated_at
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
async def criteria_analysis(coordinator: dict = Depends(require_coordinator)):
    """Average score per criterion across all submitted evaluations (strongest / weakest)."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
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
async def decisions_summary(coordinator: dict = Depends(require_coordinator)):
    """Final-recommendation breakdown + evaluation completion rate."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
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
                    "INSERT INTO interview_committee_members (committee_id, member_name) VALUES (%s,%s)",
                    (cid, name),
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
