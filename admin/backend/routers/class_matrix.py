from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Any, Optional
from core.database import get_db_connection
from core.auth import get_staff_user
import json
import os
import sys
import threading
from pathlib import Path

# Add AI Services to path to import MatrixGenerator
ROOT = Path(__file__).resolve().parent.parent.parent.parent
AI_SERVICE_PATH = ROOT / "AI Services" / "Class Trainer Matrix"

if str(AI_SERVICE_PATH) not in sys.path:
    sys.path.append(str(AI_SERVICE_PATH))

try:
    from matrix_generator import MatrixGenerator
except ImportError:
    MatrixGenerator = None

router = APIRouter(prefix="/api/admin/class-matrix", tags=["Class Matrix"])

# --- In-memory job tracker (per course_id) ---
# States: "idle" | "processing" | "done" | "error"
MATRIX_JOBS: Dict[int, Dict] = {}


@router.post("/generate/{course_id}")
async def generate_matrix(req: Request, course_id: int):
    """
    Kicks off the AI matrix generation in a background thread and returns immediately.
    The caller can poll /status/{course_id} to track progress.
    """
    if not MatrixGenerator:
        raise HTTPException(
            status_code=501,
            detail="AI Class Matrix Service is not available. Please ensure that the 'AI Services/Class Trainer Matrix' directory is correctly deployed on the server."
        )

    # Auth: staff token OR internal localhost call
    is_internal = req.client.host in ["127.0.0.1", "localhost", "::1"]

    staff = None
    auth_header = req.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from core.auth import get_current_user
            token = auth_header.split(" ")[1]
            user = get_current_user(token)
            if user["role"] in ["admin", "editor"]:
                staff = user
        except Exception:
            # BUG 14 FIX: bare 'except' also catches SystemExit/KeyboardInterrupt.
            # Using 'except Exception' limits the catch to application-level errors only,
            # preventing a non-auth exception from silently allowing localhost bypass.
            pass

    if not staff and not is_internal:
        raise HTTPException(status_code=401, detail="Unauthorized - Admin access required")

    # If already running for this course, return status
    job = MATRIX_JOBS.get(course_id, {})
    if job.get("status") == "processing":
        return {
            "status": "processing",
            "message": "Matrix generation is already running for this course.",
            "course_id": course_id
        }

    # Mark as processing
    MATRIX_JOBS[course_id] = {"status": "processing", "result": None, "error": None}

    def run_generation():
        try:
            generator = MatrixGenerator()
            result = generator.generate_matrix(course_id)
            if result.get("success"):
                MATRIX_JOBS[course_id] = {"status": "done", "result": result, "error": None}
            else:
                MATRIX_JOBS[course_id] = {
                    "status": "error",
                    "result": None,
                    "error": result.get("error", "Unknown AI error")
                }
        except Exception as e:
            MATRIX_JOBS[course_id] = {"status": "error", "result": None, "error": str(e)}

    thread = threading.Thread(target=run_generation, daemon=True)
    thread.start()

    return {
        "status": "processing",
        "message": "Matrix generation started in background. Poll /status/{course_id} for updates.",
        "course_id": course_id
    }


@router.get("/status/{course_id}")
async def get_matrix_status(req: Request, course_id: int):
    """Returns the current generation status for a course matrix job."""
    is_internal = req.client.host in ["127.0.0.1", "localhost", "::1"]
    auth_header = req.headers.get("Authorization")
    staff = None
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from core.auth import get_current_user
            token = auth_header.split(" ")[1]
            user = get_current_user(token)
            if user["role"] in ["admin", "editor"]:
                staff = user
        except Exception:
            # Token is invalid or expired — staff stays None.
            pass

    if not staff and not is_internal:
        raise HTTPException(status_code=401, detail="Unauthorized")

    job = MATRIX_JOBS.get(course_id)
    if not job:
        return {"status": "idle", "course_id": course_id}

    return {
        "status": job["status"],
        "course_id": course_id,
        "result": job.get("result"),
        "error": job.get("error")
    }


@router.get("/summary/{course_id}")
async def get_matrix_summary(course_id: int, staff: dict = Depends(get_staff_user)):
    """Returns summarized data for the main dashboard table."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT cms.*, u.full_name_ar as trainer_name, c.title as course_name
            FROM class_matrix_summary cms
            JOIN users u ON cms.trainer_id = u.id
            JOIN courses c ON cms.course_id = c.id
            WHERE cms.course_id = %s
        """, (course_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()

@router.get("/details/{course_id}/{trainer_id}")
async def get_matrix_details(course_id: int, trainer_id: int, staff: dict = Depends(get_staff_user)):
    """Returns detailed assignments for a specific trainer."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT trainer_strengths, trainer_weaknesses, trainer_reason, trainer_id, u.full_name_ar as trainer_name
            FROM class_matrix_recommendations cmr
            JOIN users u ON cmr.trainer_id = u.id
            WHERE cmr.course_id = %s AND cmr.trainer_id = %s
            LIMIT 1
        """, (course_id, trainer_id))
        trainer_info = cursor.fetchone()

        if trainer_info:
            trainer_info['trainer_analysis'] = {
                "strengths": trainer_info.pop("trainer_strengths", ""),
                "weaknesses": trainer_info.pop("trainer_weaknesses", ""),
                "reason": trainer_info.pop("trainer_reason", "")
            }

        cursor.execute("""
            SELECT cmr.trainee_id, trainee_strengths, trainee_weaknesses, trainee_reason, trainee_confidence_score, u.full_name_ar as trainee_name
            FROM class_matrix_recommendations cmr
            JOIN users u ON cmr.trainee_id = u.id
            WHERE cmr.course_id = %s AND cmr.trainer_id = %s
        """, (course_id, trainer_id))
        trainees = cursor.fetchall()

        for t in trainees:
            t['trainee_analysis'] = {
                "strengths": t.pop("trainee_strengths", ""),
                "weaknesses": t.pop("trainee_weaknesses", ""),
                "reason": t.pop("trainee_reason", ""),
                "confidence_score": t.pop("trainee_confidence_score", 50)
            }

        return {
            "trainer": trainer_info,
            "trainees": trainees
        }
    finally:
        cursor.close()
        db.close()
