"""
signup.py
=========
4-step public trainee registration for the front page.
Stores records in `front_signups` — completely independent of
the registration done in trainee/trainer portals.
"""
from datetime import date
import json

from fastapi import APIRouter, HTTPException, Request
from passlib.context import CryptContext

from core.database import get_db_connection
from core.logger_util import log_activity
from schemas.signup import SignupCreate, SignupResponse

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

router = APIRouter(prefix="/api/signup", tags=["Front Signup"])


def _derive_profile_basics(national_id: str) -> tuple[date, str]:
    national_id = national_id.strip()
    if len(national_id) != 14 or not national_id.isdigit():
        raise HTTPException(status_code=400, detail="National ID must be 14 digits.")

    century_code = national_id[0]
    if century_code == "2":
        century = 1900
    elif century_code == "3":
        century = 2000
    else:
        raise HTTPException(status_code=400, detail="Unsupported National ID century code.")

    try:
        dob = date(
            century + int(national_id[1:3]),
            int(national_id[3:5]),
            int(national_id[5:7]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="National ID contains an invalid birth date.") from exc

    gender = "male" if int(national_id[12]) % 2 else "female"
    return dob, gender


@router.get("/check/{national_id}")
async def check_national_id(national_id: str):
    """Step 1 validation — check if national_id already registered."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id FROM users WHERE national_id = %s",
            (national_id.strip(),)
        )
        existing = cursor.fetchone()
        return {"available": existing is None}
    finally:
        cursor.close()
        db.close()


@router.post("", response_model=SignupResponse, status_code=201)
async def create_signup(req: Request, body: SignupCreate):
    """Submit a completed 4-step registration."""
    ip = req.client.host if req.client else "unknown"
    dob, gender = _derive_profile_basics(body.national_id)
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Duplicate check in users
        cursor.execute(
            "SELECT id FROM users WHERE national_id = %s",
            (body.national_id,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="This National ID is already registered."
            )

        # Also check email
        if body.email:
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (body.email,)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="This email is already registered."
                )

        # Hash password
        hashed_pw = pwd_context.hash(body.password)

        # Insert into users
        cursor.execute(
            """INSERT INTO users (
                   national_id, full_name_ar, full_name_en, email,
                   dob, gender, marital_status, password_hash, role
               )
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'trainee')""",
            (
                body.national_id,
                body.full_name,
                body.full_name,
                body.email,
                dob,
                gender,
                "single",
                hashed_pw,
            )
        )
        user_id = cursor.lastrowid

        # Seed the trainee profile with the public signup data the main portal expects.
        cursor.execute(
            """INSERT INTO trainee_profiles (user_id, phone_numbers, secondary_email)
               VALUES (%s, %s, %s)""",
            (user_id, json.dumps([body.phone]), body.email)
        )

        # Optional: Keep inserting into front_signups for analytics
        cursor.execute(
            """INSERT INTO front_signups (national_id, full_name, phone, email)
               VALUES (%s, %s, %s, %s)""",
            (body.national_id, body.full_name, body.phone, body.email)
        )
        new_id = cursor.lastrowid

        db.commit()

        cursor.execute("SELECT * FROM front_signups WHERE id = %s", (new_id,))
        row = cursor.fetchone()

        log_activity(
            category="SIGNUP", event_type="FRONT_SIGNUP_CREATED",
            national_id=body.national_id, ip_address=ip,
            user_agent=req.headers.get("user-agent"),
            request_path=req.url.path,
            details={"name": body.full_name, "user_id": user_id}
        )

        return SignupResponse(
            id=row["id"],
            national_id=row["national_id"],
            full_name=row["full_name"],
            phone=row["phone"],
            email=row.get("email"),
            status=row["status"],
            created_at=str(row["created_at"])
        )
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()
