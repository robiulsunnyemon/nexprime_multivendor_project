from fastapi import APIRouter, Depends
from typing import List
from app.store.schemas import StorePublicResponse
from app.store.services import StorePublicService
from app.core.current_user import get_current_user

router = APIRouter(prefix="/stores", tags=["Store Public Management"])

@router.get("", response_model=List[StorePublicResponse], summary="Get all stores with vendor and products")
async def get_all_stores():
    return await StorePublicService.get_all_stores()

@router.get("/followed", response_model=List[StorePublicResponse], summary="Get all stores followed by the current user")
async def get_followed_stores(current_user=Depends(get_current_user)):
    return await StorePublicService.get_followed_stores(user_id=current_user.id)

@router.get("/{store_id}", response_model=StorePublicResponse, summary="Get store details with vendor and products")
async def get_store_by_id(store_id: int):
    return await StorePublicService.get_store_by_id(store_id)

@router.get("/{store_id}/follower-count", summary="Get total follower count of a store")
async def get_store_follower_count(store_id: int):
    return await StorePublicService.get_store_follower_count(store_id)

@router.post("/{store_id}/follow", summary="Follow/Unfollow a store (Toggle)")
async def toggle_follow(store_id: int, current_user=Depends(get_current_user)):
    return await StorePublicService.toggle_follow_store(store_id=store_id, user_id=current_user.id)
