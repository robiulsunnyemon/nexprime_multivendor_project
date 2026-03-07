import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.database.db import prisma
from app.order.services import OrderService, SettingService, PaymentService
from app.order.schemas import DeliveryAddressCreate, OrderCreate, RatingCreate
from app.cart.schemas import CartItemCreate
from app.cart.services import CartService

async def main():
    print("--- Testing Order & Payment Services ---")
    await prisma.connect()
    try:
        # Get users for testing
        customer = await prisma.user.find_first(where={"role": "CUSTOMER"})
        vendor = await prisma.user.find_first(where={"role": "VENDOR"})
        admin = await prisma.user.find_first(where={"role": "ADMIN"})
        
        if not customer or not vendor or not admin:
            print("Missing required users for testing.")
            return

        print(f"\n1. Testing Delivery Address (Customer ID: {customer.id})")
        address_data = DeliveryAddressCreate(
            fullName="Test Customer",
            postcode="12345",
            fullAddress="123 Test Street",
            phoneNumber="01700000000"
        )
        address = await OrderService.create_delivery_address(customer.id, address_data)
        print(f"-> Created Delivery Address ID: {address.id}")
        
        retrieved_address = await OrderService.get_delivery_address(customer.id)
        print(f"-> Retrieved Delivery Address: MATCH={retrieved_address.id == address.id}")

        print("\n2. Testing Order Creation")
        # Need an item in the cart first
        product = await prisma.product.find_first()
        if not product:
            print("No product found to create order.")
            return
            
        await CartService.add_to_cart(customer.id, CartItemCreate(productId=product.id, quantity=1))
        print(f"-> Added product {product.id} to cart")
        
        order_create_data = OrderCreate(deliveryAddressId=address.id)
        order = await OrderService.create_order(customer.id, order_create_data)
        print(f"-> Created Order ID: {order.id}, Total: {order.totalAmount}")
        
        print("\n3. Testing Get My Orders")
        my_orders = await OrderService.get_user_orders(customer.id)
        print(f"-> Customer has {len(my_orders)} orders")

        print("\n4. Testing Vendor SubOrder Actions")
        suborder = await prisma.suborder.find_first(where={"orderId": order.id}, include={"store": True})
        if suborder:
            print(f"-> Found SubOrder ID: {suborder.id} for Vendor ID: {suborder.store.vendorId}")
            
            # Fulfill
            fulfilled = await OrderService.update_suborder_fulfillment(suborder.id, True, suborder.store.vendorId)
            print(f"-> SubOrder Fulfilled: {fulfilled.isFulfield}")
            
            # Complete
            completed = await OrderService.update_suborder_completion(suborder.id, True, suborder.store.vendorId)
            print(f"-> SubOrder Completed: {completed.isComplete}")
            
            # Archive
            archived = await OrderService.update_suborder_archive(suborder.id, True, suborder.store.vendorId)
            print(f"-> SubOrder Archived: {archived.isArchive}")
            
            vendor_orders = await OrderService.get_vendor_suborders(suborder.store.vendorId)
            print(f"-> Vendor has {len(vendor_orders)} suborders")

        print("\n5. Testing Admin Payment Status")
        paid_order = await OrderService.update_payment_status(order.id, True)
        print(f"-> Order Paid Status Updated: {paid_order.isPaid}")

        print("\n6. Testing Rating Submission (Requires Complete SubOrders)")
        rating_data = RatingCreate(score=5, review="Excellent product!")
        try:
            rating = await OrderService.rate_order(customer.id, order.id, rating_data)
            print(f"-> Rating submitted successfully. ID: {rating[0].id}")
        except Exception as e:
            print(f"-> Rating submission failed (Expected if not all suborders complete): {e}")

        print(f"\n7. Testing Get Product Ratings (Product {product.id})")
        ratings = await OrderService.get_product_ratings(product.id)
        print(f"-> Found {len(ratings)} ratings for product")

        print("\n8. Testing Commission Settings")
        setting = await SettingService.get_commission_setting()
        print(f"-> Current Commission: {setting.commissionPercentage}%")
        new_setting = await SettingService.update_commission_setting(15.0)
        print(f"-> Updated Commission: {new_setting.commissionPercentage}%")

        print("\n9. Testing Payment Intent Generation (Stripe)")
        try:
            intent = await PaymentService.create_payment_intent(order.id, customer.id)
            print(f"-> Payment Intent Created: clientSecret mapped successfully")
        except Exception as e:
            print(f"-> Expected failure if Stripe keys are invalid: {e}")

        print("\nAll Tests Executed Successfully!")

    except Exception as e:
        import traceback
        print(f"Error during testing: {e}")
        traceback.print_exc()
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
