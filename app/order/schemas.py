from pydantic import BaseModel, Field, model_validator
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

class ProductMinResponse(BaseModel):
    id: int
    name: str
    images: List[str]  

    class Config:
        from_attributes = True

class OrderItemResponse(OrderItemBase):
    id: int
    subOrderId: int
    product: Optional[ProductMinResponse] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# --- SubOrder Schemas ---

class SubOrderFulfillRequest(BaseModel):
    trackingNumber: str
    courierName: Optional[str] = "Japan Post"

class SubOrderResponse(BaseModel):
    id: int
    orderId: int
    storeId: int
    subTotal: float
    commissionAmount: float
    vendorEarnings: float
    isFulfield: bool
    isComplete: bool
    isArchive: bool
    trackingNumber: Optional[str] = None
    courierName: Optional[str] = None
    trackingUrl: Optional[str] = None
    orderItems: List[OrderItemResponse] = []
    createdAt: datetime
    updatedAt: datetime

    @model_validator(mode="after")
    def generate_tracking_url(self) -> "SubOrderResponse":
        """ট্র্যাকিং নম্বর থাকলে জাপান পোস্টের ডাইরেক্ট ট্র্যাকিং URL তৈরি করে।"""
        if self.trackingNumber:
            self.trackingUrl = (
                f"https://trackings.post.japanpost.jp/services/srv/search/"
                f"direct?reqCodeNo1={self.trackingNumber}"
            )
        return self

    class Config:
        from_attributes = True
## vendor
##___________________start___________________
# --- প্রয়োজনীয় এনামসমূহ (Prisma স্কিমা অনুযায়ী) ---
class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"

class ProductSize(str, Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    XXXL = "XXXL"
    FREE_SIZE = "FREE_SIZE"

class ShippingResponsibility(str, Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"

# --- ১. কাস্টমার/ইউজারের জন্য অ্যাডমিন স্কিমা ---
class UserMinResponseForAdmin(BaseModel):
    id: int
    fullname: str
    email: str
    phonenumber: str
    is_verified: bool
    profileImageUrl: Optional[str] = None
    residentcard_frontside: Optional[str] = None 
    residentcard_backside: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


# --- ২. ডেলিভারি অ্যাড্রেসের জন্য অ্যাডমিন স্কিমা ---
class DeliveryAddressResponseForAdmin(BaseModel):
    id: int
    userId: int
    fullName: str
    postcode: str
    fullAddress: str
    buildingNameRoomNumber: Optional[str] = None
    phoneNumber: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


# --- ৩. অর্ডারের জন্য অ্যাডমিন স্কিমা ---
class OrderMinResponseForAdmin(BaseModel):
    id: int
    totalAmount: float
    isPaid: bool
    status: OrderStatus
    userId: int
    createdAt: datetime
    updatedAt: datetime
    deliveryAddress: Optional[DeliveryAddressResponseForAdmin] = None 
    user: Optional[UserMinResponseForAdmin] = None 

    class Config:
        from_attributes = True


# --- ৪. প্রোডাক্টের বিস্তারিত তথ্যের জন্য স্কিমা (নতুন) ---
class ProductDetailResponseForAdmin(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    basePrice: float
    stockUnits: int
    size: List[ProductSize]
    colors: List[str]
    isDiscountSale: bool
    salePrice: Optional[float] = None
    discountPercentage: Optional[float] = None
    shippingResponsibility: ShippingResponsibility
    shippingCharge: float
    total_payable_amount: float
    images: List[str]
    averageRating: float
    totalRatings: int
    storeId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


# --- ৫. অর্ডার আইটেমের জন্য অ্যাডমিন স্কিমা (নতুন) ---
class OrderItemResponseForAdmin(BaseModel):
    id: int
    subOrderId: int
    productId: int
    quantity: int
    price: float
    createdAt: datetime
    updatedAt: datetime
    # 🌟 এখানে প্রোডাক্টের সব ডিটেইলস ইনক্লুড করা হয়েছে
    product: Optional[ProductDetailResponseForAdmin] = None 

    class Config:
        from_attributes = True


# --- ৬. ফাইনাল সাব-অর্ডার অ্যাডমিন স্কিমা ---
class SubOrderResponseForAdmin(BaseModel):
    id: int
    orderId: int
    storeId: int
    subTotal: float
    commissionAmount: float
    vendorEarnings: float
    isFulfield: bool
    isComplete: bool
    isArchive: bool
    trackingNumber: Optional[str] = None
    courierName: Optional[str] = None
    trackingUrl: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    
    # 🌟 আপডেট করা হয়েছে: সাধারণ OrderItemResponse এর বদলে অ্যাডমিন ভার্সন ব্যবহার করা হয়েছে
    orderItems: List[OrderItemResponseForAdmin] = []
    order: Optional[OrderMinResponseForAdmin] = None 

    @model_validator(mode="after")
    def generate_tracking_url(self) -> "SubOrderResponseForAdmin":
        if self.trackingNumber:
            self.trackingUrl = (
                f"https://trackings.post.japanpost.jp/services/srv/search/"
                f"direct?reqCodeNo1={self.trackingNumber}"
            )
        return self

    class Config:
        from_attributes = True


        #_______________end__________________

# --- Setting Schemas ---

class PlatformCommissionResponse(BaseModel):
    id: int
    commissionPercentage: float
    updatedAt: datetime

    class Config:
        from_attributes = True

class PlatformCommissionUpdate(BaseModel):
    commissionPercentage: float

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

class RatingUserDetail(BaseModel):
    id: int
    fullname: str
    profileImageUrl: Optional[str] = None

class RatingWithUserResponse(BaseModel):
    id: int
    score: int
    review: Optional[str]
    productId: int
    orderId: int
    userId: int
    user: RatingUserDetail
    createdAt: datetime
    updatedAt: datetime
