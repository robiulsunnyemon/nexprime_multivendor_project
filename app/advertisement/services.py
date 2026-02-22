from app.database.db import prisma
from app.core.upload_img_helper import upload_image_helper
from fastapi import UploadFile, HTTPException, status
from typing import Optional

class BannerService:
    @staticmethod
    async def create_banner(image_file: UploadFile, link: Optional[str] = None):
        image_url = await upload_image_helper(image_file, folder="nexprime_banners")
        return await prisma.banner.create(
            data={
                "imageUrl": image_url,
                "link": link
            }
        )

    @staticmethod
    async def get_all_banners():
        return await prisma.banner.find_many(order={"createdAt": "desc"})

    @staticmethod
    async def delete_banner(banner_id: int):
        banner = await prisma.banner.find_unique(where={"id": banner_id})
        if not banner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found"
            )
        return await prisma.banner.delete(where={"id": banner_id})
