import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "apikey")
SMTP_PASS = os.getenv("SENDGRID_API_KEY", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@nta.eg")

logger = logging.getLogger(__name__)


def _send_admin_email(recipient_email: str, subject: str, html_content: str):
    """Send an HTML email to an admin recipient."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"NTA System <{SENDER_EMAIL}>"
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_PASS:
                server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())

        logger.info(f"Admin email sent to {recipient_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send admin email to {recipient_email}: {e}")
        return False


def send_new_registration_notification(
    admin_email: str,
    trainee_name: str,
    national_id: str,
):
    subject = "NEW REGISTRATION — NTA Portal"
    html = f"""
    <html>
        <body style="font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; background-color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 30px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px;">الأكاديمية الوطنية للتدريب</h1>
                    <p style="margin: 10px 0 0; opacity: 0.8;">تسجيل جديد</p>
                </div>
                <div style="padding: 40px; color: #334155;">
                    <h2 style="color: #1e293b; margin-top: 0;">مرحباً،</h2>
                    <p style="line-height: 1.6;">تم تسجيل متدرب جديد في البوابة. يرجى مراجعة الملف والبدء في عملية المراجعة.</p>
                    <div style="background-color: #f1f5f9; padding: 20px; border-radius: 8px; margin: 30px 0; border-right: 4px solid #2563eb;">
                        <p style="margin: 0 0 10px;"><strong>اسم المتدرب:</strong> {trainee_name}</p>
                        <p style="margin: 0;"><strong>الرقم القومي:</strong> {national_id}</p>
                    </div>
                    <div style="text-align: center; margin-top: 40px;">
                        <a href="https://portal.nta.eg/admin" style="background-color: #2563eb; color: #ffffff; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">مراجعة الملف</a>
                    </div>
                </div>
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 0.8em; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                    جميع الحقوق محفوظة &copy; 2026 الأكاديمية الوطنية للتدريب
                </div>
            </div>
        </body>
    </html>
    """
    return _send_admin_email(admin_email, subject, html)


def send_stage_completion_notification(
    admin_email: str,
    trainee_name: str,
    stage_name: str,
    national_id: str,
):
    subject = f"STAGE COMPLETED — {stage_name} — NTA Portal"
    html = f"""
    <html>
        <body style="font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; background-color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #059669, #047857); padding: 30px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px;">الأكاديمية الوطنية للتدريب</h1>
                    <p style="margin: 10px 0 0; opacity: 0.8;">اكتمال مرحلة</p>
                </div>
                <div style="padding: 40px; color: #334155;">
                    <h2 style="color: #1e293b; margin-top: 0;">مرحباً،</h2>
                    <p style="line-height: 1.6;">أكمل المتدرب المرحلة التالية بنجاح:</p>
                    <div style="background-color: #f1f5f9; padding: 20px; border-radius: 8px; margin: 30px 0; border-right: 4px solid #059669;">
                        <p style="margin: 0 0 10px;"><strong>اسم المتدرب:</strong> {trainee_name}</p>
                        <p style="margin: 0 0 10px;"><strong>الرقم القومي:</strong> {national_id}</p>
                        <p style="margin: 0;"><strong>المرحلة المكتملة:</strong> {stage_name}</p>
                    </div>
                    <div style="text-align: center; margin-top: 40px;">
                        <a href="https://portal.nta.eg/admin" style="background-color: #059669; color: #ffffff; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">مراجعة الملف</a>
                    </div>
                </div>
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 0.8em; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                    جميع الحقوق محفوظة &copy; 2026 الأكاديمية الوطنية للتدريب
                </div>
            </div>
        </body>
    </html>
    """
    return _send_admin_email(admin_email, subject, html)


def send_rejection_notification(
    admin_email: str,
    trainee_name: str,
    stage_name: str,
    reviewer_name: str,
    national_id: str,
):
    subject = f"REJECTION — {stage_name} — NTA Portal"
    html = f"""
    <html>
        <body style="font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; background-color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 30px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px;">الأكاديمية الوطنية للتدريب</h1>
                    <p style="margin: 10px 0 0; opacity: 0.8;">تم رفض المتدرب</p>
                </div>
                <div style="padding: 40px; color: #334155;">
                    <h2 style="color: #1e293b; margin-top: 0;">مرحباً،</h2>
                    <p style="line-height: 1.6;">تم رفض المتدرب في المرحلة التالية:</p>
                    <div style="background-color: #f1f5f9; padding: 20px; border-radius: 8px; margin: 30px 0; border-right: 4px solid #dc2626;">
                        <p style="margin: 0 0 10px;"><strong>اسم المتدرب:</strong> {trainee_name}</p>
                        <p style="margin: 0 0 10px;"><strong>الرقم القومي:</strong> {national_id}</p>
                        <p style="margin: 0 0 10px;"><strong>المرحلة:</strong> {stage_name}</p>
                        <p style="margin: 0;"><strong>المراجع:</strong> {reviewer_name}</p>
                    </div>
                    <div style="text-align: center; margin-top: 40px;">
                        <a href="https://portal.nta.eg/admin" style="background-color: #dc2626; color: #ffffff; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">مراجعة الملف</a>
                    </div>
                </div>
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 0.8em; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                    جميع الحقوق محفوظة &copy; 2026 الأكاديمية الوطنية للتدريب
                </div>
            </div>
        </body>
    </html>
    """
    return _send_admin_email(admin_email, subject, html)


def send_final_approval_notification(
    admin_email: str,
    trainee_name: str,
    national_id: str,
):
    subject = "FINAL APPROVAL — NTA Portal"
    html = f"""
    <html>
        <body style="font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; background-color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #7c3aed, #6d28d9); padding: 30px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px;">الأكاديمية الوطنية للتدريب</h1>
                    <p style="margin: 10px 0 0; opacity: 0.8;">قبول نهائي</p>
                </div>
                <div style="padding: 40px; color: #334155;">
                    <h2 style="color: #1e293b; margin-top: 0;">مرحباً،</h2>
                    <p style="line-height: 1.6;">تم قبول المتدرب نهائياً في البرنامج التدريبي:</p>
                    <div style="background-color: #f1f5f9; padding: 20px; border-radius: 8px; margin: 30px 0; border-right: 4px solid #7c3aed;">
                        <p style="margin: 0 0 10px;"><strong>اسم المتدرب:</strong> {trainee_name}</p>
                        <p style="margin: 0;"><strong>الرقم القومي:</strong> {national_id}</p>
                    </div>
                    <div style="text-align: center; margin-top: 40px;">
                        <a href="https://portal.nta.eg/admin" style="background-color: #7c3aed; color: #ffffff; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">مراجعة الملف</a>
                    </div>
                </div>
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 0.8em; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                    جميع الحقوق محفوظة &copy; 2026 الأكاديمية الوطنية للتدريب
                </div>
            </div>
        </body>
    </html>
    """
    return _send_admin_email(admin_email, subject, html)
