from typing import List, Optional
from app.database.db import prisma
from fastapi import HTTPException
from app.order.schemas import DeliveryAddressCreate, OrderCreate, RatingCreate
from app.cart.services import CartService
from decimal import Decimal
import stripe
import os

# Stripe secret key should be in .env
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class OrderService:
    @staticmethod
    async def create_delivery_address(user_id: int, data: DeliveryAddressCreate):
        existing_address = await prisma.deliveryaddress.find_first(
            where={"userId": user_id}
        )
        if existing_address:
            return await prisma.deliveryaddress.update(
                where={"id": existing_address.id},
                data={**data.model_dump()}
            )
        
        return await prisma.deliveryaddress.create(
            data={
                **data.model_dump(),
                "userId": user_id
            }
        )

    @staticmethod
    async def get_delivery_address(user_id: int):
        return await prisma.deliveryaddress.find_first(
            where={"userId": user_id}
        )

    @staticmethod
    async def create_order(user_id: int, order_data: OrderCreate):
        # 1. Get cart items
        cart = await CartService.get_user_cart(user_id)
        if not cart["items"]:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # 2. Group items by storeId
        items_by_store = {}
        for item in cart["items"]:
            if item.product.stockUnits < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Product {item.product.name} has insufficient stock."
                )
            
            store_id = item.product.storeId
            if store_id not in items_by_store:
                items_by_store[store_id] = []
            items_by_store[store_id].append(item)

        # 3. Create Order and SubOrders in a transaction
        async with prisma.tx() as tx:
            # a. Create the main Order
            order = await tx.order.create(
                data={
                    "totalAmount": cart["totalAmount"],
                    "userId": user_id,
                    "deliveryAddressId": order_data.deliveryAddressId,
                }
            )

            # b. Create SubOrders and OrderItems
            for store_id, store_items in items_by_store.items():
                sub_total = sum(
                    Decimal(str(item.product.total_payable_amount or 0)) * item.quantity 
                    for item in store_items
                )
                
                sub_order = await tx.suborder.create(
                    data={
                        "orderId": order.id,
                        "storeId": store_id,
                        "subTotal": float(sub_total)
                    }
                )

                for item in store_items:
                    price = item.product.total_payable_amount or 0
                    
                    await tx.orderitem.create(
                        data={
                            "subOrderId": sub_order.id,
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
                include={
                    "subOrders": {
                        "include": {"orderItems": True}
                    }, 
                    "deliveryAddress": True
                }
            )

    @staticmethod
    async def get_user_orders(user_id: int):
        return await prisma.order.find_many(
            where={"userId": user_id},
            include={
                "subOrders": {
                    "include": {
                        "orderItems": {"include": {"product": True}},
                        "store": True
                    }
                }, 
                "deliveryAddress": True
            },
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def rate_order(user_id: int, order_id: int, rating_data: RatingCreate):
        # 1. Verify order
        order = await prisma.order.find_unique(
            where={"id": order_id},
            include={
                "subOrders": {
                    "include": {
                        "orderItems": {"include": {"product": True}}
                    }
                }
            }
        )

        if not order or order.userId != user_id:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if all sub orders are completed? 
        # Or should we allow rating per SubOrder?
        # Requirement says "Order ID pass kore rating dibe category user, kintu backend-e sei order-er sokol ponnyer upor rating add hoye jabe"
        # Since the requirement is very specific about "all products of that order", we'll check if all suborders are completed.
        
        all_complete = all(so.isComplete for so in order.subOrders)
        if not all_complete:
            raise HTTPException(status_code=400, detail="Cannot rate until all items in the order are completed")

        existing_rating = await prisma.rating.find_first(
            where={"orderId": order_id, "userId": user_id}
        )
        if existing_rating:
            raise HTTPException(status_code=400, detail="Order already rated")

        async with prisma.tx() as tx:
            # Store already rated products to avoid duplicates (though SubOrders should be unique by store)
            processed_products = set()
            
            for sub_order in order.subOrders:
                for item in sub_order.orderItems:
                    product = item.product
                    if product.id in processed_products:
                        continue
                        
                    # a. Create Rating entry
                    await tx.rating.create(
                        data={
                            "score": rating_data.score,
                            "review": rating_data.review,
                            "productId": product.id,
                            "userId": user_id,
                            "orderId": order.id
                        }
                    )

                    # b. Update average
                    old_avg = product.averageRating or 0
                    old_count = product.totalRatings or 0
                    new_count = old_count + 1
                    new_avg = ((old_avg * old_count) + rating_data.score) / new_count

                    await tx.product.update(
                        where={"id": product.id},
                        data={
                            "averageRating": new_avg,
                            "totalRatings": new_count
                        }
                    )
                    processed_products.add(product.id)
        
        return {"message": "Rating submitted successfully for all products in the order"}

    @staticmethod
    async def get_product_ratings(product_id: int):
        ratings = await prisma.rating.find_many(
            where={"productId": product_id},
            include={
                "user": True  # To fetch user details like name & avatar
            },
            order={"createdAt": "desc"}
        )
        
        # Format the response appropriately
        formatted_ratings = []
        for r in ratings:
            formatted_ratings.append({
                "id": r.id,
                "score": r.score,
                "review": r.review,
                "productId": r.productId,
                "orderId": r.orderId,
                "userId": r.userId,
                "user": {
                    "id": r.user.id if r.user else None,
                    "fullname": r.user.fullname if r.user else "Unknown User",
                    "profileImageUrl": getattr(r.user, 'profileImageUrl', None) if r.user else None
                },
                "createdAt": r.createdAt,
                "updatedAt": r.updatedAt
            })
            
        return formatted_ratings

    @staticmethod
    async def _update_order_status(order_id: int, tx=None):
        """
        Derives and updates the main Order status based on its SubOrders:
        1. PENDING: All SubOrders isFulfield = False
        2. SHIPPED: At least one SubOrder isFulfield = True, but not all isComplete = True
        3. DELIVERED: All SubOrders isComplete = True
        """
        client = tx if tx else prisma
        
        order = await client.order.find_unique(
            where={"id": order_id},
            include={"subOrders": True}
        )
        
        if not order:
            return

        is_any_fulfilled = any(so.isFulfield for so in order.subOrders)
        is_all_completed = all(so.isComplete for so in order.subOrders)

        new_status = "PENDING"
        if is_all_completed:
            new_status = "DELIVERED"
        elif is_any_fulfilled:
            new_status = "SHIPPED"
        
        if order.status != new_status:
            await client.order.update(
                where={"id": order_id},
                data={"status": new_status}
            )

    @staticmethod
    async def update_payment_status(order_id: int, is_paid: bool):
        # Payment is at Order level
        return await prisma.order.update(
            where={"id": order_id},
            data={"isPaid": is_paid}
        )

    @staticmethod
    async def update_suborder_fulfillment(suborder_id: int, is_fulfield: bool, vendor_id: int):
        sub_order = await prisma.suborder.find_unique(
            where={"id": suborder_id},
            include={"store": True}
        )
        if not sub_order or sub_order.store.vendorId != vendor_id:
            raise HTTPException(status_code=403, detail="You do not own this sub-order.")

        updated_suborder = await prisma.suborder.update(
            where={"id": suborder_id},
            data={"isFulfield": is_fulfield},
            include={"orderItems": True}
        )
        
        # Trigger status derivation
        await OrderService._update_order_status(sub_order.orderId)
        
        return updated_suborder

    @staticmethod
    async def update_suborder_completion(suborder_id: int, is_complete: bool, vendor_id: int):
        sub_order = await prisma.suborder.find_unique(
            where={"id": suborder_id},
            include={"store": True}
        )
        if not sub_order or sub_order.store.vendorId != vendor_id:
            raise HTTPException(status_code=403, detail="You do not own this sub-order.")

        updated_suborder = await prisma.suborder.update(
            where={"id": suborder_id},
            data={"isComplete": is_complete},
            include={"orderItems": True}
        )
        
        # Trigger status derivation
        await OrderService._update_order_status(sub_order.orderId)
        
        return updated_suborder

    @staticmethod
    async def update_suborder_archive(suborder_id: int, is_archive: bool, vendor_id: int):
        sub_order = await prisma.suborder.find_unique(
            where={"id": suborder_id},
            include={"store": True}
        )
        if not sub_order or sub_order.store.vendorId != vendor_id:
            raise HTTPException(status_code=403, detail="You do not own this sub-order.")

        return await prisma.suborder.update(
            where={"id": suborder_id},
            data={"isArchive": is_archive},
            include={"orderItems": True}
        )

    @staticmethod
    async def get_vendor_suborders(vendor_id: int):
        return await prisma.suborder.find_many(
            where={
                "store": {
                    "vendorId": vendor_id
                }
            },
            include={
                "orderItems": {"include": {"product": True}},
                "order": {"include": {"deliveryAddress": True}}
            },
            order={"createdAt": "desc"}
        )

class SettingService:
    @staticmethod
    async def get_commission_setting():
        setting = await prisma.platformcommissionsetting.find_first(where={"id": 1})
        if not setting:
            # Seed default if not exists
            setting = await prisma.platformcommissionsetting.create(
                data={"id": 1, "commissionPercentage": 10.0}
            )
        return setting

    @staticmethod
    async def update_commission_setting(percentage: float):
        return await prisma.platformcommissionsetting.update(
            where={"id": 1},
            data={"commissionPercentage": percentage}
        )

class PaymentService:
    @staticmethod
    async def create_payment_intent(order_id: int, user_id: int):
        order = await prisma.order.find_unique(where={"id": order_id})
        if not order or order.userId != user_id:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Stripe expects amount in cents
        amount = int(order.totalAmount * 100)
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="usd", 
                metadata={"order_id": order.id}
            )
            return {"clientSecret": intent.client_secret}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def create_wallet_topup_intent(user_id: int, amount: float):
        # amount is in dollars, convert to cents for Stripe
        stripe_amount = int(amount * 100)
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=stripe_amount,
                currency="usd",
                metadata={
                    "type": "wallet_topup",
                    "user_id": user_id
                }
            )
            return {"clientSecret": intent.client_secret}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def handle_webhook(payload: bytes, sig_header: str):
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET") or ""
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except Exception as e:
            # Fallback for testing without a real secret during development if needed
            if not endpoint_secret:
                # DANGEROUS: Only for dev if secrets aren't set yet
                import json
                event_data = json.loads(payload)
                if event_data['type'] == 'payment_intent.succeeded':
                    intent = event_data['data']['object']
                    order_id = int(intent['metadata']['order_id'])
                    await PaymentService.process_successful_payment(order_id)
                return {"status": "success (mocked)"}
            raise HTTPException(status_code=400, detail="Invalid webhook payload")

        if event['type'] == 'payment_intent.succeeded':
            intent = event['data']['object']
            p_type = intent['metadata'].get("type")
            
            if p_type == "wallet_topup":
                user_id = int(intent['metadata']['user_id'])
                amount = intent['amount'] / 100.0
                await PaymentService.process_wallet_topup(user_id, amount)
            else:
                order_id = int(intent['metadata']['order_id'])
                await PaymentService.process_successful_payment(order_id)
        
        return {"status": "success"}

    @staticmethod
    async def process_wallet_topup(user_id: int, amount: float):
        from app.user.services.wallet_service import WalletService
        await WalletService.add_funds(user_id, amount, description=f"Stripe Top-up: ${amount}")

    @staticmethod
    async def process_successful_payment(order_id: int):
        # Using a transaction to ensure atomic split
        async with prisma.tx() as tx:
            # 1. Update Order status
            await tx.order.update(
                where={"id": order_id},
                data={"isPaid": True}
            )

            # 2. Get commission setting
            setting = await tx.platformcommissionsetting.find_first(where={"id": 1})
            commission_pct = setting.commissionPercentage if setting else 10.0

            # 3. Calculate and update SubOrders
            sub_orders = await tx.suborder.find_many(where={"orderId": order_id})
            for so in sub_orders:
                commission = so.subTotal * (commission_pct / 100)
                earnings = so.subTotal - commission
                
                await tx.suborder.update(
                    where={"id": so.id},
                    data={
                        "commissionAmount": float(Decimal(str(commission)).quantize(Decimal("0.01"))),
                        "vendorEarnings": float(Decimal(str(earnings)).quantize(Decimal("0.01")))
                    }
                )
