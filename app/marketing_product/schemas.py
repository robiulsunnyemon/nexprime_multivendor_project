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

class MarketingProductCreate(MarketingProductBase):
    pass

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
    phonenumber: str

    class Config:
        from_attributes = True

class MarketingProductWithCreatorResponse(MarketingProductResponse):
    creator: CreatorSimpleResponse
