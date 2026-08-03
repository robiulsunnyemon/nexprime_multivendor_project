from fastapi import APIRouter, Depends, status, HTTPException, Request,Header
from typing import List, Optional
from app.core.current_user import get_customer, get_admin, get_vendor
from app.order.services import OrderService, SettingService, PaymentService
from app.order.schemas import (
    DeliveryAddressCreate, DeliveryAddressResponse,
    OrderCreate, OrderResponse, RatingCreate, SubOrderResponse,
    PlatformCommissionResponse, PlatformCommissionUpdate,
    RatingWithUserResponse, SubOrderFulfillRequest,SubOrderResponseForAdmin
)

router = APIRouter(prefix="/orders", tags=["Order & Rating Management"])

# --- Delivery Address Endpoints ---

@router.post("/delivery-address", response_model=DeliveryAddressResponse)
async def create_delivery_address(
    data: DeliveryAddressCreate,
    current_customer = Depends(get_customer)
):
    return await OrderService.create_delivery_address(user_id=current_customer.id, data=data)

@router.get("/delivery-address", response_model=DeliveryAddressResponse)
async def get_delivery_address(current_customer = Depends(get_customer)):
    address = await OrderService.get_delivery_address(user_id=current_customer.id)
    if not address:
        raise HTTPException(status_code=404, detail="Delivery address not found")
    return address

# --- Order Endpoints ---

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_customer = Depends(get_customer)
):
    return await OrderService.create_order(user_id=current_customer.id, order_data=order_data)

@router.get("/me", response_model=List[OrderResponse])
async def get_my_orders(current_customer = Depends(get_customer)):
    return await OrderService.get_user_orders(user_id=current_customer.id)

@router.post("/{order_id}/ratings")
async def rate_order(
    order_id: int,
    rating_data: RatingCreate,
    current_customer = Depends(get_customer)
):
    return await OrderService.rate_order(
        user_id=current_customer.id, 
        order_id=order_id, 
        rating_data=rating_data
    )

@router.get("/product/{product_id}/ratings", response_model=List[RatingWithUserResponse])
async def get_product_ratings(product_id: int):
    return await OrderService.get_product_ratings(product_id=product_id)

# --- Admin Endpoints ---

@router.patch("/{order_id}/pay", response_model=OrderResponse)
async def update_payment_status(
    order_id: int,
    is_paid: bool,
    current_admin = Depends(get_admin)
):
    return await OrderService.update_payment_status(
        order_id=order_id, 
        is_paid=is_paid
    )

@router.get("/settings/commission", response_model=PlatformCommissionResponse)
async def get_commission_setting(current_admin = Depends(get_admin)):
    return await SettingService.get_commission_setting()

@router.patch("/settings/commission", response_model=PlatformCommissionResponse)
async def update_commission_setting(
    data: PlatformCommissionUpdate,
    current_admin = Depends(get_admin)
):
    return await SettingService.update_commission_setting(percentage=data.commissionPercentage)

# --- Vendor Endpoints ---

@router.patch("/sub-order/{suborder_id}/fulfill", response_model=SubOrderResponse)
async def update_suborder_fulfillment(
    suborder_id: int,
    fulfill_data: SubOrderFulfillRequest,
    current_vendor = Depends(get_vendor)
):
    """
    ভেন্ডর সাব-অর্ডার শিপ করে Japan Post ট্র্যাকিং নম্বর সেট করেন।
    পেইড নয় এমন অর্ডারের সাব-অর্ডার ফুলফিল করা যাবে না।
    """
    return await OrderService.update_suborder_fulfillment(
        suborder_id=suborder_id,
        is_fulfield=True,
        vendor_id=current_vendor.id,
        tracking_number=fulfill_data.trackingNumber,
        courier_name=fulfill_data.courierName or "Japan Post"
    )

@router.patch("/sub-order/{suborder_id}/complete", response_model=SubOrderResponse)
async def update_suborder_completion(
    suborder_id: int,
    is_complete: bool,
    current_vendor = Depends(get_vendor)
):
    return await OrderService.update_suborder_completion(
        suborder_id=suborder_id, 
        is_complete=is_complete, 
        vendor_id=current_vendor.id
    )

@router.patch("/sub-order/{suborder_id}/confirm-receipt", response_model=SubOrderResponse)
async def confirm_suborder_receipt(
    suborder_id: int,
    current_customer = Depends(get_customer)
):
    """
    কাস্টমার অর্ডারের ডেলিভারি রিসিভ নিশ্চিত করেন।
    """
    return await OrderService.confirm_suborder_receipt(
        suborder_id=suborder_id,
        user_id=current_customer.id
    )

@router.patch("/sub-order/{suborder_id}/archive", response_model=SubOrderResponse)
async def update_suborder_archive(
    suborder_id: int,
    is_archive: bool,
    current_vendor = Depends(get_vendor)
):
    return await OrderService.update_suborder_archive(
        suborder_id=suborder_id, 
        is_archive=is_archive, 
        vendor_id=current_vendor.id
    )

# @router.get("/vendor/me", response_model=List[SubOrderResponse])
# async def get_vendor_suborders(current_vendor = Depends(get_vendor)):
#     return await OrderService.get_vendor_suborders(vendor_id=current_vendor.id)



@router.get("/vendor/me", response_model=List[SubOrderResponseForAdmin])
async def get_vendor_suborders(current_vendor = Depends(get_vendor)):
    return await OrderService.get_vendor_suborders(vendor_id=current_vendor.id)

# --- Payment Endpoints ---

@router.post("/{order_id}/create-payment-intent")
async def create_payment_intent(
    order_id: int,
    current_customer = Depends(get_customer)
):
    return await PaymentService.create_payment_intent(order_id=order_id, user_id=current_customer.id)


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    payload = await request.body()

    return await PaymentService.handle_webhook(payload, stripe_signature)