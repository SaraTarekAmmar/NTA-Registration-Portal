from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel
from schemas.auth import LoginRequest, AdminLoginRequest, TokenResponse
from .database import get_db_connection
from .logger_util import log_activity
import os
from passlib.context import CryptContext

# Setup password hashing (using pbkdf2_sha256 for pure-python compatibility on Windows)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
admin_router = APIRouter(prefix="/api/admin/auth", tags=["Admin Auth"])

# Load environment before reading secrets (independent of main.py import order)
from pathlib import Path as _Path
from dotenv import load_dotenv as _load_dotenv
_load_dotenv(_Path(__file__).resolve().parents[1] / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY in ("your-secret-key", "super-secret-key-for-ai-proxy", "changeme"):
    raise RuntimeError(
        "SECRET_KEY is missing or set to a known default value. Set a strong, "
        "unique SECRET_KEY in the backend .env file before starting the server."
    )
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT. Returns the payload dict, or None on any error."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

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
        national_id: str = payload.get("national_id")
        session_id: int = payload.get("sid")
        if user_id is None:
            raise credentials_exception
        return {"id": int(user_id), "role": role, "national_id": national_id, "session_id": session_id}
    except JWTError:
        raise credentials_exception

def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="تبلغ الصلاحيات غير كافية - للمشرفين فقط")
    return current_user

def get_reviewer_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("admin", "superadmin", "admission_manager", "committee_member"):
        raise HTTPException(status_code=403, detail="صلاحيات غير كافية - للمقيمين والمدراء فقط")
    return current_user

def get_staff_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin", "editor"]:
        raise HTTPException(status_code=403, detail="تبلغ الصلاحيات غير كافية - للمشرفين والمحررين فقط")
    return current_user

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user

def require_editor(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "editor":
        raise HTTPException(status_code=403, detail="Editor access only")
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

@router.post("/login", response_model=TokenResponse)
async def login(req: Request, request: LoginRequest):
    client_ip = req.client.host if req.client else "unknown"
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Rate Limit Check (Persistent)
        if not check_rate_limit(cursor, client_ip, request.email):
            raise HTTPException(status_code=429, detail=f"محاولات فاشلة كثيرة. تم حظر الدخول مؤقتاً لمدة {BLOCK_WINDOW_MINUTES} دقيقة.")

        # Check user exists by email and role
        query = "SELECT id, full_name_ar, email, role, national_id, password_hash FROM users WHERE email = %s AND role = %s"
        cursor.execute(query, (request.email, request.role))
        user = cursor.fetchone()
        
        if not user:
            record_login_attempt(cursor, client_ip, request.email, request.role, False)
            db.commit()
            log_activity(
                category="AUTH",
                event_type="LOGIN_FAILED",
                ip_address=client_ip,
                user_agent=req.headers.get("user-agent"),
                request_path=req.url.path,
                details={"reason": "User not found", "email": request.email, "role": request.role}
            )
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
        
        # Validation Logic:
        # 1. Staff (Admin/Editor) or Trainee with password_hash: MUST verify password
        # 2. Trainee without password_hash: Fallback to national_id (Stage 1-6)
        
        is_authenticated = False
        reason = "Authentication failed"

        if user["role"] in ["admin", "editor"] or user.get("password_hash"):
            if not request.password:
                raise HTTPException(status_code=401, detail="كلمة المرور مطلوبة")
            
            if verify_password(request.password, user["password_hash"]):
                is_authenticated = True
            else:
                reason = "Invalid password"
        else:
            # Stage 1-6 Trainee fallback
            if request.nationalId == user["national_id"]:
                is_authenticated = True
            else:
                reason = "Invalid National ID"

        if not is_authenticated:
            record_login_attempt(cursor, client_ip, request.email, user["role"], False)
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
                details={"reason": reason, "email": request.email}
            )
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
        
        # Success
        record_login_attempt(cursor, client_ip, request.email, user["role"], True)
        
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
        
        # ── NEW: Record Session ──
        session_id = None
        try:
            cursor.execute("INSERT INTO login_sessions (user_id, role) VALUES (%s, %s)", (user["id"], user["role"]))
            db.commit()
            session_id = cursor.lastrowid
        except Exception as e:
            print(f"FAILED TO RECORD SESSION: {e}")

        access_token = create_access_token(
            data={
                "sub": str(user["id"]), 
                "role": user["role"], 
                "email": user["email"],
                "national_id": user["national_id"],
                "sid": session_id # Session ID for logging
            }
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


class StaffLoginRequest(BaseModel):
    email: str
    password: str


async def _role_login(req: Request, email: str, password: str, required_role: str, national_id: str = None):
    client_ip = req.client.host if req.client else "unknown"
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if not check_rate_limit(cursor, client_ip, email):
            raise HTTPException(status_code=429, detail=f"Too many failed attempts. Blocked for {BLOCK_WINDOW_MINUTES} minutes.")

        query = "SELECT id, full_name_ar, email, role, national_id, password_hash FROM users WHERE email = %s AND role = %s"
        cursor.execute(query, (email, required_role))
        user = cursor.fetchone()

        if not user:
            record_login_attempt(cursor, client_ip, email, required_role, False)
            db.commit()
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        if national_id and user.get("national_id") != national_id:
            record_login_attempt(cursor, client_ip, email, required_role, False)
            db.commit()
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        if not password or not user.get("password_hash") or not verify_password(password, user["password_hash"]):
            record_login_attempt(cursor, client_ip, email, required_role, False)
            db.commit()
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

        record_login_attempt(cursor, client_ip, email, required_role, True)

        session_id = None
        try:
            cursor.execute("INSERT INTO login_sessions (user_id, role) VALUES (%s, %s)", (user["id"], user["role"]))
            db.commit()
            session_id = cursor.lastrowid
        except Exception:
            pass

        access_token = create_access_token(data={
            "sub": str(user["id"]),
            "role": user["role"],
            "email": user["email"],
            "national_id": user["national_id"],
            "sid": session_id
        })

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


@admin_router.post("/login")
async def admin_login(req: Request, request: AdminLoginRequest):
    email = request.email.strip()
    national_id = request.nationalId.strip()
    password = request.password
    if not email:
        raise HTTPException(status_code=422, detail="البريد الإلكتروني مطلوب.")
    if not national_id:
        raise HTTPException(status_code=422, detail="الرقم القومي مطلوب.")
    if not password:
        raise HTTPException(status_code=422, detail="كلمة المرور مطلوبة.")
    # Try admin first; if not found, try superadmin (superadmins have full admin access)
    try:
        return await _role_login(req, email, password, "admin", national_id=national_id)
    except HTTPException as exc:
        if exc.status_code == 401:
            return await _role_login(req, email, password, "superadmin", national_id=national_id)
        raise
