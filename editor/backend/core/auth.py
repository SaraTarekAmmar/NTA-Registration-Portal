from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

from .database import get_db_connection
from .logger_util import log_activity

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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

MAX_FAILED_ATTEMPTS = 5
BLOCK_WINDOW_MINUTES = 15


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/editor/auth/login")


def get_current_editor(token: str = Depends(oauth2_scheme)):
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
        session_id = payload.get("sid")
        if user_id is None:
            raise credentials_exception
        return {"id": int(user_id), "role": role, "national_id": national_id, "session_id": session_id}
    except JWTError:
        raise credentials_exception


def require_editor(current_user: dict = Depends(get_current_editor)):
    if current_user["role"] != "editor":
        raise HTTPException(status_code=403, detail="Editor access only")
    return current_user


def check_rate_limit(cursor, ip_address, email):
    cursor.execute(
        """SELECT COUNT(*) as failed_count FROM login_attempts
           WHERE ip_address = %s AND is_successful = FALSE
           AND attempt_time > NOW() - INTERVAL %s MINUTE""",
        (ip_address, BLOCK_WINDOW_MINUTES)
    )
    result = cursor.fetchone()
    return not (result and result["failed_count"] >= MAX_FAILED_ATTEMPTS)


def record_login_attempt(cursor, ip_address, email, role, is_successful):
    cursor.execute(
        "INSERT INTO login_attempts (ip_address, email, role, is_successful) VALUES (%s, %s, %s, %s)",
        (ip_address, email, role, is_successful)
    )
