from fastapi import APIRouter, HTTPException, Request
from core.auth import (
    verify_password, create_access_token,
    check_rate_limit, record_login_attempt,
)
from core.database import get_db_connection
from core.logger_util import log_activity
from schemas.auth import CoordinatorLoginRequest

router = APIRouter(prefix="/api/coordinator/auth", tags=["Coordinator Auth"])


@router.post("/login")
async def coordinator_login(req: Request, request: CoordinatorLoginRequest):
    email = request.email.strip()
    national_id = request.nationalId.strip()
    password = request.password

    if not email:
        raise HTTPException(status_code=422, detail="البريد الإلكتروني مطلوب.")
    if not national_id:
        raise HTTPException(status_code=422, detail="الرقم القومي مطلوب.")
    if not password:
        raise HTTPException(status_code=422, detail="كلمة المرور مطلوبة.")

    client_ip = req.client.host if req.client else "unknown"
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if not check_rate_limit(cursor, client_ip, email):
            raise HTTPException(
                status_code=429,
                detail="محاولات فاشلة كثيرة. تم حظر الدخول مؤقتاً لمدة 15 دقيقة.",
            )

        cursor.execute(
            "SELECT id, full_name_ar, email, role, national_id, password_hash "
            "FROM users WHERE email = %s AND role = 'coordinator'",
            (email,),
        )
        user = cursor.fetchone()

        if not user:
            record_login_attempt(cursor, client_ip, email, "coordinator", False)
            db.commit()
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        if user.get("national_id") != national_id:
            record_login_attempt(cursor, client_ip, email, "coordinator", False)
            db.commit()
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        if (
            not password
            or not user.get("password_hash")
            or not verify_password(password, user["password_hash"])
        ):
            record_login_attempt(cursor, client_ip, email, "coordinator", False)
            db.commit()
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        record_login_attempt(cursor, client_ip, email, "coordinator", True)

        session_id = None
        try:
            cursor.execute(
                "INSERT INTO login_sessions (user_id, role) VALUES (%s, %s)",
                (user["id"], user["role"]),
            )
            db.commit()
            session_id = cursor.lastrowid
        except Exception:
            pass

        log_activity(
            category="AUTH",
            event_type="LOGIN_SUCCESS",
            user_id=user["id"],
            national_id=user["national_id"],
            role="coordinator",
            ip_address=client_ip,
            user_agent=req.headers.get("user-agent"),
            request_path=req.url.path,
        )

        access_token = create_access_token(
            data={
                "sub": str(user["id"]),
                "role": user["role"],
                "email": user["email"],
                "name": user["full_name_ar"],
                "national_id": user["national_id"],
                "sid": session_id,
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user["role"],
            "fullName": user["full_name_ar"],
            "userId": user["id"],
        }
    finally:
        cursor.close()
        db.close()
