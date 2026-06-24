"""Coordinator interview operations API.

Adds read-only interview-day endpoints for committee queue, missing evaluation
follow-up, and dashboard KPIs. The endpoints intentionally reuse existing
admission pipeline tables so they work without a new migration.
"""
from fastapi import APIRouter, Depends
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
