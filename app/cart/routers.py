from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Optional
from app.core.current_user import get_customer
from app.cart.services import CartService
from app.cart.schemas import CartItemCreate, CartItemUpdate, CartItemResponse, CartSummaryResponse

router = APIRouter(prefix="/cart", tags=["Cart Management"])

@router.post("", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED, summary="Add product to cart")
async def add_to_cart(
    cart_data: CartItemCreate,
    current_customer = Depends(get_customer)
):
    return await CartService.add_to_cart(user_id=current_customer.id, cart_data=cart_data)

@router.get("", response_model=CartSummaryResponse, summary="Get user cart")
async def get_cart(current_customer = Depends(get_customer)):
    return await CartService.get_user_cart(user_id=current_customer.id)

@router.patch("/{item_id}", response_model=Optional[CartItemResponse], summary="Update cart item quantity (Increase/Decrease)")
async def update_cart_item(
    item_id: int,
    update_data: CartItemUpdate,
    current_customer = Depends(get_customer)
):
    return await CartService.update_cart_item(
        user_id=current_customer.id,
        item_id=item_id,
        update_data=update_data
    )

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove item from cart")
async def remove_from_cart(
    item_id: int,
    current_customer = Depends(get_customer)
):
    await CartService.remove_from_cart(user_id=current_customer.id, item_id=item_id)
    return None

@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Clear entire cart")
async def clear_cart(current_customer = Depends(get_customer)):
    await CartService.clear_cart(user_id=current_customer.id)
    return None
