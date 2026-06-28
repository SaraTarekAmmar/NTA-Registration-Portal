from fastapi import APIRouter, Depends, Query
from typing import Optional
from core.auth import get_current_user
from core.database import get_db_connection
from schemas.notifications import (
    NotificationResponse,
    NotificationListResponse,
    MarkReadRequest,
    ApplicantStatusResponse,
    StatusHistoryItem,
    ApplicationStatusDetailResponse,
)

router = APIRouter(prefix="/api/notifications")


# ── Notifications ──────────────────────────────────────────────────────────────


def _map_notification(row: dict) -> dict:
    return {
        "id": row["id"],
        "titleAr": row["title_ar"],
        "messageAr": row["message_ar"],
        "notificationType": row["notification_type"],
        "relatedApplicationId": row["related_application_id"],
        "relatedStage": row["related_stage"],
        "isRead": bool(row["is_read"]),
        "readAt": row["read_at"],
        "createdAt": row["created_at"],
    }


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    current_user: dict = Depends(get_current_user),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Return paginated notifications for the current user."""
    user_id = current_user["id"]
    offset = (page - 1) * page_size
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Unread count (required by schema)
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = %s AND is_read = 0",
        (user_id,),
    )
    unread_count = cursor.fetchone()["cnt"]

    # Total count
    count_query = "SELECT COUNT(*) as total FROM notifications WHERE user_id = %s"
    params_count = [user_id]
    if is_read is not None:
        count_query += " AND is_read = %s"
        params_count.append(int(is_read))
    cursor.execute(count_query, params_count)
    total = cursor.fetchone()["total"]

    # Fetch page
    query = """
        SELECT id, title_ar, message_ar, notification_type,
               related_application_id, related_stage, is_read,
               read_at, created_at
        FROM notifications
        WHERE user_id = %s
    """
    params = [user_id]
    if is_read is not None:
        query += " AND is_read = %s"
        params.append(int(is_read))
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params += [page_size, offset]

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        "notifications": [_map_notification(r) for r in rows],
        "unreadCount": unread_count,
        "total": total,
    }


@router.post("/read")
def mark_notifications_read(
    body: MarkReadRequest,
    current_user: dict = Depends(get_current_user),
):
    """Mark one or more notifications as read."""
    user_id = current_user["id"]
    ids = body.notificationIds
    if not ids:
        return {"message": "No notifications to mark", "updated": 0}

    conn = get_db_connection()
    cursor = conn.cursor()

    placeholders = ", ".join(["%s"] * len(ids))
    cursor.execute(
        f"""
        UPDATE notifications
        SET is_read = 1, read_at = NOW()
        WHERE id IN ({placeholders}) AND user_id = %s AND is_read = 0
        """,
        ids + [user_id],
    )
    updated = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": f"{updated} notification(s) marked as read", "updated": updated}


@router.post("/read-all")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all unread notifications as read."""
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE notifications SET is_read = 1, read_at = NOW() "
        "WHERE user_id = %s AND is_read = 0",
        (user_id,),
    )
    updated = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": f"{updated} notification(s) marked as read", "updated": updated}


# ── Applicant Status ──────────────────────────────────────────────────────────


@router.get("/applicant-status", response_model=ApplicantStatusResponse)
def get_applicant_status(
    current_user: dict = Depends(get_current_user),
):
    """Return the applicant's current admission status."""
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT ap.id, ap.application_id, ap.current_stage, ap.overall_status,
               ap.status_notes, ap.last_updated_at, ap.created_at
        FROM applicant_status ap
        JOIN applications a ON a.id = ap.application_id
        WHERE a.user_id = %s
        ORDER BY ap.created_at DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return {
            "id": 0,
            "applicationId": 0,
            "currentStage": "",
            "overallStatus": "",
            "statusNotes": None,
            "lastUpdatedAt": None,
            "createdAt": None,
        }

    return {
        "id": row["id"],
        "applicationId": row["application_id"],
        "currentStage": row["current_stage"],
        "overallStatus": row["overall_status"],
        "statusNotes": row["status_notes"],
        "lastUpdatedAt": row["last_updated_at"],
        "createdAt": row["created_at"],
    }


@router.get(
    "/applicant-status/{application_id}", response_model=ApplicationStatusDetailResponse
)
def get_application_status_detail(
    application_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Return detailed status for a specific application."""
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verify ownership
    cursor.execute(
        "SELECT id, course_id FROM applications WHERE id = %s AND user_id = %s",
        (application_id, user_id),
    )
    app_row = cursor.fetchone()
    if not app_row:
        cursor.close()
        conn.close()
        return {"detail": "Application not found"}

    # Get course name
    cursor.execute(
        "SELECT course_name FROM courses WHERE id = %s",
        (app_row["course_id"],),
    )
    course = cursor.fetchone()
    course_name = course["course_name"] if course else ""

    # Get applicant_status
    cursor.execute(
        """
        SELECT current_stage, overall_status, status_notes,
               last_updated_at, created_at
        FROM applicant_status
        WHERE application_id = %s
        """,
        (application_id,),
    )
    status = cursor.fetchone()

    # Get stage history
    cursor.execute(
        """
        SELECT stage, status, notes, decided_at
        FROM admissions_stage_log
        WHERE application_id = %s
        ORDER BY decided_at ASC
        """,
        (application_id,),
    )
    history_rows = cursor.fetchall()
    cursor.close()
    conn.close()

    stages = [
        {
            "stageName": r["stage"],
            "stageStatus": r["status"],
            "reviewDate": r["decided_at"],
            "reviewerNotes": r["notes"],
        }
        for r in history_rows
    ]

    if not status:
        return {
            "applicationId": application_id,
            "courseName": course_name,
            "currentStage": "",
            "overallStatus": "",
            "statusNotes": None,
            "stages": stages,
            "lastUpdatedAt": None,
        }

    return {
        "applicationId": application_id,
        "courseName": course_name,
        "currentStage": status["current_stage"],
        "overallStatus": status["overall_status"],
        "statusNotes": status["status_notes"],
        "stages": stages,
        "lastUpdatedAt": status["last_updated_at"],
    }
