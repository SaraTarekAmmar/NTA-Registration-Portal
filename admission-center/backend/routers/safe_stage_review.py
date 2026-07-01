from fastapi import APIRouter, Depends, HTTPException
import json

from schemas.admin import StageReviewCreate
from core.auth import get_admission_manager_user
from core.database import get_db_connection
from core.logger_util import log_activity
from core.notifications import send_rejection_email
from routers import admission as legacy_admission

router = APIRouter(prefix="/api/admission", tags=["Safe Admission Reviews"])

PUBLIC_REJECTION_MESSAGE = "لم يتم قبول الطلب في هذه المرحلة."


def _is_rejection(result: str) -> bool:
    return str(result or "").strip().lower() in {"rejected", "reject", "failed", "fail"}


@router.post("/stage-review")
async def submit_stage_review_safely(
    review: StageReviewCreate,
    admin: dict = Depends(get_admission_manager_user),
):
    """Safe wrapper for stage review decisions.

    Approval/active decisions keep using the existing implementation.
    Rejections are handled here so the applicant record, uploaded files, and
    audit trail remain intact, and the public message never exposes internal
    security or committee notes.
    """
    if not _is_rejection(review.result):
        return await legacy_admission.submit_review(review, admin)

    db = get_db_connection()
    cursor = db.cursor(buffered=True)
    try:
        cursor.execute(
            "SELECT email, full_name_ar, gender, national_id FROM users WHERE id = %s",
            (review.trainee_id,),
        )
        applicant = cursor.fetchone()
        if not applicant:
            raise HTTPException(status_code=404, detail="Applicant not found")

        email, full_name, gender, national_id = applicant

        cursor.execute(
            "SELECT full_name_ar FROM users WHERE id = %s",
            (review.reviewer_id,),
        )
        reviewer_row = cursor.fetchone()
        reviewer_name = reviewer_row[0] if reviewer_row else str(admin.get("id", ""))

        details = dict(review.details or {})
        details.update({
            "silent_rejection": True,
            "internal_notes": review.notes or "",
            "rejected_trainee_national_id": national_id,
            "rejected_trainee_name": full_name,
        })

        cursor.execute(
            """
            INSERT INTO stage_reviews
                (trainee_id, reviewer_id, stage_id, result,
                 reviewer_name, review_date,
                 notes, attachment_path, details, created_at)
            VALUES (%s, %s, %s, 'Rejected', %s, CURDATE(), %s, %s, %s, NOW())
            """,
            (
                review.trainee_id,
                review.reviewer_id,
                review.stage_id,
                reviewer_name,
                PUBLIC_REJECTION_MESSAGE,
                review.attachment_path or "",
                json.dumps(details, ensure_ascii=False),
            ),
        )

        cursor.execute(
            "UPDATE pipeline_state SET status = 'rejected' WHERE trainee_id = %s",
            (review.trainee_id,),
        )
        cursor.execute(
            """
            UPDATE applications
            SET status = 'rejected'
            WHERE user_id = %s AND status <> 'approved'
            """,
            (review.trainee_id,),
        )

        send_rejection_email(email, full_name, PUBLIC_REJECTION_MESSAGE, gender)

        log_activity(
            category="ADMIN",
            event_type="APPLICATION_REJECTION_SILENT",
            user_id=admin.get("id"),
            role=admin.get("role"),
            details={
                "trainee_id": review.trainee_id,
                "stage_id": review.stage_id,
                "silent_rejection": True,
            },
        )

        db.commit()
        return {
            "message": "Review submitted successfully",
            "non_destructive": True,
            "silent_rejection": True,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not submit stage review")
    finally:
        cursor.close()
        db.close()
