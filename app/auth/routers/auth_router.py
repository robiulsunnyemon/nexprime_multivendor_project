from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.current_user import get_current_user
from app.auth.schemas.auth_schema import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    ResendOTPRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyOTPRequest,
    RefreshTokenRequest,
)

from app.auth.services.auth_service import (
    forgot_password_service,
    get_profile_service,
    login_service,
    resend_otp_service,
    reset_password_service,
    signup_service,
    verify_otp_service, vendor_signup_service,
    refresh_token_service,
    logout_service,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/refresh", response_model=TokenResponse, summary="Get a new access token using refresh token")
async def refresh_token(body: RefreshTokenRequest):
    return await refresh_token_service(refresh_token=body.refresh_token)


@router.post("/logout", response_model=MessageResponse, summary="Logout and revoke refresh token")
async def logout(body: RefreshTokenRequest):
    return await logout_service(refresh_token=body.refresh_token)


# ─────────────────────────────────────────────────────────
# POST /auth/signup
# multipart/form-data because of image upload
# ─────────────────────────────────────────────────────────
@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
    summary="Register a new user",
)
async def signup(
    fullname: str = Form(...),
    email: str = Form(...),
    phonenumber: str = Form(...),
    password: str = Form(..., min_length=6),
    residentcard_frontside: UploadFile = File(...),
    residentcard_backside: UploadFile = File(...),
):
    return await signup_service(
        fullname=fullname,
        email=email,
        phonenumber=phonenumber,
        password=password,
        role="CUSTOMER",
        front_file=residentcard_frontside,
        back_file=residentcard_backside,
    )


@router.post("/vendor/signup", status_code=status.HTTP_201_CREATED, summary="Combined Vendor & Store Signup")
async def vendor_signup(
    fullname: str = Form(...),
    email: str = Form(...),
    phonenumber: str = Form(...),
    password: str = Form(..., min_length=6),
    store_name: str = Form(...),
    store_bio: str = Form(...),
    store_address: str = Form(...),
    residentcard_frontside: UploadFile = File(...),
    residentcard_backside: UploadFile = File(...),
    store_photo: UploadFile = File(...),
    kyc_document: UploadFile = File(...),
):
    return await vendor_signup_service(
        fullname=fullname,
        email=email,
        phonenumber=phonenumber,
        password=password,
        store_name=store_name,
        store_bio=store_bio,
        store_address=store_address,
        front_file=residentcard_frontside,
        back_file=residentcard_backside,
        store_photo=store_photo,
        kyc_file=kyc_document,
    )


# ─────────────────────────────────────────────────────────
# POST /auth/verify-otp
# ─────────────────────────────────────────────────────────
@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    summary="Verify account using OTP",
)
async def verify_otp(body: VerifyOTPRequest):
    return await verify_otp_service(email=body.email, code=body.code)


# ─────────────────────────────────────────────────────────
# POST /auth/login
# ─────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login and receive JWT token",
)
async def login(body: LoginRequest):
    return await login_service(email=body.email, password=body.password)


# ─────────────────────────────────────────────────────────
# POST /auth/resend-otp
# ─────────────────────────────────────────────────────────
@router.post(
    "/resend-otp",
    response_model=MessageResponse,
    summary="Resend OTP (for signup verification)",
)
async def resend_otp(body: ResendOTPRequest):
    return await resend_otp_service(email=body.email)


# ─────────────────────────────────────────────────────────
# POST /auth/forgot-password
# ─────────────────────────────────────────────────────────
@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Send OTP for password reset",
)
async def forgot_password(body: ForgotPasswordRequest):
    return await forgot_password_service(email=body.email)


# ─────────────────────────────────────────────────────────
# POST /auth/reset-password
# ─────────────────────────────────────────────────────────
@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Verify OTP and set new password",
)
async def reset_password(body: ResetPasswordRequest):
    return await reset_password_service(
        email=body.email,
        code=body.code,
        new_password=body.new_password,
    )


# ─────────────────────────────────────────────────────────
# GET /auth/profile  (Protected)
# ─────────────────────────────────────────────────────────
@router.get(
    "/profile",
    summary="View logged-in user's profile",
)
async def get_profile(current_user=Depends(get_current_user)):
    return await get_profile_service(current_user)
