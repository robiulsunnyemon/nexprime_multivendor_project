from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Delivery Address Schemas ---

class DeliveryAddressBase(BaseModel):
    fullName: str
    postcode: str
    fullAddress: str
    buildingNameRoomNumber: Optional[str] = None
    phoneNumber: str

class DeliveryAddressCreate(DeliveryAddressBase):
    pass

class DeliveryAddressResponse(DeliveryAddressBase):
    id: int
    userId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# --- Order Item Schemas ---

class OrderItemBase(BaseModel):
    productId: int
    quantity: int
    price: float

class OrderItemResponse(OrderItemBase):
    id: int
    orderId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# --- Order Schemas ---

class OrderCreate(BaseModel):
    deliveryAddressId: int

class OrderResponse(BaseModel):
    id: int
    totalAmount: float
    isPaid: bool
    isFulfield: bool
    isArchive: bool
    deliveryAddressId: int
    deliveryAddress: Optional[DeliveryAddressResponse] = None
    userId: int
    orderItems: List[OrderItemResponse] = []
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# --- Rating Schemas ---

class RatingCreate(BaseModel):
    score: int = Field(..., ge=1, le=5)
    review: Optional[str] = None

class RatingResponse(BaseModel):
    id: int
    score: int
    review: Optional[str]
    productId: int
    userId: int
    orderId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
