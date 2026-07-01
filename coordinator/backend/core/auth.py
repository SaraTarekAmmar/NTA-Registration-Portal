from fastapi import HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY in ("your-secret-key", "super-secret-key-for-ai-proxy", "changeme"):
    raise RuntimeError(
        "SECRET_KEY is missing or set to a known default value. Set a strong, "
        "unique SECRET_KEY in the backend .env file before starting the server."
    )
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/coordinator/auth/login")


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
        return {
            "id": int(user_id),
            "role": role,
            "national_id": national_id,
            "session_id": session_id,
        }
    except JWTError:
        raise credentials_exception


def require_coordinator(current_user: dict = Depends(get_current_user)):
    """Strict coordinator-only guard. Returns 403 for any other role."""
    if current_user["role"] != "coordinator":
        raise HTTPException(
            status_code=403,
            detail="صلاحيات غير كافية — للمنسقين فقط",
        )
    return current_user


def require_coordinator_or_member(current_user: dict = Depends(get_current_user)):
    """Allows either coordinator or committee_member roles."""
    if current_user["role"] not in ("coordinator", "committee_member"):
        raise HTTPException(
            status_code=403,
            detail="صلاحيات غير كافية — للمنسقين وأعضاء اللجنة فقط",
        )
    return current_user


# Rate limiting — same pattern as admin/editor
MAX_FAILED_ATTEMPTS = 5
BLOCK_WINDOW_MINUTES = 15


def check_rate_limit(cursor, ip_address, email):
    cursor.execute(
        """SELECT COUNT(*) AS failed_count FROM login_attempts
           WHERE ip_address = %s AND is_successful = FALSE
           AND attempt_time > NOW() - INTERVAL %s MINUTE""",
        (ip_address, BLOCK_WINDOW_MINUTES),
    )
    result = cursor.fetchone()
    cnt = result["failed_count"] if isinstance(result, dict) else result[0]
    return cnt < MAX_FAILED_ATTEMPTS


def record_login_attempt(cursor, ip_address, email, role, is_successful):
    cursor.execute(
        "INSERT INTO login_attempts (ip_address, email, role, is_successful) VALUES (%s, %s, %s, %s)",
        (ip_address, email, role, is_successful),
    )
