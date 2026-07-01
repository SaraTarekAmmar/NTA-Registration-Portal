"""
Shared notification service for the NTA Registration Portal.
Creates notifications when application status changes.
"""

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.database import get_db_connection

STATUS_LABELS = {
    "submitted": "تم تقديم الطلب",
    "under_review": "قيد المراجعة",
    "needs_documents": "يحتاج مستندات",
    "interview": "مقابلة",
    "accepted": "مقبول",
    "rejected": "مرفوض",
    "waitlisted": "في قائمة الانتظار",
    "documents_verified": "تم التحقق من المستندات",
    "initial_review": "المراجعة الأولية",
    "hr_approval": "موافقة الموارد البشرية",
    "final_approval": "الموافقة النهائية",
}


def create_status_notification(
    user_id, old_status, new_status, admin_id=None, notes=None
):
    """
    Create a notification record when an application status changes.

    Args:
        user_id: The applicant's user ID.
        old_status: Previous status value.
        new_status: New status value.
        admin_id: ID of the admin who made the change (optional).
        notes: Optional note to include in the notification.

    Returns:
        dict with the created notification, or None on failure.
    """
    old_label = STATUS_LABELS.get(old_status, old_status or "غير محدد")
    new_label = STATUS_LABELS.get(new_status, new_status)

    if old_status is None or old_status == new_status:
        title = f"تحديث حالة الطلب: {new_label}"
        message = f"تم تحديث حالة طلبك إلى: {new_label}"
    else:
        title = f"تغيير حالة الطلب: {old_label} → {new_label}"
        message = f"تم تغيير حالة طلبك من '{old_label}' إلى '{new_label}'"

    if notes:
        message += f"\nملاحظة: {notes}"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO notifications (user_id, title_ar, message_ar, notification_type, is_read)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, title, message, "status_change", 0),
            )
            conn.commit()
            result = cursor.lastrowid
            if result:
                return {
                    "id": result,
                    "user_id": user_id,
                    "title_ar": title,
                    "message_ar": message,
                }
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Notification service error: {e}")

    return None
