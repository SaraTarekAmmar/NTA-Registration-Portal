from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas.permission import Permission, PermissionCreate, PermissionUpdate
from core.database import get_db_connection
from core.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/permissions", tags=["Permissions"])

@router.post("", response_model=Permission)
async def create_permission(permission: PermissionCreate, current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        query = """INSERT INTO attendance_permissions (user_id, course_id, type, date, reason) 
                   VALUES (%s, %s, %s, %s, %s)"""
        values = (current_user["id"], permission.course_id, permission.type, permission.date, permission.reason)
        cursor.execute(query, values)
        db.commit()
        
        perm_id = cursor.lastrowid

        # BUG 16 FIX: close cursor 1 before reassigning — otherwise the original
        # non-dictionary cursor is leaked and its server-side handle is never released.
        cursor.close()

        # Fetch the newly created record to return
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM attendance_permissions WHERE id = %s", (perm_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()

@router.get("", response_model=List[dict])
async def get_permissions(current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT p.*, u.full_name_ar as studentName, c.title as courseName
            FROM attendance_permissions p
            JOIN users u ON p.user_id = u.id
            JOIN courses c ON p.course_id = c.id
        """
        if current_user["role"] == "admin":
            cursor.execute(query + " ORDER BY p.created_at DESC")
        else:
            cursor.execute(query + " WHERE p.user_id = %s ORDER BY p.created_at DESC", (current_user["id"],))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()

@router.put("/{permission_id}", response_model=Permission)
async def update_permission(permission_id: int, update: PermissionUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="مراجعة الإذونات متاحة للمشرفين فقط")
    
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE attendance_permissions SET status = %s WHERE id = %s", (update.status, permission_id))
        db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="الطلب غير موجود")

        # BUG 16 FIX: close cursor 1 before reassigning.
        cursor.close()

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM attendance_permissions WHERE id = %s", (permission_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()
