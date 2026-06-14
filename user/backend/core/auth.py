from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import JWTError, jwt
from schemas.auth import LoginRequest, TokenResponse
from .database import get_db_connection
from .logger_util import log_activity
from .mail_service import send_email_background
import os
import uuid
from passlib.context import CryptContext

# Setup password hashing (using pbkdf2_sha256 for pure-python compatibility on Windows)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
        return {"id": int(user_id), "role": role}
    except JWTError:
        raise credentials_exception

async def get_optional_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            return None
        return {"id": int(user_id), "role": role}
    except JWTError:
        return None

def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="تبلغ الصلاحيات غير كافية - للمشرفين فقط")
    return current_user

def get_staff_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="تبلغ الصلاحيات غير كافية - للمشرفين والمحررين فقط")
    return current_user

MAX_FAILED_ATTEMPTS = 5
BLOCK_WINDOW_MINUTES = 15

def check_rate_limit(cursor, ip_address, email):
    # Check for failed attempts in the last 15 minutes
    query = """
        SELECT COUNT(*) as failed_count 
        FROM login_attempts 
        WHERE ip_address = %s 
        AND is_successful = FALSE 
        AND attempt_time > NOW() - INTERVAL %s MINUTE
    """
    cursor.execute(query, (ip_address, BLOCK_WINDOW_MINUTES))
    result = cursor.fetchone()
    if result and result['failed_count'] >= MAX_FAILED_ATTEMPTS:
        return False
    return True

def record_login_attempt(cursor, ip_address, email, role, is_successful):
    query = """
        INSERT INTO login_attempts (ip_address, email, role, is_successful)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (ip_address, email, role, is_successful))

@router.post("/recover")
async def recover_password(req: Request, body: dict):
    """
    POST /api/auth/recover
    Accepts { email } and sends a password-reset link.
    Always returns a generic success message to prevent user enumeration.
    """
    email = (body.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=422, detail="البريد الإلكتروني مطلوب")

    client_ip = req.client.host if req.client else "unknown"

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, full_name_ar, email FROM users WHERE email = %s AND role IN ('trainee', 'trainer')",
            (email,)
        )
        user = cursor.fetchone()

        if user:
            reset_token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=1)

            # Store the token — create table if it doesn't exist yet
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    used TINYINT(1) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_token (token),
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cursor.execute(
                "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user["id"], reset_token, expires_at)
            )
            db.commit()

            # Build the reset URL — uses the same origin the request came from
            origin = req.headers.get("origin") or req.base_url
            reset_url = f"{origin}/reset-password.html?token={reset_token}"

            html_body = f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head><meta charset="UTF-8"><title>استعادة كلمة المرور</title>
            <style>
                body{{font-family:'Tajawal',Arial,sans-serif;background:#f7f9fc;color:#333;direction:rtl;text-align:right;margin:0;padding:0;}}
                .container{{max-width:600px;margin:30px auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;}}
                .header{{background:#1a2e40;padding:30px;text-align:center;border-bottom:4px solid #d4af37;}}
                .content{{padding:40px 30px;line-height:1.8;}}
                .button{{display:inline-block;background:#1a2e40;color:#fff!important;text-decoration:none;padding:12px 30px;border-radius:30px;font-weight:bold;margin:20px 0;border:1px solid #d4af37;}}
                .footer{{background:#f1f5f9;padding:20px;text-align:center;font-size:12px;color:#64748b;border-top:1px solid #e2e8f0;}}
            </style></head>
            <body><div class="container">
                <div class="header"><h2 style="color:#fff;margin:0;">الأكاديمية الوطنية للتدريب</h2></div>
                <div class="content">
                    <p>مرحباً <strong>{user['full_name_ar']}</strong>،</p>
                    <p>تلقينا طلباً لاستعادة كلمة المرور الخاصة بحسابك. اضغط على الزر أدناه لتعيين كلمة مرور جديدة. ينتهي صلاحية هذا الرابط خلال ساعة واحدة.</p>
                    <div style="text-align:center;"><a href="{reset_url}" class="button">استعادة كلمة المرور</a></div>
                    <p style="font-size:13px;color:#64748b;">إذا لم تطلب استعادة كلمة المرور، يمكنك تجاهل هذا البريد.</p>
                </div>
                <div class="footer">هذا البريد مرسل تلقائياً. يرجى عدم الرد عليه مباشرة.</div>
            </div></body></html>
            """

            send_email_background(
                to_email=user["email"],
                subject="استعادة كلمة المرور - بوابة الأكاديمية الوطنية للتدريب",
                html_body=html_body
            )

            log_activity(
                category="AUTH",
                event_type="PASSWORD_RESET_REQUESTED",
                user_id=user["id"],
                ip_address=client_ip,
                user_agent=req.headers.get("user-agent"),
                request_path=req.url.path,
                details={"email": email}
            )
    finally:
        cursor.close()
        db.close()

    # Always return success to prevent user enumeration
    return {"detail": "تم إرسال رابط الاستعادة إلى بريدك الإلكتروني بنجاح."}


@router.post("/login", response_model=TokenResponse)
async def login(req: Request, request: LoginRequest):
    client_ip = req.client.host if req.client else "unknown"
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Rate Limit Check (Persistent)
        if not check_rate_limit(cursor, client_ip, request.email):
            raise HTTPException(status_code=429, detail=f"محاولات فاشلة كثيرة. تم حظر الدخول مؤقتاً لمدة {BLOCK_WINDOW_MINUTES} دقيقة.")

        email = request.email.strip().lower()
        role = request.role.strip().lower()
        national_id_req = request.nationalId.strip() if request.nationalId else None

        # Check user exists by email and role
        query = "SELECT id, full_name_ar, email, role, national_id, password_hash FROM users WHERE email = %s AND role = %s"
        cursor.execute(query, (email, role))
        user = cursor.fetchone()
        
        if not user:
            record_login_attempt(cursor, client_ip, email, role, False)
            db.commit()
            log_activity(
                category="AUTH",
                event_type="LOGIN_FAILED",
                ip_address=client_ip,
                user_agent=req.headers.get("user-agent"),
                request_path=req.url.path,
                details={"reason": "User not found", "email": email, "role": role}
            )
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
        
        # Validation Logic:
        # 1. Admin/Editor/Superadmin: Password required
        # 2. Trainee/Trainer: Password + National ID required
        
        is_staff = user["role"] in ["admin", "editor", "superadmin"]
        
        if not request.password or not user["password_hash"]:
            record_login_attempt(cursor, client_ip, email, role, False)
            db.commit()
            raise HTTPException(status_code=401, detail="كلمة المرور مطلوبة لهذا الحساب")
        
        if not verify_password(request.password, user["password_hash"]):
            record_login_attempt(cursor, client_ip, email, role, False)
            db.commit()
            log_activity(
                category="AUTH",
                event_type="LOGIN_FAILED",
                user_id=user["id"],
                national_id=user["national_id"],
                role=user["role"],
                ip_address=client_ip,
                user_agent=req.headers.get("user-agent"),
                request_path=req.url.path,
                details={"reason": "Invalid password", "email": email}
            )
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
            
        # For non-staff (Trainees and Trainers), verify National ID
        if not is_staff:
            if national_id_req != user["national_id"]:
                record_login_attempt(cursor, client_ip, email, role, False)
                db.commit()
                log_activity(
                    category="AUTH",
                    event_type="LOGIN_FAILED",
                    user_id=user["id"],
                    national_id=user["national_id"],
                    role=user["role"],
                    ip_address=client_ip,
                    user_agent=req.headers.get("user-agent"),
                    request_path=req.url.path,
                    details={"reason": "Invalid National ID", "email": email, "provided_nid": national_id_req, "actual_nid": user["national_id"]}
                )
                raise HTTPException(status_code=401, detail="رقم الهوية غير صحيح")

        
        # Success
        record_login_attempt(cursor, client_ip, email, role, True)
            
        log_activity(
            category="AUTH",
            event_type="LOGIN_SUCCESS",
            user_id=user["id"],
            national_id=user["national_id"],
            role=user["role"],
            ip_address=client_ip,
            user_agent=req.headers.get("user-agent"),
            request_path=req.url.path
        )
        
        access_token = create_access_token(
            data={"sub": str(user["id"]), "role": user["role"], "email": user["email"]}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user["role"],
            "fullName": user["full_name_ar"],
            "userId": user["id"]
        }
    finally:
        cursor.close()
        db.close()
