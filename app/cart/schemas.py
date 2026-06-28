from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.product.schemas import ProductResponse, ProductSize

class CartItemBase(BaseModel):
    productId: int
    quantity: int = 1
    size: Optional[ProductSize] = None
    color: Optional[str] = None

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    action: Optional[str] = None # "increase" or "decrease"

class CartItemResponse(BaseModel):
    id: int
    userId: int
    productId: int
    quantity: int
    size: Optional[ProductSize] = None
    color: Optional[str] = None
    product: ProductResponse
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class CartSummaryResponse(BaseModel):
    items: List[CartItemResponse]
    totalItems: int
    totalAmount: float
