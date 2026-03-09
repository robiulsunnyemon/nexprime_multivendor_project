from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"


class ReportAction(str, Enum):
    NONE = "NONE"
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"


# ─── Input Schema ───────────────────────────────────────────────────────────

class MarketingProductReportCreate(BaseModel):
    reporterUserId: int
    targetUserId: int
    marketingProductId: int
    content: str


# ─── Nested Response Schemas ─────────────────────────────────────────────────

class UserBasicResponse(BaseModel):
    id: int
    fullname: str
    email: str
    phonenumber: str
    role: str
    status: str
    is_verified: bool
    profileImageUrl: Optional[str] = None
    coverImageUrl: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class MarketingProductBasicResponse(BaseModel):
    id: int
    name: str
    goodsType: str
    location: str
    description: Optional[str] = None
    price: float
    publishingFee: float
    shippingCharge: float
    shippingResponsibility: str
    images: list[str]
    creatorId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


# ─── Full Report Response ────────────────────────────────────────────────────

class MarketingProductReportResponse(BaseModel):
    id: int
    content: str
    status: ReportStatus
    action: ReportAction
    reporterUserId: int
    targetUserId: int
    marketingProductId: int
    reporter: UserBasicResponse
    target: UserBasicResponse
    marketingProduct: MarketingProductBasicResponse
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


# ─── Admin Update Schema ─────────────────────────────────────────────────────

class AdminUpdateReportStatus(BaseModel):
    status: ReportStatus
