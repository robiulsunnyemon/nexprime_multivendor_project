from app.database.db import prisma
from app.core.upload_img_helper import upload_image_helper
from fastapi import UploadFile, HTTPException
from typing import List, Optional
from app.marketing_product.schemas import MarketingProductCreate, MarketingProductUpdate

class MarketingProductService:
    @staticmethod
    async def create_marketing_product(
        product_data: MarketingProductCreate, 
        creator_id: int, 
        image_files: List[UploadFile]
    ):
        from app.user.services.wallet_service import WalletService
        
        # 1. Deduct fee from wallet
        fee = product_data.publishingFee
        await WalletService.deduct_funds(
            user_id=creator_id,
            amount=fee,
            description=f"Publishing fee for product: {product_data.name}"
        )

        # 2. Upload images
        image_urls = []
        for file in image_files:
            url = await upload_image_helper(file, folder="marketing_products")
            image_urls.append(url)
        
        # 3. Create product
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

    @staticmethod
    async def delete_marketing_product(product_id: int, user_id: int, user_role: str):
        # 1. Fetch product
        product = await prisma.marketingproduct.find_unique(where={"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Marketing product not found")
        
        # 2. Check authorization: Creator or Admin
        if product.creatorId != user_id and user_role != "ADMIN":
            raise HTTPException(
                status_code=403, 
                detail="You don't have permission to delete this product"
            )
        
        # 3. Delete
        await prisma.marketingproduct.delete(where={"id": product_id})
        return {"message": "Marketing product deleted successfully"}

    @staticmethod
    async def update_marketing_product(
        product_id: int,
        user_id: int,
        update_data: MarketingProductUpdate,
        image_files: Optional[List[UploadFile]] = None
    ):
        # 1. Fetch product and check ownership
        product = await prisma.marketingproduct.find_unique(where={"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Marketing product not found")
        
        if product.creatorId != user_id:
            raise HTTPException(
                status_code=403, 
                detail="You don't have permission to update this product"
            )
        
        # 2. Prepare update data
        data_to_update = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        # 3. Handle images if provided
        if image_files:
            image_urls = []
            for file in image_files:
                url = await upload_image_helper(file, folder="marketing_products")
                image_urls.append(url)
            data_to_update["images"] = image_urls
        
        # 4. Update
        return await prisma.marketingproduct.update(
            where={"id": product_id},
            data=data_to_update,
            include={"creator": True}
        )
