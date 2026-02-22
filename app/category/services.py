from app.database.db import prisma
from app.core.upload_img_helper import upload_image_helper
from fastapi import UploadFile, HTTPException, status
from typing import Optional, Union

class CategoryService:
    @staticmethod
    async def get_all_main_categories():
        return await prisma.maincategory.find_many(
            include={"subCategories": True},
            order={"name": "asc"}
        )

    @staticmethod
    async def get_subcategories_by_main(identifier: Union[int, str]):
        if isinstance(identifier, int) or identifier.isdigit():
            main_cat_id = int(identifier)
            return await prisma.subcategory.find_many(
                where={"mainCategoryId": main_cat_id},
                order={"name": "asc"}
            )
        else:
            main_cat = await prisma.maincategory.find_unique(where={"name": identifier})
            if not main_cat:
                raise HTTPException(status_code=404, detail="Main category not found")
            return await prisma.subcategory.find_many(
                where={"mainCategoryId": main_cat.id},
                order={"name": "asc"}
            )

    @staticmethod
    async def create_subcategory(name: str, main_category_id: int, image_file: Optional[UploadFile] = None):
        image_url = None
        if image_file:
            image_url = await upload_image_helper(image_file, folder="nexprime_categories")
        
        return await prisma.subcategory.create(
            data={
                "name": name,
                "mainCategoryId": main_category_id,
                "image": image_url
            }
        )

    @staticmethod
    async def delete_subcategory(subcategory_id: int):
        sub_cat = await prisma.subcategory.find_unique(where={"id": subcategory_id})
        if not sub_cat:
            raise HTTPException(status_code=404, detail="Sub-category not found")
        return await prisma.subcategory.delete(where={"id": subcategory_id})
