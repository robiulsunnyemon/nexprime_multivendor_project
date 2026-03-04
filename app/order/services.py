from typing import List, Optional
from app.database.db import prisma
from fastapi import HTTPException
from app.order.schemas import DeliveryAddressCreate, OrderCreate, RatingCreate
from app.cart.services import CartService
from decimal import Decimal

class OrderService:
    @staticmethod
    async def create_delivery_address(user_id: int, data: DeliveryAddressCreate):
        return await prisma.deliveryaddress.create(
            data={
                **data.model_dump(),
                "userId": user_id
            }
        )

    @staticmethod
    async def get_delivery_addresses(user_id: int):
        return await prisma.deliveryaddress.find_many(
            where={"userId": user_id}
        )

    @staticmethod
    async def create_order(user_id: int, order_data: OrderCreate):
        # 1. Get cart items
        cart = await CartService.get_user_cart(user_id)
        if not cart["items"]:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # 2. Check stock for all items
        for item in cart["items"]:
            if item.product.stockUnits < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Product {item.product.name} has insufficient stock."
                )

        # 3. Create Order in a transaction
        # Note: prisma-client-py supports transactions via async with prisma.tx()
        async with prisma.tx() as tx:
            # a. Create the Order
            order = await tx.order.create(
                data={
                    "totalAmount": cart["totalAmount"],
                    "userId": user_id,
                    "deliveryAddressId": order_data.deliveryAddressId,
                }
            )

            # b. Create OrderItems and decrement stock
            for item in cart["items"]:
                # Record the price at the time of order
                price = item.product.total_payable_amount or 0
                
                await tx.orderitem.create(
                    data={
                        "orderId": order.id,
                        "productId": item.product.id,
                        "quantity": item.quantity,
                        "price": float(price)
                    }
                )

                # Update product stock
                await tx.product.update(
                    where={"id": item.product.id},
                    data={"stockUnits": {"decrement": item.quantity}}
                )

            # c. Clear cart
            await tx.cartitem.delete_many(where={"userId": user_id})

            return await tx.order.find_unique(
                where={"id": order.id},
                include={"orderItems": True, "deliveryAddress": True}
            )

    @staticmethod
    async def get_user_orders(user_id: int):
        return await prisma.order.find_many(
            where={"userId": user_id},
            include={"orderItems": {"include": {"product": True}}, "deliveryAddress": True},
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def rate_order(user_id: int, order_id: int, rating_data: RatingCreate):
        # 1. Verify order
        order = await prisma.order.find_unique(
            where={"id": order_id},
            include={"orderItems": {"include": {"product": True}}}
        )

        if not order or order.userId != user_id:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not order.isFulfield:
            raise HTTPException(status_code=400, detail="Cannot rate an unfulfilled order")

        # Check if already rated
        existing_rating = await prisma.rating.find_first(
            where={"orderId": order_id, "userId": user_id}
        )
        if existing_rating:
            raise HTTPException(status_code=400, detail="Order already rated")

        async with prisma.tx() as tx:
            for item in order.orderItems:
                product = item.product
                
                # a. Create Rating entry for this product
                await tx.rating.create(
                    data={
                        "score": rating_data.score,
                        "review": rating_data.review,
                        "productId": product.id,
                        "userId": user_id,
                        "orderId": order.id
                    }
                )

                # b. Calculate new average rating
                # Formula: new_avg = ((old_avg * old_count) + new_score) / (old_count + 1)
                old_avg = product.averageRating or 0
                old_count = product.totalRatings or 0
                new_count = old_count + 1
                new_avg = ((old_avg * old_count) + rating_data.score) / new_count

                # c. Update product
                await tx.product.update(
                    where={"id": product.id},
                    data={
                        "averageRating": new_avg,
                        "totalRatings": new_count
                    }
                )
        
        return {"message": "Rating submitted successfully for all products in the order"}

    @staticmethod
    async def update_payment_status(order_id: int, is_paid: bool):
        return await prisma.order.update(
            where={"id": order_id},
            data={"isPaid": is_paid}
        )

    @staticmethod
    async def update_fulfillment_status(order_id: int, is_fulfield: bool):
        return await prisma.order.update(
            where={"id": order_id},
            data={"isFulfield": is_fulfield}
        )
