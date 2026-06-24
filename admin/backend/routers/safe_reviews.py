from fastapi import APIRouter, Depends, HTTPException
from schemas.admin import StageReviewCreate
from core.auth import get_admin_user
from core.database import get_db_connection
from core.upload_manager import move_admission_file_to_folder
from core.logger_util import log_activity
import json

router = APIRouter(prefix="/api/admin", tags=["Admin Safe Reviews"])


@router.post("/stage-review-safe-reject")
async def submit_safe_rejection(review: StageReviewCreate, admin: dict = Depends(get_admin_user)):
    """Record a rejection without deleting the applicant or exposing sensitive reasons.

    This endpoint is used by the admin UI for rejection decisions so security
    and committee audit trails remain intact. Acceptance decisions continue to
    use the original /api/admin/stage-review route.
    """
    if review.result.lower() != "rejected":
        raise HTTPException(status_code=400, detail="This endpoint only handles rejection decisions")

    review.reviewer_id = admin["id"]
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

        applicant_email, applicant_name, applicant_gender, applicant_national_id = applicant

        if review.attachment_path:
            cursor.execute("SELECT national_id FROM users WHERE id = %s", (review.reviewer_id,))
            admin_row = cursor.fetchone()
            if admin_row:
                path_map = move_admission_file_to_folder(
                    applicant_national_id,
                    admin_row[0],
                    [review.attachment_path],
                )
                review.attachment_path = path_map.get(review.attachment_path, review.attachment_path)

        cursor.execute("SELECT full_name_ar FROM users WHERE id = %s", (review.reviewer_id,))
        reviewer_row = cursor.fetchone()
        reviewer_name = reviewer_row[0] if reviewer_row else str(admin.get("id", ""))

        safe_details = dict(review.details or {})
        safe_details["rejected_trainee_national_id"] = applicant_national_id
        safe_details["rejected_trainee_name"] = applicant_name
        safe_details["non_destructive_rejection"] = True
        safe_details["public_result_message"] = "لم يتم قبول الطلب في هذه المرحلة."

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
                review.notes or "",
                review.attachment_path or "",
                json.dumps(safe_details, ensure_ascii=False),
            ),
        )

        cursor.execute(
            "UPDATE pipeline_state SET status = 'rejected' WHERE trainee_id = %s",
            (review.trainee_id,),
        )
        cursor.execute(
            "UPDATE applications SET status = 'rejected' WHERE user_id = %s AND status <> 'approved'",
            (review.trainee_id,),
        )

        log_activity(
            category="ADMIN",
            event_type="APPLICATION_REJECTION_NON_DESTRUCTIVE",
            user_id=admin["id"],
            role=admin["role"],
            details={
                "trainee_id": review.trainee_id,
                "stage_id": review.stage_id,
                "national_id": applicant_national_id,
                "notes_stored_internal_only": bool(review.notes),
            },
        )

        db.commit()
        return {
            "message": "تم تسجيل الرفض مع الاحتفاظ بسجل المتقدم وعدم حذف بياناته.",
            "non_destructive": True,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        cursor.close()
        db.close()
