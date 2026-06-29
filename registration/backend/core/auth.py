from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import JWTError, jwt
from .database import get_db_connection
from .logger_util import log_activity
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


