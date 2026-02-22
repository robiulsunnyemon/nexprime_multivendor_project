from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from typing import List, Optional, Union
from app.core.current_user import get_admin
from app.category.services import CategoryService
from app.category.schemas import MainCategoryResponse, SubCategoryResponse

router = APIRouter(prefix="/categories", tags=["Category Management"])

@router.get("", response_model=List[MainCategoryResponse], summary="Get all main categories with subcategories")
async def get_all_categories():
    return await CategoryService.get_all_main_categories()

@router.get("/{identifier}/subcategories", response_model=List[SubCategoryResponse], summary="Get subcategories by main category ID or Name")
async def get_subcategories(identifier: str):
    return await CategoryService.get_subcategories_by_main(identifier)

@router.post("/admin/subcategories", response_model=SubCategoryResponse, status_code=status.HTTP_201_CREATED, summary="Create subcategory (Admin only)")
async def create_subcategory(
    name: str = Form(...),
    mainCategoryId: int = Form(...),
    image: UploadFile= File(...),
    admin=Depends(get_admin)
):
    return await CategoryService.create_subcategory(name=name, main_category_id=mainCategoryId, image_file=image)

@router.delete("/admin/subcategories/{subcategory_id}", summary="Delete subcategory (Admin only)")
async def delete_subcategory(
    subcategory_id: int,
    admin=Depends(get_admin)
):
    await CategoryService.delete_subcategory(subcategory_id=subcategory_id)
    return {"message": "Sub-category deleted successfully"}
