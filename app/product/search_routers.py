from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from app.product.services import ProductService
from app.product.schemas import ProductResponse
from app.core.current_user import get_current_user, get_optional_current_user

router = APIRouter(prefix="/products", tags=["Product Search"])

@router.get("/search", response_model=List[ProductResponse], summary="Global product search with history")
async def search_products(
    q: str = Query(..., min_length=1),
    current_user = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    return await ProductService.search_products(query=q, user_id=user_id)

@router.get("/search/history", summary="Get current user search history")
async def get_search_history(
    current_user = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
):
    return await ProductService.get_search_history(user_id=current_user.id, limit=limit)

@router.delete("/search/history", summary="Clear current user search history")
async def clear_search_history(current_user = Depends(get_current_user)):
    await ProductService.clear_search_history(user_id=current_user.id)
    return {"message": "Search history cleared successfully"}
