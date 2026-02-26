from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from typing import List, Optional, Union
from app.core.current_user import get_admin
from app.category.services import CategoryService
from app.category.schemas import MainCategoryResponse, SubCategoryResponse, SubCategorySimpleResponse, MainCategoryCreate, MainCategoryUpdate

router = APIRouter(prefix="/categories", tags=["Category Management"])

@router.get("", response_model=List[MainCategoryResponse], summary="Get all main categories with subcategories")
async def get_all_categories():
    return await CategoryService.get_all_main_categories()

@router.get("/{identifier}/subcategories", response_model=List[SubCategorySimpleResponse], summary="Get subcategories by main category ID or Name")
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

@router.get("/subcategories/{subcategory_id}", response_model=SubCategoryResponse, summary="Get subcategory details with products")
async def get_subcategory_details(subcategory_id: int):
    return await CategoryService.get_subcategory_details(subcategory_id)

@router.post("/admin/main", response_model=MainCategoryResponse, status_code=status.HTTP_201_CREATED, summary="Create main category (Admin only)")
async def create_main_category(
    data: MainCategoryCreate,
    admin=Depends(get_admin)
):
    return await CategoryService.create_main_category(name=data.name)

@router.patch("/admin/main/{main_category_id}", response_model=MainCategoryResponse, summary="Update main category (Admin only)")
async def update_main_category(
    main_category_id: int,
    data: MainCategoryUpdate,
    admin=Depends(get_admin)
):
    return await CategoryService.update_main_category(main_category_id=main_category_id, name=data.name)

@router.delete("/admin/main/{main_category_id}", summary="Delete main category (Admin only)")
async def delete_main_category(
    main_category_id: int,
    admin=Depends(get_admin)
):
    await CategoryService.delete_main_category(main_category_id=main_category_id)
    return {"message": "Main category deleted successfully"}
