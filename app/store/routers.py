from fastapi import APIRouter
from typing import List
from app.store.schemas import StorePublicResponse
from app.store.services import StorePublicService

router = APIRouter(prefix="/stores", tags=["Store Public Management"])

@router.get("", response_model=List[StorePublicResponse], summary="Get all stores with vendor and products")
async def get_all_stores():
    return await StorePublicService.get_all_stores()

@router.get("/{store_id}", response_model=StorePublicResponse, summary="Get store details with vendor and products")
async def get_store_by_id(store_id: int):
    return await StorePublicService.get_store_by_id(store_id)
