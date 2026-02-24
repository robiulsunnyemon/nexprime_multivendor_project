from app.database.db import prisma
from app.core.upload_img_helper import upload_image_helper
from fastapi import UploadFile, HTTPException
from typing import List, Optional
from app.marketing_product.schemas import MarketingProductCreate

class MarketingProductService:
    @staticmethod
    async def create_marketing_product(
        product_data: MarketingProductCreate, 
        creator_id: int, 
        image_files: List[UploadFile]
    ):
        image_urls = []
        for file in image_files:
            url = await upload_image_helper(file, folder="marketing_products")
            image_urls.append(url)
        
        return await prisma.marketingproduct.create(
            data={
                **product_data.model_dump(),
                "creatorId": creator_id,
                "images": image_urls
            },
            include={"creator": True}
        )

    @staticmethod
    async def get_all_marketing_products():
        return await prisma.marketingproduct.find_many(
            include={"creator": True},
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def get_my_marketing_products(creator_id: int):
        return await prisma.marketingproduct.find_many(
            where={"creatorId": creator_id},
            include={"creator": True},
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def get_marketing_product_by_id(product_id: int):
        product = await prisma.marketingproduct.find_unique(
            where={"id": product_id},
            include={"creator": True}
        )
        if not product:
            raise HTTPException(status_code=404, detail="Marketing product not found")
        return product
