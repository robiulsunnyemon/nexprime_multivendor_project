# import smtplib
# from email.mime.text import MIMEText


#
# def send_email(email: str, action: str):
#     """Background task to send email."""
#     subject = f"Your account has a '{action}' action"
#     body = f"""
#     Hello,
#
#     The following action has been performed on your account: {action}.
#
#     If you did not perform this action, please contact us immediately.
#
#     Thank you,
#     Support Team
#     """
#     smtp_pass=settings.SMTP_PASS
#     myemail=settings.EMAIL_FROM
#     msg = MIMEText(body, "plain")
#     msg['Subject'] = subject
#     msg['From'] = myemail
#     msg['To'] = email
#     port=settings.SMTP_PORT
#     host=settings.SMTP_HOST
#
#     try:
#         with smtplib.SMTP(host, port) as server:
#             server.starttls()
#             server.login(myemail, smtp_pass)
#             server.sendmail(myemail, email, msg.as_string())
#         print(f"Email sent to {email} successfully!")
#     except Exception as e:
#         print(f"Failed to send email: {e}")


from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, HtmlContent, PlainTextContent
from fastapi import HTTPException, status
from app.core.config import settings

def send_email(email: str, action: str):
    """Background task to send email with professional HTML template."""

    subject = f"Security Notice: Account Action Required ('{action}')"

    # ফলব্যাক প্লেইন টেক্সট (স্প্যাম ফিল্টার এড়াতে এবং ওল্ড ক্লায়েন্টদের জন্য)
    plain_body = (
        f"Hello,\n\n"
        f"The following action has been performed on your account: {action}.\n\n"
        f"If you did not perform this action, please contact us immediately.\n\n"
        f"Thank you,\nSupport Team"
    )

    # রেসপন্সিভ এবং মডার্ন HTML টেমপ্লেট
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{subject}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333333;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f4f6f9; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" max-width="600" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #e1e8ed;">
                        <tr>
                            <td style="background-color: #DC2626; padding: 30px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 600; letter-spacing: 0.5px;">Account Activity Alert</h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px 30px;">
                                <p style="font-size: 16px; line-height: 1.6; color: #1F2937; margin: 0;">Hello,</p>
                                <p style="font-size: 16px; line-height: 1.6; color: #4B5563; margin-top: 10px;">
                                    We detected a new activity or change on your account. Please review the details below:
                                </p>

                                <div style="background-color: #F9FAFB; border-left: 4px solid #DC2626; padding: 15px 20px; margin: 25px 0; border-radius: 0 4px 4px 0;">
                                    <p style="margin: 0; font-size: 14px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Performed Action</p>
                                    <p style="margin: 5px 0 0 0; font-size: 18px; color: #111827; font-weight: bold;">{action}</p>
                                </div>

                                <p style="font-size: 15px; line-height: 1.6; color: #EF4444; font-weight: 500; margin-bottom: 25px;">
                                    ⚠️ If you did not perform this action, your account might be at risk. Please contact our support team or change your password immediately.
                                </p>

                                <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 25px 0;">

                                <p style="font-size: 14px; color: #6B7280; margin: 0;">
                                    Thank you,<br>
                                    <strong>The Support Team</strong>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background-color: #F3F4F6; padding: 20px; text-align: center; font-size: 12px; color: #9CA3AF; border-top: 1px solid #E5E7EB;">
                                This is an automated security notification. Please do not reply directly to this email.<br>
                                &copy; {2026} Your Company Name. All rights reserved.
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    # SendGrid মেল অবজেক্ট তৈরি
    message = Mail(
        from_email=settings.SENDGRID_EMAIL_FROM,
        to_emails=email,
        subject=subject,
        plain_text_content=PlainTextContent(plain_body),
        html_content=HtmlContent(html_body)
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code not in [200, 201, 202]:
            raise Exception(f"SendGrid returned status code {response.status_code}")

    except Exception as e:
        print(f"Email Background Task Error: {str(e)}")
        # Background টাস্ক সাধারণত কোনো HTTP Response রিটার্ন করে না,
        # তবে আপনি চাইলে এটি লগার (Logger) দিয়ে ট্র্যাক করতে পারেন।
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send account action notification.",
        )