from app.database.db import prisma
from app.core.upload_img_helper import upload_image_helper
from fastapi import UploadFile, HTTPException, status
from typing import List, Optional
from app.product.schemas import ProductCreate

class ProductService:
    @staticmethod
    async def create_product(
        product_data: ProductCreate, 
        store_id: int, 
        image_files: List[UploadFile]
    ):
        image_urls = []
        for file in image_files:
            url = await upload_image_helper(file, folder="nexprime_products")
            image_urls.append(url)
        
        # Connect to subcategories
        category_connect = [{"id": cid} for cid in product_data.categoryIds]
        
        return await prisma.product.create(
            data={
                **product_data.model_dump(exclude={"categoryIds"}),
                "storeId": store_id,
                "images": image_urls,
                "categories": {
                    "connect": category_connect
                }
            },
            include={"categories": True}
        )

    @staticmethod
    async def get_products(
        main_category_id: Optional[int] = None,
        sub_category_id: Optional[int] = None,
        store_id: Optional[int] = None
    ):
        where = {}
        if store_id:
            where["storeId"] = store_id
        if sub_category_id:
            where["categories"] = {"some": {"id": sub_category_id}}
        elif main_category_id:
            where["categories"] = {"some": {"mainCategoryId": main_category_id}}
            
        return await prisma.product.find_many(
            where=where,
            include={"categories": True, "store": True},
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def get_product_by_id(product_id: int):
        product = await prisma.product.find_unique(
            where={"id": product_id},
            include={"categories": True, "store": True}
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    @staticmethod
    async def delete_product(product_id: int, store_id: int):
        product = await prisma.product.find_unique(where={"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.storeId != store_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this product")
            
        return await prisma.product.delete(where={"id": product_id})

    @staticmethod
    async def update_product(
        product_id: int,
        store_id: int,
        product_data: dict,
        category_ids: Optional[List[int]] = None,
        image_files: Optional[List[UploadFile]] = None
    ):
        product = await prisma.product.find_unique(where={"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.storeId != store_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this product")
            
        update_payload = {**product_data}
        
        if image_files:
            new_image_urls = []
            for file in image_files:
                url = await upload_image_helper(file, folder="nexprime_products")
                new_image_urls.append(url)
            update_payload["images"] = product.images + new_image_urls

        if category_ids is not None:
            update_payload["categories"] = {
                "set": [{"id": cid} for cid in category_ids]
            }

        return await prisma.product.update(
            where={"id": product_id},
            data=update_payload,
            include={"categories": True}
        )

    @staticmethod
    async def get_products_filtered(
        shop_id: Optional[int] = None,
        subcategory_ids: Optional[List[int]] = None,
        size: Optional[str] = None,
        color: Optional[str] = None
    ):
        where = {}
        if shop_id:
            where["storeId"] = shop_id
        
        if subcategory_ids:
            where["categories"] = {
                "some": {
                    "id": {"in": subcategory_ids}
                }
            }
            
        if size:
            where["size"] = {
                "contains": size,
                "mode": "insensitive"
            }
            
        if color:
            where["colors"] = {
                "contains": color,
                "mode": "insensitive"
            }
            
        return await prisma.product.find_many(
            where=where,
            include={"categories": True, "store": True},
            order={"createdAt": "desc"}
        )
