import asyncio
from app.database.db import prisma
from app.cart.services import CartService
from app.cart.schemas import CartItemCreate, CartItemUpdate

async def verify_cart():
    await prisma.connect()
    print("--- Testing Cart Module ---")
    
    # 1. Fetch a customer and a product
    customer = await prisma.user.find_first(where={"role": "CUSTOMER"})
    product = await prisma.product.find_first()
    
    if not (customer and product):
        print("Required data missing. Please seed the database.")
        await prisma.disconnect()
        return
        
    print(f"Testing with Customer: {customer.email} | Product: {product.name}")

    # 2. Add to cart
    print("1. Adding to cart...")
    item = await CartService.add_to_cart(
        user_id=customer.id,
        cart_data=CartItemCreate(productId=product.id, quantity=1)
    )
    print(f"   Added. Current Quantity: {item.quantity}")

    # 3. Increase quantity
    print("2. Increasing quantity...")
    updated_item = await CartService.update_cart_item(
        user_id=customer.id,
        item_id=item.id,
        update_data=CartItemUpdate(action="increase")
    )
    print(f"   Increased. Current Quantity: {updated_item.quantity}")

    # 4. Decrease quantity
    print("3. Decreasing quantity...")
    updated_item = await CartService.update_cart_item(
        user_id=customer.id,
        item_id=item.id,
        update_data=CartItemUpdate(action="decrease")
    )
    print(f"   Decreased. Current Quantity: {updated_item.quantity}")

    # 5. Get full cart summary
    print("4. Fetching cart summary...")
    cart_summary = await CartService.get_user_cart(user_id=customer.id)
    print(f"   Total Items: {cart_summary['totalItems']} | Total Amount: {cart_summary['totalAmount']}")

    # 6. Remove item
    print("5. Removing item from cart...")
    await CartService.remove_from_cart(user_id=customer.id, item_id=item.id)
    print("   Removed.")

    # 7. Final check
    final_cart = await CartService.get_user_cart(user_id=customer.id)
    if final_cart['totalItems'] == 0:
        print("SUCCESS: Cart module is working correctly.")
    else:
        print(f"FAILURE: Cart not empty. Total items: {final_cart['totalItems']}")

    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(verify_cart())
