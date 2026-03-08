from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.product.schemas import ProductResponse

class VendorSimpleResponse(BaseModel):
    id: int
    fullname: str
    email: str
    phonenumber: str

    class Config:
        from_attributes = True

class StorePublicResponse(BaseModel):
    id: int
    name: str
    bio: Optional[str] = None
    address: str
    photo: str
    coverImgUrl: Optional[str] = None
    vendorId: int
    vendor: VendorSimpleResponse
    products: List[ProductResponse]
    followerCount: Optional[int] = 0
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
