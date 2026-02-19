from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class Role(str, Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    ADMIN = "ADMIN"

class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPEND = "SUSPEND"
    INACTIVE = "INACTIVE"

class UserResponse(BaseModel):
    id: int
    fullname: str
    email: EmailStr
    phonenumber: str
    role: Role
    status: AccountStatus
    is_verified: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: AccountStatus
