"""
Authentication: OTP via email + JWT session.
Single admin user defined via environment variables.
"""

import os
import random
import smtplib
import string
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from jose import JWTError, jwt

# --- Config from env ---
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "phuongnst@gmail.com")
ADMIN_NAME = os.getenv("ADMIN_NAME", "phuongnst")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# Email (Gmail SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")        # Gmail address
SMTP_PASS = os.getenv("SMTP_PASS", "")        # Gmail App Password

OTP_EXPIRE_MINUTES = 5

# In-memory OTP store: {email: (otp, expires_at, attempts)}
_otp_store: dict[str, tuple[str, datetime, int]] = {}
MAX_ATTEMPTS = 5


def _gen_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _send_email(to: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.ehlo()
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, to, msg.as_string())


def request_otp(email: str) -> bool:
    """Generate OTP and send to email. Returns False if email not authorized."""
    if email.lower() != ADMIN_EMAIL.lower():
        return False
    otp = _gen_otp()
    _otp_store[email.lower()] = (otp, datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES), 0)
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0f172a;border-radius:12px;color:#f1f5f9">
      <h2 style="color:#22c55e;margin-bottom:8px">📈 TínHiệuCK</h2>
      <p style="color:#94a3b8;margin-bottom:24px">Mã xác thực đăng nhập của bạn:</p>
      <div style="background:#1e293b;border-radius:8px;padding:24px;text-align:center;letter-spacing:8px;font-size:36px;font-weight:bold;color:#22c55e">
        {otp}
      </div>
      <p style="color:#64748b;font-size:13px;margin-top:20px">
        Mã có hiệu lực trong <strong style="color:#f1f5f9">{OTP_EXPIRE_MINUTES} phút</strong>.<br>
        Nếu bạn không yêu cầu, hãy bỏ qua email này.
      </p>
    </div>
    """
    _send_email(email, "Mã OTP đăng nhập TínHiệuCK", html)
    return True


def verify_otp(email: str, otp: str) -> Optional[str]:
    """
    Verify OTP. Returns JWT token on success, None on failure.
    Raises ValueError on too many attempts or expired OTP.
    """
    key = email.lower()
    entry = _otp_store.get(key)
    if not entry:
        raise ValueError("Chưa có mã OTP nào được gửi cho email này")
    stored_otp, expires_at, attempts = entry

    if attempts >= MAX_ATTEMPTS:
        del _otp_store[key]
        raise ValueError("Quá nhiều lần thử. Vui lòng yêu cầu mã mới.")

    if datetime.utcnow() > expires_at:
        del _otp_store[key]
        raise ValueError("Mã OTP đã hết hạn. Vui lòng yêu cầu mã mới.")

    if otp != stored_otp:
        _otp_store[key] = (stored_otp, expires_at, attempts + 1)
        remaining = MAX_ATTEMPTS - attempts - 1
        raise ValueError(f"Mã OTP không đúng. Còn {remaining} lần thử.")

    del _otp_store[key]
    return _create_token(email)


def _create_token(email: str) -> str:
    payload = {
        "sub": email,
        "name": ADMIN_NAME,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate JWT. Raises JWTError if invalid."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
