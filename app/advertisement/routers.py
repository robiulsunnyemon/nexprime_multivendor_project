from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from typing import List, Optional
from app.core.current_user import get_admin
from app.advertisement.services import BannerService
from app.advertisement.schemas import BannerResponse

router = APIRouter(tags=["Advertisement"])

@router.post("/admin/banners", response_model=BannerResponse, status_code=status.HTTP_201_CREATED, summary="Upload new banner (Admin only)")
async def upload_banner(
    link: Optional[str] = Form(None),
    image: UploadFile = File(...),
    admin=Depends(get_admin)
):
    return await BannerService.create_banner(image_file=image, link=link)

@router.get("/banners", response_model=List[BannerResponse], summary="Get all banners")
async def get_banners():
    return await BannerService.get_all_banners()

@router.delete("/admin/banners/{banner_id}", summary="Delete a banner (Admin only)")
async def delete_banner(
    banner_id: int,
    admin=Depends(get_admin)
):
    await BannerService.delete_banner(banner_id=banner_id)
    return {"message": "Banner deleted successfully"}
