from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum
from typing import List

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
    profileImageUrl: Optional[str]
    residentcard_frontside: str
    residentcard_backside: str
    is_verified: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: AccountStatus


class StoreSchema(BaseModel):
    id: int
    name: str
    bio: Optional[str]
    address: str
    photo: str
    createdAt: datetime
    updatedAt: datetime

# KYC File Schema
class KYCFileSchema(BaseModel):
    id: int
    title: str
    fileUrl: str
    status: str
    createdAt: datetime
    updatedAt: datetime

# Main Vendor/User Schema
class VendorSchema(BaseModel):
    id: int
    fullname: str
    email: str
    phonenumber: str
    role: str
    status: str
    is_verified: bool
    profileImageUrl: Optional[str]
    residentcard_frontside: str
    residentcard_backside: str
    createdAt: datetime
    updatedAt: datetime
    store: Optional[StoreSchema] = None
    kycFiles: Optional[List[KYCFileSchema]] = None


class KycStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPEND = "SUSPEND"
    PENDING = "PENDING"
    REJECTED = "REJECTED"

class KYCStatusUpdate(BaseModel):
    status: KycStatus
