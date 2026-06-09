from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from core.database import get_db_connection
from core.security import get_current_user, get_password_hash
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

router = APIRouter(prefix="/management", tags=["User Management"])
logger = logging.getLogger(__name__)

# Configuration (Reused from admin/backend/core/notifications.py)
SMTP_HOST = "smtp.sendgrid.net"
SMTP_PORT = 587
SMTP_USER = "apikey"
SMTP_PASS = "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"
SENDER_EMAIL = "noreply@nta.eg"

class UserCreateRequest(BaseModel):
    national_id: str
    full_name: str
    email: EmailStr
    role: str # admin, editor, superadmin

def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def send_management_credentials(email: str, name: str, password: str, role: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"NTA Management Access - {role.upper()}"
        msg["From"] = f"NTA System <{SENDER_EMAIL}>"
        msg["To"] = email

        role_ar = {
            "admin": "مسؤول (Admin)",
            "editor": "محرر (Editor)",
            "superadmin": "مسؤول عام (Super Admin)",
            "trainer": "مدرب (Trainer)"
        }.get(role, role)

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
                    <h2 style="color: #1e293b;">مرحباً {name}،</h2>
                    <p>تم إنشاء حساب لك في نظام الأكاديمية الوطنية للتدريب بالصلاحيات التالية: <strong>{role_ar}</strong>.</p>
                    <p>يمكنك تسجيل الدخول باستخدام البيانات التالية:</p>
                    <div style="background-color: #f1f5f9; padding: 15px; border-radius: 4px;">
                        <p><strong>البريد الإلكتروني:</strong> {email}</p>
                        <p><strong>كلمة المرور:</strong> <span style="font-family: monospace; color: #6366f1;">{password}</span></p>
                    </div>
                    <p style="margin-top: 20px;">يرجى تغيير كلمة المرور فور دخولك للنظام لأول مرة.</p>
                    <p>شكراً لك.</p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

@router.post("/create-user")
async def create_management_user(request: UserCreateRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmins can create management users")
    
    if request.role not in ["admin", "editor", "superadmin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be admin, editor, or superadmin")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Check if email or national_id exists
        cursor.execute("SELECT id FROM users WHERE email = %s OR national_id = %s", (request.email, request.national_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User with this email or national ID already exists")

        temp_password = generate_random_password()
        password_hash = get_password_hash(temp_password)

        query = """
            INSERT INTO users (national_id, full_name_ar, full_name_en, email, password_hash, role, dob, gender, marital_status)
            VALUES (%s, %s, %s, %s, %s, %s, '1990-01-01', 'male', 'Single')
        """
        cursor.execute(query, (request.national_id, request.full_name, request.full_name, request.email, password_hash, request.role))
        db.commit()

        # Send Email
        email_sent = send_management_credentials(request.email, request.full_name, temp_password, request.role)

        return {
            "status": "success",
            "message": "User created successfully",
            "email_sent": email_sent,
            "temp_password": temp_password # Optional: return it in response just in case email fails
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()

@router.get("/users")
async def get_management_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT id, national_id, full_name_ar, full_name_en, email, role, created_at 
            FROM users 
            WHERE role IN ('admin', 'editor', 'superadmin')
            ORDER BY created_at DESC
        """
        cursor.execute(query)
        users = cursor.fetchall()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@router.delete("/users/{user_id}")
async def delete_management_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Check if user exists and is a management user
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user["role"] not in ["admin", "editor", "superadmin"]:
            raise HTTPException(status_code=403, detail="Cannot delete non-management users via this endpoint")

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()
        return {"status": "success", "message": "User deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()
