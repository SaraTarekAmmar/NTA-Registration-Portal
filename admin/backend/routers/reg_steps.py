from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.auth import get_admin_user, get_current_user
from core.database import get_db_connection

router = APIRouter(prefix="/api/registration-steps", tags=["Registration Steps"])


class StepUpdate(BaseModel):
    is_locked: bool


@router.get("")
async def list_steps(current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM registration_step_settings ORDER BY step_order")
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


@router.put("/{step_key}")
async def update_step(step_key: str, body: StepUpdate, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE registration_step_settings SET is_locked=%s, updated_by=%s WHERE step_key=%s",
            (1 if body.is_locked else 0, admin["id"], step_key),
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Step not found")
        return {"step_key": step_key, "is_locked": body.is_locked}
    finally:
        cursor.close()
        db.close()


@router.get("/locked")
async def get_locked_steps():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT step_key, step_order FROM registration_step_settings WHERE is_locked=1"
        )
        rows = cursor.fetchall()
        return {"locked": [r["step_key"] for r in rows], "locked_orders": [r["step_order"] for r in rows]}
    finally:
        cursor.close()
        db.close()
