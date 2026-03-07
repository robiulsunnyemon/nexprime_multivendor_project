import random
import string
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

import bcrypt
import cloudinary
import cloudinary.uploader
import jwt
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.database.db import prisma


# ─────────────────────────────────────────────────────────
# Private Utilities
# ─────────────────────────────────────────────────────────
def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


async def _create_refresh_token(user_id: int) -> str:
    expires_at = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm="HS256")
    
    # Save to DB
    await prisma.refreshtoken.create(
        data={
            "token": token,
            "userId": user_id,
            "expiresAt": expires_at,
        }
    )
    return token


async def _send_otp_email(email: str, code: str, subject: str = "OTP Verification") -> None:
    body = (
        f"Your OTP code is: {code}\n\n"
        f"Use this code within {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
        f"If you did not request this, please ignore this email."
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.EMAIL_FROM, [email], msg.as_string())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )


async def _upload_image(file: UploadFile, folder: str = "resident_cards") -> str:
    contents = await file.read()
    try:
        result = cloudinary.uploader.upload(contents, folder=folder, resource_type="image")
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}",
        )


async def _create_otp(user_id: int) -> str:
    """Deletes old OTP and saves a new OTP for the user."""
    await prisma.otp.delete_many(where={"userId": user_id})
    code = _generate_otp()
    await prisma.otp.create(
        data={
            "code": code,
            "expiresAt": datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            "userId": user_id,
        }
    )
    return code


async def _verify_otp_code(user_id: int, code: str):
    """Validates OTP. Raises exception if invalid or expired."""
    otp = await prisma.otp.find_first(
        where={
            "userId": user_id,
            "code": code,
            "expiresAt": {"gt": datetime.utcnow()},
        },
        order={"createdAt": "desc"},
    )
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
    return otp


# ─────────────────────────────────────────────────────────
# Public Service Functions
# ─────────────────────────────────────────────────────────
async def signup_service(
    fullname: str,
    email: str,
    phonenumber: str,
    password: str,
    role: str,
    front_file: UploadFile,
    back_file: UploadFile,
) -> dict:
    # Check if registration is enabled
    setting = await prisma.systemsetting.find_unique(where={"id": 1})
    # If setting is None, we assume registration is enabled by default
    if setting and not setting.isRegistrationEnabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="We are temporarily not accepting new account registrations at this time.",
        )

    # Duplicate check
    existing = await prisma.user.find_first(
        where={"OR": [{"email": email}, {"phonenumber": phonenumber}]}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Email or Phone number is already registered.",
        )

    # Upload images
    front_url = await _upload_image(front_file)
    back_url = await _upload_image(back_file)

    # Create user
    user = await prisma.user.create(
        data={
            "fullname": fullname,
            "email": email,
            "phonenumber": phonenumber,
            "password": _hash_password(password),
            "role": role,
            "residentcard_frontside": front_url,
            "residentcard_backside": back_url,
        }
    )

    # Create & send OTP
    code = await _create_otp(user.id)

    await _send_otp_email(email, code, subject="Account Verification OTP")
    return {"message": "Signup successful. OTP sent to your email.", "user_id": user.id}


async def vendor_signup_service(
    fullname: str,
    email: str,
    phonenumber: str,
    password: str,
    store_name: str,
    store_bio: str | None,
    store_address: str,
    front_file: UploadFile,
    back_file: UploadFile,
    store_photo: UploadFile,
    kyc_file: UploadFile | None = None,
) -> dict:
    # 1. Check if registration is enabled
    setting = await prisma.systemsetting.find_unique(where={"id": 1})
    if setting and not setting.isRegistrationEnabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="We are temporarily not accepting new account registrations at this time.",
        )

    # 2. Duplicate check
    existing = await prisma.user.find_first(
        where={"OR": [{"email": email}, {"phonenumber": phonenumber}]}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Email or Phone number is already registered.",
        )

    # 3. Upload images
    front_url = await _upload_image(front_file, folder="resident_cards")
    back_url = await _upload_image(back_file, folder="resident_cards")
    store_url = await _upload_image(store_photo, folder="stores")
    
    kyc_url = None
    if kyc_file:
        kyc_url = await _upload_image(kyc_file, folder="vendor_kyc")

    # 4. Create User, Store and KYC (Combined)
    user_data = {
        "fullname": fullname,
        "email": email,
        "phonenumber": phonenumber,
        "password": _hash_password(password),
        "role": "VENDOR",
        "residentcard_frontside": front_url,
        "residentcard_backside": back_url,
        "store": {
            "create": {
                "name": store_name,
                "bio": store_bio,
                "address": store_address,
                "photo": store_url,
            }
        },
    }
    
    if kyc_url:
        user_data["kycFiles"] = {
            "create": {
                "title": "vendor_kyc",
                "fileUrl": kyc_url,
                "status": "PENDING"
            }
        }

    user = await prisma.user.create(data=user_data)

    # 5. Create & send OTP
    code = await _create_otp(user.id)
    await _send_otp_email(email, code, subject="Vendor Account Verification OTP")

    return {
        "message": "Vendor signup successful. OTP sent to your email.",
        "user_id": user.id,
    }


async def verify_otp_service(email: str, code: str) -> dict:
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Account already verified.")

    await _verify_otp_code(user.id, code)

    await prisma.user.update(
        where={"id": user.id},
        data={"status": "ACTIVE", "is_verified": True},
    )
    await prisma.otp.delete_many(where={"userId": user.id})

    # KYC Check for Vendors
    if user.role == "VENDOR":
        kyc = await prisma.kycfile.find_first(where={"vendorId": user.id, "status": "ACTIVE"})
        if not kyc:
            return {
                "message": "Verification successful. However, your KYC status is not active at this time. Kindly wait for administrator approval.",
                "is_kyc_pending": True
            }

    token = _create_access_token(user.id, user.role)
    refresh_token = await _create_refresh_token(user.id)
    return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}


async def login_service(email: str, password: str) -> dict:
    user = await prisma.user.find_unique(where={"email": email})

    if not user or not _verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.is_verified:
        raise HTTPException(
            status_code=403, detail="Account not verified. Please check your email."
        )

    # KYC Check for Vendors
    if user.role == "VENDOR":
        kyc = await prisma.kycfile.find_first(where={"vendorId": user.id, "status": "ACTIVE"})
        if not kyc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your KYC status is not active at the moment. Kindly wait until it is approved by the administrator."
            )

    status_errors = {
        "SUSPEND": "Account suspended. Please contact admin.",
        "INACTIVE": "Account inactive. Please contact admin.",
    }
    if user.status in status_errors:
        raise HTTPException(status_code=403, detail=status_errors[user.status])

    token = _create_access_token(user.id, user.role)
    refresh_token = await _create_refresh_token(user.id)
    return {
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "fullname": user.fullname,
            "email": user.email,
            "phonenumber": user.phonenumber,
            "role": user.role,
            "status": user.status,
            "is_verified": user.is_verified,
            "residentcard_frontside": user.residentcard_frontside,
            "residentcard_backside": user.residentcard_backside,
        },
    }


async def resend_otp_service(email: str) -> dict:
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Account already verified.")

    code = await _create_otp(user.id)

    await _send_otp_email(email, code, subject="Resend OTP")
    return {"message": "A new OTP has been sent."}


async def forgot_password_service(email: str) -> dict:
    user = await prisma.user.find_unique(where={"email": email})
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If an account exists, an OTP has been sent."}

    code = await _create_otp(user.id)

    await _send_otp_email(email, code, subject="Password Reset OTP")
    return {"message": "Password reset OTP sent."}


async def reset_password_service(email: str, code: str, new_password: str) -> dict:
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await _verify_otp_code(user.id, code)

    await prisma.user.update(
        where={"id": user.id},
        data={"password": _hash_password(new_password)},
    )
    await prisma.otp.delete_many(where={"userId": user.id})

    return {"message": "Password changed successfully."}


async def get_profile_service(user) -> dict:
    return {
        "id": user.id,
        "fullname": user.fullname,
        "email": user.email,
        "phonenumber": user.phonenumber,
        "role": user.role,
        "status": user.status,
        "profileImageUrl": user.profileImageUrl,
        "is_verified": user.is_verified,
        "residentcard_frontside": user.residentcard_frontside,
        "residentcard_backside": user.residentcard_backside,
        "createdAt": user.createdAt,
    }


async def refresh_token_service(refresh_token: str) -> dict:
    try:
        payload = jwt.decode(refresh_token, settings.JWT_REFRESH_SECRET, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        # Cleanup expired token from DB if it exists
        await prisma.refreshtoken.delete_many(where={"token": refresh_token})
        raise HTTPException(status_code=401, detail="Refresh token expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    # Check if token exists in DB (Standard for professional systems)
    stored_token = await prisma.refreshtoken.find_unique(where={"token": refresh_token})
    if not stored_token:
        raise HTTPException(status_code=401, detail="Refresh token not found or already used.")

    user = await prisma.user.find_unique(where={"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Token Rotation: Delete old refresh token and create a new one
    await prisma.refreshtoken.delete(where={"id": stored_token.id})
    
    new_access_token = _create_access_token(user.id, user.role)
    new_refresh_token = await _create_refresh_token(user.id)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

async def get_user_by_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
        return await prisma.user.find_unique(where={"id": user_id})
    except Exception:
        return None
