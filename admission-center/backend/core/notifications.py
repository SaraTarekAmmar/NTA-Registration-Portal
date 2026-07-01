import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configuration — all values loaded from environment variables (.env).
# BUG 19 FIX: SMTP_HOST, SMTP_PORT, and SMTP_USER were previously hardcoded,
# making provider changes require a code edit. They now fall back to SendGrid
# defaults so existing deployments continue to work without any .env changes.
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "apikey")
SMTP_PASS     = os.getenv("SENDGRID_API_KEY", "")
SENDER_EMAIL  = os.getenv("SENDER_EMAIL", "noreply@nta.eg")

# Portal URLs — set in .env for production deployments
# Each role logs in through its own isolated portal:
#   trainee/applicant → TRAINEE_PORTAL_URL (port 7771)
#   trainer           → TRAINER_PORTAL_URL (port 7772)
#   admin             → http://localhost:8002
#   editor            → http://localhost:8001
TRAINEE_PORTAL_URL = os.getenv("TRAINEE_PORTAL_URL", os.getenv("USER_PORTAL_URL", "http://localhost:7771"))
TRAINER_PORTAL_URL = os.getenv("TRAINER_PORTAL_URL", "http://localhost:7772")

logger = logging.getLogger(__name__)

def send_credential_email(recipient_email: str, full_name: str, temp_password: str, gender: str = "male", role: str = "trainee"):
    """
    Sends an email with login credentials to the admitted user.
    Role is used to determine which portal URL to include in the email.
    - trainee / applicant → TRAINEE_PORTAL_URL (localhost:7771 / reg.nta.eg)
    - trainer             → TRAINER_PORTAL_URL (localhost:7772)
    """
    try:
        greeting = "عزيزي" if gender == "male" else "عزيزتي"
        congrats_msg = "تهانينا! تم قبولك في البرنامج بنجاح" if gender == "male" else "تهانينا! تم قبولكِ في البرنامج بنجاح"

        # Determine the correct portal URL for this role
        if role == "trainer":
            portal_url = TRAINER_PORTAL_URL
            portal_label = "بوابة المدربين"
        else:  # trainee / applicant / default
            portal_url = TRAINEE_PORTAL_URL
            portal_label = "بوابة المتدربين"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to NTA - Your Login Credentials"
        msg["From"] = f"NTA Admission <{SENDER_EMAIL}>"
        msg["To"] = recipient_email

        html_content = f"""
        <html>
            <body style="font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 30px; text-align: center; color: #ffffff;">
                        <h1 style="margin: 0; font-size: 24px;">الأكاديمية الوطنية للتدريب</h1>
                        <p style="margin: 10px 0 0; opacity: 0.8;">{congrats_msg}</p>
                    </div>
                    <div style="padding: 40px; color: #334155;">
                        <h2 style="color: #1e293b; margin-top: 0;">{greeting} {full_name}،</h2>
                        <p style="line-height: 1.6;">يسعدنا إبلاغك بأنه قد تم قبولك نهائياً في البرنامج التدريبي. يمكنك الآن تسجيل الدخول إلى بوابة المتدربين باستخدام البيانات التالية:</p>
                        
                        <div style="background-color: #f1f5f9; padding: 20px; border-radius: 8px; margin: 30px 0; border-right: 4px solid #6366f1;">
                            <p style="margin: 0 0 10px;"><strong>البريد الإلكتروني:</strong> {recipient_email}</p>
                            <p style="margin: 0;"><strong>كلمة المرور:</strong> <span style="font-family: monospace; color: #6366f1; font-size: 1.2em;">{temp_password}</span></p>
                        </div>
                        
                        <p style="color: #64748b; font-size: 0.9em;">* يرجى الاحتفاظ ببيانات الدخول هذه في مكان آمن.</p>
                        
                        <div style="text-align: center; margin-top: 40px;">
                            <a href="{portal_url}" style="background-color: #6366f1; color: #ffffff; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">{portal_label}</a>
                        </div>
                    </div>
                    <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 0.8em; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                        جميع الحقوق محفوظة &copy; 2026 الأكاديمية الوطنية للتدريب
                    </div>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            
        logger.info(f"Credential email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False

def send_stage4_exam_email(recipient_email: str, full_name: str, gender: str = "male"):
    """
    Sends an email with links to the 3 standardized exams for Stage 4.
    """
    try:
        greeting = "عزيزي" if gender == "male" else "عزيزتي"
        
        # Base URL for the trainee-facing portal
        # Set USER_PORTAL_URL or TRAINEE_PORTAL_URL in .env for production (e.g. https://reg.nta.eg)
        # Stage 4 exams are always taken by trainees/applicants — always use trainee portal
        portal_url = TRAINEE_PORTAL_URL
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "NTA Admission - Stage 4 Standardized Exams"
        msg["From"] = f"NTA Admission <{SENDER_EMAIL}>"
        msg["To"] = recipient_email

        html_content = f"""
        <html>
            <body style="font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 30px; text-align: center; color: #ffffff;">
                        <h1 style="margin: 0; font-size: 24px;">الأكاديمية الوطنية للتدريب</h1>
                        <p style="margin: 10px 0 0; opacity: 0.8;">المرحلة الرابعة: اختبارات اللغة والمعلومات العامة</p>
                    </div>
                    <div style="padding: 40px; color: #334155;">
                        <h2 style="color: #1e293b; margin-top: 0;">{greeting} {full_name}،</h2>
                        <p style="line-height: 1.6;">لقد اجتزت المراحل السابقة بنجاح. كجزء من عملية التقييم في المرحلة الرابعة، يرجى أداء الاختبارات التالية عبر الروابط الموضحة أدناه:</p>
                        
                        <div style="margin: 30px 0;">
                            <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-right: 4px solid #6366f1; display: flex; justify-content: space-between; align-items: center;">
                                <span><strong>1. اختبار اللغة العربية</strong></span>
                                <a href="{portal_url}/stage%204%20exams.html?subject=arabic" style="background-color: #6366f1; color: #ffffff; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 0.9em;">بدء الاختبار</a>
                            </div>
                            
                            <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-right: 4px solid #3b82f6; display: flex; justify-content: space-between; align-items: center;">
                                <span><strong>2. اختبار اللغة الإنجليزية</strong></span>
                                <a href="{portal_url}/stage%204%20exams.html?subject=english" style="background-color: #3b82f6; color: #ffffff; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 0.9em;">بدء الاختبار</a>
                            </div>
                            
                            <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-right: 4px solid #10b981; display: flex; justify-content: space-between; align-items: center;">
                                <span><strong>3. اختبار المعلومات العامة</strong></span>
                                <a href="{portal_url}/stage%204%20exams.html?subject=public_knowledge" style="background-color: #10b981; color: #ffffff; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 0.9em;">بدء الاختبار</a>
                            </div>
                        </div>
                        
                        <p style="color: #64748b; font-size: 0.9em;">* يرجى العلم أن لكل اختبار وقتاً محدداً يبدأ بمجرد فتح الرابط.</p>
                        <p style="color: #64748b; font-size: 0.9em;">* يجب إتمام الاختبارات في غضون 48 ساعة من استلام هذا البريد.</p>
                    </div>
                    <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 0.8em; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                        جميع الحقوق محفوظة &copy; 2026 الأكاديمية الوطنية للتدريب
                    </div>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            
        logger.info(f"Stage 4 exam invitation sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send exam email to {recipient_email}: {str(e)}")
        return False

def send_rejection_email(recipient_email: str, full_name: str, reason: str, gender: str = "male"):
    """
    Sends an email to the applicant informing them of their rejection and the reason.
    """
    try:
        greeting = "عزيزي" if gender == "male" else "عزيزتي"
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "NTA Admission Status Update - Rejection"
        msg["From"] = f"NTA Admission <{SENDER_EMAIL}>"
        msg["To"] = recipient_email

        html_content = f"""
        <html>
            <body style="font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <div style="background: linear-gradient(135deg, #475569, #1e293b); padding: 30px; text-align: center; color: #ffffff;">
                        <h1 style="margin: 0; font-size: 24px;">الأكاديمية الوطنية للتدريب</h1>
                        <p style="margin: 10px 0 0; opacity: 0.8;">تحديث بخصوص حالة طلب الانضمام</p>
                    </div>
                    <div style="padding: 40px; color: #334155;">
                        <h2 style="color: #1e293b; margin-top: 0;">{greeting} {full_name}،</h2>
                        <p style="line-height: 1.6;">نشكرك على اهتمامك بالانضمام إلى برامجنا التدريبية. نود إفادتك بأنه بعد مراجعة طلبك في المرحلة الحالية، يؤسفنا إبلاغك بعدم إمكانية الاستمرار في عملية الاختيار لهذه الدورة.</p>
                        
                        <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 30px 0; border-right: 4px solid #ef4444;">
                            <p style="margin: 0 0 10px; color: #991b1b;"><strong>سبب الرفض:</strong></p>
                            <p style="margin: 0; color: #334155;">{reason}</p>
                        </div>
                        
                        <p style="line-height: 1.6;">يمكنك مراجعة بياناتك وإعادة التقديم مرة أخرى في الدورات القادمة بمجرد تصحيح الملاحظات المذكورة أعلاه.</p>
                        <p style="line-height: 1.6;">نتمنى لك كل التوفيق في مسيرتك المهنية.</p>
                    </div>
                    <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 0.8em; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                        جميع الحقوق محفوظة &copy; 2026 الأكاديمية الوطنية للتدريب
                    </div>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            
        logger.info(f"Rejection email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send rejection email to {recipient_email}: {str(e)}")
        return False

def send_stage_pass_email(recipient_email: str, full_name: str, stage_name: str, gender: str = "male"):
    """
    Sends an email to the applicant informing them they have passed a stage.
    """
    try:
        greeting = "عزيزي" if gender == "male" else "عزيزتي"
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "NTA Admission - Stage Passed"
        msg["From"] = f"NTA Admission <{SENDER_EMAIL}>"
        msg["To"] = recipient_email

        html_content = f"""
        <html>
            <body style="font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <div style="background: linear-gradient(135deg, #059669, #065f46); padding: 30px; text-align: center; color: #ffffff;">
                        <h1 style="margin: 0; font-size: 24px;">الأكاديمية الوطنية للتدريب</h1>
                        <p style="margin: 10px 0 0; opacity: 0.8;">تهانينا! لقد اجتزت مرحلة بنجاح</p>
                    </div>
                    <div style="padding: 40px; color: #334155;">
                        <h2 style="color: #1e293b; margin-top: 0;">{greeting} {full_name}،</h2>
                        <p style="line-height: 1.6;">يسعدنا إبلاغك بأنك قد اجتزت مرحلة <strong>{stage_name}</strong> بنجاح.</p>
                        <p style="line-height: 1.6;">تم نقل طلبك الآن إلى المرحلة التالية من عملية التقييم. سيتم التواصل معك قريباً بخصوص الخطوات القادمة.</p>
                        
                        <div style="text-align: center; margin-top: 40px;">
                            <div style="display: inline-block; padding: 12px 24px; background-color: #ecfdf5; color: #059669; border-radius: 30px; font-weight: bold; border: 1px solid #10b981;">
                                الحالة: انتقل للمرحلة التالية
                            </div>
                        </div>
                    </div>
                    <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 0.8em; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                        جميع الحقوق محفوظة &copy; 2026 الأكاديمية الوطنية للتدريب
                    </div>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            
        logger.info(f"Stage pass email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send stage pass email to {recipient_email}: {str(e)}")
        return False
