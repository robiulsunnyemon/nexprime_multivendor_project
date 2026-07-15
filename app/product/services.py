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
        
        # Connecting to subcategories
        category_connect = [{"id": cid} for cid in product_data.categoryIds]
        
        # --- Logic for isDiscountSale and Calculations ---
        base_price = product_data.basePrice
        sale_price = product_data.salePrice
        is_discount_sale = product_data.isDiscountSale
        discount_percentage = 0.0

        if not is_discount_sale:
            sale_price = base_price
            discount_percentage = 0.0
        else:
            if sale_price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Sale price must be provided when product is on discount sale"
                )
            if sale_price >= base_price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Sale price must be less than base price when product is on discount sale"
                )
            # Calculate discountPercentage
            discount_percentage = round(((base_price - sale_price) / base_price) * 100, 2)

        # --- Logic for total_payable_amount ---
        shipping_charge = product_data.shippingCharge
        shipping_responsibility = product_data.shippingResponsibility
        
        tax_fee_pct = product_data.taxFee
        tax_amount = sale_price * (tax_fee_pct / 100)

        if shipping_responsibility == "CUSTOMER":
            total_payable_amount = sale_price + tax_amount + shipping_charge
        else:
            total_payable_amount = sale_price + tax_amount

        return await prisma.product.create(
            data={
                **product_data.model_dump(exclude={"categoryIds", "discountPercentage", "salePrice", "isDiscountSale", "total_payable_amount"}),
                "storeId": store_id,
                "images": image_urls,
                "isDiscountSale": is_discount_sale,
                "salePrice": sale_price,
                "discountPercentage": discount_percentage,
                "total_payable_amount": total_payable_amount,
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
        image_files: Optional[List[UploadFile]] = None,
        is_deleted: bool = False
    ):
        product = await prisma.product.find_unique(where={"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.storeId != store_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this product")
            
        update_payload = {**product_data}
        
        # Remove discountPercentage from payload to prevent manual input
        if "discountPercentage" in update_payload:
            del update_payload["discountPercentage"]

        # --- Logic for isDiscountSale and Calculations for Update ---
        # Get current values or fallback to existing
        base_price = update_payload.get("basePrice", product.basePrice)
        is_discount_sale = update_payload.get("isDiscountSale", product.isDiscountSale)
        sale_price = update_payload.get("salePrice", product.salePrice)

        if not is_discount_sale:
            update_payload["isDiscountSale"] = False
            update_payload["salePrice"] = base_price
            update_payload["discountPercentage"] = 0.0
        else:
            if sale_price is None or sale_price == 0:
                # If it was already on sale, we might have sale_price in 'product'
                sale_price = product.salePrice if product.isDiscountSale else None
                
            if sale_price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Sale price must be provided or exist when product is on discount sale"
                )
            if sale_price >= base_price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Sale price must be less than base price when product is on discount sale"
                )
            
            update_payload["isDiscountSale"] = True
            update_payload["salePrice"] = sale_price
            update_payload["discountPercentage"] = round(((base_price - sale_price) / base_price) * 100, 2)

        # --- Logic for total_payable_amount Update ---
        current_shipping_charge = update_payload.get("shippingCharge", product.shippingCharge)
        current_shipping_responsibility = update_payload.get("shippingResponsibility", product.shippingResponsibility)
        current_sale_price = update_payload.get("salePrice", product.salePrice)

        current_tax_fee = update_payload.get("taxFee", product.taxFee)
        tax_amount = current_sale_price * (current_tax_fee / 100)

        if current_shipping_responsibility == "CUSTOMER":
            update_payload["total_payable_amount"] = current_sale_price + tax_amount + current_shipping_charge
        else:
            update_payload["total_payable_amount"] = current_sale_price + tax_amount

        if image_files:
            new_image_urls = []
            for file in image_files:
                url = await upload_image_helper(file, folder="nexprime_products")
                new_image_urls.append(url)
            
            if is_deleted:
                update_payload["images"] = new_image_urls
            else:
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
        
        # Cumulative/Intersection filtering for subcategories (AND logic)
        if subcategory_ids:
            if "AND" not in where:
                where["AND"] = []
            for sid in subcategory_ids:
                where["AND"].append({
                    "categories": {
                        "some": {"id": sid}
                    }
                })
            
        # Note: 'contains' doesn't work directly on arrays in Prisma exactly the same way as String.
        # If filtering by size/color as a subset, we use 'has' for single value check.
        if size:
            where["size"] = {"has": size}
            
        if color:
            where["colors"] = {"has": color}
            
        return await prisma.product.find_many(
            where=where,
            include={"categories": True, "store": True},
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def search_products(query: str, user_id: Optional[int] = None):
        # Save search history in background (simplified here)
        await prisma.searchhistory.create(
            data={
                "query": query,
                "userId": user_id
            }
        )
        
        return await prisma.product.find_many(
            where={
                "OR": [
                    {"name": {"contains": query, "mode": "insensitive"}},
                    {"description": {"contains": query, "mode": "insensitive"}},
                    {"store": {"is": {"name": {"contains": query, "mode": "insensitive"}}}},
                    {"categories": {"some": {"name": {"contains": query, "mode": "insensitive"}}}}
                ]
            },
            include={"categories": True, "store": True},
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def get_search_history(user_id: int, limit: int = 10):
        return await prisma.searchhistory.find_many(
            where={"userId": user_id},
            order={"createdAt": "desc"},
            take=limit
        )

    @staticmethod
    async def clear_search_history(user_id: int):
        return await prisma.searchhistory.delete_many(
            where={"userId": user_id}
        )
    @staticmethod
    async def update_product_images(
        product_id: int,
        store_id: int,
        image_files: List[UploadFile],
        is_deleted: bool
    ):
        product = await prisma.product.find_unique(where={"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.storeId != store_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this product")
            
        new_image_urls = []
        for file in image_files:
            url = await upload_image_helper(file, folder="nexprime_products")
            new_image_urls.append(url)
            
        if is_deleted:
            final_images = new_image_urls
        else:
            # Combine existing images with new ones
            final_images = product.images + new_image_urls
            
        return await prisma.product.update(
            where={"id": product_id},
            data={"images": final_images},
            include={"categories": True}
        )


##----top discount products

    @staticmethod
    async def get_highest_discount_product():
        """
        Prisma find_first ব্যবহার করে সবচেয়ে বেশি discountPercentage থাকা ১ম প্রোডাক্টটি রিটার্ন করে।
        """
        product = await prisma.product.find_first(
            where={
                "isDiscountSale": True,
                "discountPercentage": {
                    "gt": 0.0
                }
            },
            order={
                "discountPercentage": "desc"  # সর্বোচ্চ ডিস্কাউন্টটি সবার আগে আসবে
            },
            include={
                "categories": True, 
                "store": True
            }
        )
        
        if not product:
            raise HTTPException(
                status_code=404, 
                detail="No discounted products found"
            )
            
        return product