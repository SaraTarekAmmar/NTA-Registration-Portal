"""
front_signups.py  (admin portal router)
========================================
Lightweight read + status-change view of front-page public signups.
Accessible only to admins. CSV export included.
"""
import csv, io
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from core.auth import get_current_user, get_admin_user
from core.database import get_db_connection
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin/front-signups", tags=["Admin – Front Signups"])


class StatusUpdate(BaseModel):
    status: str  # pending | approved | rejected


@router.get("")
async def list_front_signups(
    status: str = None,
    current_user: dict = Depends(get_admin_user)
):
    """Return all front-page signups, optionally filtered by status."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if status and status in ("pending", "approved", "rejected"):
            cursor.execute(
                """SELECT id, national_id, full_name, phone, email, status, created_at
                   FROM front_signups WHERE status = %s ORDER BY created_at DESC""",
                (status,)
            )
        else:
            cursor.execute(
                """SELECT id, national_id, full_name, phone, email, status, created_at
                   FROM front_signups ORDER BY created_at DESC"""
            )
        rows = cursor.fetchall()
        for r in rows:
            r["created_at"] = str(r["created_at"])
        return rows
    finally:
        cursor.close(); db.close()


@router.put("/{signup_id}/status")
async def update_signup_status(
    signup_id: int,
    body: StatusUpdate,
    current_user: dict = Depends(get_admin_user)
):
    if body.status not in ("pending", "approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status value.")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM front_signups WHERE id = %s", (signup_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Signup not found.")
        cursor.execute(
            "UPDATE front_signups SET status = %s WHERE id = %s",
            (body.status, signup_id)
        )
        db.commit()
        return {"message": f"Signup #{signup_id} marked as {body.status}."}
    finally:
        cursor.close(); db.close()


@router.get("/export/csv")
async def export_signups_csv(
    status: str = None,
    current_user: dict = Depends(get_admin_user)
):
    """Download all front-page signups as a CSV file."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if status and status in ("pending", "approved", "rejected"):
            cursor.execute(
                "SELECT * FROM front_signups WHERE status = %s ORDER BY created_at DESC",
                (status,)
            )
        else:
            cursor.execute("SELECT * FROM front_signups ORDER BY created_at DESC")
        rows = cursor.fetchall()
    finally:
        cursor.close(); db.close()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id","national_id","full_name","phone","email","status","created_at","updated_at"])
    writer.writeheader()
    for row in rows:
        row["created_at"] = str(row.get("created_at", ""))
        row["updated_at"] = str(row.get("updated_at", ""))
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=front_signups.csv"}
    )
