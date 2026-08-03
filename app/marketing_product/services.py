from app.database.db import prisma
from app.core.upload_img_helper import upload_image_helper
from fastapi import UploadFile, HTTPException
from typing import List, Optional
from app.marketing_product.schemas import MarketingProductCreate, MarketingProductUpdate

import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class MarketingProductService:
    @staticmethod
    async def create_publishing_fee_payment_intent(creator_id: int, amount: float):
        # Stripe minimum charge for JPY currency is 50 JPY
        if amount < 50:
            return {
                "clientSecret": "",
                "paymentIntentId": "",
                "fee": amount
            }

        stripe_amount = int(amount)
        try:
            intent = stripe.PaymentIntent.create(
                amount=stripe_amount,
                currency="jpy",
                metadata={
                    "type": "marketing_product_fee",
                    "creator_id": str(creator_id)
                }
            )
            return {
                "clientSecret": intent.client_secret,
                "paymentIntentId": intent.id,
                "fee": amount
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def create_marketing_product(
        product_data: MarketingProductCreate, 
        creator_id: int, 
        image_files: List[UploadFile],
        stripe_payment_intent_id: Optional[str] = None
    ):
        fee = product_data.publishingFee
        
        # Stripe requires minimum 50 JPY for JPY payments. If fee >= 50, verify live Stripe payment intent
        if fee >= 50:
            if not stripe_payment_intent_id:
                raise HTTPException(
                    status_code=400,
                    detail="Publishing fee payment is required for this product."
                )
            try:
                intent = stripe.PaymentIntent.retrieve(stripe_payment_intent_id)
                if intent.status != "succeeded":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Publishing fee payment is not completed (status: {intent.status})."
                    )
            except stripe.error.StripeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stripe payment verification failed: {str(e)}"
                )

        # Upload images
        image_urls = []
        for file in image_files:
            url = await upload_image_helper(file, folder="marketing_products")
            image_urls.append(url)
        
        # Modify data dump to calculate price with tax
        data_dump = product_data.model_dump()
        base_price = data_dump["price"]
        tax_fee_pct = data_dump.get("taxFee", 0.0)
        tax_amount = base_price * (tax_fee_pct / 100)
        data_dump["price"] = base_price + tax_amount

        # Create product
        return await prisma.marketingproduct.create(
            data={
                **data_dump,
                "creatorId": creator_id,
                "images": image_urls
            },
            include={"creator": True}
        )

    @staticmethod
    async def get_all_marketing_products(goodsType: Optional[str] = None, location: Optional[str] = None):
        where_clause = {}
        if goodsType:
            where_clause["goodsType"] = {"equals": goodsType, "mode": "insensitive"}
        if location:
            where_clause["location"] = {"contains": location, "mode": "insensitive"}
            
        return await prisma.marketingproduct.find_many(
            where=where_clause if where_clause else None,
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
        
        # Calculate new price if price or taxFee is updated
        if "price" in data_to_update or "taxFee" in data_to_update:
            if "price" in data_to_update:
                base_price = data_to_update["price"]
            else:
                # Calculate base price from existing price and taxFee
                existing_tax_pct = product.taxFee
                base_price = product.price / (1 + existing_tax_pct / 100) if existing_tax_pct > 0 else product.price

            tax_fee_pct = data_to_update.get("taxFee", product.taxFee)
            tax_amount = base_price * (tax_fee_pct / 100)
            data_to_update["price"] = base_price + tax_amount
        
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
