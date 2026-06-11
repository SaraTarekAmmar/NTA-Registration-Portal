from fastapi import APIRouter
from core.database import get_db_connection

router = APIRouter(prefix="/api/registration-steps", tags=["Registration Steps"])


@router.get("")
async def list_steps():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT step_key, title_ar, step_order, is_locked FROM registration_step_settings ORDER BY step_order")
        return cursor.fetchall()
    except Exception:
        return []
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
        return {
            "locked": [r["step_key"] for r in rows],
            "locked_orders": [r["step_order"] for r in rows],
        }
    except Exception:
        return {"locked": [], "locked_orders": []}
    finally:
        cursor.close()
        db.close()
