"""
auth_login.py
=============
Handles trainer/trainee login from the front page.
Verifies credentials against the shared `users` table and returns
a redirect URL so the browser navigates fully to the correct portal.
No JWT is issued here — the target portal manages its own session.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from core.database import get_db_connection
from core.logger_util import log_activity
from passlib.context import CryptContext
import os

router = APIRouter(prefix="/api/auth", tags=["Front Auth"])

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

TRAINEE_URL = os.getenv("TRAINEE_PORTAL_URL", "http://localhost:7771")
TRAINER_URL = os.getenv("TRAINER_PORTAL_URL", "http://localhost:7772")

# Rate-limit constants (mirrors other portals)
MAX_FAILED = 5
BLOCK_MINUTES = 15


class FrontLoginRequest(BaseModel):
    national_id: str
    password:    str
    role:        str  # "trainee" | "trainer"


def _check_rate_limit(cursor, ip: str) -> bool:
    cursor.execute(
        """SELECT COUNT(*) AS cnt FROM login_attempts
           WHERE ip_address = %s AND is_successful = FALSE
           AND attempt_time > NOW() - INTERVAL %s MINUTE""",
        (ip, BLOCK_MINUTES)
    )
    row = cursor.fetchone()
    return not (row and row["cnt"] >= MAX_FAILED)


def _record_attempt(cursor, ip: str, national_id: str, role: str, success: bool):
    cursor.execute(
        """INSERT INTO login_attempts (ip_address, email, role, is_successful)
           VALUES (%s, %s, %s, %s)""",
        (ip, national_id, role, success)
    )


@router.post("/login")
async def front_login(req: Request, body: FrontLoginRequest):
    ip = req.client.host if req.client else "unknown"
    role = body.role.strip().lower()

    if role not in ("trainee", "trainer"):
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'trainee' or 'trainer'.")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Rate limit
        if not _check_rate_limit(cursor, ip):
            raise HTTPException(
                status_code=429,
                detail=f"Too many failed attempts. Please wait {BLOCK_MINUTES} minutes."
            )

        # Look up user
        cursor.execute(
            "SELECT id, national_id, password_hash, role, full_name_ar FROM users WHERE national_id = %s AND role = %s",
            (body.national_id.strip(), role)
        )
        user = cursor.fetchone()

        if not user:
            _record_attempt(cursor, ip, body.national_id, role, False)
            db.commit()
            log_activity(
                category="AUTH", event_type="FRONT_LOGIN_FAILED",
                national_id=body.national_id, role=role, ip_address=ip,
                user_agent=req.headers.get("user-agent"),
                request_path=req.url.path,
                details={"reason": "User not found"}
            )
            raise HTTPException(status_code=401, detail="Incorrect National ID or password.")

        if not pwd_context.verify(body.password, user["password_hash"]):
            _record_attempt(cursor, ip, body.national_id, role, False)
            db.commit()
            log_activity(
                category="AUTH", event_type="FRONT_LOGIN_FAILED",
                national_id=body.national_id, role=role, ip_address=ip,
                user_agent=req.headers.get("user-agent"),
                request_path=req.url.path,
                details={"reason": "Wrong password"}
            )
            raise HTTPException(status_code=401, detail="Incorrect National ID or password.")

        # Success
        _record_attempt(cursor, ip, body.national_id, role, True)
        db.commit()
        log_activity(
            category="AUTH", event_type="FRONT_LOGIN_SUCCESS",
            user_id=user["id"], national_id=user["national_id"],
            role=role, ip_address=ip,
            user_agent=req.headers.get("user-agent"),
            request_path=req.url.path
        )

        redirect_url = TRAINEE_URL if role == "trainee" else TRAINER_URL

        return {
            "redirect_url": redirect_url,
            "role": role,
            "full_name": user.get("full_name_ar", "")
        }

    finally:
        cursor.close()
        db.close()
