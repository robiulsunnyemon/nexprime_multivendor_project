from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from app.core.current_user import get_admin
from app.static_page.services import StaticPageService
from app.static_page.schemas import StaticPageCreate, StaticPageResponse

router = APIRouter(prefix="/static-pages", tags=["Static Pages (Privacy, Terms, etc.)"])

@router.post("", response_model=StaticPageResponse, status_code=status.HTTP_200_OK, summary="Create or Update a static page (Admin only)")
async def upsert_page(
    page_data: StaticPageCreate,
    current_admin = Depends(get_admin)
):
    return await StaticPageService.create_or_update_page(page_data)

@router.get("", response_model=List[StaticPageResponse], summary="Get all static pages")
async def get_all_pages():
    return await StaticPageService.get_all_pages()

@router.get("/{key}", response_model=StaticPageResponse, summary="Get a specific static page by key")
async def get_page(key: str):
    return await StaticPageService.get_page_by_key(key)

@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a static page (Admin only)")
async def delete_page(key: str, current_admin = Depends(get_admin)):
    await StaticPageService.delete_page(key)
    return None
