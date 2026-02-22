import smtplib
from email.mime.text import MIMEText
from app.core.config import settings


def send_email(email: str, action: str):
    """Background task to send email."""
    subject = f"Your account has a '{action}' action"
    body = f"""
    Hello,

    The following action has been performed on your account: {action}.

    If you did not perform this action, please contact us immediately.

    Thank you,
    Support Team
    """
    smtp_pass=settings.SMTP_PASS
    myemail=settings.EMAIL_FROM
    msg = MIMEText(body, "plain")
    msg['Subject'] = subject
    msg['From'] = myemail
    msg['To'] = email
    port=settings.SMTP_PORT
    host=settings.SMTP_HOST

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(myemail, smtp_pass)
            server.sendmail(myemail, email, msg.as_string())
        print(f"Email sent to {email} successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")