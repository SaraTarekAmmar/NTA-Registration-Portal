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
import json
from schemas.committee import CommitteeScoreSubmit, CommitteeFinalSummarySubmit

@router.get("/committee/assigned-applicants")
async def get_assigned_applicants(
    coord: dict = Depends(require_coordinator)
):
    db = get_db_connection()
    c = db.cursor(dictionary=True)
    try:
        c.execute("""
            SELECT ca.*, cs.status as score_status
            FROM committee_assignments ca
            LEFT JOIN committee_scores cs 
              ON ca.application_id = cs.application_id 
              AND ca.step_id = cs.step_id 
              AND ca.committee_member_id = cs.committee_member_id
            WHERE ca.committee_member_id = %s
        """, (coord.get('sub'),))
        return c.fetchall()
    finally:
        db.close()

@router.post("/committee/submit-score")
async def submit_committee_score(
    payload: CommitteeScoreSubmit,
    coord: dict = Depends(require_coordinator)
):
    db = get_db_connection()
    c = db.cursor(dictionary=True)
    try:
        member_id = coord.get('sub')
        # Check assignment
        c.execute("""
            SELECT * FROM committee_assignments 
            WHERE application_id=%s AND step_id=%s AND committee_member_id=%s
        """, (payload.application_id, payload.step_id, member_id))
        assignment = c.fetchone()
        if not assignment:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="??? ???? ?? ?????? ??? ???????.")
            
        course_id = assignment['course_id']
        committee_id = assignment['committee_id']
        
        # Calculate backend total
        total = sum(payload.criteria_scores_json.values())
        
        c.execute("""
            INSERT INTO committee_scores 
            (application_id, course_id, step_id, committee_id, committee_member_id, criteria_scores_json, total_score, recommendation, notes, status, submitted_at, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Submitted', NOW(), %s)
            ON DUPLICATE KEY UPDATE 
            criteria_scores_json=VALUES(criteria_scores_json), total_score=VALUES(total_score), recommendation=VALUES(recommendation), notes=VALUES(notes), status='Submitted', submitted_at=NOW(), updated_by=%s
        """, (
            payload.application_id, course_id, payload.step_id, committee_id, member_id, 
            json.dumps(payload.criteria_scores_json), total, payload.recommendation, payload.notes, member_id, member_id
        ))
        db.commit()
        return {"message": "?? ??? ??????? ?????", "total": total}
    finally:
        db.close()

@router.get("/committee/committee-summary/{application_id}/{step_id}")
async def get_committee_summary(
    application_id: int, step_id: int,
    coord: dict = Depends(require_coordinator)
):
    db = get_db_connection()
    c = db.cursor(dictionary=True)
    try:
        member_id = coord.get('sub')
        # Check if user is Coordinator for this assignment
        c.execute("""
            SELECT committee_id FROM committee_assignments 
            WHERE application_id=%s AND step_id=%s AND committee_member_id=%s AND role='Coordinator'
        """, (application_id, step_id, member_id))
        assignment = c.fetchone()
        if not assignment:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="??? ?? ???? ???? ?????? ????? ??????.")
            
        committee_id = assignment['committee_id']
        
        c.execute("""
            SELECT * FROM committee_scores 
            WHERE application_id=%s AND step_id=%s AND committee_id=%s
        """, (application_id, step_id, committee_id))
        scores = c.fetchall()
        
        avg_scores = {}
        counts = {}
        total_sum = 0
        for sc in scores:
            if isinstance(sc['criteria_scores_json'], str):
                js = json.loads(sc['criteria_scores_json'])
            else:
                js = sc['criteria_scores_json'] or {}
                
            for k, v in js.items():
                avg_scores[k] = avg_scores.get(k, 0) + float(v)
                counts[k] = counts.get(k, 0) + 1
            if sc['total_score']:
                total_sum += float(sc['total_score'])
                
        for k in avg_scores:
            avg_scores[k] = avg_scores[k] / counts[k]
            
        avg_total = total_sum / len(scores) if scores else 0
        
        return {
            "scores": scores,
            "averages": avg_scores,
            "average_total": avg_total
        }
    finally:
        db.close()

@router.post("/committee/submit-final-summary")
async def submit_final_summary(
    payload: CommitteeFinalSummarySubmit,
    coord: dict = Depends(require_coordinator)
):
    db = get_db_connection()
    c = db.cursor(dictionary=True)
    try:
        member_id = coord.get('sub')
        c.execute("""
            SELECT course_id, committee_id FROM committee_assignments 
            WHERE application_id=%s AND step_id=%s AND committee_member_id=%s AND role='Coordinator'
        """, (payload.application_id, payload.step_id, member_id))
        assignment = c.fetchone()
        if not assignment:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="??? ???? ??.")
            
        c.execute("""
            SELECT * FROM committee_scores 
            WHERE application_id=%s AND step_id=%s AND committee_id=%s
        """, (payload.application_id, payload.step_id, assignment['committee_id']))
        scores = c.fetchall()
        
        total_sum = 0
        avg_scores = {}
        counts = {}
        for sc in scores:
            js = json.loads(sc['criteria_scores_json']) if isinstance(sc['criteria_scores_json'], str) else (sc['criteria_scores_json'] or {})
            for k, v in js.items():
                avg_scores[k] = avg_scores.get(k, 0) + float(v)
                counts[k] = counts.get(k, 0) + 1
            if sc['total_score']:
                total_sum += float(sc['total_score'])
        
        for k in avg_scores:
            avg_scores[k] = avg_scores[k] / counts[k]
        avg_total = total_sum / len(scores) if scores else 0
        
        c.execute("""
            INSERT INTO committee_final_summaries 
            (application_id, course_id, step_id, committee_id, coordinator_id, average_scores_json, final_total_score, final_recommendation, reasons, notes, status, submitted_at, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Finalized', NOW(), %s)
            ON DUPLICATE KEY UPDATE 
            average_scores_json=VALUES(average_scores_json), final_total_score=VALUES(final_total_score), final_recommendation=VALUES(final_recommendation), reasons=VALUES(reasons), notes=VALUES(notes), status='Finalized', submitted_at=NOW(), updated_by=%s
        """, (
            payload.application_id, assignment['course_id'], payload.step_id, assignment['committee_id'], member_id,
            json.dumps(avg_scores), avg_total, payload.final_recommendation, payload.reasons, payload.notes, member_id, member_id
        ))
        db.commit()
        return {"message": "?? ?????? ???? ?????? ???????."}
    finally:
        db.close()
