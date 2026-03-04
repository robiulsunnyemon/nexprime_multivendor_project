from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"

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
    subOrderId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# --- SubOrder Schemas ---

class SubOrderResponse(BaseModel):
    id: int
    orderId: int
    storeId: int
    subTotal: float
    isFulfield: bool
    isComplete: bool
    isArchive: bool
    orderItems: List[OrderItemResponse] = []
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
    status: OrderStatus
    deliveryAddressId: int
    deliveryAddress: Optional[DeliveryAddressResponse] = None
    userId: int
    subOrders: List[SubOrderResponse] = []
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# --- Rating Schemas ---
# Rating still applies to the main Order (or we could choose SubOrder)
# Based on the requirement, user rates the Order, and it applies to all products.
# We'll keep Rating related to Order for now.

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
