from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ShippingResponsibility(str, Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"

class MarketingProductBase(BaseModel):
    name: str
    goodsType: str
    location: str
    description: Optional[str] = None
    price: float
    publishingFee: float = 0
    shippingResponsibility: ShippingResponsibility = ShippingResponsibility.CUSTOMER
    shippingCharge: float = 0
    taxFee: float = 0.0

class MarketingProductCreate(MarketingProductBase):
    pass

class MarketingProductUpdate(BaseModel):
    name: Optional[str] = None
    goodsType: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    shippingResponsibility: Optional[ShippingResponsibility] = None
    shippingCharge: Optional[float] = None
    taxFee: Optional[float] = None

class MarketingProductResponse(MarketingProductBase):
    id: int
    images: List[str]
    creatorId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class CreatorSimpleResponse(BaseModel):
    id: int
    fullname: str
    email: str
    profileImageUrl: Optional[str] = None
    phonenumber: Optional[str] = None

    class Config:
        from_attributes = True

class MarketingProductWithCreatorResponse(MarketingProductResponse):
    creator: CreatorSimpleResponse
