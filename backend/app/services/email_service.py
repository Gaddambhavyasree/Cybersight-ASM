import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_verification_email(to_email: str, token: str, full_name: str) -> bool:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "CyberSight ASM - Verify Your Email"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .card {{ background: #1e293b; border-radius: 12px; padding: 40px; border: 1px solid #334155; }}
            .logo {{ font-size: 24px; font-weight: 700; color: #38bdf8; margin-bottom: 8px; }}
            .subtitle {{ color: #94a3b8; font-size: 14px; margin-bottom: 32px; }}
            h1 {{ color: #f1f5f9; font-size: 20px; margin-bottom: 16px; }}
            p {{ color: #94a3b8; line-height: 1.6; margin-bottom: 24px; }}
            .btn {{ display: inline-block; background: #38bdf8; color: #0f172a; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 14px; }}
            .footer {{ margin-top: 32px; padding-top: 24px; border-top: 1px solid #334155; color: #64748b; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="logo">CyberSight ASM</div>
                <div class="subtitle">Attack Surface Management Platform</div>
                <h1>Welcome, {full_name}!</h1>
                <p>Thank you for registering. Please verify your email address to activate your account.</p>
                <a href="{verify_url}" class="btn">Verify Email Address</a>
                <p style="margin-top: 24px; font-size: 13px;">If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; font-size: 13px; color: #38bdf8;">{verify_url}</p>
                <div class="footer">
                    <p>This link will expire in 24 hours. If you didn't create an account, you can safely ignore this email.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html_body)


def send_reset_password_email(to_email: str, token: str, full_name: str) -> bool:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    subject = "CyberSight ASM - Reset Your Password"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .card {{ background: #1e293b; border-radius: 12px; padding: 40px; border: 1px solid #334155; }}
            .logo {{ font-size: 24px; font-weight: 700; color: #38bdf8; margin-bottom: 8px; }}
            .subtitle {{ color: #94a3b8; font-size: 14px; margin-bottom: 32px; }}
            h1 {{ color: #f1f5f9; font-size: 20px; margin-bottom: 16px; }}
            p {{ color: #94a3b8; line-height: 1.6; margin-bottom: 24px; }}
            .btn {{ display: inline-block; background: #f59e0b; color: #0f172a; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 14px; }}
            .footer {{ margin-top: 32px; padding-top: 24px; border-top: 1px solid #334155; color: #64748b; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="logo">CyberSight ASM</div>
                <div class="subtitle">Attack Surface Management Platform</div>
                <h1>Password Reset Request</h1>
                <p>Hi {full_name}, we received a request to reset your password. Click the button below to set a new password.</p>
                <a href="{reset_url}" class="btn">Reset Password</a>
                <p style="margin-top: 24px; font-size: 13px;">If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; font-size: 13px; color: #f59e0b;">{reset_url}</p>
                <div class="footer">
                    <p>This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html_body)
