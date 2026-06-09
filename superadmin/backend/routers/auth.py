from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from core.database import get_db_connection
from core.security import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, full_name_ar, password_hash, role FROM users WHERE email = %s AND role = 'superadmin'", (request.email,))
        user = cursor.fetchone()
        
        if not user or not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # ── NEW: Record Session ──
        session_id = None
        try:
            cursor.execute("INSERT INTO login_sessions (user_id, role) VALUES (%s, %s)", (user["id"], user["role"]))
            db.commit()
            session_id = cursor.lastrowid
        except Exception as e:
            print(f"FAILED TO RECORD SESSION: {e}")

        token = create_access_token(data={
            "sub": str(user["id"]), 
            "role": user["role"],
            "sid": session_id
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user["role"],
            "fullName": user["full_name_ar"]
        }
    finally:
        cursor.close()
        db.close()
