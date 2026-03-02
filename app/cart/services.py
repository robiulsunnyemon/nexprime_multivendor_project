from typing import List, Optional
from app.database.db import prisma
from fastapi import HTTPException
from app.cart.schemas import CartItemCreate, CartItemUpdate
from decimal import Decimal


class CartService:
    @staticmethod
    async def add_to_cart(user_id: int, cart_data: CartItemCreate):
        # 1. Check product exists and has enough stock
        product = await prisma.product.find_unique(where={"id": cart_data.productId})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if product.stockUnits < cart_data.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {product.stockUnits}")

        # 2. Check if item already in cart
        existing_item = await prisma.cartitem.find_unique(
            where={
                "userId_productId": {
                    "userId": user_id,
                    "productId": cart_data.productId
                }
            }
        )

        if existing_item:
            # Update quantity
            new_quantity = existing_item.quantity + cart_data.quantity
            if product.stockUnits < new_quantity:
                raise HTTPException(status_code=400, detail=f"Cannot add more. Stock limit: {product.stockUnits}")
            
            return await prisma.cartitem.update(
                where={"id": existing_item.id},
                data={"quantity": new_quantity},
                include={"product": {"include": {"categories": True, "store": True}}}
            )
        
        # 3. Create new cart item
        return await prisma.cartitem.create(
            data={
                "userId": user_id,
                "productId": cart_data.productId,
                "quantity": cart_data.quantity
            },
            include={"product": {"include": {"categories": True, "store": True}}}
        )

    @staticmethod
    # async def get_user_cart(user_id: int):
    #     items = await prisma.cartitem.find_many(
    #         where={"userId": user_id},
    #         include={"product": {"include": {"categories": True, "store": True}}},
    #         order={"createdAt": "desc"}
    #     )

    #     total_amount = 0
    #     total_items = 0
    #     for item in items:
    #         price = item.product.salePrice if item.product.isOnSale and item.product.salePrice else item.product.basePrice
    #         total_amount += price * item.quantity
    #         total_items += item.quantity

    #     return {
    #         "items": items,
    #         "totalItems": total_items,
    #         "totalAmount": round(total_amount, 2)
    #     }

    async def get_user_cart(user_id: int):
        items = await prisma.cartitem.find_many(
            where={"userId": user_id},
            include={
                "product": {
                    "include": {
                        "categories": True,
                        "store": True
                    }
                }
            },
            order={"createdAt": "desc"}
        )

        total_amount = Decimal("0")
        total_items = 0

        for item in items:
            product = item.product

            if not product:
                continue  # product deleted or invalid
            
            # Using total_payable_amount from the product model
            price = Decimal(str(product.total_payable_amount or 0))

            total_amount += price * item.quantity
            total_items += item.quantity

        return {
            "items": items,
            "totalItems": total_items,
            "totalAmount": float(total_amount.quantize(Decimal("0.01")))
        }

    @staticmethod
    async def update_cart_item(user_id: int, item_id: int, update_data: CartItemUpdate):
        item = await prisma.cartitem.find_unique(
            where={"id": item_id},
            include={"product": True}
        )

        if not item or item.userId != user_id:
            raise HTTPException(status_code=404, detail="Cart item not found")

        new_quantity = item.quantity
        if update_data.action:
            if update_data.action == "increase":
                new_quantity += 1
            elif update_data.action == "decrease":
                new_quantity -= 1
        elif update_data.quantity is not None:
            new_quantity = update_data.quantity

        if new_quantity <= 0:
            await prisma.cartitem.delete(where={"id": item_id})
            return None # Or handle as deleted

        if item.product.stockUnits < new_quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {item.product.stockUnits}")

        return await prisma.cartitem.update(
            where={"id": item_id},
            data={"quantity": new_quantity},
            include={"product": {"include": {"categories": True, "store": True}}}
        )

    @staticmethod
    async def remove_from_cart(user_id: int, item_id: int):
        item = await prisma.cartitem.find_unique(where={"id": item_id})
        if not item or item.userId != user_id:
            raise HTTPException(status_code=404, detail="Cart item not found")

        await prisma.cartitem.delete(where={"id": item_id})
        return True

    @staticmethod
    async def clear_cart(user_id: int):
        await prisma.cartitem.delete_many(where={"userId": user_id})
        return True
