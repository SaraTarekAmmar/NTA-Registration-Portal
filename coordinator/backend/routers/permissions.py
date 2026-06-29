"""
Coordinator Permissions (Excuses) API — migrated from admin/backend/routers/permissions.py.
All endpoints require coordinator role. Returns 403 for admin/editor tokens.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from schemas.permission import PermissionUpdate
from core.auth import require_coordinator
from core.database import get_db_connection

router = APIRouter(prefix="/api/coordinator/permissions", tags=["Coordinator Permissions"])


@router.get("")
async def list_permissions(
    status: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    coordinator: dict = Depends(require_coordinator),
):
    """List all permission/excuse requests with optional filters."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT p.*, u.full_name_ar AS studentName, u.national_id AS studentNationalId,
                   c.title AS courseName, c.title_ar AS courseNameAr
            FROM attendance_permissions p
            JOIN users u ON p.user_id = u.id
            JOIN courses c ON p.course_id = c.id
        """
        conditions = []
        params = []

        if status:
            conditions.append("p.status = %s")
            params.append(status)
        if course_id:
            conditions.append("p.course_id = %s")
            params.append(course_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        return cursor.fetchall() or []
    finally:
        cursor.close()
        db.close()


@router.get("/summary")
async def permissions_summary(coordinator: dict = Depends(require_coordinator)):
    """Aggregate counts for dashboard KPIs."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) AS accepted,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected
            FROM attendance_permissions
        """)
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()


@router.put("/{permission_id}")
async def update_permission(
    permission_id: int,
    update: PermissionUpdate,
    coordinator: dict = Depends(require_coordinator),
):
    """Approve or reject a permission request."""
    if update.status not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="الحالة يجب أن تكون 'accepted' أو 'rejected'")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM attendance_permissions WHERE id = %s", (permission_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="الطلب غير موجود")
            
        if existing["status"] != update.status:
            cursor.execute(
                "UPDATE attendance_permissions SET status = %s WHERE id = %s",
                (update.status, permission_id),
            )
            db.commit()
            
            cursor.execute("SELECT * FROM attendance_permissions WHERE id = %s", (permission_id,))
            existing = cursor.fetchone()

        return existing
    finally:
        cursor.close()
        db.close()


@router.get("/courses")
async def list_courses_with_permissions(coordinator: dict = Depends(require_coordinator)):
    """Courses that have at least one permission request (for filter dropdown)."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT DISTINCT c.id, c.title, c.title_ar
            FROM courses c
            JOIN attendance_permissions p ON c.id = p.course_id
            ORDER BY c.title_ar
        """)
        return cursor.fetchall() or []
    finally:
        cursor.close()
        db.close()
