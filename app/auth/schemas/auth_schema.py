from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum


class RoleEnum(str, Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"


# ── Auth Schemas ──────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str


class ResendOTPRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return v



# ── Response Schemas ──────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    fullname: str
    email: str
    phonenumber: str
    role: str
    status: str
    is_verified: bool
    residentcard_frontside: str
    residentcard_backside: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageResponse(BaseModel):
    message: str