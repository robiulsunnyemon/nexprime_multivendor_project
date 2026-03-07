import asyncio
from app.order.services import OrderService
from app.order.schemas import RatingCreate
from app.database.db import prisma

async def test_ratings():
    await prisma.connect()
    print("Database connected.")

    try:
        # 1. Find an order with uncompleted SubOrders
        order = await prisma.order.find_first(
            where={"status": "PENDING"},
            include={
                "subOrders": {
                    "include": {"orderItems": True}
                },
                "user": True
            }
        )

        if not order:
            print("No pending order found. Please run seed.py to generate sample data.")
            await prisma.disconnect()
            return
            
        print(f"\n--- Testing Incomplete Order Rating ---")
        print(f"Order ID: {order.id}, User: {order.user.email}")
        
        try:
            # Try to rate the incomplete order
            rating_data = RatingCreate(score=5, review="Great product but fast delivery.")
            await OrderService.rate_order(user_id=order.userId, order_id=order.id, rating_data=rating_data)
            print("❌ FAILED: Rating was submitted but order is NOT complete!")
        except Exception as e:
            print(f"✅ SUCCESS: Caught expected error for incomplete order => {e.detail}")


        print(f"\n--- Testing Completed Order Rating ---")
        # 2. Complete all sub-orders for this order
        for sub in order.subOrders:
            await prisma.suborder.update(
                where={"id": sub.id},
                data={"isComplete": True, "isFulfield": True}
            )
        
        # Manually invoke the status derivation so the main order is updated to DELIVERED
        await OrderService._update_order_status(order.id)
        
        print(f"Order {order.id} is now complete.")

        try:
            rating_data = RatingCreate(score=4, review="Very good quality.")
            res = await OrderService.rate_order(user_id=order.userId, order_id=order.id, rating_data=rating_data)
            print(f"✅ SUCCESS: Rating submitted successfully => {res}")
        except Exception as e:
            print(f"❌ FAILED to submit rating on completed order => {e}")

        # 3. Test GET product ratings endpoint
        print(f"\n--- Testing GET Product Ratings ---")
        # Pick the first product from the rated order
        product_id = order.subOrders[0].orderItems[0].productId
        print(f"Fetching ratings for Product ID: {product_id}")
        
        ratings = await OrderService.get_product_ratings(product_id)
        if ratings:
            print(f"✅ SUCCESS: Retrieved {len(ratings)} rating(s).")
            for r in ratings:
                print(f" - Score: {r['score']}, Review: {r['review']}")
                print(f" - User Name: {r['user']['fullname']}, Avatar: {r['user']['profileImageUrl']}")
        else:
            print("❌ FAILED: No ratings retrieved for the product.")

    except Exception as e:
         print(f"An unexpected error occurred: {e}")
         
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(test_ratings())
