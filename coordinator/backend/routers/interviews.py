"""Coordinator interview operations API."""
from fastapi import APIRouter, Depends
from core.auth import require_coordinator, allow_coordinator_or_committee
from core.database import get_db_connection
from pydantic import BaseModel

class AssignRequest(BaseModel):
    trainee_id: int
    stage_id: int
    reviewer_id: int
    course_id: int | None = None

router = APIRouter(prefix="/api/coordinator/interviews", tags=["Coordinator Interviews"])


@router.get("/summary")
async def interview_summary(coordinator: dict = Depends(require_coordinator)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT COUNT(*) AS cnt
            FROM users u
            JOIN pipeline_state ps ON ps.trainee_id = u.id
            WHERE u.role = 'trainee' AND ps.current_stage_id IN (5, 6)
        """)
        waiting = cursor.fetchone()["cnt"]
        cursor.execute("""
            SELECT COUNT(*) AS cnt
            FROM users u
            JOIN pipeline_state ps ON ps.trainee_id = u.id
            LEFT JOIN stage_reviews sr ON sr.trainee_id = u.id AND sr.stage_id = ps.current_stage_id
            WHERE u.role = 'trainee' AND ps.current_stage_id IN (5, 6) AND sr.id IS NULL
        """)
        missing = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) AS cnt FROM stage_reviews WHERE stage_id IN (5, 6) AND DATE(created_at) = CURDATE()")
        completed_today = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) AS cnt FROM stage_reviews WHERE stage_id IN (5, 6) AND result = 'Rejected' AND DATE(created_at) = CURDATE()")
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
async def interview_queue(user: dict = Depends(allow_coordinator_or_committee)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
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
                   sr.created_at AS reviewed_at,
                   ia.reviewer_id AS assigned_reviewer_id,
                   ia.status AS assignment_status,
                   ru.full_name_ar AS assigned_reviewer_name
            FROM users u
            JOIN pipeline_state ps ON ps.trainee_id = u.id
            LEFT JOIN (
              SELECT user_id, course_id, status,
                     ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY applied_at DESC, id DESC) AS rn
              FROM applications
            ) a ON a.user_id = u.id AND a.rn = 1
            LEFT JOIN courses c ON c.id = a.course_id
            LEFT JOIN stage_reviews sr ON sr.trainee_id = u.id AND sr.stage_id = ps.current_stage_id
            LEFT JOIN interview_assignments ia ON ia.trainee_id = u.id AND ia.stage_id = ps.current_stage_id AND ia.status = 'pending'
            LEFT JOIN users ru ON ru.id = ia.reviewer_id
            WHERE u.role = 'trainee' AND ps.current_stage_id IN (5, 6)
            ORDER BY ps.current_stage_id, u.full_name_ar
        """)
        results = cursor.fetchall() or []

        if user["role"] == "committee_member":
            # Only return candidates assigned to this member with pending status
            cursor.execute(
                "SELECT trainee_id, stage_id FROM interview_assignments WHERE reviewer_id = %s AND status = 'pending'",
                (user["id"],)
            )
            assignments = cursor.fetchall() or []
            assigned_keys = {(a["trainee_id"], a["stage_id"]) for a in assignments}
            results = [r for r in results if (r["id"], r["stage_id"]) in assigned_keys]

        return results
    finally:
        cursor.close()
        db.close()


@router.get("/missing-evaluations")
async def missing_evaluations(coordinator: dict = Depends(require_coordinator)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
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
            LEFT JOIN stage_reviews sr ON sr.trainee_id = u.id AND sr.stage_id = ps.current_stage_id
            WHERE u.role = 'trainee' AND ps.current_stage_id IN (5, 6) AND sr.id IS NULL
            GROUP BY u.id, u.full_name_ar, u.email, ps.current_stage_id, c.title_ar, c.title
            ORDER BY ps.current_stage_id, u.full_name_ar
        """)
        return cursor.fetchall() or []
    finally:
        cursor.close()
        db.close()


@router.get("/committee-members")
async def list_committee_members(coordinator: dict = Depends(require_coordinator)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, full_name_ar, full_name_en, email FROM users WHERE role = 'committee_member'")
        return cursor.fetchall() or []
    finally:
        cursor.close()
        db.close()


@router.post("/assign")
async def assign_interview(request: AssignRequest, coordinator: dict = Depends(require_coordinator)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # UPSERT logic using ON DUPLICATE KEY UPDATE to allow reassignment or status reset
        cursor.execute("""
            INSERT INTO interview_assignments (trainee_id, stage_id, reviewer_id, course_id, assigned_by, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            ON DUPLICATE KEY UPDATE
            status = 'pending', assigned_at = CURRENT_TIMESTAMP, assigned_by = VALUES(assigned_by)
        """, (request.trainee_id, request.stage_id, request.reviewer_id, request.course_id, coordinator["id"]))
        db.commit()
        return {"status": "success", "message": "Assignment created/updated"}
    finally:
        cursor.close()
        db.close()


@router.delete("/assign/{trainee_id}/{stage_id}/{reviewer_id}")
async def remove_assignment(trainee_id: int, stage_id: int, reviewer_id: int, coordinator: dict = Depends(require_coordinator)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE interview_assignments SET status = 'cancelled' WHERE trainee_id = %s AND stage_id = %s AND reviewer_id = %s",
            (trainee_id, stage_id, reviewer_id)
        )
        db.commit()
        return {"status": "success", "message": "Assignment cancelled"}
    finally:
        cursor.close()
        db.close()
