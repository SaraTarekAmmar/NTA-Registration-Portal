"""
signup.py
=========
4-step public trainee registration for the front page.
Stores records in `front_signups` — completely independent of
the registration done in trainee/trainer portals.
"""
from fastapi import APIRouter, HTTPException, Request
from schemas.signup import SignupCreate, SignupResponse
from core.database import get_db_connection
from core.logger_util import log_activity
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

router = APIRouter(prefix="/api/signup", tags=["Front Signup"])


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
            """INSERT INTO users (national_id, full_name_ar, phone, email, password_hash, role)
               VALUES (%s, %s, %s, %s, %s, 'trainee')""",
            (body.national_id, body.full_name, body.phone, body.email, hashed_pw)
        )
        user_id = cursor.lastrowid
        
        # Insert stub into trainee_profiles
        cursor.execute(
            """INSERT INTO trainee_profiles (user_id) VALUES (%s)""",
            (user_id,)
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
