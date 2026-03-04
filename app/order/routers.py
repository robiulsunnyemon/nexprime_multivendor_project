from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Optional
from app.core.current_user import get_customer, get_admin,get_vendor
from app.order.services import OrderService
from app.order.schemas import (
    DeliveryAddressCreate, DeliveryAddressResponse,
    OrderCreate, OrderResponse, RatingCreate,SubOrderResponse
)

router = APIRouter(prefix="/orders", tags=["Order & Rating Management"])

# --- Delivery Address Endpoints ---

@router.post("/delivery-address", response_model=DeliveryAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_address(
    data: DeliveryAddressCreate,
    current_customer = Depends(get_customer)
):
    return await OrderService.create_delivery_address(user_id=current_customer.id, data=data)

@router.get("/delivery-address", response_model=List[DeliveryAddressResponse])
async def get_delivery_addresses(current_customer = Depends(get_customer)):
    return await OrderService.get_delivery_addresses(user_id=current_customer.id)

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

@router.post("/{order_id}/rate")
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

# --- Vendor Endpoints ---

@router.patch("/sub-order/{suborder_id}/fulfill", response_model=SubOrderResponse)
async def update_suborder_fulfillment(
    suborder_id: int,
    is_fulfield: bool,
    current_vendor = Depends(get_vendor)
):
    return await OrderService.update_suborder_fulfillment(
        suborder_id=suborder_id, 
        is_fulfield=is_fulfield, 
        vendor_id=current_vendor.id
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

@router.get("/vendor/me", response_model=List[SubOrderResponse])
async def get_vendor_suborders(current_vendor = Depends(get_vendor)):
    return await OrderService.get_vendor_suborders(vendor_id=current_vendor.id)
