import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from .logger_util import log_activity

# Load settings from environment/defaults
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "False").lower() in ("true", "1", "yes")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@nta.eg")

# Logs folder for fallback/sent emails
EMAILS_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "sent_emails")

def send_email_background(to_email: str, subject: str, html_body: str):
    """
    Sends an email using the configured SMTP server. 
    If it fails, it falls back to writing the email content to a local log file.
    Runs in a background thread to prevent blocking client requests.
    """
    def _send():
        email_sent = False
        error_msg = ""
        
        try:
            # Setup message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM_EMAIL
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html", "utf-8"))
            
            # Connect to SMTP
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            
            server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
            server.quit()
            email_sent = True
            
            log_activity(
                category="SYSTEM",
                event_type="EMAIL_SENT",
                level="INFO",
                component="MailService",
                details={"to": to_email, "subject": subject}
            )
        except Exception as e:
            error_msg = str(e)
            # Log failure
            log_activity(
                category="SYSTEM",
                event_type="EMAIL_FAILED",
                level="WARNING",
                component="MailService",
                details={"to": to_email, "subject": subject, "error": error_msg}
            )
            
        # Fallback: Write email to a local file for debugging and auditing
        try:
            os.makedirs(EMAILS_LOG_DIR, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_email = to_email.replace("@", "_at_").replace(".", "_")
            filename = f"{timestamp}_{safe_email}.html"
            filepath = os.path.join(EMAILS_LOG_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"<!-- \n")
                f.write(f"To: {to_email}\n")
                f.write(f"Subject: {subject}\n")
                f.write(f"Status: {'SENT' if email_sent else 'FAILED_FALLBACK'}\n")
                f.write(f"SMTP Config: Host={SMTP_HOST}, Port={SMTP_PORT}, User={SMTP_USER}\n")
                if not email_sent:
                    f.write(f"Error: {error_msg}\n")
                f.write(f"-->\n")
                f.write(html_body)
                
        except Exception as file_err:
            print(f"Failed to write fallback email log: {file_err}")

    # Start sending in a daemon thread so it runs in the background
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()

def send_registration_success_email(to_email: str, name_ar: str):
    """
    Convenience function to send a registration success email.
    """
    subject = "تم تسجيل حسابك بنجاح في بوابة الأكاديمية الوطنية للتدريب"
    
    # Premium styled HTML template
    html_body = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>تأكيد التسجيل</title>
        <style>
            body {{
                font-family: 'Tajawal', Arial, sans-serif;
                background-color: #f7f9fc;
                color: #333333;
                direction: rtl;
                text-align: right;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 30px auto;
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                overflow: hidden;
            }}
            .header {{
                background-color: #1a2e40;
                padding: 30px;
                text-align: center;
                border-bottom: 4px solid #d4af37;
            }}
            .logo {{
                max-width: 150px;
                height: auto;
            }}
            .content {{
                padding: 40px 30px;
                line-height: 1.8;
            }}
            .welcome-title {{
                color: #1a2e40;
                font-size: 22px;
                font-weight: 700;
                margin-top: 0;
                margin-bottom: 20px;
            }}
            .accent-text {{
                color: #d4af37;
                font-weight: bold;
            }}
            .info-box {{
                background-color: #f8fafc;
                border-right: 4px solid #1a2e40;
                padding: 15px 20px;
                margin: 25px 0;
                border-radius: 0 8px 8px 0;
            }}
            .footer {{
                background-color: #f1f5f9;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #64748b;
                border-top: 1px solid #e2e8f0;
            }}
            .button {{
                display: inline-block;
                background-color: #1a2e40;
                color: #ffffff !important;
                text-decoration: none;
                padding: 12px 30px;
                border-radius: 30px;
                font-weight: bold;
                margin: 20px 0;
                border: 1px solid #d4af37;
            }}
            .button:hover {{
                background-color: #2c3e50;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="color: #ffffff; margin: 0; font-family: 'Tajawal', sans-serif;">الأكاديمية الوطنية للتدريب</h2>
            </div>
            <div class="content">
                <h3 class="welcome-title">مرحباً بك يا <span class="accent-text">{name_ar}</span>،</h3>
                <p>يسعدنا إبلاغك بأنه قد تم استلام طلب تسجيلك بنجاح في بوابة الأكاديمية الوطنية للتدريب (NTA).</p>
                
                <div class="info-box">
                    <strong>تفاصيل الحساب:</strong><br>
                    • البريد الإلكتروني: {to_email}<br>
                    • حالة الطلب الحالية: قيد المراجعة والتدقيق
                </div>
                
                <p>يمكنك الآن تسجيل الدخول إلى البوابة باستخدام بريدك الإلكتروني والرقم القومي وكلمة المرور التي اخترتها لمتابعة حالة طلبك والتحقق من متطلبات البرامج التدريبية المتاحة.</p>
                
                <div style="text-align: center;">
                    <a href="https://nta.eg" class="button">الانتقال إلى البوابة</a>
                </div>
                
                <p style="margin-bottom: 0;">مع أطيب التحيات،<br>فريق عمل الأكاديمية الوطنية للتدريب</p>
            </div>
            <div class="footer">
                هذا البريد الإلكتروني مرسل تلقائياً من نظام الأكاديمية الوطنية للتدريب. يرجى عدم الرد عليه مباشرة.
            </div>
        </div>
    </body>
    </html>
    """
    
    send_email_background(to_email, subject, html_body)
