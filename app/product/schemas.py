from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ShippingResponsibility(str, Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    basePrice: float
    stockUnits: int = 0
    size: Optional[str] = None
    colors: Optional[str] = None
    isOnSale: bool = False
    salePrice: Optional[float] = None
    discountPercentage: Optional[float] = None
    shippingResponsibility: ShippingResponsibility = ShippingResponsibility.CUSTOMER
    shippingCharge: float = 0

class ProductCreate(ProductBase):
    categoryIds: List[int]

class SubCategorySimple(BaseModel):
    id: int
    name: str
    image: Optional[str] = None

    class Config:
        from_attributes = True

class StoreSimpleResponse(BaseModel):
    id: int
    name: str
    address: str
    photo: str

    class Config:
        from_attributes = True

class ProductResponse(ProductBase):
    id: int
    images: List[str]
    storeId: int
    store: Optional[StoreSimpleResponse] = None
    categories: Optional[List[SubCategorySimple]] = []
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
