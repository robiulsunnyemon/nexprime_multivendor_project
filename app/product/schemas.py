from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ShippingResponsibility(str, Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"

class ProductSize(str, Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    XXXL = "XXXL"
    FREE_SIZE = "FREE_SIZE"

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    basePrice: float
    stockUnits: int = 0
    size: List[ProductSize] = []
    colors: List[str] = []
    isDiscountSale: bool = False
    salePrice: Optional[float] = None
    discountPercentage: Optional[float] = None
    shippingResponsibility: ShippingResponsibility = ShippingResponsibility.CUSTOMER
    shippingCharge: float = 0
    total_payable_amount: float = 0

class ProductCreate(ProductBase):
    categoryIds: List[int]

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    basePrice: Optional[float] = None
    stockUnits: Optional[int] = None
    size: Optional[List[ProductSize]] = None
    colors: Optional[List[str]] = None
    isDiscountSale: Optional[bool] = None
    salePrice: Optional[float] = None
    shippingResponsibility: Optional[ShippingResponsibility] = None
    shippingCharge: Optional[float] = None
    categoryIds: Optional[List[int]] = None

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
